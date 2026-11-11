from __future__ import annotations

import base64
import io
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

import numpy as np
import requests
from PIL import Image, ImageChops

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

import cinema_funnel_renderer
import empire_publisher
import sound_studio
import story_brain
import story_visuals


class FakeResponse:
    def __init__(self, status_code: int, json_data=None, text: str = "") -> None:
        self.status_code = status_code
        self._json_data = json_data or {}
        self.text = text
        self.headers = {}

    def json(self):
        return self._json_data

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}")


class V18ResilienceTests(unittest.TestCase):
    def test_zernio_media_upload_uses_three_gateway_backoffs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            media = Path(temp_dir) / "sample.mp4"
            media.write_bytes(b"test-media")
            presign_success = FakeResponse(
                200,
                {"uploadUrl": "https://upload.example.test/signed", "publicUrl": "https://cdn.example.test/sample.mp4"},
            )
            post_responses = [FakeResponse(502), FakeResponse(504), FakeResponse(502), presign_success]
            with patch.object(empire_publisher.requests, "post", side_effect=post_responses) as post:
                with patch.object(empire_publisher.requests, "put", return_value=FakeResponse(200)):
                    with patch.object(empire_publisher.time, "sleep") as sleep:
                        url = empire_publisher.upload_media_to_zernio("test-key", media)
            self.assertEqual(url, "https://cdn.example.test/sample.mp4")
            self.assertEqual(post.call_count, 4)
            self.assertEqual([call.args[0] for call in sleep.call_args_list], [15, 30, 60])

    def test_zernio_binary_upload_retries_gateway_errors_three_times(self) -> None:
        presign = FakeResponse(
            200,
            {"uploadUrl": "https://upload.example.test/signed", "publicUrl": "https://cdn.example.test/sample.mp4"},
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            media = Path(temp_dir) / "sample.mp4"
            media.write_bytes(b"test-media")
            with patch.object(empire_publisher.requests, "post", side_effect=[presign] * 4):
                with patch.object(
                    empire_publisher.requests,
                    "put",
                    side_effect=[FakeResponse(502), FakeResponse(504), FakeResponse(502), FakeResponse(200)],
                ) as put:
                    with patch.object(empire_publisher.time, "sleep") as sleep:
                        url = empire_publisher.upload_media_to_zernio("test-key", media)
            self.assertEqual(url, "https://cdn.example.test/sample.mp4")
            self.assertEqual(put.call_count, 4)
            self.assertEqual([call.args[0] for call in sleep.call_args_list], [15, 30, 60])

    def test_zernio_post_retries_502_504_three_times(self) -> None:
        responses = [FakeResponse(502), FakeResponse(504), FakeResponse(502), FakeResponse(200)]
        with patch.object(empire_publisher.requests, "post", side_effect=responses) as post:
            with patch.object(empire_publisher.time, "sleep") as sleep:
                result = empire_publisher._post_zernio_resilient("test-key", {"title": "test"}, "test")
        self.assertEqual(result.status_code, 200)
        self.assertEqual(post.call_count, 4)
        self.assertEqual([call.args[0] for call in sleep.call_args_list], [15, 30, 60])

    def test_facebook_comment_ends_with_official_youtube_invitation_and_url(self) -> None:
        comment = empire_publisher._facebook_channel_comment(
            "اكتب توقعك هنا", "https://www.youtube.com/@daftarrawi/", "ar"
        )
        self.assertEqual(
            comment.splitlines()[-1],
            "اشترك في قناتنا الرسمية على YouTube: https://www.youtube.com/@daftarrawi",
        )

    def test_gemini_tts_switches_to_backup_key_immediately_on_429(self) -> None:
        audio_bytes = b"\x00\x00" * 400
        success = FakeResponse(
            200,
            {
                "candidates": [
                    {
                        "content": {
                            "parts": [
                                {
                                    "inlineData": {
                                        "mimeType": "audio/pcm",
                                        "data": base64.b64encode(audio_bytes).decode("ascii"),
                                    }
                                }
                            ]
                        }
                    }
                ]
            },
            text='{"inlineData":true}',
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "voice.mp3"
            with patch.dict(
                os.environ,
                {"GEMINI_API_KEY": "main-key", "GEMINI_API_KEY_2": "backup-key"},
                clear=True,
            ):
                with patch.object(
                    sound_studio.requests,
                    "post",
                    side_effect=[FakeResponse(429, text="rate limit"), success],
                ) as post:
                    with patch.object(sound_studio.subprocess, "run", side_effect=lambda cmd, **kwargs: Path(cmd[-1]).write_bytes(b"x" * 2048)):
                        with patch.object(sound_studio, "get_audio_duration", return_value=0.9):
                            with patch.object(sound_studio.time, "sleep"):
                                ok = sound_studio._try_gemini_tts_strict(
                                    "A short spoken test.", True, output, call_index=0
                                )
            self.assertTrue(ok)
            self.assertEqual(post.call_count, 2)
            self.assertIn("?key=main-key", post.call_args_list[0].args[0])
            self.assertIn("?key=backup-key", post.call_args_list[1].args[0])
            self.assertTrue(output.exists())

    def test_story_brain_gemini_json_switches_key_on_429(self) -> None:
        success = FakeResponse(
            200,
            {"candidates": [{"content": {"parts": [{"text": '{"ok": true}'}]}}]},
        )
        with patch.dict(
            os.environ,
            {"GEMINI_API_KEY": "main-key", "GEMINI_API_KEY_2": "backup-key", "GROQ_API_KEY": "groq-test"},
            clear=True,
        ):
            with patch.object(
                story_brain.requests, "post", side_effect=[FakeResponse(429), success]
            ) as post:
                with patch.object(story_brain.time, "sleep"):
                    result = story_brain._groq_json("groq-test", "system", "user")
        self.assertEqual(result, {"ok": True})
        self.assertEqual(post.call_count, 2)
        self.assertIn("?key=main-key", post.call_args_list[0].args[0])
        self.assertIn("?key=backup-key", post.call_args_list[1].args[0])

    def test_all_failed_image_providers_still_return_local_frames(self) -> None:
        prompts = [f"A quiet apartment hallway at night, visual beat {i}" for i in range(10)]
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.object(story_visuals, "_call_flux_zerogpu_raw", return_value=None):
                with patch.object(story_visuals, "generate_single_shot_image", side_effect=RuntimeError("providers offline")):
                    with redirect_stdout(io.StringIO()):
                        frames = story_visuals.generate_8sec_shots_batch(
                            prompts=prompts,
                            out_dir=Path(temp_dir),
                            prefix="local",
                            width=320,
                            height=180,
                            seed_base=51,
                            max_workers=1,
                        )
            self.assertEqual(len(frames), len(prompts))
            for frame in frames:
                self.assertTrue(frame.exists())
                with Image.open(frame) as image:
                    self.assertEqual(image.size, (320, 180))
                    self.assertGreater(float(np.asarray(image).std()), 5.0)
            with Image.open(frames[0]) as first, Image.open(frames[1]) as second:
                self.assertIsNotNone(ImageChops.difference(first, second).getbbox())

    def test_local_fallback_frame_renders_with_ken_burns(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            image = story_visuals._create_local_fallback_frame(
                Path(temp_dir) / "fallback.jpg", 1280, 720, 987, "a dark corridor and wooden door"
            )
            output = Path(temp_dir) / "ken_burns.mp4"
            _, rendered = cinema_funnel_renderer._render_single_long_8s_shot(
                1, image, 3.0, output, fps=10
            )
            self.assertTrue(rendered.exists())
            self.assertGreater(rendered.stat().st_size, 10_000)

    def test_visual_windows_never_exceed_three_point_five_seconds(self) -> None:
        windows = sound_studio.build_dynamic_pacing_windows(
            total_dur=50.0,
            teaser_end_sec=8.0,
            words=[],
            fallback_text="a story with enough words to fill every frame",
            teaser_interval_sec=8.0,
            body_interval_sec=9.0,
        )
        self.assertTrue(windows)
        self.assertEqual(windows[0]["start"], 0.0)
        self.assertAlmostEqual(windows[-1]["end"], 50.0)
        self.assertLessEqual(max(window["dur"] for window in windows), 3.5)

    def test_ass_captions_use_white_gold_black_outline_and_visible_shadow(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            long_path = Path(temp_dir) / "long.ass"
            cinema_funnel_renderer._write_long_ass([], [], "", 0, "Brand", 10, long_path)
            long_text = long_path.read_text(encoding="utf-8")
            self.assertIn("Style: Sub,Cairo,40,&H00FFFFFF,&H0000C8FF,&H00000000,&H68000000", long_text)
            self.assertIn(",1,4.4,3.0,2,85,85,42,1", long_text)

            short_path = Path(temp_dir) / "short.ass"
            cinema_funnel_renderer._write_short_ass(
                [{"word": "truth", "start": 0.2, "end": 0.8}],
                "Brand",
                "Hook",
                2.0,
                "CTA",
                12.0,
                short_path,
            )
            short_text = short_path.read_text(encoding="utf-8")
            self.assertIn("Style: Cap,Cairo,53,&H00FFFFFF,&H0000C8FF,&H00000000,&H68000000", short_text)
            self.assertIn(",1,5.0,3.0,2,42,42,262,1", short_text)
            self.assertIn(r"{\c&H0000C8FF&}truth", short_text)


if __name__ == "__main__":
    unittest.main()
