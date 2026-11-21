"""Video styles -> music recipe. Shared vocabulary with the cinematic-edit skill (same style ids).

Each style says: which genre to compose (and fallbacks), how dense/dynamic it is, tempo range, whether the
music has to stay under speech, how many sound effects, and how the video's acts map to song sections.
`peak` = the section name used for the video's most intense act. Everything is data: edit freely.
"""

STYLES = {
    "hype-highlight": dict(genre="dubstep", alt=["trap", "edm", "metal"], intensity=0.9, dynamics=1.25, bpm=(140, 150), peak="drop",
                           speech=False, sfx="dense", music_db=-11, about="gaming / sport kill-montages, edits that hit on every moment"),
    "horror-chase": dict(genre="horror_chase", alt=["metal", "dark_ambient"], intensity=0.85, dynamics=1.35, bpm=(150, 176), peak="chase",
                         speech=False, sfx="dense", music_db=-12, about="Forsaken-style survival/horror chases, tension that never lets go"),
    "trailer": dict(genre="epic_trailer", alt=["cinematic", "metal"], intensity=0.85, dynamics=1.4, bpm=(80, 110), peak="climax",
                    speech=False, sfx="medium", music_db=-12, about="trailers, teasers, launch films, anything with a big reveal"),
    "vlog": dict(genre="warm_piano", alt=["lofi", "corporate"], intensity=0.6, dynamics=0.8, bpm=(70, 96), peak="drop",
                 speech=True, sfx="light", music_db=-22, about="daily vlogs, creator videos with talking"),
    "travel": dict(genre="warm_piano", alt=["synthwave", "cinematic"], intensity=0.65, dynamics=1.0, bpm=(80, 110), peak="drop",
                   speech=False, sfx="light", music_db=-14, about="travel, nature, drone and b-roll montages"),
    "sport": dict(genre="edm", alt=["rock", "trap"], intensity=0.85, dynamics=1.1, bpm=(126, 146), peak="drop",
                  speech=False, sfx="medium", music_db=-12, about="sport and fitness reels"),
    "talking-head": dict(genre="soft_ambient", alt=["lofi", "corporate"], intensity=0.35, dynamics=0.5, bpm=(60, 80), peak="main",
                         speech=True, sfx="light", music_db=-26, about="podcasts, interviews, explainers: voice first, bed barely there"),
    "tutorial": dict(genre="corporate", alt=["lofi", "soft_ambient"], intensity=0.5, dynamics=0.6, bpm=(96, 116), peak="drop",
                     speech=True, sfx="light", music_db=-24, about="screen recordings, how-tos, courses"),
    "product-ad": dict(genre="corporate", alt=["house", "synthwave"], intensity=0.7, dynamics=1.0, bpm=(100, 124), peak="drop",
                       speech=False, sfx="medium", music_db=-13, about="product films, ads, brand spots, app promos"),
    "music-video": dict(genre=None, alt=[], intensity=0.8, dynamics=1.0, bpm=(0, 0), peak="drop",
                        speech=False, sfx="none", music_db=-6, about="you bring the song, the video is cut to it (beat montage, lyric edits)"),
    "documentary": dict(genre="soft_ambient", alt=["cinematic", "dark_ambient"], intensity=0.4, dynamics=0.8, bpm=(60, 90), peak="main",
                        speech=True, sfx="medium", music_db=-22, about="found-footage documentary, essay videos, narrated explainers"),
    "comedy-meme": dict(genre="chiptune", alt=["lofi", "edm"], intensity=0.7, dynamics=0.8, bpm=(110, 140), peak="drop",
                        speech=True, sfx="dense", music_db=-20, about="comedy shorts, memes, reaction edits: fast pops, record scratches, stings"),
    "aesthetic-lofi": dict(genre="lofi", alt=["warm_piano", "synthwave"], intensity=0.5, dynamics=0.6, bpm=(70, 88), peak="drop",
                           speech=False, sfx="light", music_db=-10, about="calm aesthetic loops, study/chill, slow-mo cityscapes"),
    "anime-amv": dict(genre="edm", alt=["dnb", "rock"], intensity=0.85, dynamics=1.2, bpm=(130, 174), peak="drop",
                      speech=False, sfx="medium", music_db=-10, about="fan edits / AMVs: fast cuts on the beat, big drops"),
    "wedding-memory": dict(genre="warm_piano", alt=["soft_ambient", "cinematic"], intensity=0.45, dynamics=0.9, bpm=(64, 84), peak="drop",
                           speech=False, sfx="none", music_db=-10, about="weddings, family films, tributes, slow emotional montages"),
    "news-explainer": dict(genre="corporate", alt=["soft_ambient", "house"], intensity=0.55, dynamics=0.7, bpm=(96, 118), peak="drop",
                           speech=True, sfx="light", music_db=-24, about="news-style explainers, data stories, business updates"),
    "real-estate": dict(genre="corporate", alt=["warm_piano", "soft_ambient"], intensity=0.5, dynamics=0.8, bpm=(90, 110), peak="drop",
                        speech=False, sfx="none", music_db=-14, about="property walkthroughs, hotel and venue tours"),
    "roblox-edit": dict(genre="roblox_guitar_cover", alt=["metal", "rock", "edm"], intensity=0.85, dynamics=0.85, bpm=(160, 170), peak="drop",
                        speech=False, sfx="medium", music_db=-6, about="Roblox / gaming edits cut to a guitar cover (style measured from a reference cover: 165 BPM, G# minor, bright distorted guitar, wide stereo)"),
    "cyber-tech": dict(genre="synthwave", alt=["techno", "edm"], intensity=0.8, dynamics=1.0, bpm=(100, 128), peak="drop",
                       speech=False, sfx="medium", music_db=-12, about="tech reveals, gadgets, AI, neon and sci-fi looks"),
}

SFX_DENSITY = {"none": 0, "light": 1, "medium": 2, "dense": 3}


def get(name):
    n = (name or "").lower().strip().replace(" ", "-").replace("_", "-")
    if n not in STYLES:
        raise SystemExit(f"unknown video style '{name}'. choices: {', '.join(sorted(STYLES))}")
    return n, STYLES[n]


def acts_to_sections(acts, dur, peak_name="drop"):
    """acts: [{name, t, intensity 0..1}] in video seconds -> [(section_name, start_s, end_s, act_name)], merged when equal.
    Rule: the most intense act is the peak section, the act right before it is the build (the approach), the first act
    is the intro, quiet acts after the peak are breaks/outro, mid acts are verses."""
    acts = sorted(acts, key=lambda a: a["t"])
    if not acts:
        acts = [dict(name="all", t=0.0, intensity=0.5)]
    if acts[0]["t"] > 0.01:
        acts[0] = dict(acts[0], t=0.0)
    vals = [float(a.get("intensity", 0.5)) for a in acts]
    mx = max(vals) or 1.0
    peak = max(i for i, v in enumerate(vals) if v >= mx - 1e-9)
    n = len(acts)
    out = []
    for i, a in enumerate(acts):
        rel = vals[i] / mx
        end = acts[i + 1]["t"] if i + 1 < n else dur
        if i == peak:
            nm = peak_name
        elif i == n - 1 and i > peak:
            nm = "outro"
        elif i == 0 and (peak > 1 or rel < 0.5):
            nm = "intro"
        elif i == peak - 1 and rel >= 0.15:
            nm = "build"
        elif i < peak:
            nm = "verse" if rel >= 0.3 else "intro"
        else:
            nm = peak_name if rel > 0.7 else "break_"
        out.append([nm, a["t"], end, a.get("name", "")])
    merged = [out[0]]
    for s in out[1:]:
        if s[0] == merged[-1][0] and s[0] not in ("build",):
            merged[-1][2] = s[2]
        else:
            merged.append(s)
    return [tuple(m) for m in merged], peak
