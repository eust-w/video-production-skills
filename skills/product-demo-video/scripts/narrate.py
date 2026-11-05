#!/usr/bin/env python3
"""Validate a product narration plan; --generate explicitly enables online TTS.

--plan and --output are required except for --help/--self-test. Captions use
provider SentenceBoundary timestamps. Optional plan.pronunciations maps display
terms to their exact spoken forms; no pronunciation is guessed.
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import importlib
import importlib.metadata
import json
import math
from pathlib import Path
import re
import shutil
import sys
import tempfile
import wave

PROFILE = Path(__file__).resolve().parents[1] / "assets" / "voice-profile.json"
TICKS = 10_000_000
QUOTES = frozenset('“”‘’"\'')
SETTINGS = ("voice", "rate", "pitch", "volume")


def sha(path):
    value = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def write_json(path, value):
    path = Path(path)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def mappings(value):
    if value is None:
        return {}
    if not isinstance(value, dict) or any(not isinstance(k, str) or not k or k != k.strip()
            or not isinstance(v, str) or not v or v != v.strip() or "\n" in k + v for k, v in value.items()):
        raise ValueError("pronunciations must map non-empty single-line display terms to spoken forms")
    return value


def expand(text, pronunciation):
    """Return spoken text plus each spoken character's original display span."""
    if not pronunciation:
        return text, [(i, i + 1) for i in range(len(text))]
    def pattern(term):
        left = r"(?<![A-Za-z0-9_])" if re.match(r"[A-Za-z0-9_]", term[0]) else ""
        right = r"(?![A-Za-z0-9_])" if re.match(r"[A-Za-z0-9_]", term[-1]) else ""
        return left + re.escape(term) + right
    matcher = re.compile("|".join(pattern(k) for k in sorted(pronunciation, key=len, reverse=True)))
    parts, spans, cursor = [], [], 0
    for match in matcher.finditer(text):
        parts.append(text[cursor:match.start()])
        spans.extend((i, i + 1) for i in range(cursor, match.start()))
        spoken = pronunciation[match.group()]
        parts.append(spoken)
        spans.extend([(match.start(), match.end())] * len(spoken))
        cursor = match.end()
    parts.append(text[cursor:])
    spans.extend((i, i + 1) for i in range(cursor, len(text)))
    return "".join(parts), spans


def chapter_text(chapter, pronunciation):
    text = chapter.get("narration")
    if not isinstance(text, str) or not text.strip():
        raise ValueError(f"{chapter.get('id')}: narration is empty")
    display = text.strip()
    spoken, _ = expand(display, pronunciation)
    explicit = chapter.get("voice_text", chapter.get("pronunciation_script"))
    if explicit is not None and (not isinstance(explicit, str) or explicit.strip() != spoken):
        raise ValueError(f"{chapter.get('id')}: voice text differs from the declared pronunciation mapping")
    return display, spoken


def significant(text):
    return [(i, c) for i, c in enumerate(text) if not c.isspace() and c not in QUOTES]


def make_captions(events, display, pronunciation=None, audio_duration=None):
    if not events:
        raise ValueError("No service sentence boundaries; timing cannot be invented")
    spoken, spans = expand(display, pronunciation or {})
    positions = significant(spoken)
    expected = "".join(c for _, c in positions)
    logical, display_cursor, captions = 0, 0, []
    for index, event in enumerate(events):
        offset, length, reported = event.get("offset"), event.get("duration"), event.get("text")
        if event.get("type") != "SentenceBoundary" or any(isinstance(n, bool) or not isinstance(n, (int, float))
                or not math.isfinite(n) for n in (offset, length)) or offset < 0 or length <= 0:
            raise ValueError("Invalid service sentence timing")
        if not isinstance(reported, str) or not reported.strip():
            raise ValueError("Empty service sentence text")
        letters = "".join(c for _, c in significant(reported))
        if not letters or expected[logical:logical + len(letters)] != letters:
            raise ValueError("Service text does not match the complete spoken narration")
        logical += len(letters)
        source_end = spans[positions[logical - 1][0]][1]
        if logical < len(positions) and spans[positions[logical][0]][0] < source_end:
            raise ValueError("A sentence boundary splits a pronunciation mapping; revise that mapping")
        while source_end < len(display) and (display[source_end].isspace() or display[source_end] in '”’'):
            source_end += 1
        text = display[display_cursor:source_end]
        display_cursor = source_end
        start, end = offset / TICKS, (offset + length) / TICKS
        if captions and start <= captions[-1]["start_seconds"]:
            raise ValueError("Out-of-order service sentences")
        if captions and start < captions[-1]["end_seconds"]:
            overlap = captions[-1]["end_seconds"] - start
            if overlap > .2500001:
                raise ValueError("Service sentence overlap exceeds 250ms")
            captions[-1]["reported_end_seconds"] = captions[-1]["end_seconds"]
            captions[-1]["end_seconds"] = round(start, 7)
            captions[-1]["overlap_trimmed_seconds"] = round(overlap, 7)
        caption = {"index": index + 1, "start_seconds": round(start, 7), "end_seconds": round(end, 7),
                   "text": text, "source": "edge_tts.SentenceBoundary", "source_event_index": index}
        if reported != text:
            caption.update(reported_text=reported, text_alignment="original display text; declared pronunciations and omitted quotes aligned")
        if audio_duration is not None and end > audio_duration:
            if end - audio_duration > .08:
                raise ValueError("Service sentence exceeds actual audio duration")
            caption.update(reported_end_seconds=end, end_seconds=round(audio_duration, 7),
                           audio_end_trimmed_seconds=round(end - audio_duration, 7))
        if not text or round(caption["end_seconds"] * 1000) <= round(start * 1000):
            raise ValueError("Empty or sub-millisecond subtitle")
        captions.append(caption)
    if logical != len(expected) or display_cursor != len(display) or "".join(c["text"] for c in captions) != display:
        raise ValueError("Service boundaries do not cover the entire narration")
    return captions


def stamp(seconds):
    value = round(seconds * 1000)
    hours, value = divmod(value, 3_600_000)
    minutes, value = divmod(value, 60_000)
    secs, ms = divmod(value, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{ms:03d}"


def subtitles(captions):
    return "\n\n".join(f"{c['index']}\n{stamp(c['start_seconds'])} --> {stamp(c['end_seconds'])}\n{c['text']}" for c in captions) + "\n"


def load_plan(path):
    document = json.loads(Path(path).read_text(encoding="utf-8"))
    pronunciation = mappings(document.get("pronunciations"))
    chapters = document.get("chapters", document.get("scenes"))
    if not isinstance(chapters, list) or not chapters:
        raise ValueError("Plan needs a non-empty chapters array")
    seen, prepared = set(), []
    for chapter in chapters:
        if not isinstance(chapter, dict):
            raise ValueError("Each chapter must be an object")
        sid = chapter.get("id")
        if not isinstance(sid, str) or not re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]{0,40}", sid) or sid in seen:
            raise ValueError("Chapter IDs must be unique, safe identifiers")
        seen.add(sid)
        display, spoken = chapter_text(chapter, pronunciation)
        prepared.append({"id": sid, "title": chapter.get("title", sid), "display_text": display,
                         "speech_text": spoken, "pronunciations": pronunciation})
    return document, prepared


def profile(path, overrides):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    result = {key: overrides.get(key) or data.get(key) for key in SETTINGS}
    if not isinstance(result["voice"], str) or not result["voice"] or len(result["voice"]) > 160 or re.search(r"[\x00-\x1f]", result["voice"]):
        raise ValueError("Voice profile needs an exact online voice ID")
    for key, suffix in (("rate", "%"), ("pitch", "Hz"), ("volume", "%")):
        if not isinstance(result[key], str) or not re.fullmatch(r"[+-]\d+" + suffix, result[key]):
            raise ValueError(f"Invalid {key} in voice profile")
    return result


def paths(output, sid):
    return {ext: Path(output) / f"{sid}.{ext}" for ext in ("mp3", "wav", "srt", "json")}


def inspect_record(chapter, output, settings):
    """Return a reusable record only after checking current text, choice and files."""
    targets = paths(output, chapter["id"])
    if not any(p.exists() for p in targets.values()):
        return None, "missing"
    try:
        if any(not p.is_file() or p.is_symlink() for p in targets.values()):
            raise ValueError("missing or linked output")
        record = json.loads(targets["json"].read_text())
        if any(record.get(k) != chapter[k] for k in ("id", "display_text", "speech_text")) or any(record.get(k) != settings[k] for k in SETTINGS):
            raise ValueError("text or selected voice parameters changed")
        for ext in ("mp3", "wav"):
            if Path(record[f"{ext}_file"]).resolve() != targets[ext].resolve() or sha(targets[ext]) != record[f"{ext}_sha256"]:
                raise ValueError("audio path/hash mismatch")
        with wave.open(str(targets["wav"]), "rb") as audio:
            actual = audio.getnframes() / audio.getframerate()
            if (audio.getnchannels(), audio.getframerate(), audio.getsampwidth()) != (1, 48000, 2) or actual <= 0:
                raise ValueError("invalid WAV format")
        if abs(actual - record["duration_seconds"]) > 1e-6:
            raise ValueError("audio duration mismatch")
        captions = make_captions(record["raw_boundaries"], chapter["display_text"], chapter["pronunciations"], actual)
        if captions != record["captions"] or targets["srt"].read_text() != subtitles(captions):
            raise ValueError("caption coverage or timing changed")
        return {**record, "title": chapter["title"]}, "valid"
    except (OSError, ValueError, KeyError, TypeError, wave.Error, ZeroDivisionError):
        return None, "stale"


async def synthesize(chapter, output, settings, edge_tts, ffmpeg, plan_hash):
    sid = chapter["id"]
    targets = paths(output, sid)
    with tempfile.TemporaryDirectory(prefix=sid + "-", dir=output) as directory:
        temp = Path(directory)
        mp3, wav = temp / "speech.mp3", temp / "speech.wav"
        events = []
        speaker = edge_tts.Communicate(chapter["speech_text"], **settings, boundary="SentenceBoundary")
        with mp3.open("wb") as stream:
            async for chunk in speaker.stream():
                if chunk["type"] == "audio":
                    stream.write(chunk["data"])
                elif chunk["type"] == "SentenceBoundary":
                    events.append({key: chunk[key] for key in ("type", "offset", "duration", "text")})
        if not mp3.stat().st_size:
            raise ValueError("No audio received")
        process = await asyncio.create_subprocess_exec(ffmpeg, "-hide_banner", "-v", "error", "-y", "-i", str(mp3),
            "-ar", "48000", "-ac", "1", "-c:a", "pcm_s16le", str(wav), stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        try:
            _, stderr = await process.communicate()
        except asyncio.CancelledError:
            if process.returncode is None:
                process.kill()
            await process.wait()
            raise
        if process.returncode:
            raise ValueError("FFmpeg audio conversion failed")
        with wave.open(str(wav), "rb") as audio:
            duration = audio.getnframes() / audio.getframerate()
        captions = make_captions(events, chapter["display_text"], chapter["pronunciations"], duration)
        record = {**chapter, **settings, "engine": "Microsoft Edge online neural speech", "client": "edge-tts",
            "client_version": importlib.metadata.version("edge-tts"), "source_plan_sha256": plan_hash,
            "duration_seconds": round(duration, 7), "sample_rate": 48000, "channels": 1,
            "mp3_file": str(targets["mp3"]), "wav_file": str(targets["wav"]), "srt_file": str(targets["srt"]),
            "mp3_sha256": sha(mp3), "wav_sha256": sha(wav), "captions": captions, "raw_boundaries": events,
            "narration_complete": True, "timing_method": "service SentenceBoundary offsets; no equal time splits"}
        mp3.replace(targets["mp3"])
        wav.replace(targets["wav"])
        targets["srt"].write_text(subtitles(captions), encoding="utf-8")
        write_json(targets["json"], record)
        return record


async def generate(args, chapters, selected, settings, plan_hash):
    current = {c["id"]: inspect_record(c, args.output, settings) for c in chapters}
    jobs, reused = [], []
    for chapter in chapters:
        if chapter["id"] not in selected:
            continue
        record, state = current[chapter["id"]]
        if state == "valid" and args.resume:
            reused.append(chapter["id"])
        elif state != "missing" and not args.overwrite:
            raise ValueError(f"{chapter['id']}: existing output; use --resume for unchanged chapters or --overwrite for changed chapters")
        else:
            jobs.append(chapter)
    args.output.mkdir(parents=True, exist_ok=True)
    failures, generated = [], []
    if jobs:
        if not shutil.which(args.ffmpeg):
            raise ValueError("FFmpeg is unavailable")
        edge_tts = importlib.import_module("edge_tts")
        try:
            catalog = await asyncio.wait_for(edge_tts.list_voices(), min(args.timeout_seconds, 45))
            if settings["voice"] not in {v["ShortName"] for v in catalog}:
                raise ValueError("VOICE_UNAVAILABLE")
        except Exception as error:
            code = "VOICE_UNAVAILABLE" if str(error) == "VOICE_UNAVAILABLE" else type(error).__name__
            failures.extend({"id": c["id"], "error": code, "stage": "voice-catalog"} for c in jobs)
        else:
            semaphore = asyncio.Semaphore(args.concurrency)
            async def one(chapter):
                async with semaphore:
                    try:
                        await asyncio.wait_for(synthesize(chapter, args.output, settings, edge_tts, args.ffmpeg, plan_hash), args.timeout_seconds)
                        generated.append(chapter["id"])
                    except Exception as error:
                        failures.append({"id": chapter["id"], "error": type(error).__name__,
                                         "detail": str(error) if isinstance(error, ValueError) else "Online synthesis failed; no fallback voice used", "stage": "synthesis"})
            await asyncio.gather(*(one(c) for c in jobs))
    valid, unavailable = [], []
    failed_ids = {f["id"] for f in failures}
    for chapter in chapters:
        record, state = inspect_record(chapter, args.output, settings)
        if record is not None:
            valid.append(record)
        elif chapter["id"] not in failed_ids:
            unavailable.append({"id": chapter["id"], "error": state, "stage": "full-plan-coverage"})
    changed = sha(args.plan) != plan_hash
    manifest = {"schema_version": 1, "status": "plan-changed" if changed else "complete" if len(valid) == len(chapters) and not failures else "partial",
        "plan": str(args.plan), "plan_sha256": plan_hash, "plan_changed_during_generation": changed,
        **settings, "selected_chapters": sorted(selected), "generated_chapters": generated, "reused_chapters": reused,
        "chapters": valid, "failures": failures + unavailable, "total_audio_seconds": round(sum(c["duration_seconds"] for c in valid), 7),
        "caption_count": sum(len(c["captions"]) for c in valid), "caption_time_origin": "each audio file at t=0; add actual placement offset in composition"}
    write_json(args.output / "manifest.json", manifest)
    print(json.dumps({k: manifest[k] for k in ("status", "generated_chapters", "reused_chapters", "failures", "total_audio_seconds", "caption_count")}, ensure_ascii=False))
    return 0 if manifest["status"] == "complete" else 2


def self_test():
    pronunciation = {"NOVA": "N O V A"}
    text = '试用 NOVA：“查看结果。”下一步由你决定。'
    spoken, _ = expand(text, pronunciation)
    assert spoken == '试用 N O V A：“查看结果。”下一步由你决定。'
    events = [{"type": "SentenceBoundary", "offset": 1_000_000, "duration": 15_000_000, "text": '试用 N O V A：“查看结果。'},
              {"type": "SentenceBoundary", "offset": 15_500_000, "duration": 10_000_000, "text": '下一步由你决定。'}]
    cues = make_captions(events, text, pronunciation, 2.6)
    assert "".join(c["text"] for c in cues) == text and cues[0]["overlap_trimmed_seconds"] == .05
    assert expand("Do not guess NOVA.", {})[0] == "Do not guess NOVA."
    print("Offline self-test passed: explicit pronunciation, full coverage, quote restoration and native-time overlap handling")


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--voice-profile", type=Path, default=PROFILE)
    for setting in SETTINGS:
        parser.add_argument("--" + setting)
    parser.add_argument("--chapters", help="Comma-separated subset; manifest still covers the complete plan")
    parser.add_argument("--generate", action="store_true")
    parser.add_argument("--resume", action="store_true", help="Reuse only current, hash-verified chapters")
    parser.add_argument("--overwrite", action="store_true", help="Allow regeneration of changed/existing selected chapters")
    parser.add_argument("--timeout-seconds", type=float, default=180)
    parser.add_argument("--concurrency", type=int, choices=(1, 2), default=2)
    parser.add_argument("--ffmpeg", default="ffmpeg")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)
    if not args.self_test and (args.plan is None or args.output is None):
        parser.error("--plan and --output are explicitly required")
    if not math.isfinite(args.timeout_seconds) or args.timeout_seconds <= 0:
        parser.error("--timeout-seconds must be positive and finite")
    return args


async def main(argv=None):
    args = parse_args(argv)
    if args.self_test:
        self_test()
        return 0
    args.plan, args.output = args.plan.resolve(), args.output.resolve()
    settings = profile(args.voice_profile, vars(args))
    _, chapters = load_plan(args.plan)
    selected = set(args.chapters.split(",")) if args.chapters else {c["id"] for c in chapters}
    if not selected <= {c["id"] for c in chapters} or not selected:
        raise ValueError("Unknown/empty chapter selection")
    plan_hash = sha(args.plan)
    if not args.generate:
        print(json.dumps({"status": "validated-only-no-network", "plan": str(args.plan), "output": str(args.output),
            "plan_sha256": plan_hash, **settings, "chapters": chapters}, ensure_ascii=False, indent=2))
        return 0
    return await generate(args, chapters, selected, settings, plan_hash)


if __name__ == "__main__":
    try:
        raise SystemExit(asyncio.run(main()))
    except Exception as error:
        print(f"Narration failed: {type(error).__name__}: {error}", file=sys.stderr)
        raise SystemExit(1)
