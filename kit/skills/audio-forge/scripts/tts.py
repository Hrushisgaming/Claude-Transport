#!/usr/bin/env python3
"""tts.py -- text to speech with automatic engine choice and a guaranteed offline fallback.

  python3 tts.py --text "Hello there" --out hello.wav
  python3 tts.py --file script.txt --engine kokoro --voice af_heart --speed 1.05 --out vo.wav
  python3 tts.py --text "Run." --voice-fx robot --out robot.wav
  python3 tts.py --list                                  # which engines are installed + voices

Engines (best first when --engine auto):
  kokoro   natural, 54 voices (en-US/UK, es, fr, hi, it, ja, pt, zh), ~350 MB model (optional download)   pip kokoro-onnx
  piper    good, fast, ~60 MB per voice, many languages (optional download)         pip piper-tts
  say      macOS built-in voices (free, nothing to install)
  espeak   robotic but tiny (apt/brew install espeak-ng), 100+ languages
  formant  built-in last-resort placeholder (pure numpy). Timing tests only - NOT for final audio.
Voice FX (--voice-fx): robot radio cave deep chipmunk whisper telephone demon
"""
import argparse, hashlib, json, os, shutil, subprocess, sys, tempfile, urllib.request
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from forge import dsp
from forge.song import write_wav, read_wav

CACHE = os.path.expanduser(os.environ.get("AUDIO_FORGE_HOME", "~/.cache/audio-forge"))
VOICES = os.path.join(CACHE, "voices")
OUT_SR = 44100

KOKORO_URLS = ["https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx",
               "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin"]
KOKORO_VOICES = ("af_alloy af_aoede af_bella af_heart af_jessica af_kore af_nicole af_nova af_river af_sarah af_sky "
                 "am_adam am_echo am_eric am_fenrir am_liam am_michael am_onyx am_puck am_santa "
                 "bf_alice bf_emma bf_isabella bf_lily bm_daniel bm_fable bm_george bm_lewis "
                 "ef_dora em_alex em_santa ff_siwis hf_alpha hf_beta hm_omega hm_psi if_sara im_nicola "
                 "jf_alpha jf_gongitsune jf_nezumi jf_tebukuro jm_kumo pf_dora pm_alex pm_santa "
                 "zf_xiaobei zf_xiaoni zf_xiaoxiao zf_xiaoyi zm_yunjian zm_yunxi zm_yunxia zm_yunyang").split()
# first letter of a Kokoro voice picks its language (a=American b=British e=Spanish f=French h=Hindi i=Italian j=Japanese p=Portuguese z=Chinese)
KOKORO_LANG = dict(a="en-us", b="en-gb", e="es", f="fr-fr", h="hi", i="it", j="ja", p="pt-br", z="cmn")
PIPER_DEFAULT = "en_US-lessac-medium"


def have(x):
    return shutil.which(x) is not None


def available():
    out = {}
    try:
        import kokoro_onnx  # noqa
        out["kokoro"] = os.path.exists(os.path.join(VOICES, "kokoro-v1.0.onnx")) and "ready" or "package ok, model not downloaded"
    except Exception:
        out["kokoro"] = None
    try:
        import piper  # noqa
        out["piper"] = "ready" if any(f.endswith(".onnx") for f in (os.listdir(VOICES) if os.path.isdir(VOICES) else [])) else "package ok, no voice downloaded"
    except Exception:
        out["piper"] = "ready" if have("piper") else None
    out["say"] = "ready" if have("say") else None
    out["espeak"] = "ready" if (have("espeak-ng") or have("espeak")) else None
    out["formant"] = "ready (placeholder quality)"
    return out


def pick_engine():
    a = available()
    for e in ("kokoro", "piper", "say", "espeak"):
        if a.get(e) == "ready":
            return e
    return "formant"


def download(url, dest):
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    if os.path.exists(dest):
        return dest
    print(f"downloading {os.path.basename(dest)} ...", file=sys.stderr)
    urllib.request.urlretrieve(url, dest + ".part")
    os.rename(dest + ".part", dest)
    return dest


def piper_voice_files(voice):
    lang, name, q = voice.split("-")
    base = f"https://huggingface.co/rhasspy/piper-voices/resolve/main/{lang.split('_')[0]}/{lang}/{name}/{q}/{voice}"
    return download(base + ".onnx", os.path.join(VOICES, voice + ".onnx")), download(base + ".onnx.json", os.path.join(VOICES, voice + ".onnx.json"))


# ── engines: each returns (float mono array, sample_rate) ───────────────────
def eng_kokoro(text, voice=None, speed=1.0, lang="en-us"):
    from kokoro_onnx import Kokoro
    m = download(KOKORO_URLS[0], os.path.join(VOICES, "kokoro-v1.0.onnx"))
    v = download(KOKORO_URLS[1], os.path.join(VOICES, "voices-v1.0.bin"))
    k = Kokoro(m, v)
    voice = voice or "af_heart"
    x, sr = k.create(text, voice=voice, speed=speed, lang=lang or KOKORO_LANG.get(voice[:1], "en-us"))
    return np.asarray(x, dtype=float), sr


def eng_piper(text, voice=None, speed=1.0, lang=None):
    voice = voice or PIPER_DEFAULT
    onnx, cfg = piper_voice_files(voice)
    out = tempfile.mktemp(suffix=".wav")
    cmd = [sys.executable, "-m", "piper", "--model", onnx, "--output_file", out, "--length-scale", str(1.0 / max(speed, 0.1))] if not have("piper") else \
          ["piper", "--model", onnx, "--output_file", out, "--length_scale", str(1.0 / max(speed, 0.1))]
    r = subprocess.run(cmd, input=text, text=True, capture_output=True)
    if r.returncode != 0 or not os.path.exists(out):
        raise RuntimeError("piper failed: " + r.stderr[-400:])
    sr, x = read_wav(out)
    os.remove(out)
    return (x if x.ndim == 1 else x.mean(axis=1)), sr


def eng_espeak(text, voice=None, speed=1.0, lang=None):
    exe = "espeak-ng" if have("espeak-ng") else "espeak"
    out = tempfile.mktemp(suffix=".wav")
    subprocess.run([exe, "-v", voice or lang or "en-us", "-s", str(int(165 * speed)), "-w", out, text], check=True, capture_output=True)
    sr, x = read_wav(out)
    os.remove(out)
    return (x if x.ndim == 1 else x.mean(axis=1)), sr


def eng_say(text, voice=None, speed=1.0, lang=None):
    aiff, wav = tempfile.mktemp(suffix=".aiff"), tempfile.mktemp(suffix=".wav")
    cmd = ["say", "-r", str(int(180 * speed)), "-o", aiff] + (["-v", voice] if voice else []) + [text]
    subprocess.run(cmd, check=True, capture_output=True)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", aiff, "-ac", "1", "-ar", str(OUT_SR), wav], check=True)
    sr, x = read_wav(wav)
    os.remove(aiff); os.remove(wav)
    return x, sr


_V = {"a": "a", "e": "e", "i": "e", "o": "o", "u": "u", "y": "e"}
_FORM = {"a": [(800, 90, 1), (1200, 110, .5)], "e": [(450, 80, 1), (1900, 100, .5)], "o": [(500, 80, 1), (850, 90, .4)],
         "u": [(320, 70, 1), (800, 80, .3)]}


def eng_formant(text, voice=None, speed=1.0, lang=None):
    """crude vowel/consonant buzz. Intelligibility ~0; useful only to test timing pipelines offline."""
    sr = OUT_SR
    rng = np.random.RandomState(abs(hash(text)) % 2 ** 31)
    out, t = [], 0
    base = 120 if (voice or "") != "high" else 190
    for word in text.split():
        pitch = base * (1 + 0.15 * rng.randn())
        for ch in word.lower():
            if ch.isalpha():
                n = int(0.075 / speed * sr)
                if ch in "aeiouy":
                    src = dsp.osc("saw", pitch * (1 + 0.1 * np.linspace(0, 1, n)), n, sr)
                    seg = dsp.formant(src, _FORM[_V[ch]], sr) * dsp.adsr(n, 0.01, 0.02, 0.9, 0.02, sr)
                else:
                    nz = np.random.uniform(-1, 1, n)
                    seg = dsp.bp(nz, 2500, 7000, sr) * 0.35 * dsp.adsr(n, 0.005, 0.02, 0.5, 0.02, sr) if ch in "sfhzxc" else \
                          dsp.lp(dsp.osc("saw", pitch, n, sr), 500, sr) * 0.5 * dsp.adsr(n, 0.005, 0.02, 0.7, 0.02, sr)
                out.append(seg)
        out.append(np.zeros(int(0.07 / speed * sr)))
        if word[-1] in ".,!?;:":
            out.append(np.zeros(int(0.22 / speed * sr)))
    x = np.concatenate(out) if out else np.zeros(100)
    return dsp.normalize(x, -6.0) * 0.8, sr


ENGINES = dict(kokoro=eng_kokoro, piper=eng_piper, say=eng_say, espeak=eng_espeak, formant=eng_formant)


def resample(x, sr_in, sr_out=OUT_SR):
    if sr_in == sr_out:
        return x
    from scipy.signal import resample_poly
    from math import gcd
    g = gcd(int(sr_in), int(sr_out))
    return resample_poly(x, sr_out // g, sr_in // g)


def trim_silence(x, thresh=0.003, pad=0.04, sr=OUT_SR):
    idx = np.where(np.abs(x) > thresh)[0]
    if len(idx) == 0:
        return x
    return x[max(idx[0] - int(pad * sr), 0): idx[-1] + int(pad * sr)]


def voice_fx(x, name, sr=OUT_SR):
    if not name:
        return x
    if name == "robot":
        t = np.arange(len(x)) / sr
        return dsp.normalize(x * (0.4 + 0.6 * np.sign(np.sin(2 * np.pi * 70 * t))) * 1.3, -3)
    if name == "radio":
        return dsp.distort(dsp.bp(x, 400, 3400, sr, 2) * 2.5, 2.0)
    if name == "telephone":
        return dsp.bp(x, 300, 3000, sr, 3) * 1.6
    if name == "cave":
        return dsp.reverb(x, 0.5, 3.5, sr)[:, 0] * 1.0
    if name in ("deep", "demon", "chipmunk"):
        r = {"deep": 0.82, "demon": 0.7, "chipmunk": 1.45}[name]
        y = resample(x, sr * r, sr) if r != 1 else x  # changes pitch AND speed (classic)
        if name == "demon":
            y = dsp.reverb(dsp.distort(y * 1.5, 2.0), 0.35, 2.5, sr)[:, 0] + dsp.delay(y * 0, 0.03)
        return y
    if name == "whisper":
        nz = np.random.uniform(-1, 1, len(x))
        env = np.abs(dsp.lp(np.abs(x), 60, sr, 1))
        return dsp.bp(nz, 1000, 7000, sr) * env * 4
    raise SystemExit("unknown --voice-fx " + name)


def synth(text, engine="auto", voice=None, speed=1.0, lang=None, fx=None, cache=True, strip=True):
    engine = pick_engine() if engine == "auto" else engine
    key = hashlib.sha1(json.dumps([text, engine, voice, speed, lang, fx]).encode()).hexdigest()[:16]
    cp = os.path.join(CACHE, "tts-cache", key + ".wav")
    if cache and os.path.exists(cp):
        sr, x = read_wav(cp)
        return x, engine
    try:
        x, sr = ENGINES[engine](text, voice, speed, lang)
    except Exception as e:
        if engine == "formant":
            raise
        print(f"[tts] engine '{engine}' failed ({str(e)[:140]}); falling back", file=sys.stderr)
        nxt = "espeak" if engine != "espeak" and (have("espeak-ng") or have("espeak")) else "formant"
        return synth(text, nxt, None, speed, lang, fx, cache, strip)
    x = resample(np.asarray(x, dtype=float), sr)
    if strip:
        x = trim_silence(x)
    x = voice_fx(x, fx)
    x = dsp.normalize(x, -3.0)
    if cache:
        os.makedirs(os.path.dirname(cp), exist_ok=True)
        write_wav(cp, x)
    return x, engine


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--text"); ap.add_argument("--file")
    ap.add_argument("--engine", default="auto", choices=["auto"] + list(ENGINES))
    ap.add_argument("--voice"); ap.add_argument("--speed", type=float, default=1.0); ap.add_argument("--lang")
    ap.add_argument("--voice-fx"); ap.add_argument("--out", default="tts.wav"); ap.add_argument("--list", action="store_true")
    a = ap.parse_args()
    if a.list:
        print(json.dumps(dict(engines=available(), auto_picks=pick_engine(), kokoro_voices=KOKORO_VOICES,
                              piper_default=PIPER_DEFAULT, cache=CACHE), indent=1))
        return
    text = a.text or (open(a.file).read() if a.file else None)
    if not text:
        ap.error("--text or --file required")
    paras = [p.strip() for p in text.split("\n\n") if p.strip()]
    parts, used = [], None
    for p in paras:
        x, used = synth(" ".join(p.split()), a.engine, a.voice, a.speed, a.lang, a.voice_fx)
        parts += [x, np.zeros(int(0.35 * OUT_SR))]
    y = np.concatenate(parts[:-1])
    write_wav(a.out, y)
    print(json.dumps(dict(out=a.out, engine=used, seconds=round(len(y) / OUT_SR, 2))))


if __name__ == "__main__":
    main()
