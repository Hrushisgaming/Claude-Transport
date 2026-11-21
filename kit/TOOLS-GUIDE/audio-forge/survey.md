# audio-forge — `survey`

Run the deep analyzer over many tracks and print **one table** of what it finds. Useful as a regression check: run it before and after any change to `deep.py` and diff the tables.

## Exact command

```
python3 af.py survey DIR_OR_FILES... [--out SURVEY.md] [--min-seconds 3]
```

### Flags

| Flag | Meaning |
|---|---|
| paths | one or more files or folders of audio. |
| `--out` | write the table here (default prints to stdout). |
| `--min-seconds` | tracks shorter than this are listed as skipped (stingers). |

## Outputs

A markdown table: for each track — length, BPM, section labels, breakdowns, builds, drops, end cut, loop-ready.

## Step-by-step tutorial

1. Baseline: `af.py survey examples/ --out survey-before.md`.
2. Make your change to `deep.py`.
3. After: `af.py survey examples/ --out survey-after.md`.
4. Diff the two tables — anything that changed unexpectedly is a regression to investigate.

## Honesty

Section labels are heuristics. The table summarizes measurements; it does not judge the music.
