# Prompts for the muscle reel

Every prompt below was used for the REPS demo (Nov 9 2026) and worked on the first try.

## 1. Shot stills: `gpt_image_2_6`, aspect `9:16`

Pass `assets/style_ref_full.png` and `assets/style_ref_close.png` as `image_references`. Upload them once with `media_upload` and reuse the media ids.

**STYLE block** (put it at the start of every shot prompt):

```
Photoreal 3D render in the exact visual style of the reference images: a smooth matte light-grey faceless mannequin athlete (egg-shaped head with no face, sculpted anatomical muscles, lean athletic build), plain black athletic shorts with no logos, barefoot, classic black round-plate dumbbells. Dark charcoal blue-grey studio backdrop with a soft vignette and a subtle dark floor. The working muscle is highlighted as glowing emissive red-orange with a hot yellow core, and a thin electric blue-white rim glow traces parts of the body's silhouette. Cinematic soft key light, high detail, no text, no logos, no watermark. Vertical 9:16 frame with the top 20% left as empty dark backdrop.
```

For lying or bent-over shots, ask for the top 25-30% to stay empty, because the selector bar covers that area.

Then add `SHOT: ...`. There are two shots per muscle. Shot A is the opener and shot B is the angle you hold on.

| Muscle | Shot A | Shot B |
|---|---|---|
| Biceps | Close-up from the side (profile), upper body from the shoulders to the hips, facing right, one arm mid-curl; biceps glow | Full body, front view, feet together, alternating curls: right arm up, left arm down; both biceps glow |
| Triceps | Full body from behind at a 3/4 angle, right arm overhead holding a dumbbell behind the head, left arm at the side; triceps glow | Close-up from behind and slightly low, back of the head plus shoulders plus the raised arm, overhead extension with the elbow up; triceps glow intensely |
| Shoulders | Full body, front view, lateral raise with both arms straight out at shoulder height; deltoids glow | Medium shot from a front 3/4 angle, head to thighs, dumbbells beside the thighs about to raise; deltoids glow |
| Chest | Wide side view, lying on a black mat with knees bent, dumbbell floor press with arms straight up; pecs glow. Figure in the lower-middle of the frame | Closer high angle from beside the knees toward the head, floor press with arms extended; pecs glow |
| Lats | Full body side view, flat-back hip hinge, bent-over row, dumbbells hanging; lats glow | Closer rear 3/4 view from above and behind, elbows pulled back, dumbbells at the hips; lats and upper back glow |

Other muscles in the same pattern:
- **Abs:** crunch on the mat.
- **Glutes:** hip thrust or Romanian deadlift.
- **Quads:** goblet squat.
- **Hamstrings:** Romanian deadlift side view.
- **Calves:** calf raise close-up.
- **Forearms:** wrist curl close-up.

## 2. Selector icons: `gpt_image_2_6`, aspect `1:1`, no references

```
Small fitness app UI icon: 3D render of a smooth matte light-grey anatomical male torso bust, {FRONT|BACK} view, cut off at the neck and at mid-thigh, arms hanging at the sides, sculpted muscles. Only the {MUSCLE} glow bright saturated neon {COLOR NAME} ({HEX}) with a soft emissive glow; the rest of the body stays neutral grey. Pure black background, centered, soft studio light, no text, no logos.
```

The overlay crops the icon to neck-to-hips and makes the greyed-out version itself. Default colors:

| Muscle | Color | View |
|---|---|---|
| Biceps | green `#35FF5C` | front |
| Triceps | teal `#2CF0D0` | back |
| Shoulders | purple `#B04DFF` | front |
| Chest | orange `#FF9A1F` | front |
| Lats | yellow `#FFD21F` | back |

Extra muscles: abs red `#FF4D5E` (front), glutes pink `#FF5CC8` (back), quads blue `#3D8BFF` (front).

## 3. Animation: `seedance_2_5`

Settings: `mode: omni_reference`, `resolution: 720p`, `generate_audio: false`, `aspect_ratio: 9:16`. The still's job id goes in as `start_image`.

Set `duration` to the clip's slot rounded up to a whole second. The assembly trims it to the exact length.

```
The grey faceless mannequin athlete performs slow, controlled {EXERCISE} with perfect form, {N} full reps: {ONE LINE OF THE MOVEMENT}. The {MUSCLE} glow(s) red-orange and pulse(s) brighter with a hot yellow core at the {TOP OF EACH REP}. A thin blue-white electric rim light flickers along the body's edges. {CAMERA: Slow subtle camera push-in | Slow camera orbit to the right}. Dark charcoal studio. Keep the exact look of the start frame: same mannequin, same lighting, same colors. No text, no logos, no extra people, no cuts.
```

How many reps per clip length:

| Clip length | Reps |
|---|---|
| 4s | 1-2 |
| 5-6s | 2-3 |
| 7s | 3 |

Shot B works best with a push-in. An orbit gives a shot A some variety.

## 4. Voiceover script (ElevenLabs, voice "Adam" `pNInz6obpgDQGcFmaJgB`)

Model `eleven_multilingual_v2`, with stability 0.5, similarity 0.8 and style 0.35. Make one file per line.

```
l0  You don't need machines. Just your dumbbells and perfect control.
l1  Biceps.
l2  Triceps.
l3  Shoulders.
l4  Chest.
l5  Lats.
l6  Save this and come back stronger.
l7  {APP TAGLINE, e.g. "Rep by rep."}
```

To make a bodyweight version, swap the first line for "No gym. No equipment. Just your body and perfect form." and use bodyweight exercises.

## 5. Music (ElevenLabs Music, POST /v1/music, music_length_ms = reel length + 1s)

```
Upbeat energetic electronic workout instrumental for a fitness app reel. Punchy four-on-the-floor drums, bright synth plucks, driving bass, confident and motivational, steady 118 BPM, builds slightly, clean ending. No vocals.
```

On Higgsfield, use `generate_audio` with `suno_music`, `instrumental: true` and the same style text.
