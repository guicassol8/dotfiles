#!/usr/bin/env python3
"""Emblema do Grimorio em pixel art (circulo magico com os seis elementos).
Gera papeis/grimorio-emblema-pixel.png (grade 48x48 ampliada x8, sem suavizacao)."""
import math
import tomllib
from pathlib import Path
from PIL import Image

RAIZ = Path(__file__).resolve().parent.parent
T = tomllib.loads((RAIZ / "dominios.toml").read_text())["grimorio"]
N, ESC = 48, 8


def rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def main():
    img = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    px = img.load()
    c = (N - 1) / 2
    mana, claro, fio = rgb(T["cor"]["primaria"]), rgb(T["cor"]["secundaria"]), rgb(T["cor"]["contorno"])
    el = [rgb(T["elementos"][k]) for k in ("fogo", "agua", "terra", "vento", "eletricidade", "mana-pura")]

    def ponto(x, y, cor):
        if 0 <= x < N and 0 <= y < N:
            px[x, y] = (*cor, 255)

    def anel(r, cor, esp=0.6):
        for y in range(N):
            for x in range(N):
                if abs(math.hypot(x - c, y - c) - r) < esp:
                    ponto(x, y, cor)
    anel(22.5, mana, 0.75)
    anel(21.0, fio, 0.5)
    anel(9.5, mana, 0.6)
    ang = [-90 + 60 * i for i in range(6)]
    for a, cor in zip(ang, el):
        ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
        for t in range(100, 168):                     # raio do anel central ao externo
            r = t / 10
            ponto(round(c + ca * r), round(c + sa * r), fio if t % 2 else mana)
    for a, cor in zip(ang, el):
        x, y = c + 16.5 * math.cos(math.radians(a)), c + 16.5 * math.sin(math.radians(a))
        for dy in range(-3, 4):
            for dx in range(-3, 4):
                d = math.hypot(dx, dy)
                if d <= 3.1:
                    f = 1.0 if d > 2.2 else 0.0
                    corp = tuple(int(v * 0.72) for v in cor) if f else cor
                    if dx + dy < -1 and d < 2.2:
                        corp = tuple(min(255, int(v * 1.2 + 40)) for v in cor)
                    ponto(round(x) + dx, round(y) + dy, corp)
    for y in range(-4, 5):
        for x in range(-4, 5):
            d = math.hypot(x, y)
            if d <= 4.2:
                ponto(round(c) + x, round(c) + y, claro if d > 3 else mana)
    img = img.resize((N * ESC, N * ESC), Image.NEAREST)
    saida = RAIZ / "papeis" / "grimorio-emblema-pixel.png"
    img.save(saida)
    print(saida)


def retrato():
    """Retrato do conjurador (hud/sprites) ampliado por vizinho mais proximo."""
    for nome, esc in (("conjurador-96.png", 4), ("conjurador-48.png", 8)):
        fonte = RAIZ / "hud/sprites" / nome
        if fonte.exists():
            im = Image.open(fonte).convert("RGBA")
            im = im.resize((im.width * esc, im.height * esc), Image.NEAREST)
            saida = RAIZ / "papeis" / "grimorio-retrato.png"
            im.save(saida)
            print(saida)
            return


def herois():
    """Corpo inteiro de cada heroi (hud/sprites/heroi-<elemento>-128.png) ampliado por vizinho
    mais proximo, para a ficha do terminal: papeis/grimorio-heroi-<elemento>-x<fator>.png.
    x3 (384 px) tem a altura da ficha; x2 (256 px) e para janela estreita. O kitty mostra o
    arquivo no tamanho nativo (sem c/r), entao cada pixel de arte vira fator x fator pixels de tela."""
    for el in T["elementos"]:
        fonte = RAIZ / "hud/sprites" / f"heroi-{el}-128.png"
        if not fonte.exists():
            continue
        im = Image.open(fonte).convert("RGBA")
        for esc in (2, 3):
            saida = RAIZ / "papeis" / f"grimorio-heroi-{el}-x{esc}.png"
            im.resize((im.width * esc, im.height * esc), Image.NEAREST).save(saida)
    print(RAIZ / "papeis" / "grimorio-heroi-*-x{2,3}.png")


def icone_barra():
    """Grimorio fechado de 10x10 pixels de arte, x3 (30 px): botao do dominio na barra."""
    desenho = [
        ".ooooooooo",
        "oslllllllo",
        "osgcccccgo",
        "oscccecc.o",
        "osccEEEcco",
        "oscccecc.o",
        "osgcccccgo",
        "osccccccco",
        "osppppppp.",
        ".oooooogo.",
    ]
    mana = rgb(T["cor"]["primaria"])
    cores = {"o": (11, 9, 16), "c": tuple(int(v * 0.55) for v in mana), "l": mana,
             "g": rgb(T["elementos"]["terra"]), "e": rgb(T["cor"]["secundaria"]), "E": (255, 255, 255),
             "p": rgb(T["cor"]["texto"]), "s": rgb(T["cor"]["secundaria"])}
    img = Image.new("RGBA", (10, 10), (0, 0, 0, 0))
    for y, linha in enumerate(desenho):
        for x, ch in enumerate(linha):
            if ch in cores:
                img.putpixel((x, y), (*cores[ch], 255))
            elif ch == "." and 0 < x < 9 and 0 < y < 9:
                img.putpixel((x, y), (*cores["c"], 255))
    saida = RAIZ / "papeis" / "grimorio-icone-barra.png"
    img.resize((30, 30), Image.NEAREST).save(saida)
    print(saida)


main()
retrato()
herois()
icone_barra()
