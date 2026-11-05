#!/usr/bin/env python3
"""Synthetic local media integration tests; never connect to a product or speech service."""
import contextlib
import io
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import compose
import verify


class CompositionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(prefix="product-video's fixture ")
        cls.root = Path(cls.temporary.name)
        for folder in ("plans", "edits", "audio", "media", "outputs"):
            (cls.root / folder).mkdir()
        cls.ffmpeg = compose.executable("ffmpeg")
        cls.ffprobe = compose.executable("ffprobe")
        cls.raw = cls.root / "media/source clip.mp4"
        cls.wav = cls.root / "audio/spoken fixture.wav"
        compose.run([cls.ffmpeg, "-v", "error", "-f", "lavfi", "-i", "testsrc2=size=320x180:rate=12:duration=6", "-c:v", "libx264", "-pix_fmt", "yuv420p", cls.raw])
        compose.run([cls.ffmpeg, "-v", "error", "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=48000:duration=2", "-c:a", "pcm_s16le", cls.wav])
        cls.plan_path = cls.root / "plans/plan.json"
        cls.edit_path = cls.root / "edits/edit.json"
        cls.audio_path = cls.root / "audio/manifest.json"
        cls.plan = {"video": {"width": 320, "height": 180, "caption_band": 100, "fps": 12}, "chapters": [
            {"id": "one", "title": "查看结果", "narration": "查看结果。", "persistent_label": "演示数据"},
            {"id": "two", "title": "编辑代码", "narration": "编辑代码。"}]}
        cls.edits = {"one": {"segments": [{"path": "../media/source clip.mp4", "start": 0, "end": 1}, {"path": "../media/source clip.mp4", "start": 2, "end": 3, "crop": {"x": 20, "y": 10, "width": 280, "height": 160}}]}, "two": {"segments": [{"path": "../media/source clip.mp4", "start": 0, "end": 5}], "fit_to_voice": True}}
        compose.write_json(cls.plan_path, cls.plan)
        compose.write_json(cls.edit_path, cls.edits)
        cls.audio = {"status": "complete", "plan_sha256": compose.sha(cls.plan_path), "chapters": [{"id": c["id"], "display_text": c["narration"], "wav_file": "spoken fixture.wav", "wav_sha256": compose.sha(cls.wav), "captions": [{"start_seconds": 0.1, "end_seconds": 1.8, "text": c["narration"]}]} for c in cls.plan["chapters"]]}
        compose.write_json(cls.audio_path, cls.audio)
        cls.output = cls.root / "outputs/result.mp4"
        cls.work = cls.root / "cache work"
        with contextlib.redirect_stdout(io.StringIO()):
            compose.main(cls.arguments(cls.output))
        cls.manifest = cls.output.with_suffix(".manifest.json")

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    @classmethod
    def arguments(cls, output, **overrides):
        return ["--plan", str(overrides.get("plan", cls.plan_path)), "--edit", str(overrides.get("edit", cls.edit_path)), "--audio-manifest", str(overrides.get("audio", cls.audio_path)), "--output", str(output), "--work", str(overrides.get("work", cls.work))]

    def test_full_decode_chapters_cjk_captions_and_relative_paths(self):
        report = verify.check(self.manifest, self.ffmpeg, self.ffprobe, self.root / "review frames")
        self.assertEqual(report["status"], "mechanical-checks-passed")
        self.assertEqual(report["chapter_count"], 2)
        self.assertEqual(report["visual_review"], "pending")
        self.assertEqual(len(report["review_frames"]), 2)
        value = compose.read_json(self.manifest)
        self.assertEqual(value["chapters"][0]["captions"][0]["start"], 0.55)
        self.assertEqual(value["chapters"][0]["label"], "演示数据")
        self.assertGreater(value["chapters"][1]["global_speed"], 1)

    def test_final_output_is_preserved_without_overwrite(self):
        before = compose.sha(self.output)
        with self.assertRaisesRegex(compose.ValidationError, "already exist"):
            compose.main(self.arguments(self.output))
        self.assertEqual(before, compose.sha(self.output))

    def test_cache_uses_actual_encoded_hash(self):
        chapter = self.work / "one/chapter.mp4"
        original = chapter.read_bytes()
        chapter.write_bytes(b"broken cache")
        try:
            target = self.root / "outputs/cache-check.mp4"
            with contextlib.redirect_stdout(io.StringIO()):
                compose.main(self.arguments(target))
            value = compose.read_json(target.with_suffix(".manifest.json"))
            self.assertFalse(value["chapters"][0]["cache_reused"])
            self.assertTrue(value["chapters"][1]["cache_reused"])
            self.assertNotEqual(chapter.read_bytes(), b"broken cache")
        finally:
            # The fresh encoded output is deterministic in this fixture; preserve initial manifest evidence.
            chapter.write_bytes(original)

    def test_stale_success_is_replaced_by_failure_on_source_change(self):
        report_path = self.root / "outputs/readback.json"
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(verify.main(["--manifest", str(self.manifest), "--report", str(report_path)]), 0)
        original = self.raw.read_bytes()
        self.raw.write_bytes(original + b"changed")
        try:
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(verify.main(["--manifest", str(self.manifest), "--report", str(report_path)]), 1)
            self.assertEqual(compose.read_json(report_path)["status"], "failed")
        finally:
            self.raw.write_bytes(original)

    def test_text_overlap_media_boundary_and_label_fail_closed(self):
        mutations = [
            ("audio", lambda data: data["chapters"][0].update(display_text="不同文本"), "display_text"),
            ("audio", lambda data: data["chapters"][0].update(captions=[{"start_seconds": 0, "end_seconds": 1, "text": "查看"}, {"start_seconds": 0.9, "end_seconds": 1.8, "text": "结果。"}]), "overlap"),
            ("edit", lambda data: data["one"]["segments"][0].update(end=10), "trim exceeds"),
            ("edit", lambda data: data["one"]["segments"][1].update(crop=[300, 0, 100, 100]), "crop exceeds"),
            ("edit", lambda data: data["one"].update(label=""), "preserve persistent_label"),
        ]
        for index, (kind, mutation, expected) in enumerate(mutations):
            with self.subTest(kind=kind, expected=expected):
                source = self.audio if kind == "audio" else self.edits
                changed = json.loads(json.dumps(source))
                mutation(changed)
                path = (self.audio_path if kind == "audio" else self.edit_path).with_name(f"bad-{index}.json")
                compose.write_json(path, changed)
                with self.assertRaisesRegex(compose.ValidationError, expected):
                    compose.main(self.arguments(self.root / f"bad-{index}.mp4", **{kind: path}))

    def test_source_change_during_encode_prevents_final_manifest(self):
        original = self.raw.read_bytes()
        real_run = compose.run
        changed = False

        def mutate_after_encode(args, log=None):
            nonlocal changed
            result = real_run(args, log)
            if "-filter_complex_script" in args and not changed:
                self.raw.write_bytes(original + b"mid-encode-change")
                changed = True
            return result

        target = self.root / "outputs/concurrent.mp4"
        try:
            with patch.object(compose, "run", side_effect=mutate_after_encode), contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaisesRegex(compose.ValidationError, "Input changed"):
                    compose.main(self.arguments(target, work=self.root / "concurrent-work"))
            self.assertFalse(target.with_suffix(".manifest.json").exists())
            self.assertFalse(target.exists())
        finally:
            self.raw.write_bytes(original)

    def test_missing_font_fails_instead_of_substitution(self):
        with self.assertRaisesRegex(compose.ValidationError, "No existing font"):
            compose.main(self.arguments(self.root / "font.mp4") + ["--font", str(self.root / "missing.ttf")])

    def test_report_cannot_overwrite_sources(self):
        before = compose.sha(self.plan_path)
        with self.assertRaisesRegex(compose.ValidationError, "cannot overwrite"):
            verify.main(["--manifest", str(self.manifest), "--report", str(self.plan_path)])
        self.assertEqual(before, compose.sha(self.plan_path))

    def test_malformed_manifest_replaces_old_success_report(self):
        manifest = self.root / "outputs/malformed.json"
        report = self.root / "outputs/malformed-report.json"
        manifest.write_text("{broken", encoding="utf-8")
        compose.write_json(report, {"status": "mechanical-checks-passed"})
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(verify.main(["--manifest", str(manifest), "--report", str(report)]), 1)
        self.assertEqual(compose.read_json(report)["status"], "failed")


if __name__ == "__main__":
    unittest.main()
