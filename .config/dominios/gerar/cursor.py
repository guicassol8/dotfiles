#!/usr/bin/env python3
"""Tema de cursor Grimorio (pixel art, RPG de magia) em Xcursor puro.

Arte base 16x16 desenhada como mapas de pixel (uma letra por cor). O contorno
escuro de 1 px e gerado em volta de tudo. Exporta em 2x (32 px), 3x (48 px) e
4x (64 px), sempre vizinho mais proximo. Saida: ~/.local/share/icons/Grimorio/.

Uso: cursor.py [--folha caminho.png]   (gera o tema e a folha de contato)
"""
import math
import os
import shutil
import struct
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

DESTINO = Path.home() / ".local/share/icons/Grimorio"
FOLHA = Path.home() / ".cache/dominios-dev/cursor/folha.png"
N = 16
ESCALAS = (2, 3, 4)
ATRASO = 100  # ms por quadro

PAL = {
    "#": "17141D",  # contorno
    "k": "17141D",  # tinta escura dentro do desenho
    "w": "F2EBD9",  # marfim
    "s": "B9AED6",  # sombra lilas
    "m": "A99BD9",  # mana
    "M": "6F5FB0",  # mana escura
    "h": "E6DFFA",  # brilho
    "y": "D9B45B",  # ouro (areia)
    "f": "F4DC94",  # ouro claro
    "r": "E8866E",  # fogo (perigo)
    "R": "B4513F",  # fogo escuro
    "e": "2C2440",  # vidro
}


def rgba(c):
    c = PAL[c]
    return (int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16), 255)


# ---------------------------------------------------------------- utilitarios

def mapa(linhas):
    g = [["."] * N for _ in range(N)]
    for y, l in enumerate(linhas):
        assert len(l) <= N, (y, l)
        for x, c in enumerate(l):
            g[y][x] = c
    return g


def grade():
    return [["."] * N for _ in range(N)]


def ret(g, x0, y0, x1, y1, c):
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            g[y][x] = c


def camada(base, topo, dx=0, dy=0):
    g = [l[:] for l in base]
    for y in range(N):
        for x in range(N):
            c = topo[y][x]
            if c != "." and 0 <= x + dx < N and 0 <= y + dy < N:
                g[y + dy][x + dx] = c
    return g


def girar(g, k=-1):
    a = np.array(g)
    return np.rot90(a, k).tolist()


def espelhar(g):
    return [l[::-1] for l in g]


def contorno(g):
    o = [l[:] for l in g]
    for y in range(N):
        for x in range(N):
            if g[y][x] != ".":
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < N and 0 <= ny < N and g[ny][nx] not in ".":
                    o[y][x] = "#"
                    break
    # nada de arte pode encostar na borda sem contorno
    for i in range(N):
        for (x, y) in ((i, 0), (i, N - 1), (0, i), (N - 1, i)):
            assert o[y][x] in ".#", f"arte vaza na borda em {x},{y}"
    return o


def sombrear(g):
    """Marfim vira lilas na borda de baixo/direita de massas com 2 px ou mais."""
    o = [l[:] for l in g]
    for y in range(N):
        for x in range(N):
            if g[y][x] != "w":
                continue
            ab = g[y - 1][x] if y else "."
            es = g[y][x - 1] if x else "."
            ba = g[y + 1][x] if y < N - 1 else "."
            di = g[y][x + 1] if x < N - 1 else "."
            if (ba == "." and ab == "w") or (di == "." and es == "w"):
                o[y][x] = "s"
    return o


# ------------------------------------------------------------------- a seta

SETA = mapa([
    "................",
    ".w..............",
    ".ww.............",
    ".wws............",
    ".wwws...........",
    ".wwwws..........",
    ".wwwwws.........",
    ".wwwwwws........",
    ".wwwwwwws.......",
    ".wwwwwwwws......",
    ".wwwwwws........",
    ".wwws.wws.......",
    ".wws...wwhm.....",
    ".ws.....mmmM....",
    "........MMM.....",
    "................",
])
# seta curta, para os que levam selo
SETA_MINI = mapa([
    "................",
    ".w..............",
    ".ww.............",
    ".wws............",
    ".wwws...........",
    ".wwwws..........",
    ".wwwwws.........",
    ".wwwwwws........",
    ".wwwws..........",
    ".wws.ws.........",
])

# ------------------------------------------------------------------- a luva

LUVA = mapa([
    "................",
    ".....ws.........",
    "....wws.........",
    "....wws.........",
    "....wws.........",
    "....wws.........",
    "....wwswws......",
    "....wwswwswws...",
    ".ww.wwswwswws...",
    ".wwwwwwwwwwwws..",
    ".wwwwwwwwwwwws..",
    ".wwwwwwwwwwwws..",
    "..wwwwwwwwwss...",
    "..mhhmmmmmmM....",
    "..MMMMMMMMMM....",
    "................",
])

LUVA_ABERTA = mapa([
    "................",
    ".......ws.......",
    ".......ws.ws....",
    "....ws.ws.ws....",
    "....ws.ws.ws.ws.",
    "....ws.ws.ws.ws.",
    "..w.ws.ws.ws.ws.",
    ".ww.wwwwwwwwwws.",
    ".wwwwwwwwwwwwws.",
    ".wwwwwwwwwwwwws.",
    "..wwwwwwwwwwwws.",
    "...wwwwwwwwwwss.",
    "....mhhmmmmmmM..",
    "....MMMMMMMMMM..",
    "................",
    "................",
])

LUVA_FECHADA = mapa([
    "................",
    "................",
    "................",
    "..ww.ww.ww.ww...",
    ".wwwswwswwswwws.",
    ".wwwswwswwswwws.",
    ".wwwwwwwwwwwwws.",
    ".wwwwwwwwwwwwws.",
    ".wsswwwwwwwwwws.",
    "..wwwwwwwwwwws..",
    "...wwwwwwwwwss..",
    "....mhhmmmmmmM..",
    "....MMMMMMMMMM..",
    "................",
    "................",
    "................",
])

# ---------------------------------------------------------------- formas simples

TEXTO = mapa(
    ["................", "....mmmmmmmM...."]
    + [".......ws......." for _ in range(12)]
    + ["....mmmmmmmM....", "................"]
)

MIRA = mapa(
    ["................"]
    + [".......ws......." for _ in range(5)]
    + ["................",
       ".wwwww.mm.wwwww.",
       ".sssss.MM.sssss.",
       "................"]
    + [".......ws......." for _ in range(5)]
    + ["................"]
)


def seta_dupla_h(comprimento=True):
    g = grade()
    for i, (a, b) in enumerate(((7, 8), (6, 9), (5, 10))):
        ret(g, 1 + i, a, 1 + i, b, "w")
        ret(g, 14 - i, a, 14 - i, b, "w")
    ret(g, 4, 7, 11, 8, "w")
    g = sombrear(g)
    ret(g, 7, 7, 8, 8, "m")
    return g


def mover():
    g = grade()
    h = seta_dupla_h()
    v = girar(h)
    for y in range(N):
        for x in range(N):
            if h[y][x] != "." and (x <= 4 or x >= 11):
                g[y][x] = h[y][x]
            if v[y][x] != "." and (y <= 4 or y >= 11):
                g[y][x] = v[y][x]
    ret(g, 7, 3, 8, 12, "w")
    ret(g, 3, 7, 12, 8, "w")
    g = sombrear(g)
    ret(g, 7, 7, 8, 8, "m")
    return g


def diagonal():
    """Seta dupla de canto a canto (noroeste-sudeste)."""
    g = grade()
    cabeca = [(1, 1), (2, 1), (3, 1), (4, 1), (1, 2), (2, 2), (3, 2),
              (1, 3), (2, 3), (1, 4)]
    for x, y in cabeca:
        g[y][x] = "w"
        g[15 - y][15 - x] = "w"
    for k in range(3, 8):
        g[k][k] = "w"
        g[k][k + 1] = "w"
        g[15 - k][15 - k] = "w"
        g[15 - k][14 - k] = "w"
    g = sombrear(g)
    ret(g, 7, 7, 8, 8, "m")
    return g


def col_resize():
    h = seta_dupla_h()
    g = grade()
    for y in range(N):
        for x in range(N):
            if x not in (7, 8):
                g[y][x] = h[y][x]
    for y in range(1, 15):
        g[y][7], g[y][8] = "m", "M"
    for y in (7, 8):
        for x in (6, 9):
            g[y][x] = "w" if y == 7 else "s"
    return g


def proibido():
    g = grade()
    for y in range(N):
        for x in range(N):
            d = math.hypot(x + 0.5 - 8, y + 0.5 - 8)
            if 4.9 <= d <= 7.0:
                g[y][x] = "r"
            elif d < 4.9 and abs(x - y) <= 1:
                g[y][x] = "r"
    for y in range(N):
        for x in range(N):
            if g[y][x] == "r" and (x + y >= 17 or (x - y) >= 2 and x + y >= 14):
                g[y][x] = "R"
    return g


def lupa(sinal):
    g = grade()
    for y in range(N):
        for x in range(N):
            d = math.hypot(x + 0.5 - 6, y + 0.5 - 6)
            if d <= 4.2:
                g[y][x] = "e"
            elif d <= 5.3:
                g[y][x] = "w"
    for k in range(0, 4):
        g[10 + k][10 + k] = "m"
        g[10 + k][11 + k] = "M"
        g[11 + k][10 + k] = "M" if k < 3 else "."
    ret(g, 4, 6, 8, 6, "h")
    ret(g, 4, 5, 8, 5, "h") if False else None
    ret(g, 4, 6, 8, 6, "m")
    if sinal:
        ret(g, 6, 4, 6, 8, "m")
    return g


def selo(glifo, cor="M", claro="m", tinta="h"):
    """Disco de mana 7x7 com um glifo 5x5 em tinta escura; devolve camada 16x16."""
    g = grade()
    forma = ["..###..", ".#####.", "#######", "#######", "#######", ".#####.", "..###.."]
    for y, l in enumerate(forma):
        for x, c in enumerate(l):
            if c == "#":
                g[8 + y][8 + x] = claro if (x + y) < 3 else cor
    for y, l in enumerate(glifo):
        for x, c in enumerate(l):
            if c != ".":
                g[9 + y][9 + x] = tinta
    return g


G_MAIS = ["..k..", "..k..", "kkkkk", "..k..", "..k.."]
G_INTER = [".kkk.", "kk.kk", "..kk.", ".....", "..k.."]
G_LINK = ["..kkk", "...kk", "..k.k", ".k...", "k...."]
G_MENU = ["kkkkk", ".....", "kkkkk", ".....", "kkkkk"]
G_XIS = ["k...k", ".k.k.", "..k..", ".k.k.", "k...k"]


def cursor_selo(glifo, **kw):
    return camada(SETA_MINI, selo(glifo, **kw))


def celula():
    g = grade()
    ret(g, 6, 2, 9, 13, "w")
    ret(g, 2, 6, 13, 9, "w")
    g = sombrear(g)
    ret(g, 7, 7, 8, 8, "m")
    return g


# ------------------------------------------------------------- animacoes

def ampulheta(r, b, corrente):
    g = grade()
    ret(g, 3, 1, 12, 1, "m")
    ret(g, 3, 14, 12, 14, "m")
    for x in range(3, 13):
        g[1][x] = "h" if x < 5 else "m"
        g[14][x] = "m" if x < 10 else "M"
    larg_c = [8, 8, 8, 6, 4]
    larg = larg_c + [4, 4] + larg_c[::-1]
    for i, w in enumerate(larg):
        y = 2 + i
        x0 = 8 - w // 2
        for x in range(x0, x0 + w):
            g[y][x] = "e"
        g[y][x0] = "w"
        g[y][x0 + w - 1] = "s"
    # areia de cima: r fileiras a partir do fundo da camara (y=6)
    for k in range(r):
        y = 6 - k
        w = larg[y - 2] - 2
        x0 = 8 - w // 2
        for x in range(x0, x0 + w):
            g[y][x] = "f" if k == r - 1 else "y"
    for k in range(b):
        y = 13 - k
        w = larg[y - 2] - 2
        x0 = 8 - w // 2
        for x in range(x0, x0 + w):
            g[y][x] = "f" if k == b - 1 else "y"
    if corrente:
        topo = 13 - b
        for y in range(7, topo + 1):
            g[y][7] = g[y][8] = "y"
    return g


def quadros_ampulheta():
    q = [(5, 0, False), (5, 0, True), (4, 1, True), (3, 2, True), (2, 3, True),
         (1, 4, True), (0, 5, False)]
    fs = [ampulheta(*p) for p in q]
    fs.append(girar(fs[-1], -1))
    return fs


def cristal(f):
    g = grade()
    meia = [0, 1, 2, 3, 3, 3, 2, 1, 0]
    cx = 11
    for i, hw in enumerate(meia):
        y = 6 + i
        w = int(round(hw * abs(f)))
        for x in range(cx - w, cx + w + 1):
            if w == 0:
                c = "h" if i in (2, 3) else "m"
            elif x == cx:
                c = "h"
            elif (x < cx) == (f > 0):
                c = "m"
            else:
                c = "M"
            g[y][x] = c
    return g


def quadros_cristal():
    return [camada(SETA_MINI, cristal(math.cos(math.radians(a))))
            for a in range(0, 360, 45)]


# --------------------------------------------------------------- catalogo
# nome -> (quadros, (hotspot x, hotspot y))

def catalogo():
    c = {}
    c["default"] = ([SETA], (1, 1))
    c["pointer"] = ([LUVA], (5.5, 1))
    c["text"] = ([TEXTO], (8, 8))
    c["vertical-text"] = ([girar(TEXTO)], (8, 8))
    c["wait"] = (quadros_ampulheta(), (8, 8))
    c["progress"] = (quadros_cristal(), (1, 1))
    c["grab"] = ([LUVA_ABERTA], (8, 8))
    c["grabbing"] = ([LUVA_FECHADA], (8, 7))
    c["crosshair"] = ([MIRA], (8, 8))
    c["not-allowed"] = ([proibido()], (8, 8))
    c["no-drop"] = ([cursor_selo(G_XIS, cor="R", claro="r", tinta="w")], (1, 1))
    c["help"] = ([cursor_selo(G_INTER)], (1, 1))
    c["move"] = ([mover()], (8, 8))
    c["ew-resize"] = ([seta_dupla_h()], (8, 8))
    c["ns-resize"] = ([girar(seta_dupla_h())], (8, 8))
    c["nwse-resize"] = ([diagonal()], (8, 8))
    c["nesw-resize"] = ([espelhar(diagonal())], (8, 8))
    c["col-resize"] = ([col_resize()], (8, 8))
    c["row-resize"] = ([girar(col_resize())], (8, 8))
    c["zoom-in"] = ([lupa(True)], (6, 6))
    c["zoom-out"] = ([lupa(False)], (6, 6))
    c["copy"] = ([cursor_selo(G_MAIS)], (1, 1))
    c["alias"] = ([cursor_selo(G_LINK)], (1, 1))
    c["context-menu"] = ([cursor_selo(G_MENU)], (1, 1))
    c["cell"] = ([celula()], (8, 8))
    return c


ATALHOS = {
    # nomes do X11 e do CSS
    "left_ptr": "default", "arrow": "default", "top_left_arrow": "default",
    "center_ptr": "default", "right_ptr": "default", "wayland-cursor": "default",
    "up-arrow": "default", "down-arrow": "default", "left-arrow": "default",
    "right-arrow": "default", "dnd-none": "default",
    "hand1": "pointer", "hand2": "pointer", "pointing_hand": "pointer",
    "xterm": "text", "ibeam": "text",
    "watch": "wait", "half-busy": "progress", "left_ptr_watch": "progress",
    "openhand": "grab", "closedhand": "grabbing", "dnd-move": "grabbing",
    "cross": "crosshair", "tcross": "crosshair", "cross_reverse": "crosshair",
    "diamond_cross": "crosshair", "pencil": "crosshair", "draft": "crosshair",
    "color-picker": "crosshair", "X_cursor": "crosshair", "x-cursor": "crosshair",
    "crossed_circle": "not-allowed", "circle": "not-allowed",
    "forbidden": "no-drop", "pirate": "not-allowed", "dnd-no-drop": "no-drop",
    "question_arrow": "help", "left_ptr_help": "help", "whats_this": "help",
    "dnd-ask": "help",
    "fleur": "move", "all-scroll": "move", "all-resize": "move",
    "size_all": "move",
    "sb_h_double_arrow": "ew-resize", "h_double_arrow": "ew-resize",
    "size_hor": "ew-resize", "e-resize": "ew-resize", "w-resize": "ew-resize",
    "left_side": "ew-resize", "right_side": "ew-resize",
    "sb_v_double_arrow": "ns-resize", "v_double_arrow": "ns-resize",
    "size_ver": "ns-resize", "n-resize": "ns-resize", "s-resize": "ns-resize",
    "top_side": "ns-resize", "bottom_side": "ns-resize",
    "bd_double_arrow": "nwse-resize", "size_fdiag": "nwse-resize",
    "nw-resize": "nwse-resize", "se-resize": "nwse-resize",
    "top_left_corner": "nwse-resize", "bottom_right_corner": "nwse-resize",
    "ul_angle": "nwse-resize", "lr_angle": "nwse-resize",
    "fd_double_arrow": "nesw-resize", "size_bdiag": "nesw-resize",
    "ne-resize": "nesw-resize", "sw-resize": "nesw-resize",
    "top_right_corner": "nesw-resize", "bottom_left_corner": "nesw-resize",
    "ur_angle": "nesw-resize", "ll_angle": "nesw-resize",
    "split_h": "col-resize", "split_v": "row-resize",
    "link": "alias", "dnd-link": "alias", "dnd-copy": "copy", "plus": "cell",
    # nomes em hash que ainda aparecem (GTK2, Qt, Wine, Java)
    "00000000000000020006000e7e9ffc3f": "progress",
    "08e8e1c95fe2fc01f976f1e063a24ccd": "progress",
    "3ecb610c1bf2410f44200f48c40d3599": "progress",
    "00008160000006810000408080010102": "ns-resize",
    "2870a09082c103050810ffdffffe0204": "ns-resize",
    "c7088f0f3e6c8088236ef8e1e3e70000": "ns-resize",
    "028006030e0e7ebffc7f7070c0600140": "ew-resize",
    "14fef782d02440884392942c11205230": "ew-resize",
    "03b6e0fcb3499374a867c041f52298f0": "not-allowed",
    "1081e37283d90000800003c07f3ef6bf": "copy",
    "6407b0e94181790501fd1e167b474872": "copy",
    "b66166c04f8c3109214a4fbd64a50fc8": "copy",
    "3085a0e285430894940527032f8b26df": "alias",
    "640fb0e74195791501fd1ed57b41487f": "alias",
    "a2a266d0498c3104214a47bd64ab0fc8": "alias",
    "4498f0e0c1937ffe01fd06f973665830": "grabbing",
    "9081237383d90e509aa00f00170e968f": "grabbing",
    "fcf21c00b30f7e3f83fe0dfd12e71cff": "grabbing",
    "fcf1c3c7cd4491d801f1e1c78f100000": "move",
    "5c6cd98b3f3ebcb1f9c7f1c204630408": "help",
    "d9ce0ab605698f320427677b458ad60b": "help",
    "9d800788f1b08800ae810202380a0822": "pointer",
    "e29285e634086352946a0e7090d73106": "pointer",
}


# ---------------------------------------------------------------- Xcursor

def imagem(quadro, esc):
    a = np.zeros((N, N, 4), np.uint8)
    o = contorno(quadro)
    for y in range(N):
        for x in range(N):
            if o[y][x] != ".":
                a[y, x] = rgba(o[y][x])
    return np.repeat(np.repeat(a, esc, 0), esc, 1)


def escrever_xcursor(caminho, quadros, hot):
    blocos = []  # (tamanho nominal, bytes)
    for esc in ESCALAS:
        for q in quadros:
            a = imagem(q, esc)  # alfa so 0 ou 255: pre-multiplicado == reto
            h, w = a.shape[:2]
            argb = (a[..., 3].astype("<u4") << 24 | a[..., 0].astype("<u4") << 16
                    | a[..., 1].astype("<u4") << 8 | a[..., 2].astype("<u4"))
            cab = struct.pack("<9I", 36, 0xFFFD0002, N * esc, 1, w, h,
                              int(hot[0] * esc), int(hot[1] * esc),
                              ATRASO if len(quadros) > 1 else 0)
            blocos.append((N * esc, cab + argb.astype("<u4").tobytes()))
    n = len(blocos)
    pos = 16 + 12 * n
    toc, corpo = b"", b""
    for tam, dados in blocos:
        toc += struct.pack("<3I", 0xFFFD0002, tam, pos + len(corpo))
        corpo += dados
    Path(caminho).write_bytes(b"Xcur" + struct.pack("<3I", 16, 0x10000, n) + toc + corpo)


def ler_xcursor(caminho):
    d = Path(caminho).read_bytes()
    assert d[:4] == b"Xcur", "magia errada"
    cab, ver, n = struct.unpack_from("<3I", d, 4)
    saida = []
    for i in range(n):
        tipo, sub, pos = struct.unpack_from("<3I", d, 16 + 12 * i)
        assert tipo == 0xFFFD0002
        c, t, s, v, w, h, xh, yh, at = struct.unpack_from("<9I", d, pos)
        assert (c, t, s, v) == (36, tipo, sub, 1)
        assert 0 <= xh < w and 0 <= yh < h, "hotspot fora da imagem"
        px = np.frombuffer(d, "<u4", w * h, pos + 36).reshape(h, w)
        arr = np.stack([(px >> 16) & 255, (px >> 8) & 255, px & 255, px >> 24], -1).astype(np.uint8)
        saida.append(dict(tam=sub, w=w, h=h, xh=xh, yh=yh, atraso=at, rgba=arr))
    return saida


def gerar():
    cur = DESTINO / "cursors"
    if cur.exists():
        shutil.rmtree(cur)
    cur.mkdir(parents=True)
    (DESTINO / "index.theme").write_text(
        "[Icon Theme]\nName=Grimorio\n"
        "Comment=Cursores em pixel art do grimorio do conjurador\n")
    cat = catalogo()
    for nome, (qs, hot) in cat.items():
        escrever_xcursor(cur / nome, qs, hot)
    for nome, alvo in ATALHOS.items():
        assert alvo in cat, (nome, alvo)
        os.symlink(alvo, cur / nome)
    return cat


# ---------------------------------------------------------- folha de contato

def folha(cat, caminho):
    nomes = list(cat)
    por_linha = 9
    cel = 76
    grupos = [nomes[i:i + por_linha] for i in range(0, len(nomes), por_linha)]
    alt_grupo = 3 * cel + 6
    img = Image.new("RGB", (por_linha * cel, len(grupos) * alt_grupo), (90, 90, 100))
    d = ImageDraw.Draw(img)
    fundos = [(0x17, 0x14, 0x1D), (255, 255, 255), (0x17, 0x14, 0x1D)]
    for gi, grupo in enumerate(grupos):
        for i, nome in enumerate(grupo):
            quadros = ler_xcursor(DESTINO / "cursors" / nome)
            q = [e for e in quadros if e["tam"] == 64][0]
            sprite = Image.fromarray(q["rgba"], "RGBA")
            for li in range(3):
                x0, y0 = i * cel, gi * alt_grupo + li * cel
                d.rectangle([x0, y0, x0 + cel - 1, y0 + cel - 1], fill=fundos[li])
                ox, oy = x0 + (cel - 64) // 2, y0 + (cel - 64) // 2
                if li == 2:
                    sprite_c = sprite.copy()
                    # na 3a linha a arte vai esmaecida para o ponto vermelho aparecer
                    sprite_c.putalpha(sprite.getchannel("A").point(lambda v: v // 3))
                    img.paste(sprite_c, (ox, oy), sprite_c)
                    d.rectangle([ox + q["xh"] - 1, oy + q["yh"] - 1,
                                 ox + q["xh"] + 1, oy + q["yh"] + 1], fill=(255, 0, 0))
                else:
                    img.paste(sprite, (ox, oy), sprite)
                if li == 0:
                    d.text((x0 + 2, y0 + 1), nome[:12], fill=(200, 200, 210))
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    img.save(caminho)
    # tira de quadros das animacoes
    anim = [n for n in nomes if len(cat[n][0]) > 1]
    linhas = []
    for n in anim:
        qs = [e for e in ler_xcursor(DESTINO / "cursors" / n) if e["tam"] == 64]
        faixa = Image.new("RGB", (len(qs) * 68, 140), (0x17, 0x14, 0x1D))
        for i, e in enumerate(qs):
            s = Image.fromarray(e["rgba"], "RGBA")
            faixa.paste(Image.new("RGB", (64, 64), (255, 255, 255)), (i * 68 + 2, 72))
            faixa.paste(s, (i * 68 + 2, 72), s)
            faixa.paste(s, (i * 68 + 2, 2), s)
        linhas.append(faixa)
    w = max(f.width for f in linhas)
    tira = Image.new("RGB", (w, sum(f.height for f in linhas)), (0x17, 0x14, 0x1D))
    y = 0
    for f in linhas:
        tira.paste(f, (0, y))
        y += f.height
    tira.save(caminho.with_name("animacoes.png"))


def validar(cat):
    cur = DESTINO / "cursors"
    ok = 0
    for nome, (qs, hot) in cat.items():
        im = ler_xcursor(cur / nome)
        assert len(im) == len(qs) * len(ESCALAS), nome
        for e in im:
            assert e["w"] == e["h"] == e["tam"]
            assert e["rgba"][..., 3].max() == 255
            assert len(np.unique(e["rgba"][..., 3])) <= 2
        ok += 1
    for nome in ATALHOS:
        assert (cur / nome).resolve().exists(), nome
    print(f"{ok} cursores validos, {len(ATALHOS)} atalhos resolvem")


if __name__ == "__main__":
    cat = gerar()
    validar(cat)
    alvo = sys.argv[sys.argv.index("--folha") + 1] if "--folha" in sys.argv else FOLHA
    folha(cat, alvo)
    print("folha:", alvo)
