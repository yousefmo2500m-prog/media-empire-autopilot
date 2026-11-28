import subprocess
from pathlib import Path
import sound_studio

scene_dir = Path("/home/user/production_vault/video_eldalil_wonders/scene_05")
audio_file = Path("/tmp/eldalil_pure_egyptian_kore/scene_05.mp3")
out_video = Path("/home/user/production_vault/video_eldalil_wonders/scene_05_complete_cinematic.mp4")

# 1. Write concat list
concat_txt = scene_dir / "concat_video_list.txt"
with open(concat_txt, "w") as f:
    for i in range(1, 11):
        f_mp4 = scene_dir / f"shot_{i:02d}_animated.mp4"
        f.write(f"file '{f_mp4.resolve()}'\n")

# 2. Concat video shots and merge with audio
temp_merged_video = scene_dir / "temp_video_only.mp4"
subprocess.run(
    [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_txt),
        "-vf", "scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720",
        "-c:v", "libx264", "-preset", "fast", "-crf", "18", "-pix_fmt", "yuv420p",
        "-r", "30", "-loglevel", "error", str(temp_merged_video)
    ],
    check=True
)

v_dur = sound_studio.get_audio_duration(temp_merged_video)
a_dur = sound_studio.get_audio_duration(audio_file)
print(f"Video duration: {v_dur:.2f}s, Audio duration: {a_dur:.2f}s")

# Combine video and audio
subprocess.run(
    [
        "ffmpeg", "-y",
        "-i", str(temp_merged_video),
        "-i", str(audio_file),
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        "-loglevel", "error", str(out_video)
    ],
    check=True
)

if temp_merged_video.exists():
    temp_merged_video.unlink()

print(f"\n Scene 5 Complete Video Created!")
print(f"Path: {out_video}")
print(f"Size: {out_video.stat().st_size} bytes ({out_video.stat().st_size / (1024*1024):.2f} MB)")
