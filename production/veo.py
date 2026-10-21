import base64, json, os, sys, time
import requests

BASE = "https://generativelanguage.googleapis.com/v1beta"
MODEL = os.environ.get("VEO_MODEL", "veo-3.1-fast-generate-preview")
KEY = os.environ["GEMINI_API_KEY"]
H = {"x-goog-api-key": KEY, "Content-Type": "application/json"}

LOOK = (
    "An original fictional woman in her late 20s, strikingly attractive and camera-ready, "
    "long glossy brunette hair in soft waves, warm confident smile, brown eyes, polished natural makeup, "
    "wearing a fitted dark charcoal blazer over a black top. Setting: a sleek, dark, modern crypto trading studio "
    "with glowing green and blue candlestick price charts on large wall monitors, soft cinematic lighting, "
    "shallow depth of field, premium commercial look, photorealistic, 16:9. "
    "No on-screen text, no logos, no subtitles."
)


def b64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def run(prompt, out, ref=None, extend=None):
    inst = {"prompt": prompt}
    params = {"aspectRatio": "16:9", "resolution": "720p", "durationSeconds": 8}
    if ref:
        inst["referenceImages"] = [{"image": {"inlineData": {"mimeType": "image/png", "data": b64(ref)}}, "referenceType": "asset"}]
        params["personGeneration"] = "allow_adult"
    elif extend:
        inst["video"] = {"inlineData": {"mimeType": "video/mp4", "data": b64(extend)}}
        params["personGeneration"] = "allow_all"
    else:
        params["personGeneration"] = "allow_all"
    r = requests.post(f"{BASE}/models/{MODEL}:predictLongRunning", headers=H, json={"instances": [inst], "parameters": params}, timeout=300)
    if r.status_code != 200:
        print("SUBMIT ERROR", r.status_code, r.text[:2000]); sys.exit(1)
    op = r.json()["name"]
    print("op", op, flush=True)
    while True:
        time.sleep(10)
        s = requests.get(f"{BASE}/{op}", headers=H, timeout=60).json()
        if s.get("done"):
            break
    if "error" in s:
        print("OP ERROR", json.dumps(s["error"])[:2000]); sys.exit(1)
    resp = s["response"]["generateVideoResponse"]
    samples = resp.get("generatedSamples")
    if not samples:
        print("NO VIDEO", json.dumps(resp)[:2000]); sys.exit(1)
    uri = samples[0]["video"]["uri"]
    v = requests.get(uri, headers={"x-goog-api-key": KEY}, timeout=300, allow_redirects=True)
    v.raise_for_status()
    with open(out, "wb") as f:
        f.write(v.content)
    print("saved", out, len(v.content), flush=True)


if __name__ == "__main__":
    mode, out, prompt = sys.argv[1], sys.argv[2], sys.argv[3]
    full = LOOK + " " + prompt if mode != "extend" else prompt
    if mode == "text":
        run(full, out)
    elif mode == "ref":
        run(full, out, ref=sys.argv[4])
    elif mode == "extend":
        run(full, out, extend=sys.argv[4])
