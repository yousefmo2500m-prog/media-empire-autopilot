import os
import sys
import shutil
import time
from pathlib import Path
from gradio_client import Client, handle_file

sys.path.insert(0, '/home/user/media-empire-autopilot')
import _env_loader

# Collect all available HF tokens
hf_tokens = []
for k, v in os.environ.items():
    if k.startswith('HF_TOKEN') and v.strip():
        hf_tokens.append(v.strip())

print(f"Loaded {len(hf_tokens)} Hugging Face tokens for animation pool.")

shots = [
    {
        "id": 1,
        "img": "shot_01_mountain_excavation.jpg",
        "prompt": "Cinematic camera push-in across dusty mountain excavation site, subtle heat shimmer, distant dust motes in sunbeams",
        "duration": 4.0
    },
    {
        "id": 2,
        "img": "shot_02_mysterious_circular_well.jpg",
        "prompt": "Slow ominous camera creep forward toward the smooth circular hole in the dark rock floor, subtle rising blue haze",
        "duration": 4.0
    },
    {
        "id": 3,
        "img": "shot_02b_smooth_walls.jpg",
        "prompt": "Cinematic camera tracking downward along the glass-smooth polished stone inner cylinder, subtle light reflections gliding",
        "duration": 4.0
    },
    {
        "id": 4,
        "img": "shot_03_dropping_stone_into_abyss.jpg",
        "prompt": "Slow motion release of the heavy jagged stone from worker's hand falling straight down into darkness, dust particles floating",
        "duration": 4.0
    },
    {
        "id": 5,
        "img": "shot_05_stone_falling.jpg",
        "prompt": "POV camera diving straight down into the infinite vertical shaft, stone tumbling away into the deep dark center",
        "duration": 4.5
    },
    {
        "id": 6,
        "img": "shot_04_stunned_workers_at_abyss.jpg",
        "prompt": "Subtle breathing and slow head movements of the workers holding flashlights aimed into the void, shifting light beams",
        "duration": 4.0
    },
    {
        "id": 7,
        "img": "shot_07_ticking_watch.jpg",
        "prompt": "Macro camera subtle tilt, the watch second hand ticking steadily, background workers standing motionless in twilight",
        "duration": 4.0
    },
    {
        "id": 8,
        "img": "shot_08_blue_mist.jpg",
        "prompt": "Mysterious glowing azure mist gently swirling and billowing upward out of the circular aperture into the cold air",
        "duration": 4.5
    },
    {
        "id": 9,
        "img": "shot_09_workers_shock.jpg",
        "prompt": "Construction workers talking animatedly in low whispers, gesturing towards the hole, flickering work lights",
        "duration": 4.0
    },
    {
        "id": 10,
        "img": "shot_10_convoy_arriving.jpg",
        "prompt": "Convoy of headlights moving along the winding mountain road, bright beams cutting through dust at night",
        "duration": 4.5
    }
]

scene_dir = Path("/home/user/production_vault/video_eldalil_wonders/scene_01")
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
    tok = hf_tokens[idx % len(hf_tokens)]
    
    animated = False
    for attempt in range(3):
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
                seed_ui=42 + idx * 7,
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
            tok = hf_tokens[(idx + attempt + 1) % len(hf_tokens)]
            time.sleep(3)

    if not animated:
        print(f"FAILED to animate shot {shot['id']}")

print("\nAll 10 shots of Scene 1 processed!")
