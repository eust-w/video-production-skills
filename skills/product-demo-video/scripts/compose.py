#!/usr/bin/env python3
"""Compose recorded product footage and native timed narration. Run --help for the contract."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata

SCHEMA_VERSION = 1
VOICE_OFFSET = 0.45
STATUS = "assembled-pending-visual-review"
PRODUCER_SHA256 = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


class ValidationError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise ValidationError(message)


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ValidationError(f"Cannot read JSON: {path}") from error


def atomic_text(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".write-", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(text)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def write_json(path, value):
    atomic_text(path, json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def resolve_input(value, owner):
    require(isinstance(value, str) and bool(value), f"Expected a file path in {owner}")
    candidate = Path(value).expanduser()
    candidate = candidate if candidate.is_absolute() else Path(owner).parent / candidate
    candidate = candidate.resolve()
    require(candidate.is_file(), f"Input file is missing: {candidate}")
    return candidate


def number(value, label, minimum=None):
    require(isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value), f"{label} must be finite")
    require(minimum is None or value >= minimum, f"{label} must be >= {minimum}")
    return float(value)


def compact(text):
    return re.sub(r"\s+", "", unicodedata.normalize("NFC", text))


def run(args, log=None):
    result = subprocess.run([str(item) for item in args], capture_output=True, text=True)
    if log:
        atomic_text(log, result.stdout + result.stderr)
    if result.returncode:
        raise ValidationError(f"Command failed ({Path(str(args[0])).name}); " + (f"see {log}" if log else result.stderr[-1200:]))
    return result.stdout, result.stderr


def executable(value):
    found = shutil.which(value)
    require(found is not None, f"Required executable not found: {value}")
    return str(Path(found).resolve())


def probe(path, ffprobe):
    output, _ = run([ffprobe, "-v", "error", "-show_format", "-show_streams", "-show_chapters", "-of", "json", path])
    result = json.loads(output)
    require(float(result.get("format", {}).get("duration", 0)) > 0, f"Media has no positive duration: {path}")
    return result


def media_duration(info):
    return float(info["format"]["duration"])


def video_config(plan):
    raw = plan.get("video", {})
    require(isinstance(raw, dict), "plan.video must be an object")
    defaults = {"width": 1600, "height": 1000, "caption_band": 120, "fps": 30}
    value = {key: raw.get(key, default) for key, default in defaults.items()}
    for key in value:
        require(type(value[key]) is int, f"video.{key} must be an integer")
    require(320 <= value["width"] <= 7680 and 180 <= value["height"] <= 4320, "Video dimensions are outside supported bounds")
    require(80 <= value["caption_band"] <= 600, "caption_band must be 80..600 pixels")
    require(all(value[key] % 2 == 0 for key in ("width", "height", "caption_band")), "Video dimensions and caption_band must be even")
    require(1 <= value["fps"] <= 60, "fps must be 1..60")
    return value


def font_faces(path):
    try:
        from fontTools.ttLib import TTFont, TTCollection
    except ImportError as error:
        raise ValidationError("Install fonttools to validate font glyph coverage: python -m pip install fonttools") from error
    if Path(path).suffix.lower() in (".ttc", ".otc"):
        collection = TTCollection(str(path), lazy=True)
        try:
            return [{codepoint for codepoint, glyph in (font.getBestCmap() or {}).items() if glyph != ".notdef"} for font in collection.fonts]
        finally:
            collection.close()
    font = TTFont(str(path), lazy=True)
    try:
        return [{codepoint for codepoint, glyph in (font.getBestCmap() or {}).items() if glyph != ".notdef"}]
    finally:
        font.close()


def choose_font(explicit, font_index, texts):
    # A CJK sample is intentional even for a Latin-only plan: a default must support Chinese.
    needed = {ord(char) for char in "中文演示数据" + "".join(texts) if not char.isspace()}
    candidates = [Path(explicit).expanduser().resolve()] if explicit else [
        Path("/System/Library/Fonts/PingFang.ttc"),
        Path("/System/Library/Fonts/STHeiti Medium.ttc"),
        Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"),
        Path("/usr/share/fonts/truetype/noto/NotoSansSC-Regular.ttf"),
        Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts/msyh.ttc",
        Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts/simhei.ttf",
    ]
    if not explicit and shutil.which("fc-list"):
        listing, _ = run(["fc-list", ":lang=zh", "--format=%{file}\n"])
        candidates.extend(Path(line) for line in listing.splitlines() if line)
    for candidate in dict.fromkeys(candidates):
        if not candidate.is_file():
            continue
        try:
            faces = font_faces(candidate)
        except ValidationError:
            raise
        except Exception:
            continue
        indexes = [font_index] if font_index is not None else range(len(faces))
        for index in indexes:
            if 0 <= index < len(faces) and needed <= faces[index]:
                return candidate.resolve(), index
    raise ValidationError("No existing font covers Chinese and all supplied text. Install a CJK font or pass --font PATH [--font-index N].")


def snapshot(paths):
    return [{"path": str(path), "sha256": sha(path), "size_bytes": path.stat().st_size} for path in sorted(set(paths), key=str)]


def verify_snapshot(items):
    for item in items:
        path = Path(item["path"])
        require(path.is_file() and path.stat().st_size == item["size_bytes"] and sha(path) == item["sha256"], f"Input changed: {path}")


def prepare(plan_path, edit_path, audio_path, ffprobe, font=None, font_index=None):
    paths = [Path(path).expanduser().resolve() for path in (plan_path, edit_path, audio_path)]
    initial = snapshot(paths)
    plan, edits, audio = [read_json(path) for path in paths]
    require(isinstance(plan, dict) and isinstance(edits, dict) and isinstance(audio, dict), "Input JSON roots must be objects")
    require(audio.get("status", "complete") == "complete", "Audio manifest must be complete")
    if "plan_sha256" in audio:
        require(audio["plan_sha256"] == sha(paths[0]), "Audio manifest plan_sha256 does not match the current plan")
    chapters = plan.get("chapters")
    require(isinstance(chapters, list) and chapters, "plan.chapters must be nonempty")
    audio_rows = audio.get("chapters")
    require(isinstance(audio_rows, list), "audio-manifest.chapters must be an array")
    ids = [chapter.get("id") for chapter in chapters if isinstance(chapter, dict)]
    require(len(ids) == len(chapters) and all(isinstance(i, str) and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}", i) for i in ids), "Chapter IDs must be safe nonempty identifiers")
    require(len(set(ids)) == len(ids), "Duplicate plan chapter IDs")
    require(all(isinstance(row, dict) and isinstance(row.get("id"), str) for row in audio_rows), "Invalid audio chapter")
    audio_ids = [row["id"] for row in audio_rows]
    require(len(set(audio_ids)) == len(audio_ids) and set(audio_ids) == set(ids), "Audio chapter IDs must exactly match the plan")
    require(set(edits) == set(ids), "Edit chapter IDs must exactly match the plan")
    by_id = {row["id"]: row for row in audio_rows}
    files = paths[:]
    file_hashes = {}
    media = {}

    def inspect(path):
        if path not in media:
            file_hashes[path] = sha(path)
            media[path] = probe(path, ffprobe)
            require(sha(path) == file_hashes[path], f"Media changed while probing: {path}")
        return media[path]

    normalized = []
    texts = ["画面适度加速 ·"]
    for chapter in chapters:
        sid = chapter["id"]
        require(isinstance(chapter.get("title"), str) and chapter["title"].strip() and not re.search(r"[\x00-\x1f]", chapter["title"]), f"{sid}: invalid title")
        require(isinstance(chapter.get("narration"), str) and chapter["narration"].strip(), f"{sid}: narration is required")
        row = by_id[sid]
        require(row.get("display_text") == chapter["narration"], f"{sid}: display_text differs from narration")
        wav = resolve_input(row.get("wav_file"), paths[2])
        info = inspect(wav)
        require(any(stream.get("codec_type") == "audio" for stream in info["streams"]), f"{sid}: WAV has no audio stream")
        duration = media_duration(info)
        if "wav_sha256" in row:
            require(row["wav_sha256"] == file_hashes[wav], f"{sid}: WAV hash differs from audio manifest")
        captions = row.get("captions")
        require(isinstance(captions, list) and captions, f"{sid}: native captions are required")
        previous = 0.0
        checked_captions = []
        for caption in captions:
            require(isinstance(caption, dict) and isinstance(caption.get("text"), str) and caption["text"].strip(), f"{sid}: invalid caption")
            start = number(caption.get("start_seconds"), f"{sid}: caption start", 0)
            end = number(caption.get("end_seconds"), f"{sid}: caption end", 0)
            require(start >= previous and end > start and end <= duration + 0.04, f"{sid}: captions overlap or exceed audio")
            checked_captions.append({"text": caption["text"], "start": start + VOICE_OFFSET, "end": end + VOICE_OFFSET})
            previous = end
        require(compact("".join(item["text"] for item in captions)) == compact(chapter["narration"]), f"{sid}: caption text does not cover narration exactly")
        edit = edits[sid]
        require(isinstance(edit, dict), f"{sid}: edit must be an object")
        require(type(edit.get("fit_to_voice", False)) is bool, f"{sid}: fit_to_voice must be boolean")
        segments = edit.get("segments")
        require(isinstance(segments, list) and segments, f"{sid}: segments must be nonempty")
        checked_segments = []
        for segment in segments:
            require(isinstance(segment, dict), f"{sid}: invalid segment")
            path = resolve_input(segment.get("path"), paths[1])
            info = inspect(path)
            streams = [stream for stream in info["streams"] if stream.get("codec_type") == "video"]
            require(streams, f"{sid}: source has no video stream")
            start = number(segment.get("start"), f"{sid}: start", 0)
            end = number(segment.get("end"), f"{sid}: end", 0)
            speed = number(segment.get("speed", 1), f"{sid}: speed", 0.01)
            require(end > start and end <= media_duration(info) + 0.001, f"{sid}: trim exceeds source duration")
            crop = segment.get("crop")
            if isinstance(crop, dict):
                crop = [crop.get(key) for key in ("x", "y", "width", "height")]
            if crop is not None:
                require(isinstance(crop, list) and len(crop) == 4 and all(type(value) is int for value in crop), f"{sid}: crop must be [x,y,width,height] or an equivalent object")
                x, y, width, height = crop
                require(x >= 0 and y >= 0 and width > 0 and height > 0 and x + width <= streams[0]["width"] and y + height <= streams[0]["height"], f"{sid}: crop exceeds source dimensions")
            checked_segments.append({"path": str(path), "start": start, "end": end, "speed": speed, **({"crop": crop} if crop else {})})
            files.append(path)
        label = edit.get("label", chapter.get("persistent_label") or "")
        require(isinstance(label, str) and not re.search(r"[\x00-\x1f]", label), f"{sid}: label must be a single line")
        required_label = chapter.get("persistent_label") or ""
        require(isinstance(required_label, str), f"{sid}: persistent_label must be text")
        require(not required_label or required_label in label, f"{sid}: edit must preserve persistent_label")
        files.append(wav)
        texts.extend([chapter["title"], label, *[c["text"] for c in checked_captions]])
        normalized.append({"id": sid, "title": chapter["title"], "narration": chapter["narration"], "audio_path": str(wav), "audio_duration": duration, "captions": checked_captions, "segments": checked_segments, "label": label, "fit_to_voice": edit.get("fit_to_voice", False)})
    selected_font, selected_index = choose_font(font, font_index, texts)
    files.append(selected_font)
    inputs = snapshot(files)
    verify_snapshot(initial)
    for path, digest in file_hashes.items():
        require(sha(path) == digest, f"Media changed during preflight: {path}")
    return {"plan_path": str(paths[0]), "edit_path": str(paths[1]), "audio_manifest_path": str(paths[2]), "video": video_config(plan), "font": {"path": str(selected_font), "index": selected_index}, "chapters": normalized, "inputs": inputs}


def band_png(path, config, font_config, title, label, caption=""):
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError as error:
        raise ValidationError("Install Pillow: python -m pip install Pillow") from error
    width, band = config["width"], config["caption_band"]
    image = Image.new("RGBA", (width, band), (250, 249, 247, 255))
    draw = ImageDraw.Draw(image)
    margin = max(12, round(width * 0.018))
    font = lambda size: ImageFont.truetype(font_config["path"], size, index=font_config["index"])
    header_size = max(10, min(22, round(width * 0.013)))
    header_font = font(header_size)
    label_width = draw.textlength(label, font=header_font) if label else 0
    require(label_width < width * 0.48, "Persistent label is too wide for caption band")
    available = width - 3 * margin - label_width
    while draw.textlength(title, font=header_font) > available and header_size > 9:
        header_size -= 1
        header_font = font(header_size)
    require(draw.textlength(title, font=header_font) <= available, "Chapter title is too wide for caption band")
    header_height = max(27, round(band * 0.29))
    draw.line((0, 0, width, 0), fill="#e6e1e4", width=2)
    draw.text((margin, header_height / 2), title, font=header_font, fill="#503648", anchor="lm")
    if label:
        draw.text((width - margin, header_height / 2), label, font=font(max(10, min(22, round(width * 0.013)))), fill="#875a22", anchor="rm")
    if caption:
        size = max(14, min(34, round(width * 0.02)))
        while size >= 12:
            chosen = font(size)
            lines, line = [], ""
            for char in caption:
                if char == "\n" or (line and draw.textlength(line + char, font=chosen) > width - 2 * margin):
                    lines.append(line)
                    line = "" if char == "\n" else char
                else:
                    line += char
            if line:
                lines.append(line)
            line_height = math.ceil(size * 1.25)
            if len(lines) <= 2 and line_height * len(lines) <= band - header_height - 6:
                break
            size -= 1
        require(size >= 12, "Caption exceeds two readable lines; split the native caption before composing")
        y = header_height + (band - header_height - line_height * len(lines)) / 2
        for line in lines:
            draw.text((width / 2, y + line_height / 2), line, font=chosen, fill="#202027", anchor="mm")
            y += line_height
    image.save(path)


def loudness_measure(wav, ffmpeg, log):
    output, error = run([ffmpeg, "-hide_banner", "-nostdin", "-i", wav, "-vn", "-af", "aresample=48000,aformat=channel_layouts=mono,loudnorm=I=-18:TP=-1.5:LRA=7:print_format=json", "-f", "null", "-"], log)
    matches = re.findall(r'\{\s*"input_i"[\s\S]*?\}', output + error)
    require(matches, "Cannot measure narration loudness")
    value = json.loads(matches[-1])
    for key in ("input_i", "input_tp", "input_lra", "input_thresh", "target_offset"):
        require(math.isfinite(float(value[key])), "Narration is silent or has invalid loudness")
    return value


def encoded_media_checks(info, video):
    streams = info["streams"]
    videos = [s for s in streams if s.get("codec_type") == "video"]
    audios = [s for s in streams if s.get("codec_type") == "audio"]
    require(len(videos) == 1 and len(audios) == 1, "Expected exactly one video and one audio stream")
    require(videos[0].get("codec_name") == "h264" and videos[0]["width"] == video["width"] and videos[0]["height"] == video["height"] + video["caption_band"], "Encoded video codec or dimensions do not match")
    require(audios[0].get("codec_name") == "aac" and int(audios[0].get("sample_rate", 0)) == 48000 and audios[0].get("channels") == 1, "Encoded audio must be mono 48kHz AAC")
    num, den = videos[0]["r_frame_rate"].split("/")
    require(abs(float(num) / float(den) - video["fps"]) < 0.001, "Encoded nominal frame rate does not match")
    num, den = videos[0]["avg_frame_rate"].split("/")
    # MP4/AAC priming and concatenation can shift the aggregate duration by less than one frame.
    require(abs(float(num) / float(den) - video["fps"]) <= max(0.001, 1 / media_duration(info)), "Encoded average frame rate exceeds one-frame timing tolerance")


def compose_chapter(chapter, project, work, ffmpeg, ffprobe, tools_version, max_hold):
    require(sha(__file__) == PRODUCER_SHA256, "Composer changed during execution")
    video = project["video"]
    width, height, band, fps = (video[key] for key in ("width", "height", "caption_band", "fps"))
    folder = work / chapter["id"]
    folder.mkdir(parents=True, exist_ok=True)
    source_duration = sum((s["end"] - s["start"]) / s["speed"] for s in chapter["segments"])
    audio_duration = chapter["audio_duration"]
    speed = min(1.35, source_duration / (audio_duration + 2)) if chapter["fit_to_voice"] and source_duration > audio_duration + 2 else 1.0
    footage_duration = source_duration / speed
    target = math.ceil(max(footage_duration, audio_duration + 1.4) * fps) / fps
    hold = target - footage_duration
    require(max_hold is None or hold <= max_hold, f"{chapter['id']}: final hold {hold:.2f}s exceeds --max-hold")
    label = chapter["label"]
    if speed > 1.05 or any(s["speed"] > 1.05 for s in chapter["segments"]):
        label = " · ".join(filter(None, (label, "画面适度加速")))
    signature = hashlib.sha256(json.dumps({"chapter": chapter, "video": video, "font": project["font"], "inputs": project["inputs"], "producer": PRODUCER_SHA256, "tools": tools_version}, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    cache_path, output = folder / "cache.json", folder / "chapter.mp4"
    cached = read_json(cache_path) if cache_path.exists() else {}
    reuse = cached.get("signature") == signature and output.is_file() and cached.get("output_sha256") == sha(output)
    verify_snapshot(project["inputs"])
    if not reuse:
        base = folder / "band.png"
        band_png(base, video, project["font"], chapter["title"], label)
        pngs = []
        for index, caption in enumerate(chapter["captions"]):
            png = folder / f"caption-{index:03}.png"
            band_png(png, video, project["font"], chapter["title"], label, caption["text"])
            pngs.append(png)
        measurement = loudness_measure(chapter["audio_path"], ffmpeg, folder / "loudness.log")
        inputs = []
        for segment in chapter["segments"]:
            inputs.extend(["-i", segment["path"]])
        audio_index = len(chapter["segments"])
        inputs.extend(["-i", chapter["audio_path"]])
        band_index = audio_index + 1
        for image in [base, *pngs]:
            inputs.extend(["-loop", "1", "-framerate", str(fps), "-i", str(image)])
        filters = []
        for index, segment in enumerate(chapter["segments"]):
            crop = segment.get("crop")
            crop_filter = f"crop={crop[2]}:{crop[3]}:{crop[0]}:{crop[1]}:exact=1," if crop else ""
            filters.append(f"[{index}:v]trim=start={segment['start']}:end={segment['end']},setpts=(PTS-STARTPTS)/{segment['speed'] * speed:.9f},{crop_filter}scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:color=white,setsar=1,fps={fps},format=yuv420p[v{index}]")
        filters.append("".join(f"[v{i}]" for i in range(audio_index)) + f"concat=n={audio_index}:v=1:a=0[cut]")
        filters.append(f"[cut]tpad=stop_mode=clone:stop_duration={hold:.9f},pad={width}:{height + band}:0:0:color=white[canvas]")
        filters.append(f"[canvas][{band_index}:v]overlay=0:{height}:format=auto[b0]")
        previous = "b0"
        for index, caption in enumerate(chapter["captions"]):
            current = f"b{index+1}"
            filters.append(f"[{previous}][{band_index+index+1}:v]overlay=0:{height}:format=auto:enable='gte(t,{caption['start']:.9f})*lt(t,{caption['end']:.9f})'[{current}]")
            previous = current
        filters.append(f"[{previous}]format=yuv420p[vout]")
        norm = f"loudnorm=I=-18:TP=-1.5:LRA=7:measured_I={measurement['input_i']}:measured_TP={measurement['input_tp']}:measured_LRA={measurement['input_lra']}:measured_thresh={measurement['input_thresh']}:offset={measurement['target_offset']}:linear=true"
        filters.append(f"[{audio_index}:a]aresample=48000,aformat=channel_layouts=mono,{norm},aresample=48000,adelay=450:all=1,apad,atrim=duration={target:.9f}[aout]")
        filter_file = folder / "filters.txt"
        atomic_text(filter_file, ";\n".join(filters))
        temporary = folder / "chapter.partial.mp4"
        run([ffmpeg, "-hide_banner", "-nostdin", "-y", *inputs, "-filter_complex_script", filter_file, "-filter_complex_threads", "1", "-map", "[vout]", "-map", "[aout]", "-t", str(target), "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-threads", "2", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-ar", "48000", "-ac", "1", "-movflags", "+faststart", temporary], folder / "encode.log")
        verify_snapshot(project["inputs"])
        require(sha(__file__) == PRODUCER_SHA256, "Composer changed during execution")
        encoded_media_checks(probe(temporary, ffprobe), video)
        os.replace(temporary, output)
        write_json(cache_path, {"signature": signature, "output_sha256": sha(output)})
    info = probe(output, ffprobe)
    encoded_media_checks(info, video)
    duration = media_duration(info)
    require(all(c["end"] <= duration for c in chapter["captions"]), f"{chapter['id']}: caption exceeds composed chapter")
    return {**chapter, "label": label, "path": str(output), "sha256": sha(output), "duration": duration, "global_speed": speed, "final_hold_seconds": hold, "cache_reused": reuse, "signature": signature}


def stamp(seconds):
    milliseconds = round(seconds * 1000)
    hours, milliseconds = divmod(milliseconds, 3600000)
    minutes, milliseconds = divmod(milliseconds, 60000)
    whole, milliseconds = divmod(milliseconds, 1000)
    return f"{hours:02}:{minutes:02}:{whole:02},{milliseconds:03}"


def captions_srt(captions):
    return "\n\n".join(f"{index+1}\n{stamp(c['start'])} --> {stamp(c['end'])}\n{c['text']}" for index, c in enumerate(captions)) + "\n"


def metadata_escape(text):
    return re.sub(r"([\\=;#])", r"\\\1", text)


def parser():
    result = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter, epilog="Input paths inside edit and audio JSON are relative to that JSON file.\nplan: {chapters:[{id,title,narration,persistent_label?}], video?:{width,height,caption_band,fps}}\nedit: {ID:{segments:[{path,start,end,speed?,crop?:[x,y,w,h]}],label?,fit_to_voice?}}\naudio: {status?:complete,plan_sha256?,chapters:[{id,display_text,wav_file,wav_sha256?,captions:[{start_seconds,end_seconds,text}]}]}\nDependencies: ffmpeg, ffprobe, Pillow, fonttools. Output status always awaits human visual/audio review.")
    for name in ("plan", "edit", "audio-manifest", "output"):
        result.add_argument("--" + name, required=True)
    result.add_argument("--work", help="Separate cache/work directory; default OUTPUT_STEM.work")
    result.add_argument("--font", help="Existing font file; relative CLI paths use the current directory")
    result.add_argument("--font-index", type=int, help="TTC/OTC face index; otherwise choose a face covering the text")
    result.add_argument("--max-hold", type=float, help="Optional maximum final-frame hold in seconds; exceedance fails")
    result.add_argument("--overwrite", action="store_true", help="Explicitly replace final output/sidecars; archive the previous version first or prefer a new output name")
    result.add_argument("--ffmpeg", default="ffmpeg")
    result.add_argument("--ffprobe", default="ffprobe")
    return result


def main(argv=None):
    args = parser().parse_args(argv)
    ffmpeg, ffprobe = executable(args.ffmpeg), executable(args.ffprobe)
    require(args.max_hold is None or number(args.max_hold, "max-hold", 0) >= 0, "Invalid max-hold")
    require(args.font_index is None or args.font_index >= 0, "font-index must be nonnegative")
    project = prepare(args.plan, args.edit, args.audio_manifest, ffprobe, args.font, args.font_index)
    output = Path(args.output).expanduser().resolve()
    require(output.suffix.lower() == ".mp4", "--output must end in .mp4")
    work = Path(args.work).expanduser().resolve() if args.work else output.with_suffix(".work")
    generated = [output, output.with_suffix(".srt"), output.with_suffix(".manifest.json"), output.with_suffix(".chapters.txt")]
    require(args.overwrite or not any(path.exists() for path in generated), "Final output or sidecars already exist; use a new name, or archive them before --overwrite")
    for item in project["inputs"]:
        path = Path(item["path"])
        require(path not in generated and not path.is_relative_to(work), "Outputs/work must not overwrite or contain input files")
    require(not output.is_relative_to(work), "Final output must be outside --work")
    work.mkdir(parents=True, exist_ok=True)
    output.parent.mkdir(parents=True, exist_ok=True)
    version = run([ffmpeg, "-version"])[0].splitlines()[0]
    results = []
    for chapter in project["chapters"]:
        result = compose_chapter(chapter, project, work, ffmpeg, ffprobe, version, args.max_hold)
        results.append(result)
        print(json.dumps({"chapter": result["id"], "cache_reused": result["cache_reused"], "duration": result["duration"]}), flush=True)
    timeline, captions = 0.0, []
    for chapter in results:
        chapter["timeline_start"] = timeline
        chapter["timeline_end"] = timeline + chapter["duration"]
        captions.extend({"chapter_id": chapter["id"], "text": caption["text"], "start": timeline + caption["start"], "end": timeline + caption["end"]} for caption in chapter["captions"])
        timeline += chapter["duration"]
    concat = work / "concat.txt"
    atomic_text(concat, "".join("file '" + Path(chapter["path"]).as_posix().replace("'", "'\\''") + "'\n" for chapter in results))
    metadata = work / "chapters.ffmeta"
    atomic_text(metadata, ";FFMETADATA1\n" + "".join(f"[CHAPTER]\nTIMEBASE=1/1000\nSTART={round(c['timeline_start']*1000)}\nEND={round(c['timeline_end']*1000)}\ntitle={metadata_escape(c['title'])}\n" for c in results))
    verify_snapshot(project["inputs"])
    temporary = output.with_name("." + output.stem + ".partial.mp4")
    run([ffmpeg, "-hide_banner", "-nostdin", "-y", "-f", "concat", "-safe", "0", "-i", concat, "-i", metadata, "-map", "0:v:0", "-map", "0:a:0", "-map_metadata", "1", "-map_chapters", "1", "-c", "copy", "-movflags", "+faststart", temporary], work / "concat.log")
    info = probe(temporary, ffprobe)
    encoded_media_checks(info, project["video"])
    require(abs(media_duration(info) - timeline) < 0.15, "Final duration differs from chapter sum")
    verify_snapshot(project["inputs"])
    os.replace(temporary, output)
    srt, chapter_file = output.with_suffix(".srt"), output.with_suffix(".chapters.txt")
    atomic_text(srt, captions_srt(captions))
    atomic_text(chapter_file, "\n".join(f"{stamp(c['timeline_start']).replace(',', '.')} {c['title']}" for c in results) + "\n")
    manifest = {"schema_version": SCHEMA_VERSION, "status": STATUS, "visual_review": "pending", "listening_review": "pending", "producer": {"script_sha256": PRODUCER_SHA256, "ffmpeg": version}, "plan_path": project["plan_path"], "edit_path": project["edit_path"], "audio_manifest_path": project["audio_manifest_path"], "inputs": project["inputs"], "video": project["video"], "font": project["font"], "audio_processing": {"native_caption_offset_seconds": VOICE_OFFSET, "integrated_lufs_target": -18, "true_peak_dbtp_target": -1.5, "normalization": "two-pass loudnorm"}, "output": str(output), "sha256": sha(output), "duration": media_duration(info), "srt": {"path": str(srt), "sha256": sha(srt)}, "chapter_file": {"path": str(chapter_file), "sha256": sha(chapter_file)}, "chapters": results, "captions": captions}
    verify_snapshot(project["inputs"])
    require(sha(__file__) == PRODUCER_SHA256, "Composer changed during execution")
    destination = output.with_suffix(".manifest.json")
    write_json(destination, manifest)
    print(json.dumps({"status": STATUS, "output": str(output), "manifest": str(destination)}))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValidationError, OSError, KeyError, TypeError) as error:
        print(f"COMPOSE_FAILED: {error}", file=sys.stderr)
        raise SystemExit(1)
