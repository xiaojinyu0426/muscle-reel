#!/usr/bin/env python3
"""Cut the clips, lay the overlay on top, mix voice + music, export a social-ready 1080x1920 mp4.

  python3 assemble.py reel.json

Needs: render_overlay.py run first (ov/ frames), ffmpeg on PATH.
Voice timing: intro line at 0.1s, each muscle name when its label wipes in, the outro line
2.15s before the end card, the tagline 0.75s into the end card. Music ducks under the voice.
"""
import json, os, subprocess, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from render_overlay import load_config  # noqa: E402


def run(args):
    subprocess.run(['ffmpeg', '-v', 'error', '-y', *args], check=True)


def main():
    cfg, tl = load_config(sys.argv[1])
    base = cfg['_base']
    P = lambda p: os.path.join(base, p)  # noqa: E731
    fps = tl['fps']
    work = P('build')
    os.makedirs(work, exist_ok=True)

    # 1) every clip trimmed to its slot, upscaled to 1080x1920 at the reel's frame rate
    parts = []
    for s in tl['sections']:
        for c in s['clips']:
            n = int(round(c['dur'] * fps))
            out = os.path.join(work, f'p{len(parts):02d}.mp4')
            run(['-i', P(c['file']), '-vf', f'scale=1080:1920:flags=lanczos,fps={fps},setsar=1', '-frames:v', str(n),
                 '-an', '-c:v', 'libx264', '-preset', 'medium', '-crf', '15', '-pix_fmt', 'yuv420p', out])
            parts.append(out)
    tail = os.path.join(work, 'tail.mp4')
    run(['-f', 'lavfi', '-i', f'color=black:s=1080x1920:r={fps}', '-frames:v', str(int(round(tl['end_seconds'] * fps))),
         '-c:v', 'libx264', '-preset', 'medium', '-crf', '15', '-pix_fmt', 'yuv420p', tail])
    parts.append(tail)
    with open(os.path.join(work, 'list.txt'), 'w') as f:
        f.writelines(f"file '{p}'\n" for p in parts)
    base_v = os.path.join(work, 'base.mp4')
    run(['-f', 'concat', '-safe', '0', '-i', os.path.join(work, 'list.txt'), '-c', 'copy', base_v])

    # 2) overlay frames on top
    total_frames = int(round(tl['total'] * fps))
    ovd = P(cfg.get('overlay_dir', 'ov'))
    video = os.path.join(work, 'video.mp4')
    run(['-i', base_v, '-framerate', str(fps), '-i', os.path.join(ovd, '%05d.png'),
         '-filter_complex', '[0:v][1:v]overlay=0:0:format=auto,format=yuv420p', '-frames:v', str(total_frames),
         '-c:v', 'libx264', '-preset', 'slow', '-crf', '17', '-r', str(fps), video])

    # 3) audio: voice lines placed on the timeline, music ducked underneath
    a = cfg['audio']
    cues = []
    if a.get('intro'):
        cues.append((a['intro'], 0.10))
    for s in tl['sections']:
        if s.get('vo'):
            cues.append((s['vo'], s['label_in'] - 0.05))
    if a.get('outro'):
        cues.append((a['outro'], tl['end_start'] - 2.15))
    if a.get('tagline'):
        cues.append((a['tagline'], tl['end_start'] + 0.75))
    inputs, chains = [], []
    for i, (f, t) in enumerate(cues):
        inputs += ['-i', P(f)]
        ms = max(0, int(t * 1000))
        chains.append(f'[{i}:a]aresample=48000,aformat=channel_layouts=stereo,adelay={ms}|{ms},apad[v{i}]')
    mi = len(cues)
    inputs += ['-i', P(a['music'])]
    T = tl['total']
    vol = a.get('music_volume', 0.32)
    fc = ';'.join(chains)
    fc += ';' + ''.join(f'[v{i}]' for i in range(len(cues))) + f'amix=inputs={len(cues)}:normalize=0:duration=longest,atrim=0:{T:.3f},asplit[vo][sc]'
    fc += f';[{mi}:a]aresample=48000,aformat=channel_layouts=stereo,atrim=0:{T:.3f},afade=t=in:d=0.2,afade=t=out:st={T - 1.3:.3f}:d=1.3,volume={vol}[mus]'
    fc += ';[mus][sc]sidechaincompress=threshold=0.04:ratio=5:attack=15:release=350[duck]'
    fc += ';[duck][vo]amix=inputs=2:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000[aout]'
    audio = os.path.join(work, 'audio.m4a')
    run([*inputs, '-filter_complex', fc, '-map', '[aout]', '-t', f'{T:.3f}', '-c:a', 'aac', '-b:a', '192k', '-ac', '2', audio])

    # 4) mux
    out = P(cfg.get('out', 'out/reel.mp4'))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    run(['-i', video, '-i', audio, '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-c:a', 'copy', '-shortest', '-movflags', '+faststart', out])
    print('done:', out, f'{T:.2f}s')


if __name__ == '__main__':
    main()
