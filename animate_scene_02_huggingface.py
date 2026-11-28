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
        "img": "shot_01_giant_crane_winch.jpg",
        "prompt": "Slow industrial camera tilt up the giant crane arm, steel winch drum slowly rotating, morning dust motes in sunbeams",
        "duration": 5.0
    },
    {
        "id": 2,
        "img": "shot_02_armored_camera_rig.jpg",
        "prompt": "Armored cylindrical camera rig gently swaying on steel cable above dark pit, blinding LED floodlights shimmering in cold air",
        "duration": 5.0
    },
    {
        "id": 3,
        "img": "shot_03_lowering_first_20m.jpg",
        "prompt": "Camera rig descending smoothly down the dark shaft, bright light beams sweeping across polished mirror-like stone walls",
        "duration": 5.0
    },
    {
        "id": 4,
        "img": "shot_04_engineers_watching_monitors.jpg",
        "prompt": "Subtle breathing and eye movements of engineers staring at glowing video monitors in dark van, flickering screen reflection",
        "duration": 5.0
    },
    {
        "id": 5,
        "img": "shot_05_lights_flicker_and_die.jpg",
        "prompt": "Camera lights violently flickering, pulsing once, and dying into pitch darkness with faint red diode glowing",
        "duration": 5.0
    },
    {
        "id": 6,
        "img": "shot_06_blue_flash_static_monitors.jpg",
        "prompt": "Violent rolling television static noise on monitor screens, intense flashing cobalt-blue light pulsing across cabin",
        "duration": 5.0
    },
    {
        "id": 7,
        "img": "shot_07_steel_cable_snapping.jpg",
        "prompt": "High tension steel cable violently snapping and recoiling across the ground, flying sparks, billowing dust cloud",
        "duration": 5.0
    },
    {
        "id": 8,
        "img": "shot_08_acoustic_team_setup.jpg",
        "prompt": "Acoustic scientists adjusting tripods and sensors in cold wind, moving cables across rocky ground under overcast sky",
        "duration": 5.0
    },
    {
        "id": 9,
        "img": "shot_09_golden_acoustic_sensor.jpg",
        "prompt": "Golden acoustic probe slowly lowered on yellow cable into the pitch-black circular hole, subtle metallic glints",
        "duration": 5.0
    },
    {
        "id": 10,
        "img": "shot_10_sound_engineer_headphones.jpg",
        "prompt": "Sound engineer pressing headphones hard against ears, trembling hands, eyes widening in disbelief, cold blue equipment lights",
        "duration": 5.3
    }
]

scene_dir = Path("/home/user/production_vault/video_eldalil_wonders/scene_02")
scene_dir.mkdir(parents=True, exist_ok=True)

neg_prompt = (
    "worst quality, inconsistent motion, blurry, jittery, warped face, bad anatomy, "
    "duplicate limbs, flickering face, morphing, watermark, text, low quality"
)

for idx, shot in enumerate(shots):
    out_mp4 = scene_dir / f"shot_{shot['id']:02d}_animated.mp4"
    if out_mp4.exists() and out_mp4.stat().st_size > 50000:
        print(f"[{shot['id']}/10] {out_mp4.name} already exists, skipping...")
        continue

    img_path = scene_dir / shot["img"]
    if not img_path.exists():
        print(f"Error: image {img_path} not found!")
        continue

    print(f"\n[{shot['id']}/10] Animating {shot['img']} via Hugging Face ZeroGPU...")
    tok = hf_tokens[(idx + 4) % len(hf_tokens)]

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
                seed_ui=88 + idx * 13,
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
            tok = hf_tokens[(idx + attempt + 5) % len(hf_tokens)]
            time.sleep(3)

    if not animated:
        print(f"FATAL: Failed to animate shot {shot['id']}")
        sys.exit(1)

print("\nAll 10 shots of Scene 2 animated successfully via Hugging Face!")
