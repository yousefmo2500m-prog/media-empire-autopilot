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
        "img": "shot_01_subterranean_sanctuary_wide.jpg",
        "prompt": "Slow majestic camera pull-back through the vast underground sanctuary, the crystal Earth sphere and seven golden beams pulsating softly",
        "duration": 4.6
    },
    {
        "id": 2,
        "img": "shot_02_rami_under_starry_sky.jpg",
        "prompt": "Dr. Rami standing on the cliff looking up with gentle smile into the brilliant starry night sky, wind softly moving his hair, camp lights twinkling",
        "duration": 4.6
    },
    {
        "id": 3,
        "img": "shot_03_seven_sites_holographic_map.jpg",
        "prompt": "3D holographic world map rotating slowly, seven golden coordinate beacon pins pulsing with concentric energy ripples",
        "duration": 4.6
    },
    {
        "id": 4,
        "img": "shot_04_like_subscribe_cta_overlay.jpg",
        "prompt": "Dynamic cinematic camera sweep over glossy 3D subscribe button and like icon, golden sparks and light embers floating gently",
        "duration": 4.6
    },
    {
        "id": 5,
        "img": "shot_05_bell_notification_next_enigma.jpg",
        "prompt": "Golden notification bell ringing with expanding golden energy rings, background shadow glimpses of submerged pyramids shifting",
        "duration": 4.6
    },
    {
        "id": 6,
        "img": "shot_06_community_comments_glow.jpg",
        "prompt": "Translucent glowing holographic comment bubbles and question marks drifting upward into the night sky above dunes, warm golden light trails",
        "duration": 4.6
    },
    {
        "id": 7,
        "img": "shot_07_second_site_teaser.jpg",
        "prompt": "Desert sand blowing gently across half-buried ancient stone portal, glowing golden solar glyphs pulsating under moonlight",
        "duration": 4.6
    },
    {
        "id": 8,
        "img": "shot_08_eldalil_elakhir_outro_card.jpg",
        "prompt": "Majestic slow camera push-in on 3D metallic typography 'الدليل الأخير', delicate blue smoke swirling, golden embers rising and slowly fading",
        "duration": 5.0
    }
]

scene_dir = Path("/home/user/production_vault/video_eldalil_wonders/scene_06")
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
    tok = hf_tokens[(idx + 20) % len(hf_tokens)]

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
                seed_ui=430 + idx * 37,
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
            tok = hf_tokens[(idx + attempt + 21) % len(hf_tokens)]
            time.sleep(3)

    if not animated:
        print(f"FATAL: Failed to animate shot {shot['id']}")
        sys.exit(1)

print("\nAll 8 shots of Scene 6 animated successfully via Hugging Face!")
