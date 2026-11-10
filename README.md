# The Claude muscle reel skill

One Claude skill, `muscle-reel`, that makes the 3D muscle workout reels for any health or fitness app. A grey 3D figure does each exercise with the working muscle glowing, a muscle picker sits at the top, each name is said out loud, and the reel ends on your app's logo and an App Store line.

## Source & credit

This skill was created by **Ernesto Lopez ([@ErnestoSOFTWARE](https://x.com/ErnestoSOFTWARE))** and shared for free.

- Original resource page: https://ernesto-x-resources.vercel.app/r/muscle-skill
- Original post: https://x.com/ErnestoSOFTWARE/status/2119926871882174818

This repository is a mirror shared for convenience. All credit for the skill, prompts and scripts goes to the original author. The demo app name "REPS" is made up — put your own app name and logo in the config.

## Install (Claude Code)

1. Clone this repo.
2. Move the folder into `~/.claude/skills/`:
   ```bash
   mv muscle-reel ~/.claude/skills/
   ```
3. Connect the Higgsfield MCP in Claude Code. It makes the stills and the clips, and uses your Higgsfield credits.

## Use it

Open Claude Code in an empty folder and say:

"Use the muscle-reel skill to make a muscle reel for my app <name>."

## What it needs

- Higgsfield MCP + credits (about 400 for a 55 second reel at 720p)
- An ElevenLabs API key for the voice and music
- ffmpeg, Python 3 and Pillow

## What's inside

- `muscle-reel/SKILL.md` — the workflow: stills, clips, voice, music, render, with a check at each step
- `muscle-reel/prompts.md` — every prompt used for the demo: shot stills, muscle icons, animation, voice script
- `muscle-reel/scripts/render_overlay.py` — draws the muscle picker, neon frame, name wipe animation and App Store end card
- `muscle-reel/scripts/assemble.py` — cuts the clips, overlays the picker, ducks the music under the voice, exports 1080x1920 mp4
- `muscle-reel/examples/reel.json` — the demo config, copy and edit it

## Note on binary assets

The two style reference images (`assets/style_ref_full.png`, `assets/style_ref_close.png`) and the Archivo font (`assets/fonts/Archivo.ttf`, OFL licensed) from the original download are not included in this repo — grab them from the [original resource page](https://ernesto-x-resources.vercel.app/r/muscle-skill) if you need them.
