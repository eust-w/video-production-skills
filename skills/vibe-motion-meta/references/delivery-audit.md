# Audit a package before sharing or removing branding

English | [简体中文](delivery-audit.zh-CN.md)

Use this procedure when the user requests branding removal, external sharing, packaging, or an explicit residue check. Inspect the actual files and package being delivered; conclusions do not extend to uninspected historical directories.

## Establish scope

Extract the names, aliases, old logos, channels, domains, internal paths, and personal details to remove or replace from the request. Do not hard-code a company or this project's term list. Preserve legitimate source attribution, third-party licenses, and AI content credentials; removing branding does not erase provenance.

If required third-party attribution contains a mark the user wants removed, prefer replacing the dependency/asset. If that is impossible, explain the specific conflict and remaining limitation. Retain required attribution and do not claim zero residue.

Check rendered text, actual visuals, and audio, then source code, unused functions shipped in the package, filenames, assets, image prompts, documents, runtime configuration, media metadata, and archive entries. After renaming, remeasure width and centering and inspect transition targets. Inspect the changed film, re-export, and rebuild the package from the latest files.

If public reproduction prompts remove identifiers or rewrite wording, label them “edited reproduction prompts,” not original generation records. Retain originals outside the delivery workspace. Use media-aware metadata tools; source search alone is insufficient.

## Optional read-only keyword helper

The bundled [audit_delivery.py](../scripts/audit_delivery.py) uses Python 3's standard library, with no network or third-party dependencies. It scans filenames and readable bytes in a directory or one ZIP, supports UTF-8, UTF-16LE/BE, and case folding, and streams ZIP contents without extracting them to disk. It does not delete, modify, or sanitize input files. It writes only a report when `--report` is supplied.

Replace these example paths and terms with the current project and user-specified list:

```bash
python3 scripts/audit_delivery.py /path/to/delivery --term 'old-product-name' --term 'old-brand'
python3 scripts/audit_delivery.py /path/to/delivery.zip --terms-file /path/to/terms.txt --report /path/to/audit.json
```

The script path is relative to this skill's root. `--terms-file` is UTF-8, with one literal term per nonempty line. Reports list relative paths, matched terms, and inspection status rather than potentially sensitive content excerpts. A report may itself contain old names; decide separately whether to share it.

- Exit `0`: complete scan, no matches for the supplied terms.
- Exit `1`: complete scan with matches requiring human interpretation.
- Exit `2`: incomplete inspection or error; takes precedence over match status. Inspect `skipped` and `errors`.

Defaults: 128 MiB per file, 512 MiB total read/input ZIP size, and 10,000 directory/archive entries. Adjust explicitly when needed. Symlinks, nested/unsupported archives, unsafe ZIP paths, encrypted entries, and over-limit content are recorded as uninspected; do not claim full coverage.

The helper does not recognize image logos, perform OCR, hear spoken names, or decode arbitrary embedded data or compressed media metadata. No matches describes only the specified scan scope and terms. Combine it with visual, listening, and metadata review before making a bounded conclusion.

## Final inspection

Inspect final ZIP entries and versions. Exclude stale exports, private assets, credentials, absolute personal paths, and unrelated projects. Deliver the requested playable video, editable source, required assets, and run instructions. A shared skill should contain reusable instructions, references, and necessary scripts rather than the current client's project.
