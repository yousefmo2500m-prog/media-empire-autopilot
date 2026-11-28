import os
import sys
import shutil
import time
from pathlib import Path
from gradio_client import Client, handle_file

sys.path.insert(0, '/home/user/media-empire-autopilot')
import _env_loader

hf_tokens = []
for k, v in os.environ.items():
    if k.startswith('HF_TOKEN') and v.strip():
        hf_tokens.append(v.strip())

print(f"Loaded {len(hf_tokens)} Hugging Face tokens.")

shots = [
    {
        "id": 1,
        "img": "shot_01_tracked_exploration_robot.jpg",
        "prompt": "Slow industrial camera pan across tracked exploration robot on staging platform, subtle blinking sensor lights, morning mist",
        "duration": 4.5
    },
    {
        "id": 2,
        "img": "shot_02_lowering_robot_platform.jpg",
        "prompt": "Suspension cage slowly descending into circular borehole, headlights cutting through dust, cables unspooling steadily",
        "duration": 4.5
    },
    {
        "id": 3,
        "img": "shot_03_robot_at_80m_depth.jpg",
        "prompt": "Tracked robot moving slowly forward across rocky subterranean floor at 80m, bright dual headlights sweeping through cold swirling fog",
        "duration": 4.5
    },
    {
        "id": 4,
        "img": "shot_04_vast_chamber_reveal.jpg",
        "prompt": "Slow majestic camera boom up behind the robot as its floodlights sweep up the colossal vertical underground structure in distance",
        "duration": 4.5
    },
    {
        "id": 5,
        "img": "shot_05_monumental_metallic_gate.jpg",
        "prompt": "Slow awe-inspiring camera push-in toward the colossal circular metallic vault door, gleaming reflections on pristine alloy surface",
        "duration": 4.5
    },
    {
        "id": 6,
        "img": "shot_06_seven_interlocking_gears.jpg",
        "prompt": "Hypnotic continuous clockwork rotation of seven massive interlocking bronze gears, mechanical clockwork in perpetual motion",
        "duration": 4.5
    },
    {
        "id": 7,
        "img": "shot_07_clockwork_teeth_close.jpg",
        "prompt": "Macro camera tracking along precision interlocking gear teeth turning steadily, metallic glints and fine coordinates shifting",
        "duration": 4.5
    },
    {
        "id": 8,
        "img": "shot_08_central_sun_eye_cavity.jpg",
        "prompt": "Slow camera creep into the golden central solar medallion, pulsating warm golden luminescence deep inside the aperture",
        "duration": 4.5
    },
    {
        "id": 9,
        "img": "shot_09_command_center_awe.jpg",
        "prompt": "Subtle breathing and frozen disbelief of scientists staring at wall of monitors, blinking telemetry lights reflected on faces",
        "duration": 4.5
    }
]

scene_dir = Path("/home/user/production_vault/video_eldalil_wonders/scene_03")
scene_dir.mkdir(parents=True, exist_ok=True)

neg_prompt = (
    "worst quality, inconsistent motion, blurry, jittery, warped face, bad anatomy, "
    "duplicate limbs, flickering face, morphing, watermark, text, low quality"
)

for idx, shot in enumerate(shots):
    out_mp4 = scene_dir / f"shot_{shot['id']:02d}_animated.mp4"
    if out_mp4.exists() and out_mp4.stat().st_size > 50000:
        print(f"[{shot['id']}/9] {out_mp4.name} already exists, skipping...")
        continue

    img_path = scene_dir / shot["img"]
    if not img_path.exists():
        print(f"Error: image {img_path} not found!")
        continue

    print(f"\n[{shot['id']}/9] Animating {shot['img']} via Hugging Face ZeroGPU...")
    tok = hf_tokens[(idx + 8) % len(hf_tokens)]

    animated = False
    for attempt in range(4):
        try:
            client = Client("Lightricks/ltx-video-distilled", token=tok)
            res = client.predict(
                prompt=shot["prompt"],
                negative_prompt=neg_prompt,
                input_image_filepath=handle_file(str(img_path)),
                input_video_filepath=None,
                height_ui=448,
                width_ui=768,
                mode="image-to-video",
                duration_ui=shot["duration"],
                ui_frames_to_use=9,
                seed_ui=140 + idx * 19,
                randomize_seed=True,
                ui_guidance_scale=1.0,
                improve_texture_flag=True,
                api_name="/image_to_video"
            )
            if res and isinstance(res, (tuple, list)) and res[0]:
                v_path = res[0].get("video") if isinstance(res[0], dict) else res[0]
                if v_path and os.path.exists(v_path):
                    shutil.copy2(v_path, str(out_mp4))
                    print(f"  ✓ Successfully animated {out_mp4.name} (size={out_mp4.stat().st_size} bytes)")
                    animated = True
                    break
        except Exception as e:
            print(f"  Attempt {attempt+1} error: {e}")
            tok = hf_tokens[(idx + attempt + 9) % len(hf_tokens)]
            time.sleep(3)

    if not animated:
        print(f"FATAL: Failed to animate shot {shot['id']}")
        sys.exit(1)

print("\nAll 9 shots of Scene 3 animated successfully via Hugging Face!")
