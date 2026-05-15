"""Single regression test for :mod:`po_branch_maps` conflict fixture.

Copies the reference PO to a temp file, splits conflict markers, parses both sides.
No external deps beyond stdlib.
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
FIXTURE = SCRIPT_DIR / "fixtures" / "conflicted_messages.po"

if str(SCRIPT_DIR) not in sys.path:
	sys.path.insert(0, str(SCRIPT_DIR))

from po_branch_maps import parse_po, split_conflicted_po  # noqa: E402


class PoBranchMapsTest(unittest.TestCase):
	def test_conflicted_fixture_on_temp_copy(self) -> None:
		with tempfile.NamedTemporaryFile(mode="w", suffix=".po", delete=False, encoding="utf-8") as f:
			f.write(FIXTURE.read_text(encoding="utf-8"))
			tmp = Path(f.name)
		try:
			head, incoming = split_conflicted_po(tmp.read_text(encoding="utf-8"))
			self.assertNotIn("<<<<<<<", head)
			self.assertNotIn("<<<<<<<", incoming)

			h = parse_po(head, non_empty_only=False)
			inc = parse_po(incoming, non_empty_only=False)

			self.assertEqual(h["Disputed label"], "Basis-Formulierung")
			self.assertEqual(inc["Disputed label"], "Anlieferungs-Formulierung")
			self.assertEqual(h["Agreed label"], inc["Agreed label"])
			self.assertEqual(h["Head-only extra"], "Nur in HEAD")
			self.assertEqual(inc.get("Head-only extra", "").strip(), "")
			self.assertEqual(inc["Incoming-only extra"], "Nur in incoming")
			self.assertEqual(h.get("Incoming-only extra", "").strip(), "")
		finally:
			tmp.unlink(missing_ok=True)


if __name__ == "__main__":
	unittest.main()
