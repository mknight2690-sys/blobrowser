import asyncio, re, sys
import edge_tts

VOICE = "en-US-AvaNeural"
RATE = sys.argv[1] if len(sys.argv) > 1 else "+0%"

DISPLAY = {
    "one ninety-nine a month": "$199/mo",
    "nineteen ninety a year": "$1,990/yr",
    "thirty-nine ninety-seven": "$3,997",
    "five hundred dollars": "$500",
    "fifteen-thousand-dollar": "$15,000",
}


def ts(t):
    h, rem = divmod(t, 3600)
    m, s = divmod(rem, 60)
    return f"{int(h):02d}:{int(m):02d}:{s:06.3f}".replace(".", ",")


async def main():
    text = open("voiceover.txt", encoding="utf-8").read().strip()
    com = edge_tts.Communicate(text, VOICE, rate=RATE, boundary="WordBoundary")
    words = []
    with open("vo.mp3", "wb") as f:
        async for c in com.stream():
            if c["type"] == "audio":
                f.write(c["data"])
            elif c["type"] == "WordBoundary":
                words.append((c["offset"] / 1e7, (c["offset"] + c["duration"]) / 1e7, c["text"]))

    toks = text.split()
    assert len(toks) == len(words), (len(toks), len(words))
    words = [(s, e, t) for (s, e, _), t in zip(words, toks)]

    for phrase, disp in DISPLAY.items():
        n = len(phrase.split())
        i = 0
        while i <= len(words) - n:
            seg = " ".join(w[2] for w in words[i:i + n])
            core = re.sub(r"[.,:?!]+$", "", seg)
            if core == phrase:
                tail = seg[len(core):]
                words[i:i + n] = [(words[i][0], words[i + n - 1][1], disp + tail)]
            i += 1

    lines, cur = [], []
    for w in words:
        cur.append(w)
        joined = " ".join(x[2] for x in cur)
        sentence_end = re.search(r"[.?!]$", w[2]) is not None
        pause = re.search(r"[,:]$", w[2]) is not None
        if sentence_end or (pause and len(cur) >= 3) or len(cur) >= 7 or len(joined) > 36:
            lines.append(cur); cur = []
    if cur:
        lines.append(cur)

    srt = []
    for i, ln in enumerate(lines, 1):
        start, end = ln[0][0], ln[-1][1]
        if i < len(lines):
            end = max(end, min(lines[i][0][0] - 0.02, end + 0.4))
        txt = " ".join(x[2] for x in ln)
        srt.append(f"{i}\n{ts(start)} --> {ts(end)}\n{txt}\n")
    open("vo.srt", "w", encoding="utf-8").write("\n".join(srt))
    print("words", len(words), "captions", len(lines), "last", words[-1][1])


asyncio.run(main())
