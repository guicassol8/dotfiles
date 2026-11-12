#!/usr/bin/env python3
"""reservas: duas cenas simples feitas por codigo para testar o motor do papel vivo
quando falta a arte de um elemento. Nao sao a arte final.
  reserva-a: ruinas ao entardecer (fogo, terra, eletricidade)
  reserva-b: lago noturno com cristais (agua, vento, mana pura)"""
import random
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

AQUI = Path(__file__).resolve().parent
L, A = 640, 360


def ceu(cores, faixas=14):
    """Degrade em faixas (cara de pixel art) entre as cores dadas, de cima para baixo."""
    c = np.array(cores, np.float32)
    y = np.floor(np.linspace(0, 1, A) * faixas) / (faixas - 1)
    pos = y * (len(c) - 1)
    i = np.minimum(pos.astype(int), len(c) - 2)
    t = (pos - i)[:, None]
    linha = c[i] * (1 - t) + c[i + 1] * t
    return Image.fromarray(np.repeat(linha[:, None], L, 1).astype(np.uint8))


def serra(d, base, amp, passo, cor, sem):
    r = random.Random(sem)
    pts, x, y = [(0, A)], 0, base
    while x <= L + passo:
        y = max(base - amp, min(base + amp // 3, y + r.randint(-amp // 3, amp // 3)))
        pts.append((x, y))
        x += r.randint(passo // 2, passo)
    pts.append((L, A))
    d.polygon(pts, fill=cor)


def reserva_a():
    im = ceu([(34, 22, 52), (92, 42, 78), (196, 92, 84), (240, 170, 110)])
    d = ImageDraw.Draw(im)
    d.ellipse((300, 196, 340, 236), fill=(255, 214, 150))
    serra(d, 230, 40, 40, (70, 36, 66), 1)
    serra(d, 262, 30, 28, (44, 26, 50), 2)
    # torre em ruina com janelas acesas
    d.rectangle((420, 120, 470, 300), fill=(28, 20, 36))
    d.polygon([(420, 120), (430, 108), (444, 118), (456, 102), (470, 120)], fill=(28, 20, 36))
    for y in (140, 176, 212):
        d.rectangle((440, y, 449, y + 14), fill=(255, 190, 90))
    d.rectangle((140, 250, 156, 300), fill=(30, 22, 38))
    d.rectangle((180, 236, 196, 300), fill=(30, 22, 38))
    d.rectangle((136, 244, 200, 252), fill=(30, 22, 38))
    d.rectangle((0, 296, L, A), fill=(24, 18, 30))
    # fogueira
    d.polygon([(300, 300), (310, 276), (316, 290), (322, 270), (330, 300)], fill=(255, 140, 60))
    d.polygon([(308, 300), (314, 284), (320, 300)], fill=(255, 230, 140))
    return im


def reserva_b():
    im = ceu([(10, 10, 26), (24, 22, 54), (46, 40, 92)], 10)
    d = ImageDraw.Draw(im)
    r = random.Random(7)
    for _ in range(160):
        x, y = r.randrange(L), r.randrange(200)
        d.point((x, y), fill=(200, 200, 240) if r.random() < 0.8 else (255, 255, 255))
    d.ellipse((480, 40, 516, 76), fill=(236, 232, 255))
    d.ellipse((470, 36, 506, 72), fill=(24, 22, 54))
    serra(d, 200, 50, 46, (34, 30, 66), 3)
    serra(d, 228, 24, 24, (22, 20, 44), 4)
    # lago com reflexo em faixas
    d.rectangle((0, 240, L, A), fill=(16, 18, 40))
    for i, y in enumerate(range(246, A, 7)):
        w = 40 + i * 6
        d.line((496 - w // 2, y, 496 + w // 2, y), fill=(120, 120, 190))
    # cristais
    for x, h, cor in ((150, 60, (150, 120, 255)), (176, 40, (120, 200, 255)), (420, 50, (180, 150, 255))):
        d.polygon([(x - 8, 240), (x, 240 - h), (x + 8, 240)], fill=cor)
        d.polygon([(x, 240 - h), (x + 8, 240), (x + 3, 240)], fill=tuple(min(255, c + 60) for c in cor))
    d.rectangle((0, 238, L, 241), fill=(20, 18, 38))
    return im


if __name__ == "__main__":
    saida = AQUI / "cenas"
    saida.mkdir(exist_ok=True)
    tmp = Path(sys.argv[1]) if len(sys.argv) > 1 else saida
    for nome, f in (("reserva-a", reserva_a), ("reserva-b", reserva_b)):
        bruta = tmp / f"{nome}-bruta.png"
        f().save(bruta)
        subprocess.run([sys.executable, str(AQUI / "pixelar.py"), str(bruta), "--nome", nome,
                        "--cores", "32", "--saida", str(saida)], check=True)
        if tmp == saida:
            bruta.unlink()
