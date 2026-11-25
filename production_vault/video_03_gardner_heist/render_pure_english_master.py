import subprocess
from pathlib import Path
import sys

sys.path.insert(0, '/home/user/media-empire-autopilot')
import sound_studio

ffmpeg = sound_studio.FFMPEG_BIN

video_in = Path("/home/user/.cache/pure_master_video.mp4")
voice_in = Path("/home/user/english_charon/full_charon_voice.wav")
srt_path = Path("/home/user/english_master.srt")

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

drone_wav = Path("/home/user/.cache/eng_drone.wav")
cmd_dr = [
    ffmpeg, "-y",
    "-f", "lavfi",
    "-i", "anoisesrc=d=229.5:c=pink:r=48000,lowpass=f=220,volume=0.22",
    str(drone_wav)
]
subprocess.run(cmd_dr, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

out_final = Path("/home/user/gardner_heist_english_master_4min.mp4")

scope_filter = "drawbox=y=0:h=48:color=black:t=fill,drawbox=y=ih-48:h=48:color=black:t=fill"
sub_filter = f"subtitles={srt_path}:force_style='Fontname=Arial,Fontsize=22,PrimaryColour=&H00FFFFFF&,SecondaryColour=&H0000FFFF&,OutlineColour=&H00000000&,BackColour=&H80000000&,BorderStyle=3,Outline=2,Shadow=1,MarginV=30,Alignment=2'"
vf = f"{scope_filter},{sub_filter}"

cmd = [
    ffmpeg, "-y",
    "-i", str(video_in),
    "-i", str(voice_in),
    "-i", str(drone_wav),
    "-filter_complex",
    f"[0:v]{vf}[v];[1:a]volume=1.0[vce];[2:a]volume=0.10[drn];[vce][drn]amix=inputs=2:duration=first[a]",
    "-map", "[v]",
    "-map", "[a]",
    "-c:v", "libx264", "-preset", "ultrafast", "-crf", "22",
    "-c:a", "aac", "-b:a", "160k",
    "-t", "229.3",
    str(out_final)
]

print("Rendering 100% PURE English Master (ZERO Arabic text)...")
res = subprocess.run(cmd, capture_output=True, text=True)
if res.returncode != 0:
    print("FFmpeg error:", res.stderr)
    sys.exit(1)

dur = sound_studio.get_audio_duration(out_final)
size_mb = out_final.stat().st_size / (1024 * 1024)
print(f"🏆 SUCCESS: 100% PURE English Master Film Created!")
print(f"Path: {out_final}")
print(f"Duration: {dur:.2f}s ({dur/60:.2f} min), Size: {size_mb:.2f} MB")
