import subprocess
import sys
from pathlib import Path

sys.path.insert(0, '/home/user/media-empire-autopilot')
import sound_studio

FFMPEG = sound_studio.FFMPEG_BIN

segments = [
    Path("/home/user/scene_00_hook_blockbuster.mp4"),
    Path("/home/user/scene_01_egyptian_blockbuster.mp4"),
    Path("/home/user/scene_02_egyptian_blockbuster.mp4"),
    Path("/home/user/scene_03_egyptian_blockbuster.mp4"),
    Path("/home/user/scene_04_egyptian_blockbuster.mp4"),
    Path("/home/user/scene_05_egyptian_blockbuster.mp4"),
    Path("/home/user/scene_06_egyptian_blockbuster.mp4"),
    Path("/home/user/scene_07_outro_blockbuster.mp4")
]

for s in segments:
    if not s.exists():
        raise FileNotFoundError(f"Missing segment: {s}")
    print(f"Segment: {s.name} -> {sound_studio.get_audio_duration(s):.2f}s")

master_concat = Path("/home/user/master_concat_list.txt")
with open(master_concat, "w") as f:
    for s in segments:
        f.write(f"file '{s}'\n")

final_master = Path("/home/user/gardner_heist_egyptian_master_4min.mp4")

# Re-encode seamlessly with matching audio sample rate 48kHz stereo and 1280x720 24fps
cmd = [
    FFMPEG, "-y",
    "-f", "concat", "-safe", "0",
    "-i", str(master_concat),
    "-c:v", "libx264", "-preset", "medium", "-crf", "18",
    "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
    str(final_master)
]

print("Rendering Final 4-Minute Master Feature...")
res = subprocess.run(cmd, capture_output=True, text=True)
if res.returncode != 0:
    print("FFmpeg error:", res.stderr)
    sys.exit(1)

dur = sound_studio.get_audio_duration(final_master)
size_mb = final_master.stat().st_size / (1024 * 1024)
print(f"🏆 SUCCESS: Ultimate Master Film Created!")
print(f"Path: {final_master}")
print(f"Duration: {dur:.2f} seconds ({dur/60:.2f} minutes)")
print(f"Size: {size_mb:.2f} MB")
