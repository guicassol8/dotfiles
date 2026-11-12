#!/usr/bin/env python3
"""pixelar: leva qualquer imagem para a grade do papel vivo (640x360, paleta curta).

    pixelar.py entrada.png [--nome fogo] [--cores 48] [--pontilhado nenhum|leve]
               [--elemento fogo] [--puxar 0.6] [--mascara luz-pintada.png]
               [--saida hud/papel/cenas] [--previa]
               [--reducao media|moda] [--limpar 2] [--vertical 0.5] [--gama 1.0]
               [--croma 1.0] [--vinheta 0.0] [--metodo mediana|octree]

Grava em <saida>:
  <nome>.png      a cena, 640x360, paleta de --cores cores
  <nome>-luz.png  RGBA: alfa = mascara de luz (pixels claros e saturados: fogo, janelas,
                  agua, cristais); RGB = brilho dessa luz ja desfocado (o shader so soma)
  <nome>-previa.png (com --previa) a cena ampliada 3x por vizinho mais proximo, 1920x1080
"""
import argparse
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

LARG, ALT = 640, 360
AQUI = Path(__file__).resolve().parent

# neutros do grimorio, do escuro ao claro (fundo, superficie, superficie2, contorno, texto_suave, texto)
NEUTROS = ["#17141D", "#1F1A28", "#2C2440", "#3A3348", "#B0A7C4", "#EDE7F6"]
ELEMENTOS = {"fogo": "#E8866E", "agua": "#7FBBE0", "terra": "#D3AE73", "vento": "#74C5B0",
             "eletricidade": "#FFD43B", "mana-pura": "#B4A5DD"}
BAYER4 = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]], np.float32) / 16 - 0.47


def hex_rgb(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32) / 255


# ---------- OKLab (para mexer na paleta sem estragar a luminancia) ----------
def _lin(c):
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def _srgb(c):
    c = np.clip(c, 0, 1)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - 0.055)


def para_oklab(rgb):
    r, g, b = np.moveaxis(_lin(rgb), -1, 0)
    l = np.cbrt(0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b)
    m = np.cbrt(0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b)
    s = np.cbrt(0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b)
    return np.stack([0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s,
                     1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s,
                     0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s], -1)


def de_oklab(lab):
    L, a, b = np.moveaxis(lab, -1, 0)
    l = (L + 0.3963377774 * a + 0.2158037573 * b) ** 3
    m = (L - 0.1055613458 * a - 0.0638541728 * b) ** 3
    s = (L - 0.0894841775 * a - 1.2914855480 * b) ** 3
    return _srgb(np.stack([4.0767416621 * l - 3.3077118913 * m + 0.2309699292 * s,
                           -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s,
                           -0.0041960404 * l - 0.7034226240 * m + 1.7076549816 * s], -1))


def puxar_paleta(pal, elemento, forca, realce=1.0):
    """Cores apagadas tomam o matiz dos neutros do grimorio na mesma luminancia;
    cores vivas giram em direcao ao matiz do elemento. Luminancia preservada."""
    lab = para_oklab(pal)
    neu = para_oklab(np.array([hex_rgb(c) for c in NEUTROS]))
    croma = np.hypot(lab[:, 1], lab[:, 2])
    viva = np.clip((croma - 0.03) / 0.10, 0, 1)
    # neutro: (a, b) do neutro de luminancia mais proxima, interpolado
    ordem = np.argsort(neu[:, 0])
    na = np.interp(lab[:, 0], neu[ordem, 0], neu[ordem, 1])
    nb = np.interp(lab[:, 0], neu[ordem, 0], neu[ordem, 2])
    k = forca * (1 - viva)
    lab[:, 1] = lab[:, 1] * (1 - k) + na * k
    lab[:, 2] = lab[:, 2] * (1 - k) + nb * k
    if elemento:
        el = para_oklab(hex_rgb(ELEMENTOS[elemento])[None])[0]
        h_el = np.arctan2(el[2], el[1])
        h = np.arctan2(lab[:, 2], lab[:, 1])
        dif = (h_el - h + np.pi) % (2 * np.pi) - np.pi
        h = h + dif * forca * 0.5 * viva
        c = np.hypot(lab[:, 1], lab[:, 2])
        lab[:, 1], lab[:, 2] = c * np.cos(h), c * np.sin(h)
    if realce != 1.0:
        # realce de croma so nas cores que ja eram vivas (os neutros ficam neutros)
        f = 1 + (realce - 1) * np.clip((croma - 0.015) / 0.05, 0, 1)
        lab[:, 1] *= f
        lab[:, 2] *= f
    return de_oklab(lab)


def cobrir(im, larg=LARG, alt=ALT, nitidez=True, vertical=0.5):
    """Corta cobrindo 16:9 e reduz para larg x alt. vertical: 0 = guarda o topo, 1 = o pe."""
    w, h = im.size
    alvo = LARG / ALT
    if w / h > alvo:
        nw = round(h * alvo)
        im = im.crop(((w - nw) // 2, 0, (w - nw) // 2 + nw, h))
    else:
        nh = round(w / alvo)
        y0 = round((h - nh) * vertical)
        im = im.crop((0, y0, w, y0 + nh))
    if im.size == (larg, alt):
        return im
    # reduz em caixa (media honesta) e devolve um pouco de nitidez
    im = im.resize((larg, alt), Image.Resampling.BOX if im.width >= 2 * larg else Image.Resampling.LANCZOS)
    return im.filter(ImageFilter.UnsharpMask(radius=1.0, percent=60, threshold=2)) if nitidez else im


def paleta(rgb, cores, elemento, forca, croma=1.0, metodo="mediana"):
    """Corte mediano na imagem 640x360, depois o puxao para o grimorio/elemento."""
    im = Image.fromarray((rgb * 255).round().astype(np.uint8))
    met = Image.Quantize.FASTOCTREE if metodo == "octree" else Image.Quantize.MEDIANCUT
    q = im.quantize(colors=cores, method=met, dither=Image.Dither.NONE)
    pal = np.array(q.getpalette()[:cores * 3], np.float32).reshape(-1, 3) / 255
    if forca > 0 or croma != 1.0:
        pal = puxar_paleta(pal, elemento, forca, croma)
    pal_im = Image.new("P", (1, 1))
    pal_im.putpalette((pal * 255).round().astype(np.uint8).ravel().tolist() + [0] * (768 - len(pal) * 3))
    return pal_im


def mapear(rgb, pal_im, pontilhado, cores):
    """Leva cada pixel para a cor mais proxima da paleta; devolve os indices."""
    h, w = rgb.shape[:2]
    if pontilhado == "leve":
        bayer = np.tile(BAYER4, (h // 4 + 1, w // 4 + 1))[:h, :w, None]
        rgb = np.clip(rgb + bayer * (1.5 / cores ** 0.5) * 0.35, 0, 1)
    base = Image.fromarray((rgb * 255).round().astype(np.uint8))
    return np.asarray(base.quantize(palette=pal_im, dither=Image.Dither.NONE), np.uint8)


def moda_blocos(idx, k):
    """Cada bloco kxk vira a cor mais frequente dentro dele (nao mistura cores)."""
    h, w = idx.shape
    b = idx.reshape(h // k, k, w // k, k).transpose(0, 2, 1, 3).reshape(h // k, w // k, k * k)
    conta = (b[..., :, None] == b[..., None, :]).sum(-1) * 2
    conta[..., (k * k) // 2] += 1  # empate: fica a cor do centro do bloco
    pega = conta.argmax(-1)
    return np.take_along_axis(b, pega[..., None], -1)[..., 0]


def limpar_orfaos(idx, passes):
    """Pixel sem nenhum vizinho (8) da mesma cor vira a cor mais comum em volta."""
    for _ in range(passes):
        p = np.pad(idx, 1, mode="edge")
        h, w = idx.shape
        viz = np.stack([p[1 + dy:1 + dy + h, 1 + dx:1 + dx + w]
                        for dy in (-1, 0, 1) for dx in (-1, 0, 1) if dy or dx])
        orfao = (viz == idx[None]).sum(0) == 0
        if not orfao.any():
            break
        conta = (viz[:, None] == viz[None, :]).sum(1)
        maior = np.take_along_axis(viz, conta.argmax(0)[None], 0)[0]
        idx = np.where(orfao, maior, idx)
    return idx


def quantizar(rgb, cores, pontilhado, elemento, forca, fino=None, limpar=0, croma=1.0, metodo="mediana"):
    """rgb: 640x360. fino (opcional): a mesma cena em 1920x1080 para reduzir por moda."""
    pal_im = paleta(rgb, cores, elemento, forca, croma, metodo)
    if fino is not None:
        idx = moda_blocos(mapear(fino, pal_im, pontilhado, cores), 3)
    else:
        idx = mapear(rgb, pal_im, pontilhado, cores)
    idx = limpar_orfaos(idx, limpar)
    q = Image.fromarray(idx, "P")
    q.putpalette(pal_im.getpalette())
    return q.convert("RGB")


def vinheta(w, h, forca):
    """Fator de brilho: 1 no terco central, caindo nas laterais e no pe da tela."""
    x = np.abs(np.linspace(-1, 1, w))[None, :]
    y = np.linspace(0, 1, h)[:, None]
    lado = np.clip((x - 0.30) / 0.70, 0, 1) ** 1.5
    pe = np.clip((y - 0.70) / 0.30, 0, 1) ** 1.5
    return (1 - forca * np.clip(lado + pe * 0.8, 0, 1))[..., None].astype(np.float32)


def mascara_luz(rgb):
    """Fontes de luz: claras e saturadas, ou quase brancas. Em degraus, como pixel art."""
    v = rgb.max(-1)
    mn = rgb.min(-1)
    s = np.where(v > 1e-4, (v - mn) / np.maximum(v, 1e-4), 0)
    # brilho relativo a vizinhanca: luz e o que se destaca do entorno
    viz = np.asarray(Image.fromarray((v * 255).astype(np.uint8)).filter(ImageFilter.BoxBlur(12)), np.float32) / 255
    destaque = np.clip((v - viz) / 0.25, 0, 1)

    def suave(a, b, x):
        t = np.clip((x - a) / (b - a), 0, 1)
        return t * t * (3 - 2 * t)
    # area grande e clara (ceu de dia) nao e luz: o branco so conta se destacar do entorno
    m = suave(0.55, 0.85, v) * suave(0.30, 0.65, s) * (0.5 + 0.5 * destaque) + suave(0.82, 0.97, v) * 0.8 * destaque
    m = np.clip(m + destaque * suave(0.4, 0.7, v) * 0.3, 0, 1)
    return np.round(m * 4) / 4


def brilho(rgb, m):
    """Luz colorida das fontes, desfocada em dois raios (perto e longe)."""
    fonte = Image.fromarray((np.clip(rgb * m[..., None], 0, 1) * 255).astype(np.uint8))
    perto = np.asarray(fonte.filter(ImageFilter.GaussianBlur(3)), np.float32) / 255
    longe = np.asarray(fonte.filter(ImageFilter.GaussianBlur(14)), np.float32) / 255
    return np.clip(perto * 0.9 + longe * 1.6, 0, 1)


def main():
    ap = argparse.ArgumentParser(description="Leva uma imagem para a grade de pixel do papel vivo.")
    ap.add_argument("entrada")
    ap.add_argument("--nome", help="nome de saida (padrao: nome do arquivo)")
    ap.add_argument("--cores", type=int, default=48)
    ap.add_argument("--pontilhado", choices=["nenhum", "leve"], default="nenhum")
    ap.add_argument("--elemento", choices=sorted(ELEMENTOS), help="gira as cores vivas para este elemento")
    ap.add_argument("--puxar", type=float, default=None,
                    help="0..1, quanto puxar a paleta para os neutros do grimorio (padrao 0.6 com --elemento, 0 sem)")
    ap.add_argument("--mascara", help="mascara de luz pintada a mao (cinza; claro = luz) no lugar da automatica")
    ap.add_argument("--saida", default=str(AQUI / "cenas"))
    ap.add_argument("--previa", action="store_true", help="grava tambem <nome>-previa.png em 1920x1080")
    ap.add_argument("--reducao", choices=["media", "moda"], default="media",
                    help="media: reduz direto para 640x360; moda: mapeia a paleta em 1920x1080 e cada bloco 3x3 "
                         "fica com a cor mais frequente (bordas mais limpas em arte de IA)")
    ap.add_argument("--limpar", type=int, default=0, help="passadas de limpeza de pixels orfaos (0 = nenhuma)")
    ap.add_argument("--vertical", type=float, default=0.5,
                    help="onde cortar quando a imagem e mais alta que 16:9 (0 topo, 0.5 meio, 1 pe)")
    ap.add_argument("--gama", type=float, default=1.0, help="gama aplicada antes da paleta (>1 escurece os medios)")
    ap.add_argument("--metodo", choices=["mediana", "octree"], default="mediana",
                    help="como escolher a paleta; octree guarda melhor cores pequenas e vivas (orbes, gemas)")
    ap.add_argument("--croma", type=float, default=1.0,
                    help="multiplica a croma das cores vivas da paleta (1.2 = 20%% mais saturado)")
    ap.add_argument("--vinheta", type=float, default=0.0,
                    help="0..1, escurece os tercos laterais e a faixa de baixo (onde ficam as janelas)")
    a = ap.parse_args()

    forca = a.puxar if a.puxar is not None else (0.6 if a.elemento else 0.0)
    nome = a.nome or Path(a.entrada).stem
    saida = Path(a.saida)
    saida.mkdir(parents=True, exist_ok=True)

    orig = Image.open(a.entrada).convert("RGB")
    rgb = np.asarray(cobrir(orig, vertical=a.vertical), np.float32) / 255
    fino = None
    if a.reducao == "moda":
        fino = np.asarray(cobrir(orig, LARG * 3, ALT * 3, nitidez=False, vertical=a.vertical), np.float32) / 255
    if a.gama != 1.0:
        rgb = rgb ** a.gama
        fino = None if fino is None else fino ** a.gama
    if a.vinheta > 0:
        rgb = rgb * vinheta(LARG, ALT, a.vinheta)
        fino = None if fino is None else fino * vinheta(LARG * 3, ALT * 3, a.vinheta)
    px = quantizar(rgb, max(2, min(256, a.cores)), a.pontilhado, a.elemento, forca, fino, a.limpar, a.croma, a.metodo)
    prgb = np.asarray(px, np.float32) / 255

    if a.mascara:
        m = np.asarray(cobrir(Image.open(a.mascara).convert("L"), vertical=a.vertical), np.float32) / 255
    else:
        m = mascara_luz(prgb)
    luz = np.dstack([brilho(prgb, m), m])

    px.save(saida / f"{nome}.png", optimize=True)
    Image.fromarray((luz * 255).round().astype(np.uint8), "RGBA").save(saida / f"{nome}-luz.png", optimize=True)
    if a.previa:
        px.resize((LARG * 3, ALT * 3), Image.Resampling.NEAREST).save(saida / f"{nome}-previa.png", optimize=True)
    cores = len(px.getcolors(4096) or [])
    print(f"{nome}: {cores} cores, luz em {100 * (m > 0).mean():.1f}% dos pixels -> {saida}")


if __name__ == "__main__":
    sys.exit(main())
