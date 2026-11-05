#!/usr/bin/env python3
"""Verify current media, source hashes, native captions and chapters; human visual/listening review remains pending."""
from __future__ import annotations

import argparse
from pathlib import Path
import struct
import sys

import compose


def faststart(path):
    atoms = []
    size = Path(path).stat().st_size
    with Path(path).open("rb") as handle:
        while handle.tell() + 8 <= size:
            offset = handle.tell()
            length, kind = struct.unpack(">I4s", handle.read(8))
            header = 8
            if length == 1:
                compose.require(handle.tell() + 8 <= size, "Truncated MP4 atom")
                length = struct.unpack(">Q", handle.read(8))[0]
                header = 16
            elif length == 0:
                length = size - offset
            compose.require(length >= header and offset + length <= size, "Malformed MP4 atom size")
            atoms.append(kind)
            handle.seek(offset + length)
    compose.require(b"moov" in atoms and b"mdat" in atoms and atoms.index(b"moov") < atoms.index(b"mdat"), "MP4 is not faststart (moov must precede mdat)")


def check(manifest_path, ffmpeg, ffprobe, extract_dir=None):
    path = Path(manifest_path).expanduser().resolve()
    before = compose.sha(path)
    value = compose.read_json(path)
    compose.require(value.get("schema_version") == compose.SCHEMA_VERSION, "Unsupported manifest schema")
    compose.require(value.get("status") == compose.STATUS, "Manifest must describe an assembled result awaiting review")
    compose.require(value.get("visual_review") == "pending" and value.get("listening_review") == "pending", "Automated manifest must not claim human review")
    # File references in a manifest are relative to that manifest, just as all other JSON references are.
    resolve = lambda item: compose.resolve_input(item, path)
    inputs = [{**item, "path": str(resolve(item["path"]))} for item in value["inputs"]]
    compose.verify_snapshot(inputs)
    project = compose.prepare(resolve(value["plan_path"]), resolve(value["edit_path"]), resolve(value["audio_manifest_path"]), ffprobe, str(resolve(value["font"]["path"])), value["font"]["index"])
    compose.require(project["inputs"] == inputs, "Manifest input set/hash differs from the current source contract")
    compose.require(project["video"] == value["video"] and project["font"] == value["font"], "Video/font configuration differs from current sources")
    output = resolve(value["output"])
    compose.require(compose.sha(output) == value["sha256"], "Final video hash mismatch")
    srt = resolve(value["srt"]["path"])
    chapter_file = resolve(value["chapter_file"]["path"])
    compose.require(compose.sha(srt) == value["srt"]["sha256"], "SRT hash mismatch")
    compose.require(compose.sha(chapter_file) == value["chapter_file"]["sha256"], "Chapter-list hash mismatch")
    chapters = value.get("chapters")
    compose.require(isinstance(chapters, list) and [c["id"] for c in chapters] == [c["id"] for c in project["chapters"]], "Chapter order/IDs differ from plan")
    timeline = 0.0
    expected_captions = []
    for chapter, expected in zip(chapters, project["chapters"]):
        for key in ("id", "title", "narration", "audio_path", "audio_duration", "captions", "segments", "fit_to_voice"):
            compose.require(chapter[key] == expected[key], f"{chapter['id']}: {key} differs from current source")
        global_speed = compose.number(chapter["global_speed"], "global_speed", 1)
        source_duration = sum((s["end"] - s["start"]) / s["speed"] for s in expected["segments"])
        expected_speed = min(1.35, source_duration / (expected["audio_duration"] + 2)) if expected["fit_to_voice"] and source_duration > expected["audio_duration"] + 2 else 1.0
        compose.require(abs(global_speed - expected_speed) < 1e-8, "Unexpected chapter speed")
        label = expected["label"]
        if global_speed > 1.05 or any(s["speed"] > 1.05 for s in expected["segments"]):
            label = " · ".join(filter(None, (label, "画面适度加速")))
        compose.require(chapter["label"] == label, "Persistent label differs from source or speed disclosure")
        compose.require(abs(chapter["timeline_start"] - timeline) < 0.001, "Chapter timeline has gaps or overlaps")
        chapter_path = resolve(chapter["path"])
        compose.require(compose.sha(chapter_path) == chapter["sha256"], "Chapter video hash mismatch")
        info = compose.probe(chapter_path, ffprobe)
        compose.encoded_media_checks(info, value["video"])
        duration = compose.media_duration(info)
        compose.require(abs(duration - chapter["duration"]) < 0.002, "Chapter duration mismatch")
        compose.require(abs(chapter["timeline_end"] - (timeline + duration)) < 0.001, "Chapter end does not match duration")
        previous = 0.0
        for caption in chapter["captions"]:
            compose.require(previous <= caption["start"] < caption["end"] <= duration, "Native captions overlap or exceed chapter")
            expected_captions.append({"chapter_id": chapter["id"], "text": caption["text"], "start": timeline + caption["start"], "end": timeline + caption["end"]})
            previous = caption["end"]
        timeline += duration
    compose.require(value["captions"] == expected_captions, "Final captions differ from native source timings/text")
    compose.require(srt.read_text(encoding="utf-8") == compose.captions_srt(expected_captions), "SRT text or millisecond timing differs from manifest")
    expected_chapter_file = "\n".join(f"{compose.stamp(c['timeline_start']).replace(',', '.')} {c['title']}" for c in chapters) + "\n"
    compose.require(chapter_file.read_text(encoding="utf-8") == expected_chapter_file, "Chapter-list content differs from plan")
    previous_ms = 0
    for caption in expected_captions:
        start_ms, end_ms = round(caption["start"] * 1000), round(caption["end"] * 1000)
        compose.require(start_ms >= previous_ms and end_ms > start_ms and end_ms <= round(timeline * 1000), "Serialized SRT overlaps or is out of bounds")
        previous_ms = end_ms
    info = compose.probe(output, ffprobe)
    compose.encoded_media_checks(info, value["video"])
    duration = compose.media_duration(info)
    compose.require(abs(duration - value["duration"]) < 0.002 and abs(duration - timeline) < 0.15, "Final media duration is inconsistent")
    embedded = info.get("chapters", [])
    compose.require(len(embedded) == len(chapters), "Embedded chapter count is incorrect")
    for actual, expected in zip(embedded, chapters):
        compose.require(actual.get("tags", {}).get("title") == expected["title"], "Embedded chapter title differs")
        compose.require(abs(float(actual["start_time"]) - expected["timeline_start"]) < 0.003 and abs(float(actual["end_time"]) - expected["timeline_end"]) < 0.003, "Embedded chapter timing differs")
    faststart(output)
    # Decode both complete streams afresh. Prior test reports are deliberately not consulted.
    compose.run([ffmpeg, "-hide_banner", "-nostdin", "-v", "error", "-xerror", "-err_detect", "explode", "-i", output, "-map", "0:v:0", "-map", "0:a:0", "-f", "null", "-"])
    frames = []
    if extract_dir:
        directory = Path(extract_dir).expanduser().resolve()
        directory.mkdir(parents=True, exist_ok=True)
        for chapter in chapters:
            at = chapter["timeline_start"] + chapter["duration"] / 2
            destination = directory / f"{chapter['id']}.png"
            compose.require(not destination.exists(), f"Review frame already exists: {destination}; choose a new --extract-frames directory")
            compose.run([ffmpeg, "-hide_banner", "-nostdin", "-v", "error", "-ss", str(at), "-i", output, "-frames:v", "1", destination])
            frames.append({"chapter_id": chapter["id"], "at_seconds": at, "path": str(destination), "sha256": compose.sha(destination), "visual_review": "pending"})
    compose.verify_snapshot(inputs)
    compose.require(compose.sha(path) == before and compose.sha(output) == value["sha256"] and compose.sha(srt) == value["srt"]["sha256"] and compose.sha(chapter_file) == value["chapter_file"]["sha256"], "An artifact changed during verification")
    return {"schema_version": 1, "status": "mechanical-checks-passed", "manifest": str(path), "manifest_sha256": before, "output_sha256": value["sha256"], "duration": duration, "chapter_count": len(chapters), "caption_count": len(expected_captions), "checks": {"current_input_hashes": True, "source_contract": True, "full_audio_video_decode": True, "native_caption_text_and_timing": True, "nonoverlap_and_bounds": True, "embedded_chapters": True, "faststart": True}, "visual_review": "pending", "listening_review": "pending", "review_frames": frames}


def parser():
    result = argparse.ArgumentParser(description=__doc__, epilog="A passing report covers mechanical checks only. Review extracted frames and listen to the current output separately. A failed run overwrites its report with status=failed and returns nonzero.")
    result.add_argument("--manifest", required=True, help="The .manifest.json emitted by compose.py")
    result.add_argument("--report", help="Default: MANIFEST_STEM.verify.json")
    result.add_argument("--extract-frames", help="New directory for one review frame per chapter")
    result.add_argument("--ffmpeg", default="ffmpeg")
    result.add_argument("--ffprobe", default="ffprobe")
    return result


def main(argv=None):
    args = parser().parse_args(argv)
    manifest = Path(args.manifest).expanduser().resolve()
    report = Path(args.report).expanduser().resolve() if args.report else manifest.with_suffix(".verify.json")
    compose.require(report != manifest, "Report cannot overwrite its manifest")
    if manifest.is_file():
        try:
            existing = compose.read_json(manifest)
            compose.require(isinstance(existing, dict), "Manifest must be a JSON object")
        except Exception as error:
            compose.write_json(report, {"status": "failed", "manifest": str(manifest), "manifest_sha256": compose.sha(manifest), "error": str(error), "visual_review": "pending", "listening_review": "pending"})
            print(f"VERIFY_FAILED: {error}", file=sys.stderr)
            return 1
        protected = [existing.get("output"), existing.get("plan_path"), existing.get("edit_path"), existing.get("audio_manifest_path")]
        protected.extend(item.get("path") for item in existing.get("inputs", []) if isinstance(item, dict))
        protected.extend(item.get("path") for item in existing.get("chapters", []) if isinstance(item, dict))
        protected.extend(existing.get(key, {}).get("path") for key in ("srt", "chapter_file"))
        for item in protected:
            if isinstance(item, str):
                candidate = Path(item).expanduser()
                candidate = (candidate if candidate.is_absolute() else manifest.parent / candidate).resolve()
                compose.require(report != candidate, "Report cannot overwrite a source or output artifact")
    # Make stale success impossible even when this run fails before media probing.
    compose.write_json(report, {"status": "checking", "manifest": str(manifest), "visual_review": "pending", "listening_review": "pending"})
    try:
        result = check(manifest, compose.executable(args.ffmpeg), compose.executable(args.ffprobe), args.extract_frames)
    except Exception as error:
        compose.write_json(report, {"status": "failed", "manifest": str(manifest), "manifest_sha256": compose.sha(manifest) if manifest.is_file() else None, "error": str(error), "visual_review": "pending", "listening_review": "pending"})
        print(f"VERIFY_FAILED: {error}", file=sys.stderr)
        return 1
    compose.write_json(report, result)
    print(f"Mechanical checks passed; visual/listening review pending. Report: {report}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (compose.ValidationError, OSError, KeyError, TypeError) as error:
        print(f"VERIFY_FAILED: {error}", file=sys.stderr)
        raise SystemExit(1)
