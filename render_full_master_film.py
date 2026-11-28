import subprocess
from pathlib import Path
import sound_studio

base_dir = Path("/home/user/production_vault/video_eldalil_wonders")
dist_dir = Path("/home/user/media-empire-autopilot/dist/completed_scenes")
out_film = base_dir / "film_complete_well_of_wonders_master.mp4"

# Ensure all 7 scene files are accessible
scenes_paths = []
for i in range(7):
    fn = f"scene_{i:02d}_complete_cinematic.mp4"
    p1 = base_dir / fn
    p2 = dist_dir / fn
    if p1.exists():
        scenes_paths.append(p1)
    elif p2.exists():
        scenes_paths.append(p2)
    else:
        print(f"Error: Missing {fn}!")

print(f"Found {len(scenes_paths)}/7 scenes for full master film assembly.")

concat_txt = base_dir / "master_film_concat.txt"
with open(concat_txt, "w") as f:
    for sc in scenes_paths:
        f.write(f"file '{sc.resolve()}'\n")

print("Rendering full master film with FFmpeg...")
subprocess.run(
    [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_txt),
        "-c", "copy",
        "-loglevel", "error", str(out_film)
    ],
    check=True
)

dur = sound_studio.get_audio_duration(out_film)
sz_mb = out_film.stat().st_size / (1024 * 1024)
print(f"\n FULL CINEMATIC MASTER MOVIE CREATED!")
print(f"Path: {out_film}")
print(f"Duration: {dur:.2f}s ({dur/60:.2f} minutes)")
print(f"Size: {sz_mb:.2f} MB")
