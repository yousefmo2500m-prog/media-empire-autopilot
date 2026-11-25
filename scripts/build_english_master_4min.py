import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, '/home/user/media-empire-autopilot')
import sound_studio

FFMPEG = sound_studio.FFMPEG_BIN
eng_dir = Path("/home/user/english_build")
eng_dir.mkdir(parents=True, exist_ok=True)

# 1. Prepare English SRT Subtitles with exact timings across the 8 chapters
srt_path = eng_dir / "english_master.srt"
srt_content = """1
00:00:00,000 --> 00:00:06,500
In a single night, two disguised thieves walked into a museum...

2
00:00:06,500 --> 00:00:12,000
and vanished with the greatest treasure in human history: half a billion dollars in stolen art!

3
00:00:12,000 --> 00:00:17,500
But the real shock is not what they stole.

4
00:00:17,500 --> 00:00:23,770
It's the chilling, unsolved secret waiting at the end of this video...

5
00:00:23,770 --> 00:00:30,000
On a freezing rainy night in Boston, during St. Patrick's Day celebrations,

6
00:00:30,000 --> 00:00:36,000
a red car pulled quietly outside the historic Isabella Stewart Gardner Museum.

7
00:00:36,000 --> 00:00:43,000
Two men stepped out disguised as Boston Police officers, badges gleaming in the dark.

8
00:00:43,000 --> 00:00:50,970
They walked up to the security door... and pressed the buzzer.

9
00:00:50,970 --> 00:00:57,000
Inside the security desk, young night watchman Richard Abath watched the CRT monitors.

10
00:00:57,000 --> 00:01:03,000
Hearing police investigating a disturbance, he broke protocol and buzzed them in.

11
00:01:03,000 --> 00:01:10,000
The officer ordered: "You have a warrant out for your arrest, step out from the desk!"

12
00:01:10,000 --> 00:01:19,300
Abath stepped away from the panic button... and cold steel handcuffs snapped around his wrists!

13
00:01:19,300 --> 00:01:25,000
The guards were marched into the dark basement cellar,

14
00:01:25,000 --> 00:01:31,000
duct tape wrapped around their eyes and mouths, and handcuffed to steam pipes.

15
00:01:31,000 --> 00:01:37,000
Upstairs in the Dutch Room, the thieves stood before Rembrandt's masterpiece:

16
00:01:37,000 --> 00:01:48,900
The Storm on the Sea of Galilee. A razor slashed the centuries-old canvas from its gold frame!

17
00:01:48,900 --> 00:01:54,500
They didn't stop there. They seized Vermeer's 'The Concert'—the most valuable stolen object on Earth!

18
00:01:54,500 --> 00:02:00,000
Along with Degas drawings and a Napoleonic eagle, they collected 13 treasures worth $500M.

19
00:02:00,000 --> 00:02:08,000
In 81 minutes, they loaded the rolled canvases into their red car and vanished into the fog,

20
00:02:08,000 --> 00:02:18,360
leaving empty frames crying on the museum walls.

21
00:02:18,360 --> 00:02:24,000
At 8:00 AM, the morning relief guards found locked doors and eerie silence.

22
00:02:24,000 --> 00:02:30,000
Police broke inside and discovered the night watchmen bound in the dark basement.

23
00:02:30,000 --> 00:02:37,000
When FBI agents stepped into the Dutch Room, they froze in utter horror.

24
00:02:37,000 --> 00:02:46,000
The walls were stripped bare, severed threads dangling from empty frames...

25
00:02:46,000 --> 00:02:54,900
and the thieves were gone without leaving a single fingerprint!

26
00:02:54,900 --> 00:03:01,000
Federal investigations led straight into Boston's ruthless Italian mob.

27
00:03:01,000 --> 00:03:08,000
Informants revealed paintings were traded as 'get-out-of-jail-free' cards among mob bosses.

28
00:03:08,000 --> 00:03:15,000
But whenever anyone came close to talking to the FBI, they were silenced!

29
00:03:15,000 --> 00:03:25,190
A bloody trail of gangland murders buried the secret with the victims beneath the earth.

30
00:03:25,190 --> 00:03:31,000
To this day, the empty frames still hang waiting on the walls...

31
00:03:31,000 --> 00:03:37,000
and a $10,000,000 FBI reward remains completely unclaimed!

32
00:03:37,000 --> 00:03:42,500
Are the paintings buried underground, or hidden inside a secret billionaire's vault?

33
00:03:42,500 --> 00:03:49,560
Comment your theory below, hit Like, and Subscribe with notifications on for the next mystery!
"""
srt_path.write_text(srt_content, encoding="utf-8")
print("English master SRT generated!")

# 2. Extract clean video track from our Egyptian Master (strip audio and subtitles via cropping/re-encoding)
# Notice: In gardner_heist_egyptian_master_4min.mp4, the subtitles are in the bottom matte.
# But we can take the clean video from the raw video files or overlay English subtitles on top with opaque box!
# Even cleaner: we take the full 229.56s video from gardner_heist_egyptian_master_4min.mp4,
# apply a clean bottom black matte box over the bottom 110px, and burn in the English subtitles!
# That ensures 100% frame-perfect sync with identical visuals!

out_mp4 = Path("/home/user/gardner_heist_english_master_4min.mp4")

# Re-composite with English audio and English subtitles:
# English voice files concatenation
eng_audio_list = eng_dir / "audio_list.txt"
audio_files = [
    eng_dir / f"en_{i:02d}_{name}.mp3" for i, name in [
        (0, "hook"), (1, "arrival"), (2, "infiltration"), (3, "rembrandt"),
        (4, "vermeer"), (5, "fbi"), (6, "mafia"), (7, "outro")
    ]
]

# Adjust each English audio to exact chapter duration with padding/atempo
durations = [23.77, 27.20, 28.33, 29.60, 29.46, 36.54, 30.29, 24.33]
adjusted_audios = []

for i, (af, dur) in enumerate(zip(audio_files, durations)):
    adj_out = eng_dir / f"adj_{i:02d}.wav"
    raw_dur = sound_studio.get_audio_duration(af)
    
    # Pad or pad with silent room tone to exactly dur
    cmd = [
        FFMPEG, "-y",
        "-i", str(af),
        "-af", f"apad=whole_dur={dur:.3f}",
        "-t", f"{dur:.3f}",
        "-ar", "48000", "-ac", "2",
        str(adj_out)
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    adjusted_audios.append(adj_out)

print("Adjusted all English audio chapters to exact timeline")

concat_audio_txt = eng_dir / "concat_audio.txt"
with open(concat_audio_txt, "w") as f:
    for a in adjusted_audios:
        f.write(f"file '{a}'\n")

full_eng_audio = eng_dir / "full_english_voice.wav"
cmd_ca = [
    FFMPEG, "-y",
    "-f", "concat", "-safe", "0",
    "-i", str(concat_audio_txt),
    "-c", "copy",
    str(full_eng_audio)
]
subprocess.run(cmd_ca, check=True)
print(f"Full English voice track ready: {sound_studio.get_audio_duration(full_eng_audio):.2f}s")

# Generate continuous tension drone for English film
drone_wav = eng_dir / "eng_drone.wav"
cmd_drone = [
    FFMPEG, "-y",
    "-f", "lavfi",
    "-i", f"anoisesrc=d=229.56:c=pink:r=48000,lowpass=f=220,volume=0.22",
    str(drone_wav)
]
subprocess.run(cmd_drone, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

# Now composite: take video from gardner_heist_egyptian_master_4min.mp4,
# Black box over bottom matte to cleanly wipe Arabic text, then burn in English subtitles!
clean_box = "drawbox=y=ih-80:h=80:color=black:t=fill"
sub_filter = f"subtitles={srt_path}:force_style='Fontname=Arial,Fontsize=22,PrimaryColour=&H00FFFFFF&,SecondaryColour=&H0000FFFF&,OutlineColour=&H00000000&,BackColour=&H80000000&,BorderStyle=3,Outline=2,Shadow=1,MarginV=25,Alignment=2'"
vf = f"{clean_box},{sub_filter}"

cmd_final = [
    FFMPEG, "-y",
    "-i", "/home/user/gardner_heist_egyptian_master_4min.mp4",
    "-i", str(full_eng_audio),
    "-i", str(drone_wav),
    "-filter_complex",
    f"[0:v]{vf}[v];[1:a]volume=1.0[vce];[2:a]volume=0.10[drn];[vce][drn]amix=inputs=2:duration=first[a]",
    "-map", "[v]",
    "-map", "[a]",
    "-c:v", "libx264", "-preset", "fast", "-crf", "18",
    "-c:a", "aac", "-b:a", "192k",
    "-t", "229.56",
    str(out_mp4)
]

print("Rendering Final English 4-Minute Master...")
res = subprocess.run(cmd_final, capture_output=True, text=True)
if res.returncode != 0:
    print("FFmpeg error:", res.stderr)
    sys.exit(1)

dur = sound_studio.get_audio_duration(out_mp4)
size_mb = out_mp4.stat().st_size / (1024 * 1024)
print(f"🏆 SUCCESS: English Master Feature Created successfully!")
print(f"Path: {out_mp4}")
print(f"Duration: {dur:.2f} seconds ({dur/60:.2f} minutes)")
print(f"Size: {size_mb:.2f} MB")
