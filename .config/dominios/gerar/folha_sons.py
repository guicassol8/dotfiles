#!/usr/bin/env python3
"""Controle de qualidade sem tocar: mede cada som do grimorio e gera a folha de contato
(forma de onda + espectrograma). Uso: folha_sons.py [saida.png]"""
import sys
import wave
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from sons_grimorio import EVENTO, INTERFACE, SONS  # noqa: E402

SAIDA = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.home() / ".cache/dominios-dev/sons/folha.png"
PASTA = Path(sys.argv[2]) if len(sys.argv) > 2 else RAIZ / "sons" / "grimorio" / "chiptune"
ESTUDIO = len(sys.argv) > 2   # pasta alheia: so mede o que existe, sem os limites do chiptune
LIMITES = {"janela-abrir": (40, 150), "janela-fechar": (40, 150), "workspace": (40, 150),
           "dialogo-letra": (40, 150), "oficio-concluido": (800, 1300), "dia-completo": (2200, 2900),
           "nivel": (2700, 3500), "login": (3600, 4600)}


def le(p):
    with wave.open(str(p)) as w:
        assert w.getframerate() == 48000 and w.getnchannels() == 2 and w.getsampwidth() == 2
        x = np.frombuffer(w.readframes(w.getnframes()), "<i2").reshape(-1, 2) / 32768.0
    return x


def cor(v):                       # escuro -> roxo -> ouro
    v = np.clip(v, 0, 1)
    pts = np.array([[23, 20, 29], [90, 60, 150], [180, 165, 221], [255, 212, 59]], float)
    pos = v * 3
    i = np.minimum(pos.astype(int), 2)
    f = (pos - i)[..., None]
    return (pts[i] * (1 - f) + pts[i + 1] * f).astype(np.uint8)


def espectro(m, larg, alt):
    n = 1024
    if len(m) < n:
        m = np.pad(m, (0, n - len(m)))
    passo = max(1, (len(m) - n) // larg)
    quadros = np.array([m[i:i + n] * np.hanning(n) for i in range(0, len(m) - n + 1, passo)][:larg])
    S = 20 * np.log10(np.abs(np.fft.rfft(quadros, axis=1)) + 1e-6).T
    S = S[::-1]
    # eixo de frequencia em escala raiz para ver graves e agudos
    idx = (np.linspace(0, 1, alt) ** 2 * (S.shape[0] - 1)).astype(int)
    S = S[idx][::-1][::-1]
    S = (S - (S.max() - 70)) / 70
    img = Image.fromarray(cor(S)).resize((larg, alt), Image.NEAREST)
    return img


def main():
    linhas, erros = [], []
    W, H, L = 380, 170, 5
    nomes = [n for n in SONS if (PASTA / f"{n}.wav").exists()]
    folha = Image.new("RGB", (W * L, H * ((len(nomes) + L - 1) // L)), (23, 20, 29))
    d = ImageDraw.Draw(folha)
    for k, nome in enumerate(nomes):
        x = le(PASTA / f"{nome}.wav")
        m = x.mean(axis=1)
        dur = len(m) / 48000 * 1000
        pico = 20 * np.log10(np.abs(x).max())
        alvo = -6.0 if ESTUDIO else SONS[nome][1]
        dc = abs(m.mean())
        topo = (np.abs(x) > 0.999).sum()
        ini, fim = abs(m[0]), abs(m[-1])
        rms = 20 * np.log10(np.sqrt((m ** 2).mean()) + 1e-9)
        lo, hi = (30, 8000) if ESTUDIO else LIMITES.get(nome, (30, 6000))
        problemas = []
        if abs(pico - alvo) > 0.3: problemas.append("pico")
        if topo: problemas.append("clip")
        if dc > 0.002: problemas.append("dc")
        if ini > 0.01 or fim > 0.01: problemas.append("estalo")
        if not lo <= dur <= hi: problemas.append("duracao")
        if rms < -45: problemas.append("quase mudo")
        linhas.append((nome, dur, pico, rms, dc, ini, fim, problemas))
        cx, cy = (k % L) * W, (k // L) * H
        d.text((cx + 6, cy + 3), f"{nome}  {dur:.0f} ms  {pico:.1f} dB" + ("  !" + ",".join(problemas) if problemas else ""),
               fill=(255, 212, 59) if problemas else (237, 231, 246))
        # forma de onda
        wf = Image.new("RGB", (W - 12, 60), (31, 26, 40))
        wd = ImageDraw.Draw(wf)
        cols = np.array_split(m, W - 12)
        for i, c in enumerate(cols):
            if len(c):
                wd.line([(i, 30 - c.max() * 29 / 0.8), (i, 30 - c.min() * 29 / 0.8)], fill=(180, 165, 221))
        wd.line([(0, 30), (W, 30)], fill=(58, 51, 72))
        folha.paste(wf, (cx + 6, cy + 18))
        folha.paste(espectro(m, W - 12, 80), (cx + 6, cy + 82))
    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    folha.save(SAIDA)
    tot = sum(p.stat().st_size for p in PASTA.glob("*.wav") if p.stem in nomes)
    print(f"{'som':24}{'ms':>7}{'pico':>7}{'rms':>7}  problemas")
    for n, du, pi, rm, dc, i, f, pr in linhas:
        print(f"{n:24}{du:7.0f}{pi:7.1f}{rm:7.1f}  {','.join(pr)}")
    print(f"\ntotal {tot / 1024:.0f} KiB em {len(linhas)} arquivos; folha em {SAIDA}")


main()
