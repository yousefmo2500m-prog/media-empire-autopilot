from __future__ import annotations

import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

import numpy as np
from PIL import Image

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

import cinema_funnel_renderer
import run_empire
import story_visuals


class VisualUpgradeTests(unittest.TestCase):
    def test_turning_point_selector_prefers_story_reveal(self) -> None:
        windows = [
            {"start": i * 10, "end": (i + 1) * 10, "text": ""}
            for i in range(20)
        ]
        windows[10]["text"] = "وصلت رسالة قديمة إلى الشاهد."
        windows[14]["text"] = "اكتشف الدليل الحقيقي عند باب الشقة."
        self.assertEqual(run_empire._choose_highlight_motion_index(windows), 14)

    def test_cloudflare_budget_is_persistent_and_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            state_path = Path(temp_dir) / "budget.json"
            with patch.dict(os.environ, {"MEDIA_EMPIRE_CF_BUDGET_PATH": str(state_path)}):
                with redirect_stdout(io.StringIO()):
                    for _ in range(story_visuals._CLOUDFLARE_IMAGE_CALLS_PER_UTC_DAY):
                        self.assertTrue(story_visuals._reserve_cloudflare_image_slot())
                    self.assertFalse(story_visuals._reserve_cloudflare_image_slot())
            saved = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual(saved["reserved_image_calls"], story_visuals._CLOUDFLARE_IMAGE_CALLS_PER_UTC_DAY)

    def test_priority_refinement_saves_only_high_resolution_result(self) -> None:
        rng = np.random.default_rng(123)
        high_res = Image.fromarray(rng.integers(0, 256, (1024, 1024, 3), dtype=np.uint8), mode="RGB")
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "hero.jpg"
            with patch.dict(os.environ, {"CF_ACCOUNT_ID": "test-account", "CF_API_TOKEN": "test-token"}):
                with patch.object(story_visuals, "_try_cloudflare_flux", return_value=high_res):
                    ok = story_visuals._refine_priority_frame_with_cloudflare(
                        "Photorealistic hallway scene", output, 1280, 720, 17
                    )
            self.assertTrue(ok)
            self.assertTrue(output.exists())
            with Image.open(output) as saved:
                self.assertEqual(saved.size, (1280, 720))

    def test_batch_keeps_all_nine_frames_and_limits_refinement_to_requested_indices(self) -> None:
        rng = np.random.default_rng(456)
        grid = Image.fromarray(rng.integers(0, 256, (864, 1536, 3), dtype=np.uint8), mode="RGB")
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.object(story_visuals, "_call_flux_zerogpu_raw", return_value=grid):
                with patch.object(story_visuals, "_refine_priority_frame_with_cloudflare", return_value=False) as refine:
                    frames = story_visuals.generate_8sec_shots_batch(
                        prompts=[f"Scene {i}: a realistic apartment clue" for i in range(9)],
                        out_dir=Path(temp_dir),
                        prefix="test",
                        width=1280,
                        height=720,
                        seed_base=100,
                        max_workers=1,
                        refine_indices=[0, 5],
                    )
            self.assertEqual(len(frames), 9)
            self.assertEqual(refine.call_count, 2)
            for frame in frames:
                with Image.open(frame) as saved:
                    self.assertEqual(saved.size, (1280, 720))

    def test_renderer_uses_motion_clip_for_nonopening_long_shot(self) -> None:
        motion = Path("highlight.mp4")
        output = Path("highlight_segment.mp4")
        with patch.object(cinema_funnel_renderer, "_render_motion_clip_segment", return_value=True) as render:
            idx, result = cinema_funnel_renderer._render_single_long_8s_shot(
                12, Path("still.jpg"), 8.0, output, 20, None, motion
            )
        self.assertEqual((idx, result), (12, output))
        render.assert_called_once_with(motion, 8.0, output, 1280, 720, 20, crf=22)


if __name__ == "__main__":
    unittest.main()
