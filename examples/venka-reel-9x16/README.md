# Venka Reel 9:16 — synthetic export fixture

Four seconds, **1080×1920, 30/1fps**, SDR. This project demonstrates native video, image/logo and editable text clips. No listed property, private data, AI model, voice recording or commercial song is included. The audio is a quiet generated440Hz test tone.

The checked-in `concat.json` uses relative media references for portability. The current native project model uses absolute paths; prepare a writable scratch copy before opening it:

```text
python examples/venka-reel-9x16/prepare.py --output /path/to/new/scratch/venka-reel-test
```

Open the printed **project directory**, not the JSON file, in the editor or its project.open API. The preparer does not launch the app and refuses to overwrite a nonempty destination. It changes only the two media paths in the scratch copy.

## Stable IDs and expected content

| ID | Content |
| --- | --- |
| `TL1` | Active9:16timeline, video1080×1920,rateNum30,rateDen1 |
| `T1` | Upper track with text clips |
| `T2` | Middle track with original Venka logo |
| `T3` | Bottom track with generated background and tone |
| `m1` | `media/venka-test-1080x1920-30fps.mp4`, H.264yuv420p+AACAUDIO,4s |
| `m2` | `media/venka-logo.png`,1881×511RGBA |
| `c1` | Video `m1`, trackT3, start0,duration4 |
| `c2` | Logo `m2`, trackT2, start0,duration4,scale0.7,offsetY−0.32 |
| `c3` | Text “VENKA IMÓVEIS / EDITOR”, trackT1, start0,duration2 |
| `c4` | Text “SEU PRÓXIMO / TOUR COMEÇA AQUI”, trackT1, start2,duration2 |
| `c5` | Text “DEMONSTRAÇÃO • 9:16 / SEM IMÓVEL ANUNCIADO”, trackT1,start0,duration4 |

Titles use bundled Montserrat with explicit wrapping width, navy/gold branding and safe insets. The generated source video contains coloured geometry; the titles and logo are separate native clips and are **not burned into that source**.

## Expected native validation

Read the document without dropping clips/media; optionally edit `c3` through the actual edit.apply contract; exportH.264MP4 at1080×1920/30fps withAAC. Decode the complete native export and verify4s/120frames, audible tone, logo and the title change at2s. Restore only the scratch copy or create a new scratch copy for repeat tests.

The source video was fully decoded and probed successfully when prepared. The checked-in provenance explicitly marks native import/export and mobile performance as unverified. Passing a Windows headless export or startup smoke is not a performance claim for Android or iOS.

## Origin and license

- Video/tone generated locally with FFmpeg7.1`lavfi`: colour`#101C2D`, geometry`#DCBC64`/`#1E3045`,1080×1920/30fps/4s; sine440Hz/48kHz with low volume and fades;libx264+yuv420p+AAC. No externally sourced footage/audio.
- Logo copied byte for byte from `assets/venka/venka-logo-horizontal.png`; original Venka brand, technical crop documented in `docs/branding-venka.md`. Trademark rights remain with their holders.
- JSON and preparer follow the current `concat-project` version1 document schema and are provided underAGPL-3.0-or-later, as the repository. The unmodified original license is included as `LICENSE`. Concat ©Jareer/jub0t and contributors; those original notices remain in the source repository.
