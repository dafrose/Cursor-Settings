#!/usr/bin/env python3
"""Build per-locale msgid→msgstr maps for backport PO replay.

Supports:
- Two clean git refs (``--source-ref`` / ``--target-ref``), or
- A working-tree ``.po`` file that still contains git conflict markers.

Subcommands: ``build``, ``replay``, ``clean``.

Replay runs ``bench generate-pot-file`` / ``bench update-po-files`` then applies
saved maps in-process. **Run this script with** ``<bench-root>/env/bin/python``;
the interpreter is checked against the bench venv on startup. **polib** must be
installed there (see skill workflow); the script does not install dependencies.

If base and incoming both provide a different non-empty ``msgstr`` for the same
``msgid``, ``replay`` keeps the preferred side (``--prefer``) and prints an
**ambiguous translation** warning to stderr with both wordings for human or LLM review.

Unit test: ``test_po_branch_maps.py`` (fixture under ``fixtures/``); ``python3 -m unittest`` from this directory."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import TextIO

SCRIPT_DIR = Path(__file__).resolve().parent


def replay_maps_into_po_file(
	po_path: Path | str,
	source: dict[str, str],
	target: dict[str, str],
	*,
	prefer_base: bool,
	warn_to: TextIO | None = None,
) -> None:
	"""Apply *source* (incoming) and *target* (base) maps to a ``.po`` file using polib.

	When both sides have a non-empty, different ``msgstr`` for the same ``msgid``, the
	value from the preferred side is written and a warning is printed so a human or LLM
	can confirm or re-run with ``--prefer`` flipped.

	``prefer_base=True`` matches ``replay --prefer base`` (JSON ``target`` wins on ties).
	"""
	import polib

	out: TextIO = warn_to if warn_to is not None else sys.stderr
	po = polib.pofile(str(po_path))
	chosen_side = "base" if prefer_base else "incoming"

	for entry in po:
		if not entry.msgid:
			continue
		if isinstance(entry.msgid, (tuple, list)):
			continue
		mid = entry.msgid
		base_ok = mid in target and bool(target[mid].strip())
		inc_ok = mid in source and bool(source[mid].strip())
		if base_ok and inc_ok and source[mid] != target[mid]:
			other = "incoming" if prefer_base else "base"
			print(
				f"po_branch_maps.py: ambiguous translation for msgid;"
				f" kept {chosen_side} per --prefer {chosen_side}\n"
				f"  msgid: {mid!r}\n"
				f"  base (JSON target): {target[mid]!r}\n"
				f"  incoming (JSON source): {source[mid]!r}\n"
				f"  escalate: confirm wording and hand-edit resulting PO file if needed\n",
				file=out,
				flush=True,
			)
		if prefer_base:
			if mid in target and target[mid].strip():
				entry.msgstr = target[mid]
			elif mid in source:
				entry.msgstr = source[mid]
		else:
			if mid in source and source[mid].strip():
				entry.msgstr = source[mid]
			elif mid in target:
				entry.msgstr = target[mid]
		if entry.msgstr and getattr(entry, "fuzzy", False):
			entry.fuzzy = False
	po.save()


def _bench_env_python(bench_root: Path) -> Path:
	"""Return resolved ``env/bin/python`` (or ``python3``) under *bench_root*."""
	bin_dir = bench_root / "env" / "bin"
	for name in ("python", "python3"):
		p = bin_dir / name
		if p.is_file():
			return p.resolve()
	raise SystemExit(
		f"po_branch_maps.py replay: no venv interpreter at {bin_dir / 'python'} "
		f"(or python3). Is --bench-root correct?"
	)


def _require_same_interpreter_as_bench_venv(bench_root: Path) -> None:
	"""Fail if ``sys.executable`` is not the bench virtualenv Python."""
	bench_py = _bench_env_python(bench_root)
	current = Path(sys.executable).resolve()
	try:
		same = current == bench_py or current.samefile(bench_py)
	except OSError:
		same = current == bench_py
	if not same:
		script = Path(__file__).resolve()
		raise SystemExit(
			"po_branch_maps.py replay: run with the bench virtualenv Python so gettext and polib "
			"match this bench.\n"
			f"  expected: {bench_py}\n"
			f"  current:  {current}\n"
			f"  example:  {bench_py} {script} replay --bench-root {bench_root.resolve()} ..."
		)


def _require_polib_in_process() -> None:
	try:
		import polib  # noqa: F401
	except ImportError as e:
		raise SystemExit(
			"po_branch_maps.py replay: polib is required in the bench env.\n"
			f"  install: {sys.executable} -m pip install polib"
		) from e


def _run_git(repo: Path, *args: str) -> str:
	result = subprocess.run(
		["git", "-C", str(repo), *args],
		check=False,
		capture_output=True,
		text=True,
	)
	if result.returncode != 0:
		raise RuntimeError(result.stderr.strip() or f"git {' '.join(args)} failed")
	return result.stdout


def _unescape_po(s: str) -> str:
	out: list[str] = []
	i = 0
	while i < len(s):
		if s[i] == "\\" and i + 1 < len(s):
			nxt = s[i + 1]
			if nxt == "n":
				out.append("\n")
			elif nxt == "t":
				out.append("\t")
			elif nxt == '"':
				out.append('"')
			elif nxt == "\\":
				out.append("\\")
			else:
				out.append(nxt)
			i += 2
		else:
			out.append(s[i])
			i += 1
	return "".join(out)


def _read_po_string_line(line: str) -> str | None:
	line = line.strip()
	if not (line.startswith('"') and line.endswith('"')):
		return None
	return _unescape_po(line[1:-1])


def parse_po(text: str, *, non_empty_only: bool = True) -> dict[str, str]:
	"""Parse a PO file into msgid → msgstr (header entry excluded).

	Skips lines that look like conflict markers (so a partially conflicted file
	can still be parsed for the non-conflicted prefix—prefer ``split_conflicted_po``)."""
	entries: dict[str, str] = {}
	msgid_parts: list[str] = []
	msgstr_parts: list[str] = []
	state: str | None = None

	def flush() -> None:
		nonlocal msgid_parts, msgstr_parts, state
		if not msgid_parts:
			msgid_parts = []
			msgstr_parts = []
			state = None
			return
		msgid = "".join(msgid_parts)
		msgstr = "".join(msgstr_parts)
		if msgid and (not non_empty_only or msgstr.strip()):
			entries[msgid] = msgstr
		msgid_parts = []
		msgstr_parts = []
		state = None

	for line in text.splitlines():
		if line.startswith("<<<<<<<") or line.startswith("=======") or line.startswith(">>>>>>>"):
			continue
		if line.startswith("msgid "):
			flush()
			state = "msgid"
			part = _read_po_string_line(line[5:].strip())
			msgid_parts = [part] if part is not None else []
			if line.strip() == 'msgid ""':
				msgid_parts = []
			continue
		if line.startswith("msgstr "):
			state = "msgstr"
			part = _read_po_string_line(line[6:].strip())
			msgstr_parts = [part] if part is not None else []
			if line.strip() == 'msgstr ""':
				msgstr_parts = []
			continue
		if state and line.startswith('"'):
			part = _read_po_string_line(line)
			if part is not None:
				if state == "msgid":
					msgid_parts.append(part)
				else:
					msgstr_parts.append(part)

	flush()
	return entries


def split_conflicted_po(text: str) -> tuple[str, str]:
	"""Split a ``.po`` with git conflict markers into two synthetic PO bodies.

	For each ``<<<<<<< … ======= … >>>>>>>`` hunk, the first side (between
	``<<<<<<<`` and ``=======``) is *ours*; the second side is *theirs*.

	Raises:
		ValueError: unterminated conflict or stray ``=======`` / ``>>>>>>>``.
	"""
	lines = text.splitlines(keepends=True)
	out_ours: list[str] = []
	out_theirs: list[str] = []
	state = "normal"
	buf_ours: list[str] = []
	buf_theirs: list[str] = []

	for line in lines:
		if line.startswith("<<<<<<<"):
			if state != "normal":
				raise ValueError("nested or malformed conflict: saw <<<<<<< while inside a hunk")
			state = "ours"
			buf_ours = []
			continue
		if line.startswith("======="):
			if state != "ours":
				raise ValueError("malformed conflict: ======= without preceding <<<<<<<")
			state = "theirs"
			buf_theirs = []
			continue
		if line.startswith(">>>>>>>"):
			if state != "theirs":
				raise ValueError("malformed conflict: >>>>>>> without =======/theirs body")
			out_ours.extend(buf_ours)
			out_theirs.extend(buf_theirs)
			state = "normal"
			continue
		if state == "normal":
			out_ours.append(line)
			out_theirs.append(line)
		elif state == "ours":
			buf_ours.append(line)
		else:
			buf_theirs.append(line)

	if state != "normal":
		raise ValueError("unterminated conflict marker in PO file")
	return "".join(out_ours), "".join(out_theirs)


def _git_po_text(repo: Path, ref: str, po_path: str) -> str | None:
	spec = f"{ref}:{po_path}"
	try:
		return _run_git(repo, "show", spec)
	except RuntimeError:
		return None


def _list_po_files(repo: Path, locale_dir: str, source_ref: str, target_ref: str) -> list[str]:
	seen: set[str] = set()
	for ref in (source_ref, target_ref):
		try:
			out = _run_git(repo, "ls-tree", "-r", "--name-only", ref, "--", locale_dir)
		except RuntimeError:
			continue
		for line in out.splitlines():
			if line.endswith(".po"):
				seen.add(line)
	if seen:
		return sorted(seen)

	base = repo / locale_dir
	if base.is_dir():
		return sorted(str(p.relative_to(repo)) for p in base.glob("*.po"))
	return []


def _discover_conflicted_po(repo: Path, locale_dir: str) -> list[str]:
	rel = Path(locale_dir)
	base = repo / rel
	if not base.is_dir():
		return []
	out: list[str] = []
	for p in sorted(base.glob("*.po")):
		text = p.read_text(encoding="utf-8", errors="replace")
		if "<<<<<<<" in text:
			out.append(str(p.relative_to(repo)))
	return out


def _read_worktree_po(repo: Path, po_path: str) -> str:
	path = repo / po_path
	if not path.is_file():
		raise FileNotFoundError(f"Missing PO file: {path}")
	return path.read_text(encoding="utf-8", errors="strict")


def cmd_build(args: argparse.Namespace) -> int:
	repo = Path(args.repo).resolve()
	locale_dir = args.locale_dir.strip("/")
	out_dir = Path(args.out_dir).resolve()
	out_dir.mkdir(parents=True, exist_ok=True)

	use_refs = args.source_ref is not None and args.target_ref is not None
	use_conflict = bool(args.conflict_po) or bool(args.discover_conflicts)
	if use_refs == use_conflict:
		print("Specify either (--source-ref and --target-ref) or conflict mode (--conflict-po / --discover-conflicts)", file=sys.stderr)
		return 2

	po_paths: list[str]
	if use_refs:
		po_paths = _list_po_files(repo, locale_dir, args.source_ref, args.target_ref)
	else:
		po_paths = list(args.conflict_po or [])
		if args.discover_conflicts:
			po_paths.extend(_discover_conflicted_po(repo, locale_dir))
		po_paths = sorted(set(po_paths))
		if not po_paths:
			print("No conflicted .po files found.", file=sys.stderr)
			return 1

	written: list[Path] = []
	for po_path in po_paths:
		if not po_path.endswith(".po"):
			print(f"skip (not .po): {po_path}", file=sys.stderr)
			continue
		locale = Path(po_path).stem
		if use_refs:
			source_text = _git_po_text(repo, args.source_ref, po_path)
			target_text = _git_po_text(repo, args.target_ref, po_path)
			src_ref, tgt_ref = args.source_ref, args.target_ref
		else:
			raw = _read_worktree_po(repo, po_path)
			try:
				ours, theirs = split_conflicted_po(raw)
			except ValueError as e:
				print(f"{po_path}: {e}", file=sys.stderr)
				return 1
			# In merge: ours = first hunk; map PR side via --pr-maps
			if args.pr_maps_first_side == "source":
				source_text, target_text = ours, theirs
			else:
				source_text, target_text = theirs, ours
			src_ref = tgt_ref = f"working-tree:conflict:{po_path}"

		payload = {
			"locale": locale,
			"po_path": po_path,
			"source_ref": src_ref,
			"target_ref": tgt_ref,
			"source": parse_po(source_text or "", non_empty_only=args.non_empty_only),
			"target": parse_po(target_text or "", non_empty_only=args.non_empty_only),
		}
		if use_refs:
			if source_text is None:
				print(f"warning: missing {args.source_ref}:{po_path}", file=sys.stderr)
			if target_text is None:
				print(f"warning: missing {args.target_ref}:{po_path}", file=sys.stderr)

		out_file = out_dir / f"{locale}.json"
		out_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
		written.append(out_file)

	print(f"Wrote {len(written)} map(s) to {out_dir}")
	for path in written:
		data = json.loads(path.read_text(encoding="utf-8"))
		print(f"  {path.name}: source={len(data['source'])} target={len(data['target'])} msgids")
	return 0


def _bench_executable(bench_root: Path) -> str:
	env_bench = bench_root / "env" / "bin" / "bench"
	if env_bench.is_file():
		return str(env_bench)
	return "bench"


def _run(cmd: list[str], *, cwd: Path | None = None) -> None:
	print("+", " ".join(cmd), file=sys.stderr)
	r = subprocess.run(cmd, cwd=str(cwd) if cwd else None, check=False)
	if r.returncode != 0:
		raise SystemExit(r.returncode)


def cmd_replay(args: argparse.Namespace) -> int:
	repo = Path(args.repo).resolve()
	bench = Path(args.bench_root).resolve()
	app = args.app
	_require_same_interpreter_as_bench_venv(bench)
	_require_polib_in_process()
	if args.source_first:
		print(
			"po_branch_maps.py: warning: --source-first is deprecated; use --prefer incoming",
			file=sys.stderr,
		)
	prefer_incoming = args.prefer == "incoming" or args.source_first
	# JSON ``target`` = base branch; ``source`` = incoming. Prefer base = apply target first.
	target_first = not prefer_incoming

	maps_dir = Path(args.maps_dir).resolve()
	json_files = sorted(maps_dir.glob("*.json"))
	if args.locales:
		allowed = {x.strip() for x in args.locales.split(",") if x.strip()}
		json_files = [p for p in json_files if p.stem in allowed]
	if not json_files:
		print(f"No map JSON files in {maps_dir}", file=sys.stderr)
		return 1

	bexe = _bench_executable(bench)
	if not args.skip_generate:
		_run([bexe, "generate-pot-file", "--app", app], cwd=bench)
		for jf in json_files:
			loc = jf.stem
			_run([bexe, "update-po-files", "--app", app, "--locale", loc], cwd=bench)

	for jf in json_files:
		data = json.loads(jf.read_text(encoding="utf-8"))
		rel_po = data.get("po_path")
		if not rel_po:
			print(f"{jf.name}: missing po_path in JSON", file=sys.stderr)
			return 1
		po_file = repo / rel_po
		if not po_file.is_file():
			print(f"{jf.name}: PO not found at {po_file} (run generate from app repo?)", file=sys.stderr)
			return 1

		source_map = data.get("source") or {}
		target_map = data.get("target") or {}
		if not isinstance(source_map, dict) or not isinstance(target_map, dict):
			print(f"{jf.name}: invalid source/target in JSON", file=sys.stderr)
			return 1

		print(f"Replay {jf.stem}: {po_file}", file=sys.stderr)
		replay_maps_into_po_file(
			po_file,
			source_map,
			target_map,
			prefer_base=target_first,
		)

	if not args.skip_compile:
		for jf in json_files:
			loc = jf.stem
			_run([bexe, "compile-po-to-mo", "--app", app, "--locale", loc], cwd=bench)

	return 0


def cmd_clean(args: argparse.Namespace) -> int:
	out_dir = Path(args.out_dir).resolve()
	if not out_dir.exists():
		print(f"Nothing to clean: {out_dir} does not exist")
		return 0

	removed = 0
	for path in out_dir.glob("*.json"):
		path.unlink()
		removed += 1
	if removed:
		print(f"Removed {removed} file(s) from {out_dir}")
	try:
		out_dir.rmdir()
	except OSError:
		pass
	return 0


def main() -> int:
	parser = argparse.ArgumentParser(
		description="PO msgid maps + optional bench regenerate + replay.",
	)
	sub = parser.add_subparsers(dest="command", required=True)

	build = sub.add_parser("build", help="Write one JSON map per locale .po")
	build.add_argument(
		"--repo",
		type=Path,
		default=Path("."),
		help="Git repository root (default: current directory)",
	)
	build.add_argument(
		"--locale-dir",
		required=True,
		help="Locale dir relative to repo (e.g. eu_einvoice/locale)",
	)
	build.add_argument(
		"--source-ref",
		default=None,
		help="Git ref: incoming side (PR / feature branch) translations → JSON key ``source``",
	)
	build.add_argument(
		"--target-ref",
		default=None,
		help="Git ref: base side (integration / target branch) translations → JSON key ``target``",
	)
	build.add_argument(
		"--conflict-po",
		action="append",
		default=[],
		metavar="REL_PATH",
		help="Working-tree .po with conflict markers (repeatable)",
	)
	build.add_argument(
		"--discover-conflicts",
		action="store_true",
		help='Scan --locale-dir for *.po files that contain "<<<<<<<" conflict markers',
	)
	build.add_argument(
		"--pr-maps-first-side",
		choices=("source", "target"),
		default="source",
		help=(
			"For conflict hunks: first side (<<<<<<< … =======) maps to this JSON key. "
			"``source`` = incoming; ``target`` = base. Typical merge into PR: first side is your branch → "
			"--pr-maps-first-side source. Rebase onto base: first side may be base → use target."
		),
	)
	build.add_argument("--out-dir", type=Path, required=True, help="Output directory for <locale>.json")
	build.add_argument(
		"--include-empty",
		action="store_true",
		help="Include entries with empty msgstr",
	)
	build.set_defaults(func=cmd_build, non_empty_only=True)

	replay = sub.add_parser(
		"replay",
		help="Regenerate POT/PO via bench then replay maps into .po files "
		"(must run this script with <bench-root>/env/bin/python)",
	)
	replay.add_argument("--repo", type=Path, required=True, help="App git repo root (contains locale/)")
	replay.add_argument("--bench-root", type=Path, required=True, help="Bench directory (sites/, apps/)")
	replay.add_argument("--app", required=True, help="App name on bench")
	replay.add_argument("--maps-dir", type=Path, required=True, help="Directory with build output *.json")
	replay.add_argument(
		"--locales",
		default="",
		help="Comma-separated locale stems (default: all *.json in maps-dir)",
	)
	replay.add_argument(
		"--prefer",
		choices=("base", "incoming"),
		default="base",
		help=(
			"When both base and incoming maps have a non-empty msgstr for the same msgid: "
			"which wins. ``base`` uses JSON ``target`` (--target-ref / second conflict side per build flags); "
			"``incoming`` uses JSON ``source``. Default: base (original integration branch, then overlay incoming)."
		),
	)
	replay.add_argument(
		"--source-first",
		action="store_true",
		help=argparse.SUPPRESS,
	)
	replay.add_argument(
		"--skip-generate",
		action="store_true",
		help="Only replay into existing .po (no bench generate-pot-file / update-po-files)",
	)
	replay.add_argument(
		"--skip-compile",
		action="store_true",
		help="Skip bench compile-po-to-mo after replay",
	)
	replay.set_defaults(func=cmd_replay)

	clean = sub.add_parser("clean", help="Remove temporary map JSON files")
	clean.add_argument("--out-dir", type=Path, required=True)
	clean.set_defaults(func=cmd_clean)

	args = parser.parse_args()

	if args.command == "build" and args.include_empty:
		args.non_empty_only = False

	return args.func(args)


if __name__ == "__main__":
	raise SystemExit(main())
