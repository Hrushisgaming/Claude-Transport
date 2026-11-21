#!/usr/bin/env python3
"""preview.py — a 10-second self-test of the Canvas style, made from the kit alone (no recording needed), rendered and opened.

    source <skill>/scripts/env.sh && "$CV_PY" <skill>/scripts/preview.py [--short]

Builds ~/canvas/_preview/ (or _preview_short/): a painting sliding in with words in its dark side, icons that draw
themselves with a flow arrow, a versus card, a donut chart, the blue cut-out of a painted figure, and a quote on blue,
each word blurring in, the kit's own sounds under it. Writes preview.mp4 and preview-sheet.jpg, then opens the video.
"""
import os, shutil, subprocess, sys

SK = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
SHORT = '--short' in sys.argv
OUT = os.path.expanduser('~/canvas/_preview_short' if SHORT else '~/canvas/_preview')
sys.path.insert(0, os.path.join(SK, 'components'))
import cv_devices as cv
cv.set_format('9x16' if SHORT else '16x9')


def run(*a, **k):
    return subprocess.run(list(a), check=True, **k)


def main():
    if os.path.exists(OUT):
        shutil.rmtree(OUT)
    os.makedirs(os.path.join(OUT, 'assets', 'img'))
    os.makedirs(os.path.join(OUT, 'assets', 'cv'))
    for f in ('tokens.css', 'canvas.css'):
        shutil.copy(os.path.join(SK, 'assets', f), os.path.join(OUT, 'assets', 'cv', f))
    for d in ('fonts', 'vendor', 'tex'):
        shutil.copytree(os.path.join(SK, 'assets', d), os.path.join(OUT, 'assets', 'cv', d))
    shutil.copytree(os.path.join(SK, 'assets', 'icons'), os.path.join(OUT, 'assets', 'icons'))
    ex = os.path.join(SK, 'assets', 'examples')
    for f in ('figure.png', 'figure_halo.png'):
        shutil.copy(os.path.join(ex, f), os.path.join(OUT, 'assets', 'img', f))
    side = ['--side', 'full', '--portrait', '--fx', '0.3'] if SHORT else ['--side', 'left']
    run(sys.executable, os.path.join(SK, 'scripts', 'cv_treat.py'), 'painting', os.path.join(ex, 'painting.jpg'),
        os.path.join(OUT, 'assets', 'img', 'p_painter.jpg'), *side, stdout=subprocess.DEVNULL)
    os.chdir(OUT)
    import cvx
    from cv_devices import Comp, Scene, cap, painting, figure, sfx
    W, H = cv.W, cv.H
    c = Comp(10.0)
    c.css.append(cvx.CSS)
    c.css.append(cvx.CSS2)
    # 1. a painting, words in its dark side
    P = painting(c, 0.0, 2.0, 'assets/img/p_painter.jpg', enter='slide')
    cap(c, P, 2.0, [('l', [('A painter could spend', 0.15, 's')]), ('c', [('months', 0.55, 'b')])],
        x=W / 2 if SHORT else 1400, y=1330 if SHORT else 540, tone='light', scrim=SHORT)
    P.close()
    # 2. icons that draw themselves
    s = Scene(c, 2.0, 4.0, ground='paper'); s.drift(s=1.03); sfx(c, 2.0, 'tick')
    cvx.icons_flow(s, [('video', 'your video', None, 2.1), ('scissors', 'the cut', None, 2.6), ('sparkles', 'the edit', None, 3.1)], tone='ink')
    s.close()
    # 3. versus
    s = Scene(c, 4.0, 5.8, ground='paper'); s.drift(s=1.03); sfx(c, 4.0, 'tick')
    cvx.versus(s, {'tag': 'by hand', 'icon': 'clock', 't': 4.05, 'lines': [('days', 4.2, 'b')]},
               {'tag': 'Canvas', 'icon': 'sparkles', 't': 4.3, 'lines': [('an hour', 4.6, 'i')]}, t_win=5.0, win='right', tone='ink')
    s.close()
    # 4. a donut on dark
    s = Scene(c, 5.8, 7.2, ground='dark'); s.drift(s=1.03); sfx(c, 5.8, 'tick')
    cvx.donut(s, 6.0, 0.35, tone='light', label='face on screen')
    s.close()
    # 5. the blue cut-out of a painted figure
    G = Scene(c, 7.2, 8.6, ground='paper'); G.drift(s=1.012)
    fw = 640 if SHORT else 760
    figure(G, 'assets/img/figure.png', 'assets/img/figure_halo.png', 7.2, cx=W / 2, fig_w=fw, nat=(945, 1311), halo_w=int(fw * 1.5))
    sfx(c, 7.2, 'pop')
    cap(c, G, 8.6, [('l', [('the only thing', 7.3, 's')]), ('c', [('left', 7.6, 'b')])], x=W / 2 if SHORT else 400,
        y=380 if SHORT else 460, tone='ink')
    G.close()
    # 6. a quote on blue
    Q = Scene(c, 8.6, 10.0, ground='blue_vig'); Q.drift(s=1.035); sfx(c, 8.6, 'tick')
    cap(c, Q, 10.0, [('l', [('“', 8.7, 'q'), ("it's what you", 8.7, 's')]), ('c', [('have to', 9.0, 'b'), ('say.', 9.3, 'i'), ('”', 9.4, 'q')])],
        x=W / 2, y=H / 2, tone='light')
    Q.close()
    c.write('index.html', title='Canvas preview')
    c.write_cues('sfx-cues.txt')
    hfv = os.environ.get('HF_VERSION', '0.9.16')
    print('preview: rendering (about a minute the first time)...')
    run('npx', '-y', f'hyperframes@{hfv}', 'render', '.', '-o', 'silent.mp4', '--workers', '2', stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    run(sys.executable, os.path.join(SK, 'scripts', 'mix-sfx.py'), 'silent.mp4', 'sfx-cues.txt', 'preview.mp4', stdout=subprocess.DEVNULL)
    run('ffmpeg', '-nostdin', '-v', 'error', '-y', '-i', 'preview.mp4', '-vf', f'fps=1,scale={360 if SHORT else 480}:-2,tile={10 if SHORT else 5}x{1 if SHORT else 2}',
        '-frames:v', '1', 'preview-sheet.jpg')
    print(f'preview: {OUT}/preview.mp4  and  {OUT}/preview-sheet.jpg')
    if sys.platform == 'darwin':
        subprocess.run(['open', 'preview.mp4'])


if __name__ == '__main__':
    main()
