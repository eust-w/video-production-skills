#!/usr/bin/env python3
"""Read-only keyword audit of a delivery directory or ZIP; not visual QA."""
import argparse
import codecs
import json
import os
from pathlib import Path
import stat
import sys
import zipfile

CHUNK = 1024 * 1024
ENCODINGS = ("utf-8", "utf-16le", "utf-16be")
ZIP_MAGIC = (b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08")
ARCHIVE_SUFFIXES = (".zip", ".tar", ".tgz", ".gz", ".bz2", ".xz", ".7z", ".rar", ".zst")


class Audit:
    def __init__(self, terms, entry_limit, total_limit, file_limit, report):
        self.terms = terms
        self.folded = {t: t.casefold() for t in terms}
        self.patterns = {t: [t.encode(e) for e in ENCODINGS] for t in terms}
        self.byte_tail = max(len(p) for ps in self.patterns.values() for p in ps) - 1
        self.text_tail = max(len(v) for v in self.folded.values()) - 1
        self.entry_limit, self.total_limit, self.file_limit = entry_limit, total_limit, file_limit
        self.report = report
        self.result = {"method": "keyword scan", "complete": True, "scannedFiles": 0,
                       "scannedBytes": 0, "hits": [], "skipped": [], "errors": [],
                       "excluded": [], "limitations": [
                           "Not OCR or visual/logo recognition; inspect actual encoded media separately.",
                           "Does not decompress image/media metadata or arbitrary embedded payloads.",
                           "Nested/encrypted archives, symlinks and resource-limit skips make the audit incomplete.",
                           "Byte limits allow one probe byte to detect a stream exceeding its declared size.",
                           "A keyword match is a review finding, not proof of a brand leak."]}
        self.seen_files = 0

    def skip(self, name, reason):
        self.result["complete"] = False
        self.result["skipped"].append({"path": name, "reason": reason})
        self.record_hits(name, self.filename_hits(name))

    def error(self, name, exc):
        self.result["complete"] = False
        self.result["errors"].append({"path": name, "error": type(exc).__name__})

    def filename_hits(self, name):
        return {t for t, folded in self.folded.items() if folded in name.casefold()}

    def allow_entry(self):
        if self.seen_files >= self.file_limit:
            self.skip(".", "entry-count limit reached; remaining entries not inspected")
            return False
        self.seen_files += 1
        return True

    def record_hits(self, name, found):
        if not found:
            return
        for hit in self.result["hits"]:
            if hit["path"] == name:
                hit["terms"] = sorted(set(hit["terms"]) | found)
                return
        self.result["hits"].append({"path": name, "terms": sorted(found)})

    def scan(self, stream, name, size):
        found = self.filename_hits(name)
        try:
            if size > self.entry_limit:
                self.skip(name, "per-file byte limit")
                return
            if size > self.total_limit - self.result["scannedBytes"]:
                self.skip(name, "total byte limit")
                return
            specs = [(e, offset) for e in ENCODINGS for offset in ([0] if e == "utf-8" else [0, 1])]
            decoders = [codecs.getincrementaldecoder(e)(errors="ignore") for e, _ in specs]
            tails = [""] * len(decoders)
            raw_tail, read = b"", 0
            while True:
                chunk = stream.read(min(CHUNK, self.entry_limit - read + 1,
                                        self.total_limit - self.result["scannedBytes"] + 1))
                if not chunk:
                    break
                read += len(chunk)
                self.result["scannedBytes"] += len(chunk)
                if read > self.entry_limit or self.result["scannedBytes"] > self.total_limit:
                    self.skip(name, "stream exceeded byte limit")
                    return
                if read == len(chunk) and (chunk[:4] in ZIP_MAGIC or name.lower().endswith(ARCHIVE_SUFFIXES)):
                    self.skip(name, "nested/unsupported archive not inspected")
                    return
                raw = raw_tail + chunk
                for term, patterns in self.patterns.items():
                    if any(p in raw for p in patterns):
                        found.add(term)
                raw_tail = raw[-self.byte_tail:] if self.byte_tail else b""
                for i, decoder in enumerate(decoders):
                    data = chunk[specs[i][1]:] if read == len(chunk) else chunk
                    text = tails[i] + decoder.decode(data).casefold()
                    found.update(t for t, folded in self.folded.items() if folded in text)
                    tails[i] = text[-self.text_tail:] if self.text_tail else ""
            self.result["scannedFiles"] += 1
        except (OSError, RuntimeError, EOFError, zipfile.BadZipFile, NotImplementedError) as exc:
            self.error(name, exc)
        finally:
            self.record_hits(name, found)

    def directory(self, root):
        def walk_error(exc):
            self.error(".", exc)
        for directory, dirs, files in os.walk(root, followlinks=False, onerror=walk_error):
            base = Path(directory)
            for d in list(dirs):
                if not self.allow_entry():
                    return
                path = base / d
                self.record_hits(path.relative_to(root).as_posix(), self.filename_hits(path.relative_to(root).as_posix()))
                if path.is_symlink():
                    self.skip(path.relative_to(root).as_posix(), "symlink directory")
                    dirs.remove(d)
            for f in sorted(files):
                path = base / f
                name = path.relative_to(root).as_posix()
                if not self.allow_entry():
                    return
                if path.is_symlink():
                    self.skip(name, "symlink file")
                    continue
                if self.report is not None and path.resolve() == self.report:
                    self.result["excluded"].append(name)
                    continue
                try:
                    if not stat.S_ISREG(path.stat().st_mode):
                        self.skip(name, "non-regular file")
                        continue
                    with path.open("rb") as stream:
                        self.scan(stream, name, path.stat().st_size)
                except OSError as exc:
                    self.error(name, exc)

    def archive(self, path):
        try:
            if path.stat().st_size > self.total_limit:
                self.skip(".", "input ZIP exceeds archive byte limit")
                return
            with zipfile.ZipFile(path) as archive:
                for index, entry in enumerate(archive.infolist()):
                    if not self.allow_entry():
                        return
                    name = entry.filename.replace("\\", "/")
                    if name.startswith("/") or ".." in name.split("/") or ":" in name.split("/")[0]:
                        self.skip("<entry %d>" % index, "unsafe/non-relative ZIP path")
                        continue
                    if entry.is_dir():
                        self.record_hits(name, self.filename_hits(name))
                        continue
                    mode = entry.external_attr >> 16
                    if stat.S_ISLNK(mode):
                        self.skip(name, "symlink ZIP entry")
                    elif entry.flag_bits & 1:
                        self.skip(name, "encrypted ZIP entry")
                    else:
                        try:
                            with archive.open(entry) as stream:
                                self.scan(stream, name, entry.file_size)
                        except (OSError, RuntimeError, zipfile.BadZipFile, NotImplementedError) as exc:
                            self.error(name, exc)
        except (OSError, zipfile.BadZipFile, NotImplementedError) as exc:
            self.error(".", exc)


def positive(value):
    number = int(value)
    if number <= 0:
        raise argparse.ArgumentTypeError("must be positive")
    return number


def main():
    parser = argparse.ArgumentParser(description=__doc__, epilog="Exit 0: complete/no hits; 1: hits; 2: incomplete/error (takes precedence).")
    parser.add_argument("input", type=Path, help="directory or one ZIP file; never extracted")
    parser.add_argument("--term", action="append", default=[], help="literal keyword; repeat as needed")
    parser.add_argument("--terms-file", type=Path, help="UTF-8 file with one keyword per nonempty line")
    parser.add_argument("--report", type=Path, help="optional JSON report path; the only output file written")
    parser.add_argument("--max-file-bytes", type=positive, default=128 * 1024 * 1024,
                        help="maximum bytes per file/ZIP entry (default: 128 MiB)")
    parser.add_argument("--max-total-bytes", type=positive, default=512 * 1024 * 1024,
                        help="read budget and maximum input ZIP size (default: 512 MiB)")
    parser.add_argument("--max-files", type=positive, default=10000,
                        help="maximum directory/archive entries, including folders (default: 10000)")
    args = parser.parse_args()
    try:
        terms = args.term + (args.terms_file.read_text(encoding="utf-8-sig").splitlines() if args.terms_file else [])
        terms = sorted({t.strip() for t in terms if t.strip()})
        if not terms:
            parser.error("provide --term or --terms-file; there are no built-in brand keywords")
        if max(map(len, terms)) > 4096:
            parser.error("keywords must be at most 4096 characters")
        report = args.report.resolve() if args.report else None
        if report is not None and report == args.input.resolve():
            parser.error("report must not overwrite the input")
        audit = Audit(terms, args.max_file_bytes, args.max_total_bytes, args.max_files, report)
        if args.input.is_symlink():
            audit.skip(".", "symlink input")
        elif args.input.is_dir():
            audit.directory(args.input)
        elif args.input.is_file() and zipfile.is_zipfile(args.input):
            audit.archive(args.input)
        else:
            audit.error(".", ValueError("input must be a directory or ZIP"))
        result = audit.result
        result["skippedCount"] = len(result["skipped"])
        result["errorCount"] = len(result["errors"])
        result["status"] = "incomplete" if not result["complete"] else "matches" if result["hits"] else "no_matches"
        encoded = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
        if report is not None:
            report.parent.mkdir(parents=True, exist_ok=True)
            report.write_text(encoded, encoding="utf-8")
        print(encoded, end="")
        return 2 if not result["complete"] else 1 if result["hits"] else 0
    except (OSError, UnicodeError, RuntimeError) as exc:
        print(json.dumps({"status": "error", "complete": False, "error": type(exc).__name__}))
        return 2


if __name__ == "__main__":
    sys.exit(main())
