---
name: muscle-reel
description: Make the viral 3D muscle workout reel for any health or fitness app (the @joinyoucan format, 4M-9M views per video). A grey faceless 3D mannequin does dumbbell exercises with the working muscle glowing red-orange. A frosted selector bar at the top shows muscle-map icons with a neon frame in each muscle's color, the muscle name wipes in as it's spoken, and it ends on the app's logo + "Download on the App Store". One config file goes to a finished 1080x1920 mp4 with voice and music. Use when asked for "the muscle video", "workout reel like youcan", "3D mannequin exercise video", "glowing muscle video", "fitness app reel", or "/muscle-reel".
---

# Muscle reel

The format, measured from the reference reel (55s, 30fps):

| Time | What happens |
|---|---|
| 0-4.3s | Intro line over the first shot: "You don't need machines. Just your dumbbells and perfect control." |
| 5 sections, ~10.5s each | Biceps (green), Triceps (teal), Shoulders (purple), Chest (orange), Lats (yellow). Each section has shot A (close or angled, about 4s) and shot B (the hold, about 6.5s). The name is spoken about 1.3s into the section, and that's when the label wipes in. |
| Section change | The label smears out about 0.7s before the cut. The carousel slides one slot left with motion blur, and the neon frame changes color. |
| Last ~2s of the final section | "Save this and come back stronger." |
| End card (3s) | Fade to black. The app logo tile scales in and the App Store line fades in. The tagline is spoken. |

Everything visual except the mannequin footage is drawn by `scripts/render_overlay.py`: the bar, icons, neon frame, labels, slide and end card. The timing all comes from the clip durations in `reel.json`.

## What you need
- **Higgsfield MCP:** stills, icons and animation.
- **ElevenLabs API key:** voice and music. Higgsfield `generate_audio` also works.
- **Local tools:** `ffmpeg` and Python 3 with Pillow.

## Steps

1. **Brief.** Get the app name, the logo text (one or two short lines), the tagline, and the muscles. The defaults are the 5 above with dumbbells.

2. **Workdir.** Copy `examples/reel.json` into a new folder and create `stills/ clips/ thumbs/ vo/` inside it.

3. **Stills.** Upload `assets/style_ref_full.png` and `assets/style_ref_close.png` once with `media_upload`, PUT the bytes, then `media_confirm`. Then generate 2 stills per muscle with `gpt_image_2_6` at 9:16, using the STYLE block and shot table in `prompts.md`.
   - Higgsfield returns 429 when about 9 jobs are running, so submit in waves of 8 or fewer.
   - Look at every still before animating it. Check that the right muscle glows, the top 20% is empty and the pose is clean.

4. **Icons.** Generate one `gpt_image_2_6` 1:1 icon per muscle in its color (prompt in `prompts.md`), and save it as `thumbs/<muscle>.png`.

5. **Animation.** Run `seedance_2_5` with `omni_reference`, the still's job id as `start_image`, 720p, `generate_audio: false` and 9:16. Set the duration to the slot length rounded up.
   - Download each clip to `clips/cN.mp4` in shot order.
   - Check a contact sheet of each clip (`ffmpeg -vf fps=1.5,scale=180:-2,tile=8x1`) before you assemble. You want real reps and the glow on the right muscle.

6. **Audio.**
   - **Voice:** generate one ElevenLabs TTS file per line (script and voice in `prompts.md`) and save them as `vo/l0.mp3` … `vo/l7.mp3`.
   - **Music:** generate a track at the reel length + 1s and save it as `vo/music.mp3`.

7. **Config.** Fill in `reel.json`: the app block, plus for each section its name, color, thumb, vo file and clips with `dur`.
   - The clip durations set the whole timeline. Keep each section around 10-10.5s and the total around 52s plus the 3s end card.
   - If the intro line is longer than about 4.2s, raise `intro_seconds` so the first label doesn't talk over it.

8. **Render.**
   ```
   python3 scripts/render_overlay.py reel.json   # about 7s for 1,650 frames on an M-series Mac
   python3 scripts/assemble.py reel.json         # trims, overlays, mixes, exports reel.json "out"
   ```

9. **Check.** Pull frames at a label wipe-in, mid-slide, a steady label and the end card. Open the mp4 and watch it once all the way through.

## Cost (Higgsfield credits, Nov 2026)

| Item | Credits |
|---|---|
| 10 stills + 5 icons, `gpt_image_2_6` at 0.25 each | ~4 |
| 55s of Seedance 2.5 at 720p (7/s) | ~385 |
| **Total** | **under 400** |

At 1080p it's 16/s, which works out to about 880.

## Gotchas
- **Keep the labels off the shorts.** `gpt_image_2_6` sometimes writes a brand name on them, so the STYLE block says "plain black athletic shorts with no logos". Keep that line.
- **Don't let Seedance cut.** It sometimes adds a second camera angle. "No cuts" in the prompt plus a start image stops that.
- **24fps clips are fine.** Seedance outputs 24fps, and the assembly converts to 30fps.
- **The App Store glyph needs SF Pro.** It's drawn with the macOS font (`/System/Library/Fonts/SFNS.ttf`). On Linux the badge falls back to plain text.
- **Keep text in the safe area.** The bar spans x 128-956, which is inside the Instagram tall-phone side crop (about 97-128px per side).

## Files
- `scripts/render_overlay.py`: the UI overlay. All geometry constants were measured from the reference.
- `scripts/assemble.py`: trims and upscales the clips, overlays the UI, places the voice lines, ducks the music, loudnorm -14 LUFS, faststart.
- `prompts.md`: every image, video, voice and music prompt.
- `examples/reel.json`: the REPS demo config.
- `assets/`: Archivo variable font (OFL) and the two style reference stills (our own renders).
