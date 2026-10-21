"""Lip-sync the presenter to vo.mp3 with MoDA (Hugging Face Space), then frame and join into head.mp4."""
import json, os, shutil, subprocess, sys, time
from gradio_client import Client, handle_file
from huggingface_hub import get_token

IMG = "presenter/p27.png"
SPACE = "multimodalart/MoDA-fast-talking-head"
TARGET = 10.0
TAIL_PAD = 1.2
W, H, FPS = 1280, 720, 30
FACE_X, FACE_Y = 0.37, 0.34
os.makedirs("head", exist_ok=True)


def probe(path):
    return float(json.loads(subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", path]))["format"]["duration"])


def split_points():
    def p(t):
        h, m, s = t.replace(",", ".").split(":")
        return int(h) * 3600 + int(m) * 60 + float(s)
    caps = []
    for b in open("vo.srt", encoding="utf-8").read().strip().split("\n\n"):
        ls = b.splitlines()
        a, z = [p(x.strip()) for x in ls[1].split("-->")]
        caps.append((a, z, " ".join(ls[2:])))
    cuts, last = [0.0], 0.0
    for i in range(len(caps) - 1):
        if caps[i][2].rstrip().endswith((".", "?", "!")) and caps[i][1] - last >= TARGET * 0.75:
            cut = (caps[i][1] + caps[i + 1][0]) / 2
            if probe("vo.mp3") - cut > 5:
                cuts.append(cut); last = cut
    cuts.append(probe("vo.mp3"))
    return cuts


def lipsync(i, wav, out):
    if os.path.exists(out):
        return
    failures = 0
    while True:
        try:
            c = Client(SPACE, token=get_token(), verbose=False)
            r = c.predict(handle_file(IMG), handle_file(wav), "Happiness", 1.2, api_name="/generate_motion")
            shutil.copy(r["video"] if isinstance(r, dict) else r, out)
            print(f"{time.strftime('%H:%M')} seg {i} ok", flush=True)
            return
        except Exception as e:
            msg = str(e)
            if "quota" in msg.lower():
                print(f"{time.strftime('%H:%M')} seg {i}: GPU quota empty, retrying in 20 min", flush=True)
                time.sleep(1200)
                continue
            failures += 1
            print(f"{time.strftime('%H:%M')} seg {i} error {failures}: {msg[:300]}", flush=True)
            if failures >= 6:
                sys.exit(f"segment {i} failed")
            time.sleep(60)


def frame(i, src, dur, out):
    up = f"scale={W * 2}:{H * 2}:force_original_aspect_ratio=increase,crop={W * 2}:{H * 2},fps={FPS}"
    n = max(int(dur * FPS), 1)
    if i % 2 == 0:
        z = f"1+0.12*on/{n}"
    else:
        z = f"1.42+0.05*on/{n}"
    zp = (f"zoompan=z='{z}':x='max(0,min(iw-iw/zoom,iw*{FACE_X}-iw/zoom/2))'"
          f":y='max(0,min(ih-ih/zoom,ih*{FACE_Y}-ih/zoom/2))':d=1:s={W}x{H}:fps={FPS}")
    vf = f"{up},{zp},tpad=stop_mode=clone:stop_duration=2,trim=duration={dur:.3f},setpts=PTS-STARTPTS,format=yuv420p"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", src, "-an", "-vf", vf, "-c:v", "libx264", "-crf", "16", "-preset", "fast", out], check=True)


def main():
    cuts = split_points()
    print("cuts", [round(c, 2) for c in cuts])
    parts = []
    for i in range(len(cuts) - 1):
        a, b = cuts[i], cuts[i + 1]
        last = i == len(cuts) - 2
        wav = f"head/a{i}.wav"
        af = ["-af", f"apad=pad_dur={TAIL_PAD}"] if last else []
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", "vo.mp3", "-ss", f"{a:.3f}", "-to", f"{b:.3f}", *af,
                        "-ar", "16000", "-ac", "1", wav], check=True)
        dur = (round(b * FPS) - round(a * FPS)) / FPS + (TAIL_PAD if last else 0)
        raw = f"head/raw{i}.mp4"
        lipsync(i, wav, raw)
        fr = f"head/f{i}.mp4"
        frame(i, raw, dur, fr)
        parts.append(fr)
    with open("head/list.txt", "w") as f:
        f.writelines(f"file '{os.path.basename(p)}'\n" for p in parts)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", "head/list.txt", "-c", "copy", "head.mp4"], check=True)
    print("head.mp4", round(probe("head.mp4"), 2), "s; vo", round(probe("vo.mp3"), 2), "s")


if __name__ == "__main__":
    main()
