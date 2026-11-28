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
        "img": "shot_01_rami_steps_out.jpg",
        "prompt": "Slow camera tracking behind Dr. Rami walking into illuminated underground hall, boots clicking on smooth stone, light reflecting",
        "duration": 5.4
    },
    {
        "id": 2,
        "img": "shot_02_celestial_chamber_wide.jpg",
        "prompt": "Slow awe-inspiring camera tilt up across colossal vaulted basalt dome, glowing geometric fiber veins pulsing with faint celestial blue light",
        "duration": 5.4
    },
    {
        "id": 3,
        "img": "shot_03_floating_crystal_earth.jpg",
        "prompt": "Majestic camera push-in toward the floating crystalline Earth sphere, glowing azure oceans and gold continents refracting prismatic light",
        "duration": 5.4
    },
    {
        "id": 4,
        "img": "shot_04_rotating_crystal_globe.jpg",
        "prompt": "Continuous smooth orbital camera rotation around the weightless crystal globe spinning slowly on its axis, atmospheric cloud bands drifting",
        "duration": 5.4
    },
    {
        "id": 5,
        "img": "shot_05_microscopic_continents_macro.jpg",
        "prompt": "Macro camera panning across illuminated crystal mountain ridges and river deltas, tiny golden contour lines pulsing softly",
        "duration": 5.4
    },
    {
        "id": 6,
        "img": "shot_06_rami_gazing_wonder.jpg",
        "prompt": "Dr. Rami slowly raising gloved hand toward the floating sphere in reverent awe, tears in his eyes, earth light reflecting on his helmet visor",
        "duration": 5.4
    },
    {
        "id": 7,
        "img": "shot_07_black_monolith_tablet.jpg",
        "prompt": "Slow camera tracking down the polished black monolith, carved geometric glyphs and cuneiform diagrams pulsing with warm amber glow",
        "duration": 5.4
    },
    {
        "id": 8,
        "img": "shot_08_seven_golden_beams.jpg",
        "prompt": "Seven razor-thin golden laser vectors shooting out from the monolith to strike seven glowing coordinate nodes on the floating crystal globe",
        "duration": 5.4
    },
    {
        "id": 9,
        "img": "shot_09_ancient_message_illumination.jpg",
        "prompt": "Golden holographic glyphs on the black stone shimmering and streaming volumetric god-rays outward through the cool subterranean air",
        "duration": 5.4
    },
    {
        "id": 10,
        "img": "shot_10_global_scientific_shock.jpg",
        "prompt": "Auditorium of scientists standing in breathless shock, camera panning across stunned faces staring at giant screen showing the crystal Earth",
        "duration": 5.4
    }
]

scene_dir = Path("/home/user/production_vault/video_eldalil_wonders/scene_05")
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
    tok = hf_tokens[(idx + 16) % len(hf_tokens)]

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
                seed_ui=320 + idx * 31,
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
            tok = hf_tokens[(idx + attempt + 17) % len(hf_tokens)]
            time.sleep(3)

    if not animated:
        print(f"FATAL: Failed to animate shot {shot['id']}")
        sys.exit(1)

print("\nAll 10 shots of Scene 5 animated successfully via Hugging Face!")
