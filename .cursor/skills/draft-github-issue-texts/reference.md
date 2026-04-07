# draft-github-issue-texts — reference

## Rewrite offline sources → issue-safe text

| Offline source | In the issue, write instead |
| -------------- | --------------------------- |
| `[[Spike PDF-A-3 annex embed]]` | Inlined pipeline: plain PDF → PDF/A-3 → `facturx.generate_from_binary(...)` |
| `notes/decisions/Keep Ghostscript…` | “Decision: keep Ghostscript; pdftopdfa evaluated at https://github.com/iRedPaul/pdftopdfa” |
| `bench --site dev.local execute my_app.scripts.spike_pdfa3_annex` | Omit unless script is **merged** on default branch; then blob URL + one-line purpose |
| “Step 12 PASS, 7/11 checks” | “On a sample EN 16931 invoice, veraPDF PDF/A-3b passed after plain → PDF/A-3 → factur-x embed” |
| `owner/repo#issue-42` | `https://github.com/<owner>/<repo>/issues/42` |

## Bad vs good excerpts

### Bad (depends on offline context)

```markdown
See [[PDF annex embedding approaches]] and spike step 12.
Run `bench --site dev.local execute my_app.scripts.spike_pdfa3_annex.run`.
Blocked per [[Embed annexes before attach xml to pdf]].
```

### Good (self-contained)

```markdown
**PDF pipeline (ZUGFeRD / EN 16931):**

1. Plain print PDF bytes
2. Convert to PDF/A-3 once (Ghostscript when `gs` is on PATH)
3. `facturx.generate_from_binary(pdfa_plain, xml, attachments={…})` for invoice XML and N annexes

Do not run Ghostscript on a PDF that already has embedded files — conversion strips user annexes.

**References**

- Parent: https://github.com/<owner>/<repo>/issues/42
- pdftopdfa (evaluated, not adopted): https://github.com/iRedPaul/pdftopdfa
- Factur-X overview: https://www.ferd-net.de/standards/zugferd
```

### Bad (vague external ref)

```markdown
Must comply with XRechnung chapter 8.2.
```

### Good (cited external ref)

```markdown
MIME types must match XRechnung §8.2 Binary Object (allowed Mime Code values for embedded attachments):
https://xeinkauf.de/xrechnung/ (see specification PDF, section 8.2).
```

## References section template

```markdown
## References

- [parent-repo#42](https://github.com/<owner>/<repo>/issues/42) — parent feature
- [OZG-RE attachment FAQ](https://e-rechnung-bund.de/faq/wie-konnen-rechnungsbegrundende-unterlagen-bzw-anlagen-in-einer-e-rechnung-an-die-ozg-re-mitgegeben-werden/) — 15 MB / 200 files embed limits
- [`attach_xml_to_pdf`](https://github.com/<owner>/<repo>/blob/<default-branch>/<app_package>/custom/sales_invoice.py) — current PDF/XML embed entry point
```

Use `blob/<branch>/` only when the path exists on that branch; otherwise cite path as text without a broken link.

## When user insists on mentioning a spike

Inline **outcomes**, not the spike artefact:

- What was compared  
- What passed/failed and **why** (one sentence each)  
- **Production decision**  

Optional: “Regression script may be added in a follow-up PR” — do not require an unmerged script to implement the issue.

## Repo template reminder

If the target repo ships a feature-request template (e.g. four GitHub form sections), keep its structure — do not remove boilerplate unless asked.

## PR bodies

The same self-contained and no-offline-reference rules apply to PR descriptions; link the implementing issue with full URL.
