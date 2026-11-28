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
        "img": "shot_01_dr_rami_study.jpg",
        "prompt": "Slow cinematic camera push-in on Dr. Rami working late at his desk, holographic equations and gear wireframes glowing softly",
        "duration": 4.8
    },
    {
        "id": 2,
        "img": "shot_02_deciphering_solar_key.jpg",
        "prompt": "Macro camera subtle tracking shot, hands drawing geometric alignment vector over ancient gear photos, soft indicator lights blinking",
        "duration": 4.8
    },
    {
        "id": 3,
        "img": "shot_03_armored_capsule_rig.jpg",
        "prompt": "Massive spherical steel capsule suspended over the dark borehole at dusk, amber beacon lights flashing, technicians walking around",
        "duration": 4.8
    },
    {
        "id": 4,
        "img": "shot_04_rami_entering_capsule.jpg",
        "prompt": "Dr. Rami stepping through the capsule hatch in his suit, putting on his helmet with determined gaze, amber warning light revolving",
        "duration": 4.8
    },
    {
        "id": 5,
        "img": "shot_05_global_live_broadcast.jpg",
        "prompt": "Massive crowd staring up at giant outdoor LED news screen, camera flashes going off, broadcast news ticker scrolling dynamically",
        "duration": 4.8
    },
    {
        "id": 6,
        "img": "shot_06_capsule_descending.jpg",
        "prompt": "Spherical capsule descending steadily down the dark cylindrical shaft, bright exterior lights cutting through rising subterranean mist",
        "duration": 4.8
    },
    {
        "id": 7,
        "img": "shot_07_capsule_arriving_gate.jpg",
        "prompt": "POV from inside capsule looking out the porthole as capsule touches down in front of the massive rotating gate, headlights reflecting",
        "duration": 4.8
    },
    {
        "id": 8,
        "img": "shot_08_rami_aiming_beam.jpg",
        "prompt": "Dr. Rami fine-tuning optical crosshair controls in the cockpit, glowing targeting reticles reflected on his helmet visor, breathing calmly",
        "duration": 4.8
    },
    {
        "id": 9,
        "img": "shot_09_golden_laser_firing.jpg",
        "prompt": "Intense concentrated beam of golden laser light firing from capsule into the central sun cavity, blinding golden energy expanding",
        "duration": 4.8
    },
    {
        "id": 10,
        "img": "shot_10_gears_stop_gate_opens.jpg",
        "prompt": "Seven gears violently lock and freeze, colossal gate splitting down the middle and sliding into rock walls as golden light pours out",
        "duration": 5.0
    }
]

scene_dir = Path("/home/user/production_vault/video_eldalil_wonders/scene_04")
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
    tok = hf_tokens[(idx + 12) % len(hf_tokens)]

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
                seed_ui=210 + idx * 23,
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
            tok = hf_tokens[(idx + attempt + 13) % len(hf_tokens)]
            time.sleep(3)

    if not animated:
        print(f"FATAL: Failed to animate shot {shot['id']}")
        sys.exit(1)

print("\nAll 10 shots of Scene 4 animated successfully via Hugging Face!")
