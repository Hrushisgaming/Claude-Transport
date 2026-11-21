#!/usr/bin/env python3
"""styles.py - one preset per kind of video. A preset fills a draft plan (arc, looks, how hard it hits, text, loudness).

  styles.py list                              the styles, one line each
  styles.py show hype-highlight               the full preset (JSON)
  styles.py doc > reference/video-styles.md   regenerate the style guide
  analyze.py video.mp4 --style vlog ...       use a preset when drafting a plan

Style ids are shared with the audio-forge skill (same names), so `audioforge.py score` picks matching music.
A preset is a starting point: the plan.json it writes is the edit, and you change it by hand.

events.mode:  moments  = loud/motion peaks (action, sport, b-roll)      emphasis = only the few strongest peaks (speech-led)
              beats    = hits on the music's bar lines + top moments    none     = no hits at all (calm styles)
acts: [name, share-of-duration, look, drone 0-1, heartbeat bpm, extras]  extras: raw (no grade) / halftone 0-1
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

A = lambda n, f, lk, dr=0.0, hb=0, **x: dict(name=n, f=f, look=lk, drone=dr, heart_bpm=hb, **x)

STYLES = {
    "hype-highlight": dict(
        about="gaming / sport kill-montages: hits on every moment, escalating arc", format="9:16", reframe=dict(mode="cover", x=0.5, bg="blur"),
        look=dict(grain=0.05, vignette=0.45, bloom=0.25, letterbox=0.0, beat_zoom=0.02),
        acts=[A("calm", 0, "cold", .10, 55), A("the hunt", .14, "teal", .30, 70), A("escalation", .42, "teal", .55, 90), A("finale", .72, "bleach", .85, 115), A("payoff", .92, "warm", .25, 60)],
        events=dict(mode="moments", per_min=8, gap=1.4, big_frac=0.12, ramps=3, riser=1.2, fx_big=["punch", "shake", "flash", "chroma"], fx_mid=["punch", "shake"], fx_small=["punch"], sfx=["impact", "boom", "tick"]),
        visualizer=dict(style="bars", pos="bottom", color="#ffffff", opacity=0.8),
        audio=dict(game_db=-4, music_db=-13, duck_db=-7, sfx_db=-3, lufs=-14), pacing="hook in 1.5 s; a hit every 1.5-3 s, every 0.6-1.2 s in the finale; one freeze on the best moment",
        workflow=["analyze --style", "hud_events (optional)", "plan", "preview", "final", "export"]),
    "horror-chase": dict(
        about="survival / horror chase footage (Forsaken-style): dread, then relentless escalation", format="9:16", reframe=dict(mode="fit", x=0.5, bg="blur"),
        look=dict(grain=0.09, vignette=0.6, bloom=0.2, letterbox=0.0, beat_zoom=0.02),
        acts=[A("calm", 0, "cold", .10, 55), A("the hunt", .14, "horror", .35, 72), A("escalation", .42, "horror", .6, 95), A("finale", .72, "bleach", .9, 120, halftone=0.25), A("payoff", .92, "cold", .25, 58)],
        events=dict(mode="moments", per_min=9, gap=1.2, big_frac=0.12, ramps=2, riser=1.4, fx_big=["punch", "shake", "flash", "chroma", "glitch"], fx_mid=["punch", "shake"], fx_small=["punch"], sfx=["impact", "boom", "tick"]),
        visualizer=dict(style="line", pos="bottom", color="#ff3030", opacity=0.6),
        audio=dict(game_db=-4, music_db=-12, duck_db=-7, sfx_db=-3, lufs=-14), pacing="slow dread first; counters (5 LEFT ... LAST ONE) at each down; silence 0.5 s before the last hit",
        workflow=["analyze --style", "hud_events for downs", "plan", "preview", "final", "export"]),
    "trailer": dict(
        about="trailers / teasers / launch films: long tension, one huge hit, title cards", format="16:9", reframe=dict(mode="cover", x=0.5, bg="blur"),
        look=dict(grain=0.06, vignette=0.5, bloom=0.3, letterbox=0.1, beat_zoom=0.0),
        acts=[A("open", 0, "cold", .12, 0), A("rising", .22, "teal", .35, 0), A("build", .5, "teal", .6, 0), A("hit", .78, "bleach", .9, 0), A("title", .93, "warm", .2, 0)],
        events=dict(mode="moments", per_min=5, gap=2.2, big_frac=0.2, ramps=1, riser=2.0, fx_big=["punch", "flash"], fx_mid=["punch"], fx_small=[], sfx=["impact", "boom", "whoosh"]),
        visualizer=None, overlays_hint=["title at the open", "2-4 words per card", "name/date card on the last act"],
        audio=dict(game_db=-8, music_db=-11, duck_db=-5, sfx_db=-3, lufs=-14), pacing="few, big hits: every card gets a riser; the biggest hit is followed by a clean 1 s of silence then the title",
        workflow=["analyze --style", "plan with title cards", "audioforge score", "preview", "final", "export"]),
    "vlog": dict(
        about="creator vlogs with talking: natural colour, captions, light emphasis", format="9:16", reframe=dict(mode="cover", x=0.5, bg="blur"),
        look=dict(grain=0.02, vignette=0.2, bloom=0.12, letterbox=0.0, beat_zoom=0.0),
        acts=[A("hook", 0, "vivid"), A("story", .1, "natural"), A("peak", .7, "vivid"), A("wrap", .92, "natural")],
        events=dict(mode="emphasis", per_min=5, gap=3.0, big_frac=0.0, ramps=0, riser=0, fx_big=["punch"], fx_mid=["punch"], fx_small=["punch"], sfx=["tick", "tick", "tick"]),
        visualizer=None, captions=dict(pos="lower", size=62, max_words=4), overlays_hint=["title in the first 2 s", "lower_third for places/people"],
        audio=dict(game_db=0, music_db=-22, duck_db=-12, sfx_db=-9, lufs=-14, mode="voice"), pacing="cut every sentence; a punch-in on emphasis; remove pauses (silence_cut.py)",
        workflow=["silence_cut", "transcribe", "analyze --style vlog", "captions", "audioforge score (quiet bed)", "final", "export"]),
    "travel": dict(
        about="travel / nature / drone b-roll montage: golden colour, slow ramps, soft whooshes", format="16:9", reframe=dict(mode="cover", x=0.5, bg="blur"),
        look=dict(grain=0.03, vignette=0.3, bloom=0.35, letterbox=0.06, beat_zoom=0.01),
        acts=[A("arrival", 0, "natural", .1), A("explore", .2, "golden", .2), A("high", .6, "vivid", .3), A("sunset", .85, "golden", .15)],
        events=dict(mode="moments", per_min=7, gap=2.0, big_frac=0.1, ramps=2, riser=0.8, fx_big=["punch"], fx_mid=["punch"], fx_small=[], sfx=["whoosh", "tick", "tick"]),
        visualizer=None, overlays_hint=["lower_third with the real place name", "title card"],
        audio=dict(game_db=-12, music_db=-12, duck_db=-5, sfx_db=-8, lufs=-14), pacing="3-5 s per shot, cut on the beat of a mid-tempo bed; one slow-mo on the best view",
        workflow=["montage.py with music", "analyze --style travel", "plan", "preview", "final", "export"]),
    "sport": dict(
        about="sport / fitness reels: punchy saturated colour, fast hits, speed ramps", format="9:16", reframe=dict(mode="cover", x=0.5, bg="blur", follow=True),
        look=dict(grain=0.03, vignette=0.35, bloom=0.2, letterbox=0.0, beat_zoom=0.025),
        acts=[A("warm-up", 0, "sport", .1, 0), A("play", .2, "sport", .3, 0), A("peak", .7, "sport", .6, 0, halftone=0.0), A("celebrate", .93, "vivid", .2, 0)],
        events=dict(mode="moments", per_min=10, gap=1.1, big_frac=0.15, ramps=3, riser=0.9, fx_big=["punch", "shake", "flash"], fx_mid=["punch", "shake"], fx_small=["punch"], sfx=["impact", "boom", "tick"]),
        visualizer=None, audio=dict(game_db=-5, music_db=-12, duck_db=-7, sfx_db=-4, lufs=-14), pacing="slow-mo on the key play, then a hit on the action frame",
        workflow=["analyze --style sport", "follow reframe", "plan", "preview", "final", "export"]),
    "talking-head": dict(
        about="podcasts / interviews / explainers: voice first, tight pauses, clean captions, barely any effects", format="16:9", reframe=dict(mode="cover", x=0.5, bg="blur"),
        look=dict(grain=0.0, vignette=0.15, bloom=0.0, letterbox=0.0, beat_zoom=0.0),
        acts=[A("take", 0, "clean", raw=True)],
        events=dict(mode="none", per_min=0, gap=4.0, big_frac=0, ramps=0, riser=0, fx_big=[], fx_mid=[], fx_small=[], sfx=["tick", "tick", "tick"]),
        visualizer=None, captions=dict(pos="lower", size=56, max_words=6), overlays_hint=["lower_third with the speaker's real name/role"],
        audio=dict(game_db=0, music_db=-26, duck_db=-14, sfx_db=-12, lufs=-16, mode="voice"), pacing="remove silences > 0.6 s; a slow push-in every 20-30 s is enough",
        workflow=["silence_cut", "transcribe", "analyze --style talking-head", "captions", "audioforge score (soft bed)", "final", "export"]),
    "tutorial": dict(
        about="screen recordings / how-tos / courses: legible, steady, step markers", format="16:9", reframe=dict(mode="fit", x=0.5, bg="blur"),
        look=dict(grain=0.0, vignette=0.0, bloom=0.0, letterbox=0.0, beat_zoom=0.0),
        acts=[A("intro", 0, "clean", raw=True), A("steps", .08, "clean", raw=True), A("recap", .92, "clean", raw=True)],
        events=dict(mode="emphasis", per_min=3, gap=5.0, big_frac=0, ramps=0, riser=0, fx_big=["punch"], fx_mid=["punch"], fx_small=["punch"], sfx=["tick", "tick", "tick"]),
        visualizer=None, captions=dict(pos="bottom", size=48, max_words=7), overlays_hint=["a `counter` per step (STEP 2/5)", "lower_third naming the tool", "terminal/code_scroll device for commands"],
        audio=dict(game_db=0, music_db=-24, duck_db=-14, sfx_db=-12, lufs=-16, mode="voice"), pacing="cut dead air, zoom (punch) only to point at the thing being clicked",
        workflow=["silence_cut", "transcribe", "analyze --style tutorial", "step counters", "final", "export"]),
    "product-ad": dict(
        about="product films / ads / app promos: clean bright colour, controlled punches, whooshes", format="9:16", reframe=dict(mode="cover", x=0.5, bg="blur"),
        look=dict(grain=0.02, vignette=0.2, bloom=0.3, letterbox=0.0, beat_zoom=0.015),
        acts=[A("hook", 0, "vivid", .1), A("feature", .2, "clean", .2), A("proof", .6, "clean", .3), A("cta", .88, "vivid", .2)],
        events=dict(mode="beats", per_min=10, gap=1.3, big_frac=0.1, ramps=1, riser=0.8, fx_big=["punch", "flash"], fx_mid=["punch"], fx_small=["punch"], sfx=["whoosh", "tick", "tick"], every=4),
        visualizer=None, captions=dict(pos="lower", size=64, max_words=3), overlays_hint=["title = the benefit, not the brand", "counter/lower_third for numbers (real ones)", "CTA card last 2 s"],
        audio=dict(game_db=-6, music_db=-13, duck_db=-8, sfx_db=-7, lufs=-14), pacing="a new picture every 1-2 s, cut on the beat, one number or claim per card",
        workflow=["montage.py", "analyze --style product-ad", "audioforge score", "preview", "final", "export"]),
    "music-video": dict(
        about="you bring the song: beat-cut montage, flashes on the downbeats, optional visualizer", format="9:16", reframe=dict(mode="cover", x=0.5, bg="blur"),
        look=dict(grain=0.04, vignette=0.35, bloom=0.3, letterbox=0.0, beat_zoom=0.04),
        acts=[A("intro", 0, "film", .1), A("verse", .15, "vivid", .2), A("drop", .45, "vivid", .4), A("outro", .9, "film", .1)],
        events=dict(mode="beats", per_min=24, gap=0.5, big_frac=0.1, ramps=1, riser=0, fx_big=["punch", "flash", "chroma"], fx_mid=["punch"], fx_small=["punch"], sfx=["impact", "tick", "tick"], every=4),
        visualizer=dict(style="ring", pos="center", color="#ffffff", opacity=0.5), audio=dict(game_db=-30, music_db=-6, duck_db=0, sfx_db=-10, lufs=-14, mode="music"),
        pacing="cut every 2 beats (1 in the drop, 4 in the intro); strongest clip on the downbeat of the drop", workflow=["montage.py --music", "analyze --style music-video --music", "preview", "final", "export"]),
    "documentary": dict(
        about="found-footage documentary / essay: a new real picture every 0.6-1.5 s (see Documentary mode)", format="9:16", reframe=dict(mode="cover", x=0.5, bg="blur"),
        look=dict(grain=0.03, vignette=0.3, bloom=0.1, letterbox=0.0, beat_zoom=0.0),
        acts=[A("hook", 0, "natural", raw=True), A("world", .1, "teal", .15), A("turn", .55, "bleach", .3), A("close", .88, "natural", raw=True)],
        events=dict(mode="none", per_min=0, gap=3.0, big_frac=0, ramps=0, riser=0, fx_big=[], fx_mid=[], fx_small=[], sfx=["tick", "tick", "tick"]),
        visualizer=None, captions=dict(pos="lower", size=62, max_words=5), overlays_hint=["devices: tile_reveal / strobe / pop_collage / wall3d", "sources for every picture"],
        audio=dict(game_db=0, music_db=-22, duck_db=-12, sfx_db=-8, lufs=-14, mode="voice"), pacing="a picture per 0.6-1.5 s; sound on every change", workflow=["transcribe", "source footage", "plan with sources", "plancheck", "final", "verify.py"]),
    "comedy-meme": dict(
        about="comedy shorts / memes / reactions: snap zooms, pops, record scratches, caption punchlines", format="9:16", reframe=dict(mode="cover", x=0.5, bg="blur"),
        look=dict(grain=0.0, vignette=0.15, bloom=0.0, letterbox=0.0, beat_zoom=0.0),
        acts=[A("setup", 0, "vivid"), A("punchline", .6, "vivid"), A("tag", .9, "natural")],
        events=dict(mode="emphasis", per_min=10, gap=1.5, big_frac=0.2, ramps=1, riser=0, fx_big=["punch", "shake", "glitch"], fx_mid=["punch"], fx_small=["punch"], sfx=["boom", "tick", "tick"]),
        visualizer=None, captions=dict(pos="center", size=76, max_words=3), overlays_hint=["caption = the punchline word, big", "sound: pop/scratch/sting from audio-forge sfx"],
        audio=dict(game_db=0, music_db=-20, duck_db=-12, sfx_db=-6, lufs=-14, mode="voice"), pacing="fast; zoom the beat BEFORE the joke, hold the punchline, then cut", workflow=["silence_cut", "transcribe", "analyze --style comedy-meme", "audioforge sfx", "final", "export"]),
    "aesthetic-lofi": dict(
        about="calm aesthetic loops / study / city b-roll: faded film colour, grain, bars, no hits", format="9:16", reframe=dict(mode="cover", x=0.5, bg="blur"),
        look=dict(grain=0.11, vignette=0.5, bloom=0.4, letterbox=0.08, beat_zoom=0.008),
        acts=[A("drift", 0, "film", .1), A("glow", .5, "pastel", .15)],
        events=dict(mode="none", per_min=0, gap=4.0, big_frac=0, ramps=0, riser=0, fx_big=[], fx_mid=[], fx_small=[], sfx=["tick", "tick", "tick"]),
        visualizer=dict(style="line", pos="bottom", color="#ffe9d6", opacity=0.55), audio=dict(game_db=-20, music_db=-8, duck_db=0, sfx_db=-14, lufs=-14, mode="music"),
        pacing="long shots (4-8 s), slow cuts on the bar line, no effects", workflow=["montage.py --every 4", "analyze --style aesthetic-lofi", "final", "export"]),
    "anime-amv": dict(
        about="fan edits / AMVs: very fast cuts, flashes and chroma on every hit, big drop", format="16:9", reframe=dict(mode="cover", x=0.5, bg="blur"),
        look=dict(grain=0.03, vignette=0.3, bloom=0.4, letterbox=0.0, beat_zoom=0.05),
        acts=[A("intro", 0, "film", .1), A("build", .2, "vivid", .3), A("drop", .5, "vivid", .6), A("outro", .9, "pastel", .15)],
        events=dict(mode="beats", per_min=30, gap=0.4, big_frac=0.12, ramps=2, riser=1.0, fx_big=["punch", "flash", "chroma", "glitch"], fx_mid=["punch", "chroma"], fx_small=["punch"], sfx=["impact", "tick", "tick"], every=2),
        visualizer=None, audio=dict(game_db=-30, music_db=-6, duck_db=0, sfx_db=-10, lufs=-14, mode="music"), pacing="cut every beat in the drop; slow-mo hold on the key frame before it",
        workflow=["montage.py --every 1", "analyze --style anime-amv --music", "preview", "final", "export"]),
    "wedding-memory": dict(
        about="weddings / family films / tributes: warm soft colour, no hits, gentle bed", format="16:9", reframe=dict(mode="cover", x=0.5, bg="blur"),
        look=dict(grain=0.04, vignette=0.35, bloom=0.5, letterbox=0.06, beat_zoom=0.0),
        acts=[A("opening", 0, "pastel", .1), A("moments", .15, "warm", .15), A("vows", .7, "golden", .2), A("end", .93, "pastel", .1)],
        events=dict(mode="none", per_min=0, gap=4.0, big_frac=0, ramps=0, riser=0, fx_big=[], fx_mid=[], fx_small=[], sfx=["tick", "tick", "tick"]),
        visualizer=None, overlays_hint=["names + date (real) on the title card"], audio=dict(game_db=-6, music_db=-10, duck_db=-10, sfx_db=-20, lufs=-16, mode="hybrid"),
        pacing="3-6 s per shot, dissolves; keep the speech in the vows, music under everything else", workflow=["montage.py --every 4", "analyze --style wedding-memory", "final"]),
    "news-explainer": dict(
        about="news-style explainers / data stories: clean, lower thirds, counters for numbers", format="16:9", reframe=dict(mode="fit", x=0.5, bg="blur"),
        look=dict(grain=0.0, vignette=0.1, bloom=0.0, letterbox=0.0, beat_zoom=0.0),
        acts=[A("headline", 0, "clean", raw=True), A("body", .1, "clean", raw=True), A("so-what", .85, "clean", raw=True)],
        events=dict(mode="emphasis", per_min=3, gap=5.0, big_frac=0, ramps=0, riser=0, fx_big=["punch"], fx_mid=["punch"], fx_small=["punch"], sfx=["tick", "tick", "tick"]),
        visualizer=None, captions=dict(pos="lower", size=50, max_words=7), overlays_hint=["lower_third for every named person/place", "counter for every figure (verify it, quote the source)"],
        audio=dict(game_db=0, music_db=-24, duck_db=-14, sfx_db=-12, lufs=-16, mode="voice"), pacing="steady; one visual change every 3-5 s; numbers on screen when spoken", workflow=["silence_cut", "transcribe", "overlays", "final"]),
    "real-estate": dict(
        about="property / hotel / venue tours: bright, stable, wide shots, zero effects", format="16:9", reframe=dict(mode="cover", x=0.5, bg="blur"),
        look=dict(grain=0.0, vignette=0.12, bloom=0.2, letterbox=0.0, beat_zoom=0.0),
        acts=[A("arrive", 0, "clean"), A("inside", .2, "clean"), A("highlight", .75, "golden")],
        events=dict(mode="none", per_min=0, gap=4.0, big_frac=0, ramps=0, riser=0, fx_big=[], fx_mid=[], fx_small=[], sfx=["tick", "tick", "tick"]),
        visualizer=None, overlays_hint=["lower_third: room name; counter: real size/price only if given"], audio=dict(game_db=-10, music_db=-14, duck_db=-6, sfx_db=-20, lufs=-14, mode="hybrid"),
        pacing="4-6 s per shot, cut on the bar line, a soft whoosh between rooms", workflow=["montage.py --every 4", "analyze --style real-estate", "final"]),
    "cyber-tech": dict(
        about="tech reveals / gadgets / AI / sci-fi: neon grade, glitch + chroma, line visualizer", format="9:16", reframe=dict(mode="cover", x=0.5, bg="blur"),
        look=dict(grain=0.05, vignette=0.4, bloom=0.45, letterbox=0.0, beat_zoom=0.02),
        acts=[A("boot", 0, "cold", .15, 0), A("reveal", .3, "cyber", .4, 0), A("overdrive", .65, "cyber", .7, 0, halftone=0.15), A("end", .92, "cold", .15, 0)],
        events=dict(mode="moments", per_min=9, gap=1.3, big_frac=0.12, ramps=1, riser=1.0, fx_big=["punch", "chroma", "glitch", "flash"], fx_mid=["punch", "chroma"], fx_small=["glitch"], sfx=["impact", "glitch", "tick"]),
        visualizer=dict(style="line", pos="bottom", color="#38f9ff", opacity=0.7), overlays_hint=["terminal / code_scroll / typewriter devices for real text"],
        audio=dict(game_db=-6, music_db=-12, duck_db=-7, sfx_db=-4, lufs=-14), pacing="glitch on every state change; one calm beat before the reveal", workflow=["analyze --style cyber-tech", "devices", "audioforge score", "preview", "final"]),
}
ALIAS = {"gaming": "hype-highlight", "highlight": "hype-highlight", "kill-montage": "hype-highlight", "horror": "horror-chase", "forsaken": "horror-chase",
         "teaser": "trailer", "podcast": "talking-head", "interview": "talking-head", "explainer": "news-explainer", "screencast": "tutorial",
         "ad": "product-ad", "product": "product-ad", "lyric": "music-video", "amv": "anime-amv", "meme": "comedy-meme", "lofi": "aesthetic-lofi",
         "wedding": "wedding-memory", "memory": "wedding-memory", "news": "news-explainer", "property": "real-estate", "tech": "cyber-tech", "fitness": "sport"}


def load_user_styles():
    """JSON presets: shipped in ../styles.d/ and personal in ~/.config/cinematic-edit/styles/ (made by study_video.py / style-copy)"""
    import glob
    dirs = [os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "styles.d"), os.path.expanduser(os.environ.get("CINEMATIC_EDIT_STYLES", "~/.config/cinematic-edit/styles"))]
    for d in dirs:
        for f in sorted(glob.glob(os.path.join(d, "*.json"))):
            try:
                j = json.load(open(f)); nm = j.pop("name", os.path.splitext(os.path.basename(f))[0]); al = j.pop("aliases", [])
                for a in j["acts"]: a.setdefault("drone", 0.0); a.setdefault("heart_bpm", 0)
                STYLES[nm] = j
                for x in al: ALIAS[x] = nm
            except Exception as e:
                print(f"cinematic-edit: skipped style file {f}: {e}", file=sys.stderr)


def get(name):
    n = (name or "").lower().strip().replace("_", "-").replace(" ", "-"); n = ALIAS.get(n, n)
    if n not in STYLES: raise SystemExit(f"unknown style '{name}'. choices: {', '.join(sorted(STYLES))}")
    return n, STYLES[n]


def build_plan(style, ev, info, source, music=None, fmt=None, start=0.0):
    """-> a draft plan.json dict. ev = analyze's events dict (moments, beats, duration)."""
    name, st = get(style); D = ev["duration"]; moms = ev["moments"]; E = st["events"]; mode = E["mode"]
    beats = ev.get("beats") or []
    cand = []
    if mode in ("moments", "emphasis"):
        cap = max(1, int(round(E["per_min"] * D / 60.0))) if E["per_min"] else 0
        cand = sorted(moms, key=lambda m: -m["strength"])[:cap]; cand = sorted(cand, key=lambda m: m["t"])
    elif mode == "beats":
        step = max(1, int(E.get("every", 4))); grid = beats[::step] if beats else []
        cap = max(1, int(round(E["per_min"] * D / 60.0)))
        cand = [dict(t=round(t, 3), strength=0.45, kind="beat") for t in grid][:cap * 2]
        strong = sorted(moms, key=lambda m: -m["strength"])[:max(2, cap // 4)]
        for m in strong:
            if all(abs(m["t"] - c["t"]) > E["gap"] for c in cand): cand.append(m)
        cand = sorted(cand, key=lambda m: m["t"])
        kept = []
        for c in cand:
            if not kept or c["t"] - kept[-1]["t"] >= E["gap"]: kept.append(c)
        cand = kept
    order = sorted(range(len(cand)), key=lambda i: -cand[i]["strength"])
    nbig = int(round(len(cand) * E["big_frac"])); big = set(order[:max(1, nbig)]) if (cand and E["big_frac"] > 0) else set()
    ramp = set(order[:E["ramps"]]) if E.get("ramps") else set()
    sfx_big, sfx_mid, sfx_small = (E["sfx"] + ["tick"] * 3)[:3]
    events = []
    for i, m in enumerate(cand):
        s = m["strength"]
        if i in big: e = dict(t=m["t"], strength=s, fx=list(E["fx_big"]), sfx=sfx_big, riser=E.get("riser", 0.0))
        elif s > 0.45: e = dict(t=m["t"], strength=s, fx=list(E["fx_mid"]), sfx=sfx_mid, riser=0.0)
        else: e = dict(t=m["t"], strength=s, fx=list(E["fx_small"]), sfx=sfx_small, riser=0.0)
        if i in ramp and m["t"] > 6: e["ramp"] = dict(speed=0.3, dur=1.0)
        events.append(e)
    acts = []
    for a in st["acts"]:
        x = dict(name=a["name"], t=round(a["f"] * D, 2), look=a["look"], drone=a["drone"], heart_bpm=a["heart_bpm"])
        for k in ("raw", "halftone"):
            if k in a: x[k] = a[k]
        acts.append(x)
    au = dict(st["audio"]); au["music_beat_sync"] = bool(music)
    plan = dict(style=name, source=source, music=music, format=fmt or st["format"], fps=30, start=start, dur=round(D, 2), reframe=dict(st["reframe"]), look=dict(st["look"]),
                acts=acts, events=events, overlays=[], audio=au)
    if st.get("visualizer"): plan["visualizer"] = dict(st["visualizer"])
    if st.get("captions"): plan["captions"] = dict(st["captions"], words="work/tx/words.json")
    return plan


def _music_genres():
    """genre per style from audio-forge's table, when audio-forge is installed next to us (documentation only)"""
    try:
        import importlib.util, audioforge
        d = audioforge.find_af()
        if not d: return {}
        spec = importlib.util.spec_from_file_location("af_styles", os.path.join(d, "scripts", "forge", "styles.py")); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
        return {k: (v["genre"] or "your own song") for k, v in m.STYLES.items()}
    except Exception:
        return {}


def doc():
    mg = _music_genres()
    L = ["# Video styles", "", "Generated by `styles.py doc`. Pass `--style <id>` to `analyze.py`; every value is a starting point you can edit in plan.json.", "",
         "| style | for | format | hits | look arc | audio mode | bed genre (audio-forge) |", "|---|---|---|---|---|---|---|"]
    for k, v in sorted(STYLES.items()):
        E = v["events"]; hits = {"moments": f"~{E['per_min']}/min, peaks", "emphasis": f"~{E['per_min']}/min, emphasis only", "beats": f"~{E['per_min']}/min, on the beat", "none": "none"}[E["mode"]]
        arc = " > ".join(a["look"] for a in v["acts"]); mode = v["audio"].get("mode", "hybrid")
        L.append(f"| `{k}` | {v['about']} | {v['format']} | {hits} | {arc} | {mode}, bed {v['audio']['music_db']} dB | {mg.get(k, '-')} |")
    L += ["", "audio mode: `voice` = speech first (bed ducks hard, effects quieter), `music` = the track leads, `hybrid` = both.", "", "## Pacing and workflow per style"]
    L += [f"- **{k}**: {v['pacing']}. Workflow: {' > '.join(v['workflow'])}." for k, v in sorted(STYLES.items())]
    return "\n".join(L) + "\n"


load_user_styles()


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "list"
    if cmd == "list":
        for k, v in sorted(STYLES.items()): print(f"{k:16s} {v['format']:5s} {v['about']}")
    elif cmd == "show": print(json.dumps(get(sys.argv[2])[1], indent=1))
    elif cmd == "doc": print(doc())
    else: sys.exit(__doc__)
