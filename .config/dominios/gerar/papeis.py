#!/usr/bin/env python3
"""Gera os papeis de parede dos dominios (arte procedural, sem assets externos).

Uso: papeis.py [dominio ...] [--tamanho 1920x1080]
Le as cores de ../dominios.toml e escreve ../papeis/<dominio>.png.
O Grimorio le o sigilo e a textura de papel do repositorio do Despertar da Mana
quando ele existe; sem o repositorio, desenha o sigilo pela geometria do SVG.
"""
import math
import random
import subprocess
import sys
import tomllib
from pathlib import Path

import cairo
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

RAIZ = Path(__file__).resolve().parent.parent
TOKENS = tomllib.loads((RAIZ / "dominios.toml").read_text())
SAIDA = RAIZ / "papeis"
LIVRO = Path.home() / "Projetos/despertar-da-mana/identidade/assets"

W, H = 1920, 1080


def hexrgb(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)], dtype=np.float32)


# ------------------------------------------------------------ infraestrutura
class Tela:
    """Canvas float32 RGB com camadas cairo/PIL compostas por cima."""

    def __init__(self, fundo):
        self.px = np.ones((H, W, 3), np.float32) * hexrgb(fundo)

    def camada(self):
        surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
        ctx = cairo.Context(surf)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        return surf, ctx

    @staticmethod
    def _np(surf):
        buf = np.frombuffer(surf.get_data(), np.uint8).reshape(H, W, 4).astype(np.float32) / 255
        return buf[..., 2::-1].copy(), buf[..., 3].copy()  # rgb pre-multiplicado, alfa

    @staticmethod
    def _desfoca(rgb, a, raio):
        im = Image.fromarray((np.clip(np.dstack([rgb, a]), 0, 1) * 255).astype(np.uint8), "RGBA")
        im = im.filter(ImageFilter.GaussianBlur(raio))
        arr = np.asarray(im).astype(np.float32) / 255
        return arr[..., :3], arr[..., 3]

    def sobre(self, surf, opacidade=1.0, desfoque=0):
        rgb, a = self._np(surf)
        if desfoque:
            rgb, a = self._desfoca(rgb, a, desfoque)
        rgb, a = rgb * opacidade, a * opacidade
        self.px = self.px * (1 - a[..., None]) + rgb

    def brilho(self, surf, raio, forca=1.0):
        """Soma aditiva da camada desfocada: halo de luz."""
        rgb, a = self._np(surf)
        rgb, _ = self._desfoca(rgb, a, raio)
        self.px += rgb * forca

    def luz(self, surf, raios=(6, 24, 70), forcas=(0.9, 0.6, 0.45)):
        """Camada nitida + halos em tres escalas (efeito neon)."""
        for r, f in zip(raios, forcas):
            self.brilho(surf, r, f)
        self.sobre(surf)

    def pil(self, imagem, opacidade=1.0, aditivo=False):
        arr = np.asarray(imagem.convert("RGBA")).astype(np.float32) / 255
        rgb, a = arr[..., :3] * arr[..., 3:4] * opacidade, arr[..., 3] * opacidade
        if aditivo:
            self.px += rgb
        else:
            self.px = self.px * (1 - a[..., None]) + rgb

    def salva(self, caminho, grao=0.012, semente=7):
        rng = np.random.default_rng(semente)
        px = self.px + rng.normal(0, grao, (H, W, 1)).astype(np.float32)
        px += (rng.random((H, W, 3), dtype=np.float32) - 0.5) / 255  # dither contra banding
        Image.fromarray((np.clip(px, 0, 1) * 255 + 0.5).astype(np.uint8), "RGB").save(caminho, optimize=True)
        print("escrito", caminho)


def ruido(semente, escala=6, oitavas=5, persistencia=0.55):
    """Ruido fractal 0..1 no tamanho da tela."""
    rng = np.random.default_rng(semente)
    total = np.zeros((H, W), np.float32)
    amp, soma = 1.0, 0.0
    for o in range(oitavas):
        n = escala * 2 ** o
        peq = rng.random((max(2, int(n * H / W) + 2), n + 2), dtype=np.float32)
        im = Image.fromarray((peq * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC)
        total += np.asarray(im, np.float32) / 255 * amp
        soma += amp
        amp *= persistencia
    return total / soma


def radial(cx, cy, raio, potencia=2.0, achatamento=1.0):
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.sqrt((x - cx) ** 2 + ((y - cy) * achatamento) ** 2) / raio
    return np.clip(1 - d, 0, 1) ** potencia


def vinheta(tela, forca=0.55, raio=1.25):
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.sqrt(((x - W / 2) / (W / 2)) ** 2 + ((y - H / 2) / (H / 2)) ** 2) / raio
    tela.px *= (1 - forca * np.clip(d, 0, 1) ** 2.2)[..., None]


_cache_fonte = {}


def fonte(familia, tamanho, estilo="Regular", eixos=None):
    chave = (familia, estilo)
    if chave not in _cache_fonte:
        out = subprocess.run(["fc-match", "-f", "%{file}|%{index}", f"{familia}:style={estilo}"],
                             capture_output=True, text=True).stdout
        arq, idx = out.split("|")
        _cache_fonte[chave] = (arq, int(idx))
    arq, idx = _cache_fonte[chave]
    f = ImageFont.truetype(arq, int(tamanho), index=idx)
    if eixos:
        try:
            f.set_variation_by_axes(eixos)
        except Exception:
            pass
    return f


def texto(tela, txt, xy, fnt, cor, opacidade=1.0, espaco=0, ancora="l", brilho=0, aditivo=False):
    """Texto com entreletra em pixels. ancora: l, m ou r (horizontal)."""
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    larg = sum(d.textlength(c, font=fnt) for c in txt) + espaco * (len(txt) - 1)
    x, y = xy
    if ancora == "m":
        x -= larg / 2
    elif ancora == "r":
        x -= larg
    rgba = tuple(int(v * 255) for v in hexrgb(cor)) + (255,)
    for c in txt:
        d.text((x, y), c, font=fnt, fill=rgba)
        x += d.textlength(c, font=fnt) + espaco
    if brilho:
        halo = im.filter(ImageFilter.GaussianBlur(brilho))
        tela.pil(halo, opacidade * 0.8, aditivo=True)
    tela.pil(im, opacidade, aditivo=aditivo)
    return larg


def cor(ctx, hexa, a=1.0):
    r, g, b = hexrgb(hexa)
    ctx.set_source_rgba(float(r), float(g), float(b), a)


# ------------------------------------------------------------------ SISTEMA
def sistema():
    c = TOKENS["sistema"]["cor"]
    t = Tela(c["fundo"])
    rng = random.Random(2814)
    azul, violeta, menta = hexrgb(c["primaria"]), hexrgb(c["secundaria"]), hexrgb(c["terciaria"])
    gx, gy = W * 0.66, H * 0.47  # centro do portal

    # nevoa do fundo: azul frio subindo do portal, violeta nas bordas
    n1, n2 = ruido(11, 5), ruido(12, 9)
    t.px += (radial(gx, gy, 1100, 1.6) * (0.35 + 0.65 * n1))[..., None] * azul * 0.16
    t.px += (radial(gx - 120, gy + 60, 760, 2.4, 1.25) * n2)[..., None] * violeta * 0.20

    # piso em perspectiva convergindo para o portal
    surf, ctx = t.camada()
    horizonte = gy + 150
    ctx.set_line_width(1)
    for i in range(-40, 41):
        x0 = gx + i * 150
        cor(ctx, c["primaria"], 0.10 if i % 4 else 0.20)
        ctx.move_to(gx + i * 6, horizonte)
        ctx.line_to(x0 + (x0 - gx) * 2.2, H + 40)
        ctx.stroke()
    for k in range(1, 22):
        yy = horizonte + (H - horizonte + 40) * (k / 21) ** 2.2
        cor(ctx, c["primaria"], 0.05 + 0.13 * (k / 21))
        ctx.move_to(0, yy)
        ctx.line_to(W, yy)
        ctx.stroke()
    t.brilho(surf, 5, 0.5)
    t.sobre(surf)
    t.px *= (1 - 0.92 * radial(gx, horizonte + 10, 360, 1.2, 3.0))[..., None]  # sombra no pe do portal

    # portal: aneis elipticos turbulentos, interior negro
    surf, ctx = t.camada()
    rx, ry = 210, 330
    for anel in range(150):
        f = anel / 150
        esc = 0.74 + f * 0.62
        fase, amp = rng.uniform(0, math.tau), rng.uniform(4, 26) * (0.4 + f)
        pts = []
        for s in range(0, 361, 3):
            a = math.radians(s)
            ond = 1 + (math.sin(a * 5 + fase) + 0.6 * math.sin(a * 11 - fase * 2)) * amp / 400
            pts.append((gx + math.cos(a) * rx * esc * ond, gy + math.sin(a) * ry * esc * ond))
        mistura = azul * (1 - f) + violeta * f
        ctx.set_source_rgba(*[float(v) for v in mistura], 0.42 * (1 - f) ** 1.5 + 0.02)
        ctx.set_line_width(rng.uniform(0.6, 2.4))
        ini = rng.randrange(len(pts))
        compr = rng.randrange(40, 115)
        ctx.move_to(*pts[ini])
        for j in range(1, compr):
            ctx.line_to(*pts[(ini + j) % len(pts)])
        ctx.stroke()
    t.luz(surf, (4, 22, 80), (1.0, 0.8, 0.7))
    # nucleo: disco negro com borda branca-azulada
    surf, ctx = t.camada()
    ctx.save(); ctx.translate(gx, gy); ctx.scale(rx * 0.74, ry * 0.74)
    ctx.arc(0, 0, 1, 0, math.tau); ctx.restore()
    cor(ctx, "#010204", 0.97); ctx.fill()
    t.sobre(surf, desfoque=7)
    surf, ctx = t.camada()
    ctx.save(); ctx.translate(gx, gy); ctx.scale(rx * 0.75, ry * 0.75)
    ctx.arc(0, 0, 1, 0, math.tau); ctx.restore()
    cor(ctx, "#CFF1FF", 0.9); ctx.set_line_width(2.2); ctx.stroke()
    t.luz(surf, (3, 14, 46), (1.2, 1.0, 0.8))

    # particulas subindo (chama das sombras)
    surf, ctx = t.camada()
    for _ in range(420):
        ang = rng.uniform(0, math.tau)
        d = rng.gauss(1.25, 0.42)
        px, py = gx + math.cos(ang) * rx * d * 1.3, gy + math.sin(ang) * ry * d
        compr = rng.uniform(4, 34) * (1.3 - min(1.2, abs(d - 1)))
        mist = azul * rng.random() + menta * 0.25 + violeta * rng.random() * 0.7
        ctx.set_source_rgba(*[float(min(1, v)) for v in mist], rng.uniform(0.15, 0.85))
        ctx.set_line_width(rng.uniform(0.7, 2.0))
        ctx.move_to(px, py); ctx.line_to(px + rng.uniform(-1.5, 1.5), py - compr); ctx.stroke()
    t.luz(surf, (2, 9, 26), (0.9, 0.7, 0.5))

    # a janela do Sistema nao e pintada aqui: e o widget vivo de missoes do shell
    vinheta(t, 0.62)
    # reforca a area livre no alto para a barra
    t.px *= (1 - 0.25 * np.clip(1 - np.mgrid[0:H, 0:W][0] / 70, 0, 1))[..., None]
    t.salva(SAIDA / "sistema.png", grao=0.010)


# ----------------------------------------------------------------- GRIMORIO
def grimorio():
    d = TOKENS["grimorio"]
    c, el = d["cor"], d["elementos"]
    t = Tela(c["fundo"])
    mana = hexrgb(c["primaria"])

    # papel: textura do proprio livro, escurecida; sem o repositorio, ruido
    tex = LIVRO / "textura-papel.png"
    if tex.exists():
        im = Image.open(tex).convert("L")
        lado = im.size[0]
        mosaico = Image.new("L", (W, H))
        for yy in range(0, H, lado):
            for xx in range(0, W, lado):
                mosaico.paste(im, (xx, yy))
        g = np.asarray(mosaico, np.float32) / 255
        g = (g - g.mean()) / (g.std() + 1e-6)
    else:
        g = (ruido(5, 40, 4) - 0.5) * 4
    t.px *= (1 + 0.035 * g)[..., None]
    t.px += (ruido(21, 3, 4) - 0.5)[..., None] * hexrgb(c["superficie2"]) * 0.22
    cx, cy, R = W / 2, 404, 2.75  # R: pixels por unidade do viewBox 100 do sigilo.svg

    # halo e grande circulo ao fundo (eco do numeral gigante das aberturas)
    t.px += radial(cx, cy, 720, 2.0)[..., None] * mana * 0.085
    surf, ctx = t.camada()
    cor(ctx, c["superficie2"], 0.9); ctx.set_line_width(1.2)
    for raio in (470, 640, 900):
        ctx.arc(cx, cy, raio, 0, math.tau); ctx.stroke()
    t.sobre(surf, 0.55)

    # sigilo da mana: mesma geometria de identidade/assets/sigilo.svg
    def u(x, y):
        return cx + (x - 50) * R, cy + (y - 50) * R
    surf, ctx = t.camada()
    cor(ctx, c["primaria"], 1.0)
    ctx.set_line_width(1.2 * R); ctx.arc(cx, cy, 47 * R, 0, math.tau); ctx.stroke()
    cor(ctx, c["primaria"], 0.55)
    ctx.set_line_width(0.8 * R); ctx.arc(cx, cy, 38 * R, 0, math.tau); ctx.stroke()
    ctx.arc(cx, cy, 11 * R, 0, math.tau); ctx.stroke()
    cor(ctx, c["primaria"], 1.0); ctx.set_line_width(1.1 * R)
    for (a, b) in (((50, 35), (50, 17)), ((62.99, 42.5), (78.58, 33.5)), ((62.99, 57.5), (78.58, 66.5)),
                   ((50, 65), (50, 83)), ((37.01, 57.5), (21.42, 66.5)), ((37.01, 42.5), (21.42, 33.5))):
        ctx.move_to(*u(*a)); ctx.line_to(*u(*b)); ctx.stroke()
    ctx.arc(cx, cy, 6.5 * R, 0, math.tau); ctx.fill()
    t.brilho(surf, 26, 0.45)
    t.sobre(surf)
    pontos = (("fogo", 50, 12), ("agua", 82.91, 31), ("terra", 82.91, 69),
              ("vento", 50, 88), ("eletricidade", 17.09, 69), ("mana-pura", 17.09, 31))
    surf, ctx = t.camada()
    for chave, x, y in pontos:
        cor(ctx, c["fundo"], 1); ctx.arc(*u(x, y), 4.6 * R, 0, math.tau); ctx.fill()
        cor(ctx, el[chave], 1); ctx.arc(*u(x, y), 3.4 * R, 0, math.tau); ctx.fill()
    t.brilho(surf, 14, 0.55)
    t.sobre(surf)

    # tipografia da capa
    texto(t, "SISTEMA DE RPG DE MESA", (cx, cy - 47 * R - 66), fonte("Alegreya Sans", 20, "Medium"), c["primaria"], espaco=5, ancora="m")
    cin = fonte("Cinzel", 92, "Bold", [700])
    larg_d = ImageDraw.Draw(Image.new("L", (8, 8))).textlength("D", font=cin)
    # versaletes como na capa: inicial alta, resto menor
    def versalete(frase, y, alto, baixo):
        fa, fb = fonte("Cinzel", alto, "Bold", [700]), fonte("Cinzel", baixo, "Bold", [700])
        med = ImageDraw.Draw(Image.new("L", (8, 8)))
        partes, x = [], 0
        for palavra in frase.split(" "):
            for i, ch in enumerate(palavra):
                alta = i == 0 and ch.isupper()
                f_ = fa if alta else fb
                partes.append((ch.upper(), f_, x, 0 if alta else (alto - baixo) * 0.72))
                x += med.textlength(ch.upper(), font=f_) + 3
            x += alto * 0.30
        total = x - alto * 0.30
        for ch, f_, px, dy in partes:
            texto(t, ch, (cx - total / 2 + px, y + dy), f_, c["texto"])
    versalete("Despertar da Mana", cy + 47 * R + 44, 96, 76)
    ly = cy + 47 * R + 172
    surf, ctx = t.camada()
    cor(ctx, c["texto_suave"], 0.8); ctx.set_line_width(1)
    ctx.move_to(cx - 150, ly); ctx.line_to(cx - 20, ly); ctx.stroke()
    ctx.move_to(cx + 20, ly); ctx.line_to(cx + 150, ly); ctx.stroke()
    cor(ctx, c["primaria"], 1); ctx.arc(cx, ly, 7, 0, math.tau); ctx.stroke()
    ctx.arc(cx, ly, 2.2, 0, math.tau); ctx.fill()
    t.sobre(surf)
    texto(t, d["lema"], (cx, ly + 22), fonte("Alegreya", 25, "Italic"), c["texto_suave"], ancora="m")

    # legenda dos seis elementos e assinatura
    nomes = [("fogo", "FOGO"), ("agua", "ÁGUA"), ("terra", "TERRA"), ("vento", "VENTO"),
             ("eletricidade", "ELETRICIDADE"), ("mana-pura", "MANA PURA")]
    fl = fonte("Alegreya Sans", 15, "Medium")
    med = ImageDraw.Draw(Image.new("L", (8, 8)))
    larguras = [sum(med.textlength(ch, font=fl) + 3.2 for ch in n) for _, n in nomes]
    total = sum(larguras) + len(nomes) * 18 + (len(nomes) - 1) * 34
    x, y = cx - total / 2, H - 132
    surf, ctx = t.camada()
    for (chave, nome), lg in zip(nomes, larguras):
        cor(ctx, el[chave], 1); ctx.arc(x + 5, y + 10, 4.5, 0, math.tau); ctx.fill()
        texto(t, nome, (x + 18, y), fl, c["texto_suave"], espaco=3.2)
        x += 18 + lg + 34
    t.sobre(surf)
    texto(t, ".CASSOL", (cx, H - 92), fonte("Cinzel", 24, "Regular", [400]), c["texto"], espaco=7, ancora="m")

    # moldura dupla da capa
    surf, ctx = t.camada()
    ctx.set_line_cap(cairo.LINE_CAP_SQUARE)
    cor(ctx, c["primaria"], 0.85); ctx.set_line_width(1.4); ctx.rectangle(34.5, 34.5, W - 69, H - 69); ctx.stroke()
    cor(ctx, c["texto_suave"], 0.45); ctx.set_line_width(1); ctx.rectangle(46.5, 46.5, W - 93, H - 93); ctx.stroke()
    t.sobre(surf)
    vinheta(t, 0.42, 1.3)
    t.salva(SAIDA / "grimorio.png", grao=0.008)


# --------------------------------------------------------------- SETOR 2814
def setor2814():
    d = TOKENS["setor2814"]
    c = d["cor"]
    t = Tela(c["fundo"])
    rng = random.Random(2814)
    verde, claro = hexrgb(c["primaria"]), hexrgb(c["secundaria"])
    cx, cy = W / 2, 410

    # nebulosa
    n1, n2, n3 = ruido(31, 4, 6), ruido(32, 7, 5), ruido(33, 14, 4)
    neb = np.clip((n1 - 0.42) * 2.6, 0, 1) ** 1.7 * (0.5 + n2)
    t.px += neb[..., None] * verde * 0.16
    t.px += (np.clip((n2 - 0.5) * 3, 0, 1) * n3)[..., None] * hexrgb("#1C6BFF") * 0.07
    t.px += radial(cx, cy, 900, 1.7)[..., None] * verde * 0.13

    # estrelas
    surf, ctx = t.camada()
    for _ in range(1500):
        x, y = rng.uniform(0, W), rng.uniform(0, H)
        b = rng.random() ** 3.2
        tom = claro * (0.5 + 0.5 * rng.random()) + np.array([0.5, 0.5, 0.5], np.float32) * rng.random()
        ctx.set_source_rgba(*[float(min(1, v)) for v in tom], 0.25 + 0.75 * b)
        ctx.arc(x, y, 0.5 + 1.5 * b, 0, math.tau); ctx.fill()
    t.brilho(surf, 3, 0.9)
    t.sobre(surf)
    surf, ctx = t.camada()
    for _ in range(16):
        x, y, s = rng.uniform(0, W), rng.uniform(0, H * 0.7), rng.uniform(5, 15)
        cor(ctx, "#E9FFF3", 0.85); ctx.set_line_width(1)
        ctx.move_to(x - s, y); ctx.line_to(x + s, y); ctx.stroke()
        ctx.move_to(x, y - s); ctx.line_to(x, y + s); ctx.stroke()
        ctx.arc(x, y, 1.6, 0, math.tau); ctx.fill()
    t.luz(surf, (2, 6, 14), (0.8, 0.6, 0.4))

    # raios saindo do emblema
    surf, ctx = t.camada()
    for i in range(140):
        a = rng.uniform(0, math.tau)
        r0, r1 = rng.uniform(190, 260), rng.uniform(420, 1250)
        cor(ctx, c["primaria"], rng.uniform(0.015, 0.075)); ctx.set_line_width(rng.uniform(1, 9))
        ctx.move_to(cx + math.cos(a) * r0, cy + math.sin(a) * r0)
        ctx.line_to(cx + math.cos(a) * r1, cy + math.sin(a) * r1); ctx.stroke()
    t.sobre(surf, desfoque=5)

    # planeta: limbo com atmosfera verde
    pr = 2500
    pcx, pcy = W / 2, H + pr - 215
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)
    dist = np.sqrt((x - pcx) ** 2 + (y - pcy) ** 2)
    dentro = np.clip((pr - dist) / 2.0, 0, 1)
    t.px = t.px * (1 - dentro[..., None]) + dentro[..., None] * (hexrgb("#010403") + ruido(41, 9, 5)[..., None] * hexrgb("#0A2B1A") * 0.5 * np.clip((pr - dist) / 260, 0, 1)[..., None])
    atm = np.exp(-np.clip(dist - pr, 0, None) / 34) * (dist >= pr) + np.exp(-np.clip(pr - dist, 0, None) / 9) * (dist < pr)
    luz_lado = 0.35 + 0.65 * np.exp(-((x - W * 0.5) / 760) ** 2)
    t.px += (atm * luz_lado)[..., None] * verde * 0.85
    t.px += (np.exp(-np.abs(dist - pr) / 2.2) * luz_lado)[..., None] * hexrgb("#E9FFF3") * 0.75

    # emblema: anel com duas barras (a lanterna)
    def emblema(ctx, e=1.0):
        ro, ri, bl, bh = 148 * e, 104 * e, 322 * e, 46 * e
        ctx.new_path()
        ctx.arc(cx, cy, ro, 0, math.tau)
        ctx.new_sub_path()
        ctx.arc_negative(cx, cy, ri, math.tau, 0)
        ctx.fill()
        for sinal in (-1, 1):
            ctx.rectangle(cx - bl / 2, cy + sinal * (ro - bh * 0.26) - bh / 2, bl, bh)
            ctx.fill()
    surf, ctx = t.camada()
    cor(ctx, c["primaria"], 1)
    emblema(ctx)
    t.brilho(surf, 120, 0.9)
    t.brilho(surf, 38, 0.8)
    t.brilho(surf, 9, 0.7)
    t.sobre(surf)
    # nucleo claro: energia branca no miolo do tracado
    surf, ctx = t.camada()
    cor(ctx, "#F1FFF6", 1)
    emblema(ctx)
    rgb, a = t._np(surf)
    im = Image.fromarray((a * 255).astype(np.uint8)).filter(ImageFilter.MinFilter(25)).filter(ImageFilter.GaussianBlur(7))
    miolo = np.asarray(im, np.float32) / 255
    t.px = t.px * (1 - miolo[..., None] * 0.72) + miolo[..., None] * 0.72 * hexrgb("#DFFFEA")

    texto(t, "SETOR 2814", (cx, cy + 232), fonte("Chakra Petch", 44, "SemiBold"), c["texto"], espaco=22, ancora="m", brilho=10)
    texto(t, "TROPA DOS LANTERNAS VERDES", (cx, cy + 296), fonte("Chakra Petch", 17, "Medium"), c["primaria"], espaco=9, ancora="m", brilho=5)
    juramento = "NO DIA MAIS CLARO, NA NOITE MAIS DENSA, O MAL SUCUMBIRÁ ANTE A MINHA PRESENÇA."
    texto(t, juramento, (cx, H - 86), fonte("Chakra Petch", 15, "Medium"), c["secundaria"], opacidade=0.9, espaco=5, ancora="m")
    vinheta(t, 0.5, 1.3)
    t.salva(SAIDA / "setor2814.png", grao=0.009)


# ----------------------------------------------------------------- MALDICAO
def maldicao():
    d = TOKENS["maldicao"]
    c = d["cor"]
    t = Tela(c["fundo"])
    rng = random.Random(1989)
    nprng = np.random.default_rng(1989)
    sangue, osso, roxo = hexrgb(c["primaria"]), hexrgb(c["texto"]), hexrgb(c["secundaria"])
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)

    # brasa vermelha atras do kanji e fumaca
    fum = ruido(51, 4, 6)
    t.px += (radial(W * 0.68, H * 0.52, 880, 1.5) * (0.3 + 0.9 * fum))[..., None] * sangue * 0.30
    t.px += (radial(W * 0.2, H * 0.9, 700, 2.0) * ruido(52, 6, 5))[..., None] * roxo * 0.10

    # reticula (halftone) em diagonal
    passo = 15
    gx_, gy_ = (x * 0.866 + y * 0.5), (-x * 0.5 + y * 0.866)
    cel = np.sqrt(((gx_ % passo) - passo / 2) ** 2 + ((gy_ % passo) - passo / 2) ** 2)
    faixa = np.clip(1 - np.abs((x * 0.55 + y) - 880) / 560, 0, 1) ** 1.3 * np.clip((x - 120) / 900, 0, 1)
    pontos = np.clip((faixa * passo * 0.62 - cel) * 1.6, 0, 1)
    t.px = t.px * (1 - pontos[..., None] * 0.82) + pontos[..., None] * 0.82 * sangue * 0.92

    # palavra gigante vazada ao fundo
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    fa = fonte("Anton", 330)
    dr.text((-18, H - 392), "EXPANSÃO DE DOMÍNIO", font=fa, fill=(0, 0, 0, 0), stroke_width=2,
            stroke_fill=tuple(int(v * 255) for v in osso) + (70,))
    t.pil(im)

    # kanji gigante com glitch: tres canais deslocados e fatias horizontais
    mascara = Image.new("L", (W, H), 0)
    fk = fonte("Noto Sans CJK JP", 900, "Black")
    ImageDraw.Draw(mascara).text((W * 0.685, H * 0.47), "呪", font=fk, fill=255, anchor="mm")
    m = np.asarray(mascara, np.float32) / 255
    # desgaste: tinta falhando
    m *= 1 - 0.55 * (nprng.random((H, W), dtype=np.float32) > 0.985)  # falhas finas de tinta
    yy = 0
    while yy < H:  # fatias
        h_ = rng.choice((3, 5, 8, 13, 21, 34, 55))
        if rng.random() < 0.22:
            m[yy:yy + h_] = np.roll(m[yy:yy + h_], rng.choice((-1, 1)) * rng.randrange(5, 60), axis=1)
        yy += h_
    cam = np.zeros((H, W, 3), np.float32)
    cam += np.roll(m, -16, axis=1)[..., None] * sangue
    cam += np.roll(m, 13, axis=1)[..., None] * np.array([0.10, 0.22, 0.95], np.float32) * 0.75
    bruto = Image.fromarray((np.clip(cam, 0, 1) * 255).astype(np.uint8))
    t.px += np.asarray(bruto.filter(ImageFilter.GaussianBlur(40)), np.float32) / 255 * 0.55
    t.px = np.maximum(t.px, cam * 0.95)
    t.px = t.px * (1 - m[..., None]) + m[..., None] * osso

    # rasgos (motosserra): cortes finos com sangria
    surf, ctx = t.camada()
    ctx.set_line_cap(cairo.LINE_CAP_BUTT)
    for _ in range(11):
        x0, y0 = rng.uniform(W * 0.05, W * 0.95), rng.uniform(-40, H * 0.7)
        compr, ang = rng.uniform(260, 980), math.radians(rng.uniform(58, 66))
        x1, y1 = x0 - math.cos(ang) * compr, y0 + math.sin(ang) * compr
        ctx.set_line_width(rng.uniform(1.0, 3.2))
        cor(ctx, c["texto"], rng.uniform(0.5, 0.95))
        ctx.move_to(x0, y0); ctx.line_to(x1, y1); ctx.stroke()
    rgb, a = t._np(surf)
    t.px += np.asarray(Image.fromarray((a * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(10)), np.float32)[..., None] / 255 * sangue * 1.3
    t.sobre(surf)

    # coluna vertical e etiquetas
    fv = fonte("Noto Sans CJK JP", 62, "Black")
    for i, ch in enumerate("領域展開"):
        texto(t, ch, (112, 150 + i * 84), fv, c["primaria"], brilho=12)
    surf, ctx = t.camada()
    ctx.set_line_cap(cairo.LINE_CAP_BUTT)
    cor(ctx, c["primaria"], 1); ctx.rectangle(94, 150, 5, 4 * 84 - 12); ctx.fill()
    cor(ctx, c["texto"], 1); ctx.rectangle(112, 150 + 4 * 84 + 14, 62, 5); ctx.fill()
    t.sobre(surf)
    texto(t, "EXPANSÃO DE DOMÍNIO", (112, 150 + 4 * 84 + 34), fonte("Barlow Condensed", 30, "SemiBold"), c["texto"], espaco=6)
    texto(t, "呪術  ·  ENERGIA AMALDIÇOADA  ·  無量空処", (112, 150 + 4 * 84 + 80), fonte("Noto Sans CJK JP", 15, "Medium"), c["texto_suave"], espaco=4)

    # linhas de varredura, grao pesado e manchas
    t.px *= (0.90 + 0.10 * ((y.astype(np.int32) % 3) != 0))[..., None]
    t.px += nprng.normal(0, 0.030, (H, W, 1)).astype(np.float32) * (0.4 + 1.2 * ruido(71, 5, 4))[..., None]
    vinheta(t, 0.7, 1.15)
    t.salva(SAIDA / "maldicao.png", grao=0.016)


# ------------------------------------------------------------------ NEUTRO
def neutro():
    """Papel comum para apresentacao: ondas largas em camadas, grafite e azul, sem
    simbolo e sem texto. O terco de cima fica liso para a barra e os titulos."""
    c = TOKENS["neutro"]["cor"]
    fundo, alto, azul, verde = (hexrgb(c[k]) for k in ("fundo", "superficie2", "primaria", "terciaria"))
    t = Tela(c["fundo"])
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)
    u, v = x / W, y / H
    # degrade diagonal de base: um pouco mais claro em cima, a direita
    g = np.clip((0.55 * u + 0.75 * (1 - v)) / 1.3, 0, 1)[..., None]
    t.px = fundo * 0.78 * (1 - g) + alto * 0.92 * g
    t.px += azul * radial(W * 0.80, H * 0.16, W * 0.60, 2.2)[..., None] * 0.15
    t.px += verde * radial(W * 0.10, H * 1.00, W * 0.50, 2.4)[..., None] * 0.05
    # ondas, da mais distante (alta, clara) para a mais proxima (baixa, escura)
    ondas = ((0.46, 0.070, 0.85, 0.10, 0.34), (0.57, 0.062, 1.10, 0.62, 0.27), (0.67, 0.055, 0.95, 0.31, 0.20),
             (0.77, 0.050, 1.30, 0.85, 0.13), (0.88, 0.042, 1.05, 0.47, 0.07))
    for base_y, amp, freq, fase, tinta in ondas:
        curva = H * (base_y + amp * np.sin(2 * np.pi * (u * freq + fase))
                     + amp * 0.35 * np.sin(2 * np.pi * (u * freq * 2.3 + fase * 3.1)))
        dentro = np.clip((y - curva) / 1.5, 0, 1)[..., None]                 # borda com antisserrilhado
        queda = np.exp(-np.clip(y - curva, 0, None) / (H * 0.26))[..., None]   # clareia perto da crista
        cor_onda = fundo * (1 - tinta) + azul * tinta
        cor_onda = cor_onda * (0.42 + 0.58 * queda)
        t.px = t.px * (1 - dentro * 0.86) + cor_onda * dentro * 0.86
        crista = np.exp(-((y - curva) / 2.0) ** 2)[..., None]
        t.px += azul * crista * (0.035 + tinta * 0.10)
    vinheta(t, 0.30, 1.35)
    t.salva(SAIDA / "neutro.png", grao=0.006)


# ------------------------------------------------- logos, braille e desfoque
# Recorte do emblema de cada papel: (centro x, centro y, meio lado) em 1920x1080
RECORTES = {"sistema": (1267, 508, 400), "grimorio": (960, 404, 172),
            "setor2814": (960, 410, 225), "maldicao": (1290, 553, 475)}
# Expoente da mascara: 2 = circulo; maior = quadrado de cantos redondos (emblemas largos)
MASCARA = {"setor2814": 6}


def derivados(nome):
    """<dominio>-logo.png (emblema com borda suave), logo.txt (braille truecolor) e -desfocado.png."""
    base = Image.open(SAIDA / f"{nome}.png").convert("RGB")
    esc = base.size[0] / 1920
    if nome not in RECORTES:            # dominio sem emblema (Neutro): so a versao desfocada
        _desfocado(nome, base, esc)
        return
    cx, cy, m = (v * esc for v in RECORTES[nome])
    rec = base.crop((int(cx - m), int(cy - m), int(cx + m), int(cy + m))).resize((512, 512), Image.LANCZOS)
    arr = np.asarray(rec).astype(np.float32) / 255
    yy, xx = np.mgrid[0:512, 0:512].astype(np.float32)
    e = MASCARA.get(nome, 2)
    d = (np.abs(xx - 255.5) ** e + np.abs(yy - 255.5) ** e) ** (1 / e) / 256
    fundo = hexrgb(TOKENS[nome]["cor"]["fundo"])
    dist_fundo = np.clip(np.abs(arr - fundo).sum(axis=2) * 3.2, 0, 1)   # some com o fundo do papel
    alfa = np.clip((1.0 - d) / 0.16, 0, 1) * np.clip(dist_fundo * 1.4, 0, 1)
    logo = np.dstack([arr, alfa])
    if nome == "maldicao":
        # o kanji e quadrado e fica sobre reticula: em vez do recorte circular, isola o
        # branco-osso e recoloca as duas sombras deslocadas (sangue e azul) por baixo
        cores_ = TOKENS[nome]["cor"]
        osso_, sangue_ = hexrgb(cores_["texto"]), hexrgb(cores_["primaria"])
        branco = np.clip((arr.min(axis=2) - 0.50) / 0.22, 0, 1)
        borda = np.clip(np.minimum(np.minimum(xx, 511 - xx), np.minimum(yy, 511 - yy)) / 14, 0, 1)
        branco *= borda
        verm = np.roll(branco, -9, axis=1)
        azul_ = np.roll(branco, 7, axis=1)
        rgb = np.zeros((512, 512, 3), np.float32)
        a = np.zeros((512, 512), np.float32)
        for mascara, tinta in ((verm, sangue_), (azul_, np.array([0.16, 0.26, 0.95], np.float32)), (branco, osso_)):
            rgb = rgb * (1 - mascara[..., None]) + tinta * mascara[..., None]
            a = np.maximum(a, mascara)
        logo = np.dstack([rgb, a])
    Image.fromarray((logo * 255).astype(np.uint8), "RGBA").save(SAIDA / f"{nome}-logo.png", optimize=True)

    # braille: 2x4 pontos por celula
    col, lin = 30, 14
    peq = Image.fromarray((logo * 255).astype(np.uint8), "RGBA").resize((col * 2, lin * 4), Image.LANCZOS)
    p = np.asarray(peq).astype(np.float32) / 255
    lum = (p[..., :3].max(axis=2)) * p[..., 3]
    limiar = max(0.16, float(np.percentile(lum, 58)))
    bits = ((0, 0, 0x01), (1, 0, 0x02), (2, 0, 0x04), (0, 1, 0x08), (1, 1, 0x10), (2, 1, 0x20), (3, 0, 0x40), (3, 1, 0x80))
    linhas = []
    for r in range(lin):
        s = ""
        for c in range(col):
            bloco = lum[r * 4:r * 4 + 4, c * 2:c * 2 + 2]
            cores = p[r * 4:r * 4 + 4, c * 2:c * 2 + 2, :3]
            codigo, soma, n = 0, np.zeros(3), 0
            for (dy, dx, bit) in bits:
                if bloco[dy, dx] > limiar:
                    codigo |= bit
                    soma += cores[dy, dx]
                    n += 1
            if not codigo:
                s += " "
                continue
            cor_ = soma / n
            cor_ = cor_ / max(cor_.max(), 1e-3) * min(1.0, cor_.max() * 1.5 + 0.25)  # reforca o brilho
            r_, g_, b_ = (int(v * 255) for v in np.clip(cor_, 0, 1))
            s += f"\x1b[38;2;{r_};{g_};{b_}m{chr(0x2800 + codigo)}"
        linhas.append(s.rstrip() + "\x1b[0m")
    destino = RAIZ / "_build" / nome
    destino.mkdir(parents=True, exist_ok=True)
    (destino / "logo.txt").write_text("\n".join(linhas) + "\n")

    _desfocado(nome, base, esc)


def _desfocado(nome, base, esc):
    """Versao desfocada e escurecida para tela de bloqueio e login."""
    desf = base.filter(ImageFilter.GaussianBlur(22 * esc))
    a = np.asarray(desf).astype(np.float32) * 0.72
    Image.fromarray(a.astype(np.uint8)).save(SAIDA / f"{nome}-desfocado.png", optimize=True)
    print("derivados de", nome)


GERADORES = {"sistema": sistema, "grimorio": grimorio, "setor2814": setor2814, "maldicao": maldicao,
             "neutro": neutro}

if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if "--tamanho" in sys.argv:
        W, H = (int(v) for v in sys.argv[sys.argv.index("--tamanho") + 1].split("x"))
        args = [a for a in args if "x" not in a or not a.replace("x", "").isdigit()]
    SAIDA.mkdir(exist_ok=True)
    so_derivados = "--derivados" in sys.argv
    for nome in (args or GERADORES):
        if not so_derivados:
            GERADORES[nome]()
        derivados(nome)
