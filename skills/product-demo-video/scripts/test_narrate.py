"""Offline regression checks for narration text, timing, cache and failure paths."""
import argparse
import asyncio
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import types
import unittest
from unittest.mock import AsyncMock, patch
import wave

SCRIPT = Path(__file__).with_name("narrate.py")
spec = importlib.util.spec_from_file_location("narrate", SCRIPT)
narrate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(narrate)
SETTINGS = {"voice": "zh-CN-XiaoxiaoNeural", "rate": "+0%", "pitch": "+0Hz", "volume": "+0%"}


def event(text, start=.1, end=.4):
    return {"type": "SentenceBoundary", "offset": round(start * narrate.TICKS),
            "duration": round((end - start) * narrate.TICKS), "text": text}


class TextAndTimingTests(unittest.TestCase):
    def test_no_implicit_pronunciation(self):
        self.assertEqual(narrate.chapter_text({"id": "A", "narration": "NOVA helps."}, {}), ("NOVA helps.", "NOVA helps."))
        with self.assertRaises(ValueError):
            narrate.chapter_text({"id": "A", "narration": "NOVA helps.", "voice_text": "N O V A helps."}, {})

    def test_declared_mapping_only_and_no_recursive_replacement(self):
        mapping = {"NOVA": "N O V A", "N O V A": "unexpected"}
        self.assertEqual(narrate.expand("NOVA 与 SUPERNOVA。", mapping)[0], "N O V A 与 SUPERNOVA。")
        self.assertEqual(narrate.chapter_text({"id": "A", "narration": "NOVA works.", "voice_text": "N O V A works."}, {"NOVA":"N O V A"})[1], "N O V A works.")
        with self.assertRaises(ValueError):
            narrate.chapter_text({"id":"A", "narration":"NOVA works.", "voice_text":"N O V A repairs everything."}, {"NOVA":"N O V A"})

    def test_original_display_quotes_and_native_timestamps(self):
        text = '试用 NOVA：“查看结果。”下一步由你决定。'
        events = [event('试用 N O V A：“查看结果。', .1, 1.6), event('下一步由你决定。', 1.55, 2.5)]
        cues = narrate.make_captions(events, text, {"NOVA":"N O V A"}, 2.6)
        self.assertEqual(''.join(c['text'] for c in cues), text)
        self.assertEqual(cues[0]['end_seconds'], 1.55)
        self.assertEqual(cues[0]['reported_end_seconds'], 1.6)
        self.assertEqual(cues[0]['overlap_trimmed_seconds'], .05)
        self.assertIn('00:00:01,550 --> 00:00:02,500', narrate.subtitles(cues))
        self.assertNotIn('N O V A', narrate.subtitles(cues))

    def test_missing_changed_or_split_words_are_rejected(self):
        for events, expected, mapping in [([], 'hello', {}), ([event('goodbye')], 'hello', {}),
                ([event('hello')], 'hello world', {}),
                ([event('N O', .1, .3),event('V A', .3, .5)], 'NOVA', {'NOVA':'N O V A'})]:
            with self.subTest(events=events), self.assertRaises(ValueError):
                narrate.make_captions(events, expected, mapping, 1)

    def test_invalid_timing_fails_closed(self):
        bad = [dict(event('a'), offset=-1), dict(event('a'), duration=float('nan')), dict(event('a'), offset=True)]
        for candidate in bad:
            with self.subTest(candidate=candidate), self.assertRaises(ValueError):
                narrate.make_captions([candidate], 'a', {}, 1)
        for events in [[event('a', .1, 1),event('b', .5, 1.2)], [event('a', .5, 1),event('b', .2, .4)]]:
            with self.assertRaises(ValueError):
                narrate.make_captions(events, 'ab', {}, 2)
        with self.assertRaises(ValueError):
            narrate.make_captions([event('a', .1, 2)], 'a', {}, 1)

    def test_help_and_self_test_need_no_site_packages(self):
        for flag in ('--help', '--self-test'):
            result = subprocess.run([sys.executable, '-S', str(SCRIPT), flag], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
        result = subprocess.run([sys.executable, '-S', str(SCRIPT)], capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('--plan and --output', result.stderr)


class ResumeTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.output = self.root / 'audio'
        self.output.mkdir()
        self.plan = self.root / 'plan.json'
        self.plan.write_text(json.dumps({'chapters':[{'id':'A','narration':'你好。'},{'id':'B','narration':'再见。'}]}))
        _, self.chapters = narrate.load_plan(self.plan)
        self.args = argparse.Namespace(output=self.output, plan=self.plan, resume=True, overwrite=False,
            ffmpeg='ffmpeg', timeout_seconds=5, concurrency=2)

    def tearDown(self):
        self.temp.cleanup()

    def record(self, chapter, settings=None):
        settings = settings or SETTINGS
        targets = narrate.paths(self.output, chapter['id'])
        targets['mp3'].write_bytes(b'explicit offline media fixture')
        with wave.open(str(targets['wav']), 'wb') as wav:
            wav.setnchannels(1); wav.setsampwidth(2); wav.setframerate(48000)
            wav.writeframes(b'\x01\x00' * 24000)
        events = [event(chapter['speech_text'])]
        cues = narrate.make_captions(events, chapter['display_text'], chapter['pronunciations'], .5)
        value = {**chapter, **settings, 'duration_seconds':.5, 'raw_boundaries':events, 'captions':cues,
                 'mp3_file':str(targets['mp3']), 'wav_file':str(targets['wav']),
                 'mp3_sha256':narrate.sha(targets['mp3']), 'wav_sha256':narrate.sha(targets['wav'])}
        targets['srt'].write_text(narrate.subtitles(cues));narrate.write_json(targets['json'],value)
        return value

    async def test_unchanged_resume_is_offline(self):
        for chapter in self.chapters: self.record(chapter)
        with patch.object(narrate.importlib,'import_module',side_effect=AssertionError('network module loaded')):
            code=await narrate.generate(self.args,self.chapters,{'A','B'},SETTINGS,narrate.sha(self.plan))
        self.assertEqual(code,0)
        result=json.loads((self.output/'manifest.json').read_text())
        self.assertEqual(result['reused_chapters'],['A','B'])
        self.assertEqual(result['status'],'complete')

    async def test_changed_chapter_needs_explicit_overwrite(self):
        self.record(self.chapters[0]);changed={**self.chapters[0],'display_text':'改变了。','speech_text':'改变了。'}
        with self.assertRaises(ValueError):
            await narrate.generate(self.args,[changed],{'A'},SETTINGS,narrate.sha(self.plan))

    async def test_overwrite_only_changes_stale_selected_chapter(self):
        for chapter in self.chapters:self.record(chapter)
        before={ext:narrate.sha(self.output/f'B.{ext}') for ext in ('mp3','wav','srt','json')}
        changed={**self.chapters[0],'display_text':'改变了。','speech_text':'改变了。'}
        self.args.overwrite=True
        fake=types.SimpleNamespace(list_voices=AsyncMock(return_value=[{'ShortName':SETTINGS['voice']}]))
        async def fake_synthesis(chapter,*args):return self.record(chapter)
        with patch.object(narrate.importlib,'import_module',return_value=fake),patch.object(narrate.shutil,'which',return_value='/fixture/ffmpeg'),patch.object(narrate,'synthesize',side_effect=fake_synthesis) as synthesis:
            code=await narrate.generate(self.args,[changed,self.chapters[1]],{'A','B'},SETTINGS,narrate.sha(self.plan))
        self.assertEqual(code,0);self.assertEqual(synthesis.call_count,1)
        self.assertEqual(before,{ext:narrate.sha(self.output/f'B.{ext}') for ext in before})

    async def test_subset_cannot_claim_complete_for_missing_chapter(self):
        self.record(self.chapters[0])
        code=await narrate.generate(self.args,self.chapters,{'A'},SETTINGS,narrate.sha(self.plan))
        result=json.loads((self.output/'manifest.json').read_text())
        self.assertEqual(code,2);self.assertEqual(result['status'],'partial')
        self.assertEqual(result['failures'][0]['id'],'B')

    async def test_unavailable_voice_has_no_fallback(self):
        fake=types.SimpleNamespace(list_voices=AsyncMock(return_value=[]))
        with patch.object(narrate.importlib,'import_module',return_value=fake),patch.object(narrate.shutil,'which',return_value='/fixture/ffmpeg'),patch.object(narrate,'synthesize',new_callable=AsyncMock) as synthesis:
            code=await narrate.generate(self.args,self.chapters,{'A','B'},SETTINGS,narrate.sha(self.plan))
        self.assertEqual(code,2);synthesis.assert_not_called()
        result=json.loads((self.output/'manifest.json').read_text())
        self.assertEqual({e['error'] for e in result['failures']},{'VOICE_UNAVAILABLE'})

    async def test_plan_changes_are_not_marked_complete(self):
        original=narrate.sha(self.plan)
        for chapter in self.chapters:self.record(chapter)
        self.plan.write_text('{}')
        code=await narrate.generate(self.args,self.chapters,{'A','B'},SETTINGS,original)
        self.assertEqual(code,2)
        self.assertEqual(json.loads((self.output/'manifest.json').read_text())['status'],'plan-changed')

    def test_hash_corruption_and_changed_voice_invalidate_cache(self):
        self.record(self.chapters[0])
        (self.output/'A.mp3').write_bytes(b'changed')
        self.assertEqual(narrate.inspect_record(self.chapters[0],self.output,SETTINGS)[1],'stale')
        self.record(self.chapters[0])
        self.assertEqual(narrate.inspect_record(self.chapters[0],self.output,{**SETTINGS,'voice':'zh-CN-YunxiNeural'})[1],'stale')

    def test_validate_only_does_not_create_output_or_import_edge(self):
        profile=self.root/'voice-profile.json';profile.write_text(json.dumps(SETTINGS))
        destination=self.root/'not-created'
        result=subprocess.run([sys.executable,'-S',str(SCRIPT),'--plan',str(self.plan),'--output',str(destination),'--voice-profile',str(profile)],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(json.loads(result.stdout)['voice'],SETTINGS['voice'])
        self.assertFalse(destination.exists())


if __name__ == '__main__':
    unittest.main()
