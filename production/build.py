"""Assemble the BloBrowser promo from head.mp4 + vo.mp3 + vo.srt.

Usage (from production/): python build.py [out_dir]   (default: ../media, the live site folder)
"""
import json, os, re, subprocess, sys
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H, FPS = 1280, 720, 30
TITLE_DUR, END_DUR, XF = 2.5, 3.5, 0.5
VO_DELAY = TITLE_DUR - XF
MAX_BYTES = 12 * 1024 * 1024
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join("..", "media")
CLIPS = ["head.mp4"]
POSTER_SRC = "presenter/p27.png"
FONTS = r"C:\Windows\Fonts"


def font(name, size):
    return ImageFont.truetype(os.path.join(FONTS, name), size)


def dur(path):
    out = subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", path])
    return float(json.loads(out)["format"]["duration"])


def backdrop():
    img = Image.new("RGB", (W, H), (6, 7, 11))
    glow = Image.new("RGB", (W, H), (0, 0, 0))
    d = ImageDraw.Draw(glow)
    d.ellipse((140, -120, 720, 380), fill=(30, 50, 120))
    d.ellipse((620, -80, 1200, 360), fill=(70, 30, 110))
    d.ellipse((380, 300, 900, 720), fill=(20, 80, 65))
    glow = glow.filter(ImageFilter.GaussianBlur(140))
    img = Image.blend(img, glow, 0.55)
    d = ImageDraw.Draw(img)
    for x in range(0, W, 56):
        d.line([(x, 0), (x, H)], fill=(16, 19, 30))
    for y in range(0, H, 56):
        d.line([(0, y), (W, y)], fill=(16, 19, 30))
    return img


def gradient_text(img, xy, text, fnt):
    mask = Image.new("L", img.size, 0)
    ImageDraw.Draw(mask).text(xy, text, font=fnt, fill=255, anchor="mm")
    grad = Image.new("RGB", img.size)
    gd = ImageDraw.Draw(grad)
    stops = [(124, 247, 197), (91, 140, 255), (196, 107, 255)]
    for x in range(W):
        t = x / (W - 1) * 2
        a, b = (stops[0], stops[1]) if t < 1 else (stops[1], stops[2])
        f = t if t < 1 else t - 1
        gd.line([(x, 0), (x, H)], fill=tuple(int(a[i] + (b[i] - a[i]) * f) for i in range(3)))
    img.paste(grad, (0, 0), mask)


def blob(img, cx, cy, r):
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for i in range(r, 0, -1):
        t = i / r
        col = (int(124 + (196 - 124) * t), int(247 + (107 - 247) * t), int(197 + (255 - 197) * t), 255)
        d.ellipse((cx - i, cy - i * 0.92, cx + i, cy + i * 0.92), fill=col)
    halo = layer.filter(ImageFilter.GaussianBlur(28))
    img.paste(halo, (0, 0), halo)
    img.paste(layer, (0, 0), layer)


def cards():
    t = backdrop()
    blob(t, W // 2, 250, 54)
    d = ImageDraw.Draw(t)
    d.text((W // 2, 375), "BloBrowser", font=font("segoeuib.ttf", 96), fill=(232, 236, 245), anchor="mm")
    gradient_text(t, (W // 2, 455), "AI trading engine for BloFin", font("seguisb.ttf", 38))
    d.text((W // 2, 520), "Harmonics  ·  Cadence  ·  Momentum  ·  Pulse", font=font("consola.ttf", 22), fill=(138, 147, 168), anchor="mm")
    t.save("title.png")

    e = backdrop()
    d = ImageDraw.Draw(e)
    d.text((W // 2, 230), "Choose your plan below", font=font("segoeuib.ttf", 72), fill=(232, 236, 245), anchor="mm")
    gradient_text(e, (W // 2, 330), "$199/mo   ·   $1,990/yr   ·   $3,997 lifetime", font("seguisb.ttf", 40))
    bx = (W // 2 - 170, 405, W // 2 + 170, 467)
    d.rounded_rectangle(bx, radius=14, outline=(124, 247, 197), width=3)
    d.text((W // 2, 436), "See Pricing  ↓", font=font("segoeuib.ttf", 28), fill=(124, 247, 197), anchor="mm")
    d.text((W // 2, 540), "Developer-reported results. Not financial advice. Leveraged trading carries serious risk.",
           font=font("segoeui.ttf", 20), fill=(110, 118, 140), anchor="mm")
    e.save("end.png")


def srt_to_ass(delay):
    def parse(t):
        h, m, s = t.replace(",", ".").split(":")
        return int(h) * 3600 + int(m) * 60 + float(s) + delay

    def fmt(x):
        h, r = divmod(x, 3600)
        m, s = divmod(r, 60)
        return f"{int(h)}:{int(m):02d}:{s:05.2f}"

    blocks = open("vo.srt", encoding="utf-8").read().strip().split("\n\n")
    ev = []
    for b in blocks:
        ls = b.splitlines()
        a, z = [parse(x.strip()) for x in ls[1].split("-->")]
        ev.append(f"Dialogue: 0,{fmt(a)},{fmt(z)},Cap,,0,0,0,,{' '.join(ls[2:])}")
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,Segoe UI Semibold,40,&H00FFFFFF,&H00FFFFFF,&H00000000,&H96000000,0,0,0,0,100,100,0.5,0,1,2.6,1.5,2,80,80,78,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    open("captions.ass", "w", encoding="utf-8").write(head + "\n".join(ev) + "\n")


def build():
    os.makedirs(OUT, exist_ok=True)
    cards()
    srt_to_ass(VO_DELAY)
    lens = [TITLE_DUR] + [dur(c) for c in CLIPS] + [END_DUR]
    total = sum(lens) - XF * (len(lens) - 1)

    args = ["ffmpeg", "-y", "-v", "error", "-loop", "1", "-t", str(TITLE_DUR), "-i", "title.png"]
    for c in CLIPS:
        args += ["-i", c]
    args += ["-loop", "1", "-t", str(END_DUR), "-i", "end.png", "-i", "vo.mp3"]

    norm = ",".join([f"scale={W}:{H}:force_original_aspect_ratio=increase", f"crop={W}:{H}", f"fps={FPS}", "setsar=1", "format=yuv420p"])
    f = [f"[{i}:v]{norm},trim=duration={lens[i]},setpts=PTS-STARTPTS[v{i}]" for i in range(len(lens))]
    prev, off = "v0", 0.0
    for i in range(1, len(lens)):
        off += lens[i - 1] - XF
        nxt = f"x{i}"
        f.append(f"[{prev}][v{i}]xfade=transition=fade:duration={XF}:offset={off:.3f}[{nxt}]")
        prev = nxt
    f.append(f"[{prev}]ass=captions.ass,fade=t=out:st={total - 0.6:.3f}:d=0.6[vout]")
    vo_idx = len(lens)
    ms = int(VO_DELAY * 1000)
    f.append(f"[{vo_idx}:a]adelay={ms}|{ms},apad,atrim=duration={total:.3f},afade=t=out:st={total - 0.6:.3f}:d=0.6,loudnorm=I=-16:TP=-1.5:LRA=11[aout]")

    out_mp4 = os.path.join(OUT, "blobrowser-promo.mp4")
    for kbps in (1300, 1050, 850):
        cmd = args + ["-filter_complex", ";".join(f), "-map", "[vout]", "-map", "[aout]",
                      "-c:v", "libx264", "-preset", "slow", "-profile:v", "high", "-crf", "23",
                      "-maxrate", f"{kbps}k", "-bufsize", f"{kbps * 2}k", "-pix_fmt", "yuv420p",
                      "-c:a", "aac", "-b:a", "128k", "-ar", "48000", "-movflags", "+faststart", "-t", f"{total:.3f}", out_mp4]
        subprocess.run(cmd, check=True)
        size = os.path.getsize(out_mp4)
        print(f"encoded at maxrate {kbps}k -> {size / 1048576:.2f} MB, {total:.1f}s")
        if size < MAX_BYTES:
            break
    else:
        sys.exit("could not get under 12 MB")

    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", POSTER_SRC, "-frames:v", "1", "-vf", f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}", "-q:v", "3",
                    os.path.join(OUT, "blobrowser-promo.jpg")], check=True)
    print("poster saved")


if __name__ == "__main__":
    build()
