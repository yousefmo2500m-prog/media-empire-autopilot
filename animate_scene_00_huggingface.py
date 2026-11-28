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
        "img": "shot_01_hook_gate_breach.jpg",
        "prompt": "Dynamic cinematic push-in on armored capsule firing intense golden laser beam into ancient gate, brilliant volumetric light rays",
        "duration": 5.4
    },
    {
        "id": 2,
        "img": "shot_02_hook_cable_snap_glitch.jpg",
        "prompt": "Steel winch cable snapping violently across rocky ground with flying sparks and blue electric arcs, dust billowing",
        "duration": 5.4
    },
    {
        "id": 3,
        "img": "shot_03_hook_crystal_earth_flash.jpg",
        "prompt": "Slow camera creep around the weightless glowing crystal Earth sphere rotating in dark mid-air, prismatic flares dancing",
        "duration": 5.4
    },
    {
        "id": 4,
        "img": "shot_04_hook_monolith_laser_beams.jpg",
        "prompt": "Black monolith stone slab shooting intense golden laser vectors horizontally across dark cavern mist, beams pulsing with energy",
        "duration": 5.4
    },
    {
        "id": 5,
        "img": "shot_05_hook_rami_cockpit_intensity.jpg",
        "prompt": "Tight camera focus on Dr. Rami's eyes through helmet visor, glowing targeting reticles reflected dynamically, heavy breathing",
        "duration": 5.4
    },
    {
        "id": 6,
        "img": "shot_06_hook_well_aperture_blue_mist.jpg",
        "prompt": "Vortex of luminescent blue vapor swirling and billowing upward out of the smooth circular hole into the cold mountain night",
        "duration": 5.4
    },
    {
        "id": 7,
        "img": "shot_07_hook_gears_freezing_shudder.jpg",
        "prompt": "Massive bronze gear teeth violently shuddering and locking into place with erupting sparks and heavy mechanical vibration",
        "duration": 5.4
    },
    {
        "id": 8,
        "img": "shot_08_hook_title_card.jpg",
        "prompt": "Slow dramatic camera push-in on 3D metallic typography 'لغز بئر الأسرار - دفتر راوي', blue smoke swirling, golden sparks floating",
        "duration": 5.5
    }
]

scene_dir = Path("/home/user/production_vault/video_eldalil_wonders/scene_00")
scene_dir.mkdir(parents=True, exist_ok=True)

neg_prompt = (
    "worst quality, inconsistent motion, blurry, jittery, warped face, bad anatomy, "
    "duplicate limbs, flickering face, morphing, watermark, text, low quality"
)

for idx, shot in enumerate(shots):
    out_mp4 = scene_dir / f"shot_{shot['id']:02d}_animated.mp4"
    if out_mp4.exists() and out_mp4.stat().st_size > 50000:
        print(f"[{shot['id']}/8] {out_mp4.name} already exists, skipping...")
        continue

    img_path = scene_dir / shot["img"]
    if not img_path.exists():
        print(f"Error: image {img_path} not found!")
        continue

    print(f"\n[{shot['id']}/8] Animating {shot['img']} via Hugging Face ZeroGPU...")
    tok = hf_tokens[(idx + 6) % len(hf_tokens)]

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
                seed_ui=550 + idx * 41,
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
            tok = hf_tokens[(idx + attempt + 7) % len(hf_tokens)]
            time.sleep(3)

    if not animated:
        print(f"FATAL: Failed to animate shot {shot['id']}")
        sys.exit(1)

print("\nAll 8 shots of Scene 00 animated successfully via Hugging Face!")
