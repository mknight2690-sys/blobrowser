"""Build head.mp4 from whatever lip-sync exists: frames head/raw{i}.mp4 where present and
fills the other segments with branded feature cards. No GPU needed."""
import os, subprocess
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from make_head import frame

W, H, FPS = 1280, 720, 30
CUTS = [0.0, 11.83, 20.1, 29.99, 38.61, 49.25, 60.55]
TAIL_PAD = 1.2
FONTS = r"C:\Windows\Fonts"
MINT, BLUE, VIOLET, TXT, MUT = (124, 247, 197), (91, 140, 255), (196, 107, 255), (232, 236, 245), (150, 158, 180)

CARDS = {
    3: ("// THE RECOVERY ENGINE", [("DCA recovery", "Scales in at better prices"),
                                   ("Leverage step-down", "Less exposure the deeper it goes"),
                                   ("Winner-first harvesting", "Banks the green")]),
    4: ("// THE MATTHEW METRIC", None),
    5: ("// CHOOSE YOUR PLAN", [("$199/mo", "Monthly"), ("$1,990/yr", "Annual · best value"), ("$3,997", "Lifetime founder")]),
}


def f(name, size):
    return ImageFont.truetype(os.path.join(FONTS, name), size)


def base():
    bg = Image.open("presenter/p27.png").convert("RGB").resize((W, H))
    bg = bg.filter(ImageFilter.GaussianBlur(18))
    return Image.blend(bg, Image.new("RGB", (W, H), (6, 7, 11)), 0.72)


def grad_text(img, xy, text, fnt):
    mask = Image.new("L", img.size, 0)
    ImageDraw.Draw(mask).text(xy, text, font=fnt, fill=255, anchor="mm")
    g = Image.new("RGB", img.size)
    d = ImageDraw.Draw(g)
    for x in range(W):
        t = x / (W - 1) * 2
        a, b = (MINT, BLUE) if t < 1 else (BLUE, VIOLET)
        k = t if t < 1 else t - 1
        d.line([(x, 0), (x, H)], fill=tuple(int(a[i] + (b[i] - a[i]) * k) for i in range(3)))
    img.paste(g, (0, 0), mask)


def card(i):
    img = base()
    d = ImageDraw.Draw(img, "RGBA")
    eyebrow, items = CARDS[i]
    d.text((W // 2, 118), eyebrow, font=f("consola.ttf", 24), fill=MINT, anchor="mm")
    if i == 4:
        d.text((W // 2, 200), "Withdrawable cash, not paper gains", font=f("segoeuib.ttf", 46), fill=TXT, anchor="mm")
        grad_text(img, (W // 2, 340), "~$500 / week", f("segoeuib.ttf", 128))
        d.text((W // 2, 445), "on a $15,000 account", font=f("seguisb.ttf", 36), fill=TXT, anchor="mm")
        d.text((W // 2, 500), "Developer-reported figure. Not a guarantee.", font=f("segoeui.ttf", 22), fill=MUT, anchor="mm")
    else:
        n = len(items)
        cw, gap = 340, 30
        x0 = (W - (n * cw + (n - 1) * gap)) // 2
        for k, (title, sub) in enumerate(items):
            x = x0 + k * (cw + gap)
            box = (x, 200, x + cw, 470)
            hot = i == 5 and k == 1
            d.rounded_rectangle(box, radius=22, fill=(15, 18, 27, 225), outline=MINT if hot else (45, 53, 80), width=3 if hot else 2)
            cx = x + cw // 2
            if i == 5:
                grad_text(img, (cx, 310), title, f("segoeuib.ttf", 58))
                d = ImageDraw.Draw(img, "RGBA")
                d.text((cx, 385), sub, font=f("seguisb.ttf", 26), fill=TXT, anchor="mm")
            else:
                d.ellipse((cx - 26, 240, cx + 26, 292), fill=(124, 247, 197, 40), outline=MINT, width=2)
                d.text((cx, 266), "✓", font=f("seguisym.ttf", 30), fill=MINT, anchor="mm")
                d.text((cx, 345), title, font=f("segoeuib.ttf", 28), fill=TXT, anchor="mm")
                d.text((cx, 395), sub, font=f("segoeui.ttf", 22), fill=MUT, anchor="mm")
    path = f"head/card{i}.png"
    img.save(path)
    return path


def seg_dur(i):
    a, b = CUTS[i], CUTS[i + 1]
    return (round(b * FPS) - round(a * FPS)) / FPS + (TAIL_PAD if i == len(CUTS) - 2 else 0)


def render(i):
    dur = seg_dur(i)
    n = int(round(dur * FPS))
    src = card(i)
    vf = (f"scale={W * 2}:{H * 2},zoompan=z='1+0.05*on/{n}':x='iw/2-iw/zoom/2':y='ih/2-ih/zoom/2':d={n}:s={W}x{H}:fps={FPS},"
          f"fade=t=in:st=0:d=0.35,trim=duration={dur:.3f},setpts=PTS-STARTPTS,format=yuv420p")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-loop", "1", "-framerate", str(FPS), "-t", f"{dur:.3f}", "-i", src,
                    "-vf", vf, "-c:v", "libx264", "-crf", "16", "-preset", "fast", f"head/f{i}.mp4"], check=True)
    print("broll", i, dur)


for i in range(len(CUTS) - 1):
    if os.path.exists(f"head/raw{i}.mp4"):
        frame(i, f"head/raw{i}.mp4", seg_dur(i), f"head/f{i}.mp4")
        print("talking", i)
    elif i in CARDS:
        render(i)
    else:
        raise SystemExit(f"segment {i} has no lip-sync and no card; run make_head.py")

parts = [f"f{i}.mp4" for i in range(len(CUTS) - 1)]
open("head/list.txt", "w").writelines(f"file '{p}'\n" for p in parts)
subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", "head/list.txt", "-c", "copy", "head.mp4"], check=True)
print("head.mp4 rebuilt")
