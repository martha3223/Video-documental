#!/usr/bin/env python3
"""Arma el documental "Reconociendo prácticas escolares desde una mirada decolonial".

Uso:  python3 scripts/build.py RUTA/AL/VIDEO_ORIGINAL.MOV CARPETA_DE_TRABAJO

Genera CARPETA_DE_TRABAJO/documental_final.mp4 a partir del video original,
las imágenes de assets/imagenes y la música de assets/musica.
Requiere ffmpeg y Pillow.
"""
import os
import subprocess
import sys
import textwrap

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG = os.path.join(ROOT, "assets", "imagenes")
MUS = os.path.join(ROOT, "assets", "musica")
SRC = os.path.abspath(sys.argv[1])
WORK = os.path.abspath(sys.argv[2])
os.makedirs(WORK, exist_ok=True)

W, H, FPS = 1920, 1080, 30
GOLD = (224, 176, 74)
SERIF_B = "/usr/share/fonts/truetype/crosextra/Caladea-Bold.ttf"
SERIF_I = "/usr/share/fonts/truetype/crosextra/Caladea-Italic.ttf"
SERIF_R = "/usr/share/fonts/truetype/crosextra/Caladea-Regular.ttf"
SANS_M = "/usr/share/fonts/opentype/inter/Inter-Medium.otf"
SANS_S = "/usr/share/fonts/opentype/inter/Inter-SemiBold.otf"
SANS_R = "/usr/share/fonts/opentype/inter/Inter-Regular.otf"
SANS_L = "/usr/share/fonts/opentype/inter/Inter-Light.otf"

VENC = ["-c:v", "libx264", "-preset", "medium", "-crf", "21", "-pix_fmt", "yuv420p", "-r", str(FPS)]
AENC = ["-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2"]


def run(cmd):
    print("+", " ".join(cmd)[:300], flush=True)
    subprocess.run(cmd, check=True)


def w(*p):
    return os.path.join(WORK, *p)


def img(n):
    return os.path.join(IMG, f"c{n:02d}.jpg")


# ---------------------------------------------------------------- guion
# Escenas: (número, título, subtítulo, imagen de fondo, inicio, fin) en segundos del video original.
SCENES = [
    (1, "Introducción", "¿Qué sucede dentro de nuestras escuelas?", 1, 7.8, 69.3),
    (2, "Pedagogía decolonial", "Reconocer que todos tenemos algo que enseñar", 2, 69.3, 126.9),
    (3, "Globalización y mundialización", "Lo que sucede en el mundo también llega al aula", 3, 126.9, 170.1),
    (4, "Sujetos y conocimientos situados", "Aprender desde lo que vivimos", 4, 170.1, 227.9),
    (5, "Ciudadanía y educación", "Aprender a participar y convivir", 12, 227.9, 277.2),
    (6, "Educadores sentipensantes transhumantes", "Enseñar también es comprender", 14, 277.2, 334.85),
    (7, "Normas y libertad", "Entre el orden y la autonomía", 7, 334.85, 373.0),
    (8, "Sexualidades y militancias", "El respeto a la diversidad", 8, 373.0, 412.3),
    (9, "Perspectiva de género", "Las mismas oportunidades para todos", 9, 412.3, 447.7),
    (10, "Narrativas emancipadoras", "Dar voz a los estudiantes y a su comunidad", 10, 447.7, 491.0),
    (11, "Conclusión", "¿Qué nos deja esta experiencia como futuros docentes?", 11, 491.0, 561.9),
]

# Imágenes de apoyo (B-roll) sobre la voz: (inicio en el original, imagen, duración)
BROLL = [
    (12.0, 13, 5.5), (21.5, 1, 5.5), (48.0, 2, 5.5),
    (80.0, 14, 5.5), (113.0, 17, 5.5),
    (131.0, 3, 5.5), (156.0, 10, 5.0),
    (178.0, 18, 5.5), (210.0, 4, 5.5),
    (238.0, 15, 5.5), (262.0, 12, 5.5),
    (290.0, 16, 5.0),
    (338.0, 7, 5.0), (360.0, 5, 5.5),
    (380.0, 8, 5.5),
    (436.0, 9, 5.5),
    (455.0, 19, 5.5), (481.0, 6, 5.0),
    (501.0, 15, 5.0), (520.0, 20, 6.0),
]

# Rótulos con nombre: primera aparición de cada participante.
LOWER = [(7.8, "Osmar"), (40.1, "Jenny"), (146.9, "Miriam"), (200.0, "Martha")]

ROMAN = ["", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI"]


# ---------------------------------------------------------------- gráficos
def font(path, size):
    return ImageFont.truetype(path, size)


def spaced(draw, xy, text, fnt, fill, tracking, anchor_center=True):
    widths = [draw.textlength(c, font=fnt) for c in text]
    total = sum(widths) + tracking * (len(text) - 1)
    x, y = xy
    if anchor_center:
        x -= total / 2
    for c, cw in zip(text, widths):
        draw.text((x, y), c, font=fnt, fill=fill)
        x += cw + tracking
    return total


def centered_lines(draw, lines, fnt, y, fill, gap):
    for ln in lines:
        tw = draw.textlength(ln, font=fnt)
        draw.text(((W - tw) / 2, y), ln, font=fnt, fill=fill)
        y += fnt.size + gap
    return y


def cover(path, w_, h_):
    im = Image.open(path).convert("RGB")
    r = max(w_ / im.width, h_ / im.height)
    im = im.resize((round(im.width * r), round(im.height * r)), Image.LANCZOS)
    l, t = (im.width - w_) // 2, (im.height - h_) // 2
    return im.crop((l, t, l + w_, t + h_))


def plate(n, out, blur=0, dark=0.0):
    """Imagen 16:9 a 2x de resolución para el efecto Ken Burns.

    Las fotos verticales se colocan completas al centro sobre una versión desenfocada de sí mismas.
    """
    src = Image.open(img(n))
    if src.width / src.height < 1.2:
        im = cover(img(n), W * 2, H * 2).filter(ImageFilter.GaussianBlur(40))
        im = Image.blend(im, Image.new("RGB", im.size, (8, 8, 10)), 0.45)
        fg = src.convert("RGB")
        r = (H * 2 * 0.94) / fg.height
        fg = fg.resize((round(fg.width * r), round(fg.height * r)), Image.LANCZOS)
        x, y = (im.width - fg.width) // 2, (im.height - fg.height) // 2
        sh = Image.new("L", im.size, 0)
        ImageDraw.Draw(sh).rectangle([x + 12, y + 18, x + fg.width + 12, y + fg.height + 18], fill=150)
        sh = sh.filter(ImageFilter.GaussianBlur(30))
        im = Image.composite(Image.new("RGB", im.size, (0, 0, 0)), im, sh)
        im.paste(fg, (x, y))
    else:
        im = cover(img(n), W * 2, H * 2)
    if blur:
        im = im.filter(ImageFilter.GaussianBlur(blur))
    if dark:
        im = Image.blend(im, Image.new("RGB", im.size, (8, 8, 10)), dark)
    im.save(out, quality=93)
    return out


def vignette_layer():
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    g = Image.radial_gradient("L").resize((W, H))
    g = g.point(lambda v: int(min(255, max(0, (v - 90) * 1.3))))
    lay.putalpha(g)
    return lay


VIGNETTE = None


def chapter_png(num, title, subtitle, out):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    lay.alpha_composite(VIGNETTE)
    d = ImageDraw.Draw(lay)
    f_cap = font(SANS_M, 30)
    f_title = font(SERIF_B, 96 if len(title) < 28 else 80)
    f_sub = font(SERIF_I, 46)
    title_lines = textwrap.wrap(title, 26 if len(title) >= 28 else 40)
    sub_lines = textwrap.wrap(subtitle, 48)
    block = 30 + 40 + len(title_lines) * (f_title.size + 10) + 34 + len(sub_lines) * (f_sub.size + 12)
    y = (H - block) / 2 - 20
    spaced(d, (W / 2, y), f"CAPÍTULO {ROMAN[num]}", f_cap, GOLD + (255,), 10)
    y += 30 + 26
    d.line([(W / 2 - 60, y), (W / 2 + 60, y)], fill=GOLD + (255,), width=2)
    y += 30
    y = centered_lines(d, title_lines, f_title, y, (255, 255, 255, 255), 10)
    y += 24
    centered_lines(d, sub_lines, f_sub, y, (226, 222, 214, 255), 12)
    lay.save(out)


def quote_png(lines, out, size=58, attribution=None, small=None):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    lay.alpha_composite(VIGNETTE)
    d = ImageDraw.Draw(lay)
    f = font(SERIF_I, size)
    total = len(lines) * (size + 18) + (70 if attribution else 0)
    y = (H - total) / 2
    y = centered_lines(d, lines, f, y, (255, 255, 255, 255), 18)
    if attribution:
        y += 30
        spaced(d, (W / 2, y), attribution, font(SANS_M, 28), GOLD + (255,), 8)
    lay.save(out)


def title_png(out):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    lay.alpha_composite(VIGNETTE)
    d = ImageDraw.Draw(lay)
    spaced(d, (W / 2, 330), "UN DOCUMENTAL", font(SANS_M, 30), GOLD + (255,), 14)
    y = 400
    y = centered_lines(d, ["Reconociendo prácticas", "escolares"], font(SERIF_B, 120), y, (255, 255, 255, 255), 6)
    y += 18
    d.line([(W / 2 - 80, y), (W / 2 + 80, y)], fill=GOLD + (255,), width=2)
    y += 30
    centered_lines(d, ["desde una mirada decolonial"], font(SERIF_I, 64), y, (236, 230, 220, 255), 0)
    spaced(d, (W / 2, 900), "JORNADAS DE PRÁCTICA EN TELESECUNDARIA", font(SANS_L, 26), (220, 220, 220, 255), 6)
    lay.save(out)


def lower_png(name, out):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    grad = Image.new("L", (W, 260), 0)
    gd = ImageDraw.Draw(grad)
    for x in range(W):
        a = int(170 * max(0.0, 1 - x / 1100))
        gd.line([(x, 0), (x, 260)], fill=a)
    vmask = Image.new("L", (W, 260), 0)
    vd = ImageDraw.Draw(vmask)
    for y in range(260):
        vd.line([(0, y), (W, y)], fill=int(255 * min(1.0, y / 70, (260 - y) / 40)))
    grad = Image.composite(grad, Image.new("L", (W, 260), 0), vmask)
    band = Image.new("RGBA", (W, 260), (10, 10, 12, 255))
    band.putalpha(grad)
    lay.alpha_composite(band, (0, H - 330))
    d = ImageDraw.Draw(lay)
    x0, y0 = 120, H - 285
    d.rectangle([x0, y0, x0 + 6, y0 + 118], fill=GOLD + (255,))
    d.text((x0 + 30, y0 - 4), name, font=font(SANS_S, 62), fill=(255, 255, 255, 255))
    d.text((x0 + 32, y0 + 78), "Docente en formación", font=font(SANS_R, 32), fill=(225, 225, 225, 255))
    lay.save(out)


def credits_png(out):
    lines = []
    def add(kind, text):
        lines.append((kind, text))
    add("h", "Reconociendo prácticas escolares")
    add("hi", "desde una mirada decolonial")
    add("gap", "")
    add("cap", "PARTICIPANTES")
    for n in ["Osmar", "Jenny", "Miriam", "Martha"]:
        add("n", n)
    add("gap", "")
    add("cap", "BASADO EN EL REGISTRO DE OBSERVACIÓN")
    add("t", "Jornadas de práctica en la Telesecundaria 2, La Carmona")
    add("gap", "")
    add("cap", "FOTOGRAFÍAS DE LA TELESECUNDARIA")
    add("t", "Archivo del equipo")
    add("gap", "")
    add("cap", "MÚSICA")
    add("t", "“The Long Dark” — Scott Buckley (CC BY 3.0)")
    add("t", "“I Don't See the Branches, I See the Leaves” — Chris Zabriskie (CC BY 4.0)")
    add("gap", "")
    add("cap", "IMÁGENES DE ARCHIVO · WIKIMEDIA COMMONS")
    for row in open(os.path.join(IMG, "credits.tsv"), encoding="utf8"):
        _, title, author, lic = row.rstrip("\n").split("\t")
        author = author.replace("Unknown authorUnknown author", "Autor desconocido").replace("…", "")
        title = os.path.splitext(title)[0].replace(" - panoramio", "")
        add("s", f"{title} — {author} ({lic})")
    add("gap", "")
    add("gap", "")
    add("q", "La educación comienza cuando aprendemos")
    add("q", "a mirar, escuchar y reconocer a los demás.")
    st = {
        "h": (font(SERIF_B, 64), (255, 255, 255), 14),
        "hi": (font(SERIF_I, 48), (230, 225, 215), 14),
        "cap": (font(SANS_M, 26), GOLD, 22),
        "n": (font(SERIF_R, 50), (255, 255, 255), 12),
        "t": (font(SANS_R, 30), (225, 225, 225), 14),
        "s": (font(SANS_L, 24), (200, 200, 200), 10),
        "q": (font(SERIF_I, 46), (255, 255, 255), 12),
        "gap": (None, None, 60),
    }
    height = sum((st[k][0].size if st[k][0] else 0) + st[k][2] for k, _ in lines) + 40
    lay = Image.new("RGBA", (W, height), (0, 0, 0, 255))
    d = ImageDraw.Draw(lay)
    y = 20
    for k, t in lines:
        f, col, gap = st[k]
        if f:
            if k == "cap":
                spaced(d, (W / 2, y), t, f, col, 8)
            else:
                tw = d.textlength(t, font=f)
                d.text(((W - tw) / 2, y), t, font=f, fill=col)
            y += f.size + gap
        else:
            y += gap
    lay.save(out)
    return height


# ---------------------------------------------------------------- clips
def kenburns(plate_path, dur, out, zoom_in=True, pan=0):
    """Clip de video con movimiento lento sobre una imagen fija."""
    frames = int(round(dur * FPS))
    z = f"1.0+0.12*on/{frames}" if zoom_in else f"1.12-0.12*on/{frames}"
    x = "iw/2-(iw/zoom/2)" if pan == 0 else f"(iw-iw/zoom)*({'on' if pan > 0 else f'{frames}-on'})/{frames}"
    vf = (f"zoompan=z='{z}':x='{x}':y='ih/2-(ih/zoom/2)':d={frames}:s={W}x{H}:fps={FPS},"
          f"setsar=1,format=yuv420p")
    run(["ffmpeg", "-y", "-v", "error", "-loop", "1", "-framerate", str(FPS), "-i", plate_path,
         "-vf", vf, "-frames:v", str(frames), *VENC, "-an", out])
    return out


def card_segment(bg_plate, text_png, dur, out, zoom_in=True, text_in=0.6):
    """Tarjeta de texto: fondo animado + texto que aparece; entra y sale a negro, audio en silencio."""
    bg = kenburns(bg_plate, dur, out + ".bg.mp4", zoom_in)
    fc = (f"[1:v]format=rgba,fade=in:st={text_in}:d=0.8:alpha=1,fade=out:st={dur-1.0}:d=0.7:alpha=1[t];"
          f"[0:v][t]overlay=0:0,fade=in:st=0:d=0.6,fade=out:st={dur-0.6}:d=0.6,format=yuv420p[v]")
    run(["ffmpeg", "-y", "-v", "error", "-i", bg, "-loop", "1", "-framerate", str(FPS), "-t", str(dur),
         "-i", text_png, "-f", "lavfi", "-t", str(dur), "-i", "anullsrc=r=48000:cl=stereo",
         "-filter_complex", fc, "-map", "[v]", "-map", "2:a", *VENC, *AENC, "-t", str(dur), out])
    os.remove(bg)


def scene_segment(num, t0, t1, out):
    dur = t1 - t0
    inputs = ["-ss", f"{t0:.3f}", "-to", f"{t1:.3f}", "-i", SRC]
    chains = [f"[0:v]scale={W}:{H}:flags=lanczos,setsar=1,fps={FPS},format=yuv420p[base]"]
    last = "base"
    k = 1
    for (bt, n, bd) in BROLL:
        if t0 <= bt and bt + bd <= t1:
            clip = w("broll", f"b_{n:02d}_{int(bt)}.mp4")
            if not os.path.exists(clip):
                kenburns(plate(n, w("broll", f"p_{n:02d}.jpg")), bd, clip, zoom_in=(int(bt) % 2 == 0))
            inputs += ["-i", clip]
            off = bt - t0
            chains.append(f"[{k}:v]format=yuva420p,fade=in:st=0:d=0.6:alpha=1,"
                          f"fade=out:st={bd-0.6}:d=0.6:alpha=1,setpts=PTS-STARTPTS+{off:.3f}/TB[b{k}]")
            chains.append(f"[{last}][b{k}]overlay=0:0:eof_action=pass[o{k}]")
            last = f"o{k}"
            k += 1
    for (lt, name) in LOWER:
        if t0 <= lt < t1:
            png = w("gfx", f"lower_{name}.png")
            lower_png(name, png)
            inputs += ["-loop", "1", "-framerate", str(FPS), "-t", "6", "-i", png]
            off = lt - t0 + 0.8
            chains.append(f"[{k}:v]format=rgba,fade=in:st=0:d=0.5:alpha=1,fade=out:st=5.3:d=0.5:alpha=1,"
                          f"setpts=PTS-STARTPTS+{off:.3f}/TB[l{k}]")
            chains.append(f"[{last}][l{k}]overlay=0:0:eof_action=pass[o{k}]")
            last = f"o{k}"
            k += 1
    chains.append(f"[{last}]fade=in:st=0:d=0.5,fade=out:st={dur-0.5:.3f}:d=0.5,format=yuv420p[v]")
    chains.append(f"[0:a]aresample=48000,afade=in:st=0:d=0.12,afade=out:st={dur-0.25:.3f}:d=0.25[a]")
    run(["ffmpeg", "-y", "-v", "error", *inputs, "-filter_complex", ";".join(chains),
         "-map", "[v]", "-map", "[a]", *VENC, *AENC, "-t", f"{dur:.3f}", out])


def opening(out):
    """Apertura: dos frases sobre imágenes y el título principal, unidas con fundidos cruzados."""
    parts = [
        (1, ["Cada escuela guarda historias,", "saberes y voces."], 6.5, True),
        (2, ["No existe una sola manera", "de aprender o de conocer el mundo."], 6.5, False),
    ]
    clips = []
    for i, (n, lines, dur, zin) in enumerate(parts):
        png = w("gfx", f"open_{i}.png")
        quote_png(lines, png, size=64)
        c = w("seg", f"open_{i}.mp4")
        card_segment(plate(n, w("gfx", f"open_p{i}.jpg"), blur=3, dark=0.5), png, dur, c, zoom_in=zin, text_in=0.8)
        clips.append(c)
    tp = w("gfx", "title.png")
    title_png(tp)
    c = w("seg", "open_title.mp4")
    card_segment(plate(4, w("gfx", "open_ptitle.jpg"), blur=6, dark=0.5), tp, 9.0, c, zoom_in=True, text_in=0.7)
    clips.append(c)
    return clips


def ending():
    png = w("gfx", "end_quote.png")
    quote_png(["“La educación comienza cuando aprendemos", "a mirar, escuchar y reconocer a los demás.”"],
              png, size=56, attribution="OSMAR · JENNY · MIRIAM · MARTHA")
    c1 = w("seg", "end_quote.mp4")
    card_segment(plate(1, w("gfx", "end_p.jpg"), blur=4, dark=0.55), png, 8.0, c1, zoom_in=False)
    cp = w("gfx", "credits.png")
    hgt = credits_png(cp)
    dur = 26.0
    c2 = w("seg", "end_credits.mp4")
    speed = (hgt + H) / (dur - 1.0)
    fc = (f"color=c=black:s={W}x{H}:r={FPS}:d={dur}[bg];[1:v]format=rgba[c];"
          f"[bg][c]overlay=x=0:y='{H}-t*{speed:.3f}':shortest=0,fade=in:st=0:d=0.8,"
          f"fade=out:st={dur-1.2}:d=1.2,format=yuv420p[v]")
    run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-t", str(dur), "-i", "anullsrc=r=48000:cl=stereo",
         "-loop", "1", "-framerate", str(FPS), "-t", str(dur), "-i", cp,
         "-filter_complex", fc, "-map", "[v]", "-map", "0:a", *VENC, *AENC, "-t", str(dur), c2])
    return [c1, c2]


def main():
    global VIGNETTE
    for d in ("gfx", "seg", "broll"):
        os.makedirs(w(d), exist_ok=True)
    VIGNETTE = vignette_layer()
    only = set(sys.argv[3].split(",")) if len(sys.argv) > 3 else None

    seq = []
    if not only or "open" in only:
        seq += opening(w("seg", "x"))
    else:
        seq += [w("seg", f) for f in ("open_0.mp4", "open_1.mp4", "open_title.mp4")]
    for (num, title, sub, bgimg, t0, t1) in SCENES:
        card = w("seg", f"s{num:02d}_card.mp4")
        clip = w("seg", f"s{num:02d}_clip.mp4")
        if not only or str(num) in only:
            png = w("gfx", f"chapter_{num:02d}.png")
            chapter_png(num, title, sub, png)
            card_segment(plate(bgimg, w("gfx", f"chap_p{num:02d}.jpg"), blur=5, dark=0.45), png, 5.5, card,
                         zoom_in=(num % 2 == 1))
            scene_segment(num, t0, t1, clip)
        seq += [card, clip]
    if not only or "end" in only:
        seq += ending()
    else:
        seq += [w("seg", "end_quote.mp4"), w("seg", "end_credits.mp4")]

    lst = w("concat.txt")
    with open(lst, "w") as f:
        for s in seq:
            f.write(f"file '{s}'\n")
    body = w("body.mp4")
    run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", body])

    # Mezcla final: voz normalizada + música ambiental que baja cuando hay voz.
    total = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                           "-of", "csv=p=0", body]).decode())
    m1 = os.path.join(MUS, "scott_buckley_the_long_dark.mp3")
    m2 = os.path.join(MUS, "chris_zabriskie_branches_leaves.mp3")
    fc = (
        "[0:a]highpass=f=80,loudnorm=I=-16:LRA=9:TP=-1.5,aresample=48000,asplit=2[voz][sc];"
        "[1:a][2:a]acrossfade=d=8:c1=tri:c2=tri,aresample=48000,loudnorm=I=-21:LRA=12:TP=-3[mus0];"
        f"[mus0]atrim=0:{total:.3f},afade=in:st=0:d=2,afade=out:st={total-6:.3f}:d=6[mus];"
        "[mus][sc]sidechaincompress=threshold=0.03:ratio=4:attack=60:release=900:makeup=1[duck];"
        "[voz][duck]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.95[a]"
    )
    final = w("documental_final.mp4")
    run(["ffmpeg", "-y", "-v", "error", "-i", body, "-ss", "0", "-t", "430", "-i", m1, "-i", m2,
         "-filter_complex", fc, "-map", "0:v", "-map", "[a]", "-c:v", "copy", *AENC,
         "-movflags", "+faststart", final])
    print("LISTO:", final)


if __name__ == "__main__":
    main()
