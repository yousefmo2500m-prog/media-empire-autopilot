import subprocess
from pathlib import Path
import imageio_ffmpeg
import sound_studio

ffmpeg_bin = imageio_ffmpeg.get_ffmpeg_exe()
work_dir = Path("/tmp/room_1046_kore_official")
out_dir = Path("/home/user/media-empire-autopilot/production_vault/video_01_room_1046")
out_dir.mkdir(parents=True, exist_ok=True)

# 1. Create 0.65s silence
pause_mp3 = work_dir / "pause.mp3"
subprocess.run(
    [
        ffmpeg_bin, "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono",
        "-t", "0.65", "-c:a", "libmp3lame", "-b:a", "192k", "-loglevel", "error", str(pause_mp3)
    ],
    check=True
)

# 2. Concat list
concat_list = work_dir / "concat_list.txt"
with open(concat_list, "w") as f:
    for i in range(1, 7):
        sc_file = work_dir / f"scene_{i:02d}.mp3"
        f.write(f"file '{sc_file.resolve()}'\n")
        if i < 6:
            f.write(f"file '{pause_mp3.resolve()}'\n")

# 3. Merge raw voice
raw_voice_path = out_dir / "audio_room_1046_egyptian_raw_voice.mp3"
subprocess.run(
    [
        ffmpeg_bin, "-y", "-f", "concat", "-safe", "0", "-i", str(concat_list),
        "-c:a", "libmp3lame", "-b:a", "192k", "-loglevel", "error", str(raw_voice_path)
    ],
    check=True
)
print("Raw voice merged successfully! Duration:", sound_studio.get_audio_duration(raw_voice_path))

# 4. Generate tension bed
tension_wav = sound_studio._build_psychological_tension_bed(work_dir / "tension_bed.wav", duration_sec=60.0)

# 5. Master audio with subtle background drone
master_mp3 = out_dir / "audio_room_1046_egyptian_master.mp3"
subprocess.run(
    [
        ffmpeg_bin, "-y",
        "-i", str(raw_voice_path),
        "-stream_loop", "-1", "-i", str(tension_wav),
        "-filter_complex",
        "[0:a]acompressor=threshold=-16dB:ratio=2.8:attack=5:release=60,loudnorm=I=-16:TP=-1.5:LRA=9[v];"
        "[1:a]volume=0.08[bg];"
        "[v][bg]amix=inputs=2:duration=first:dropout_transition=2[out]",
        "-map", "[out]",
        "-ar", "44100", "-ac", "2", "-c:a", "libmp3lame", "-b:a", "192k",
        "-loglevel", "error", str(master_mp3)
    ],
    check=True
)
dur = sound_studio.get_audio_duration(master_mp3)
print(f"Master audio created! Path: {master_mp3}, Duration: {dur:.2f}s ({dur/60:.2f} min), Size: {master_mp3.stat().st_size} bytes")

# Copy to voice_samples for easy access
samples_dir = Path("/home/user/media-empire-autopilot/voice_samples")
samples_dir.mkdir(parents=True, exist_ok=True)
sample_master = samples_dir / "audio_room_1046_egyptian_master_kore.mp3"
import shutil
shutil.copy2(master_mp3, sample_master)
print(f"Copied to {sample_master}")
