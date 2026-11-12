#!/usr/bin/env python3
"""Sintetiza os sons de interface de cada dominio (sem amostras externas).

Uso: sons.py [dominio ...]   ->  ../sons/<dominio>/{notificar,expandir,concluir,alerta}.wav
48 kHz, 16 bits, estereo, pico em -7 dBFS. Tudo curto: o som marca, nao toca musica.
"""
import sys
import wave
from pathlib import Path

import numpy as np

RAIZ = Path(__file__).resolve().parent.parent
SR = 48000
rng = np.random.default_rng(2814)


def t(dur):
    return np.arange(int(SR * dur)) / SR


def seno(f, dur, fase=0.0):
    return np.sin(2 * np.pi * f * t(dur) + fase)


def varre(f0, f1, dur, curva=1.0):
    """Seno com frequencia indo de f0 a f1 (curva > 1 acelera no fim)."""
    x = (t(dur) / dur) ** curva
    f = f0 * (f1 / f0) ** x
    return np.sin(2 * np.pi * np.cumsum(f) / SR)


def decai(dur, meia_vida, ataque=0.004):
    x = t(dur)
    return np.minimum(x / ataque, 1.0) * 0.5 ** (x / meia_vida)


def ruido(dur):
    return rng.standard_normal(int(SR * dur))


def filtra(x, baixo=None, alto=None):
    """Passa-faixa por FFT (corte suave)."""
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    g = np.ones_like(f)
    if baixo:
        g *= 1 / (1 + (baixo / np.maximum(f, 1e-6)) ** 4)
    if alto:
        g *= 1 / (1 + (f / alto) ** 4)
    return np.fft.irfft(X * g, len(x))


def em(base, som, inicio, ganho=1.0):
    """Soma `som` em `base` a partir de `inicio` segundos."""
    i = int(inicio * SR)
    n = min(len(som), len(base) - i)
    if n > 0:
        base[i:i + n] += som[:n] * ganho
    return base


def sala(x, tamanho=0.55, mistura=0.22, brilho=6000):
    """Reverberacao curta: convolucao com ruido que decai."""
    n = int(SR * tamanho)
    ir = filtra(rng.standard_normal(n), 200, brilho) * 0.5 ** (np.arange(n) / (SR * tamanho / 7))
    m = len(x) + n
    molhado = np.fft.irfft(np.fft.rfft(x, m) * np.fft.rfft(ir, m), m)
    molhado /= max(1e-9, np.abs(molhado).max())
    seco = np.concatenate([x, np.zeros(n)])
    return seco * (1 - mistura) + molhado * mistura * np.abs(x).max()


def sino(f, dur, parciais=((1, 1.0), (2.76, 0.45), (5.4, 0.22), (8.93, 0.10)), meia=0.22):
    s = np.zeros(int(SR * dur))
    for mult, amp in parciais:
        s += seno(f * mult, dur) * amp * decai(dur, meia / mult ** 0.5)
    return s


def cowbell(f=1.0, dur=0.32):
    """Cowbell 808: duas ondas quadradas desafinadas num passa-faixa."""
    x = t(dur)
    q = np.sign(np.sin(2 * np.pi * 540 * f * x)) + np.sign(np.sin(2 * np.pi * 800 * f * x))
    env = 0.75 * 0.5 ** (x / 0.018) + 0.25 * 0.5 ** (x / 0.085)
    return filtra(q * env, 500 * f, 2600 * f)


def grave808(f=52, dur=0.9):
    x = t(dur)
    freq = f + f * 1.6 * 0.5 ** (x / 0.03)
    s = np.sin(2 * np.pi * np.cumsum(freq) / SR)
    return np.tanh(s * 2.4) * 0.5 ** (x / 0.22)


def finaliza(x, caminho, abre=0.004, fecha=0.06, pico_db=-7.0, largura=0.0):
    x = np.asarray(x, dtype=np.float64)
    n_a, n_f = int(SR * abre), int(SR * fecha)
    x[:n_a] *= np.linspace(0, 1, n_a)
    x[-n_f:] *= np.linspace(1, 0, n_f) ** 2
    x = x / max(1e-9, np.abs(x).max()) * 10 ** (pico_db / 20)
    if largura:                     # estereo por microatraso
        d = int(SR * largura)
        esq, dir_ = x, np.concatenate([np.zeros(d), x[:-d]]) if d else x
    else:
        esq = dir_ = x
    pcm = (np.stack([esq, dir_], axis=1) * 32767).astype("<i2")
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(caminho), "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(pcm.tobytes())


# ----------------------------------------------------------------- SISTEMA
def sistema(p):
    # ding de vidro digital: duas parciais em quinta, com brilho uma oitava acima
    def ding(f, dur=0.5):
        s = seno(f, dur) * decai(dur, 0.07) + seno(f * 1.5, dur) * 0.5 * decai(dur, 0.05)
        return s + seno(f * 2, dur) * 0.25 * decai(dur, 0.03)
    finaliza(sala(ding(1318.5), 0.35, 0.18), p / "notificar.wav", largura=0.0006)
    # ativacao: varredura subindo, quatro notas e o ding final
    b = np.zeros(int(SR * 1.5))
    em(b, (varre(180, 1400, 0.55, 1.6) + 0.4 * varre(360, 2800, 0.55, 1.6)) * np.linspace(0, 1, int(SR * 0.55)) ** 2, 0.0, 0.35)
    for i, f in enumerate((659.3, 987.8, 1318.5, 1661.2)):
        em(b, ding(f, 0.4), 0.42 + i * 0.075, 0.55)
    em(b, ding(1975.5, 0.6), 0.76, 0.9)
    finaliza(sala(b, 0.5, 0.22), p / "expandir.wav", largura=0.0008)
    b = np.zeros(int(SR * 0.7))
    em(b, ding(987.8, 0.4), 0.0, 0.8); em(b, ding(1318.5, 0.5), 0.11)
    finaliza(sala(b, 0.35, 0.18), p / "concluir.wav", largura=0.0006)
    b = np.zeros(int(SR * 0.5))
    for i in range(2):
        em(b, (seno(440, 0.14) + 0.5 * seno(466.2, 0.14)) * decai(0.14, 0.05), i * 0.19)
    finaliza(b, p / "alerta.wav")


# ---------------------------------------------------------------- GRIMORIO
def grimorio(p):
    finaliza(sala(sino(587.3, 1.3), 0.7, 0.3, 4500), p / "notificar.wav", fecha=0.3, largura=0.0009)
    # o grimorio se abre: pagina virando, bordao grave e acorde de sinos em re maior
    b = np.zeros(int(SR * 2.2))
    pag = filtra(ruido(0.5), 1200, 7000) * np.sin(np.pi * t(0.5) / 0.5) ** 2
    em(b, pag * (0.6 + 0.4 * np.sin(2 * np.pi * 9 * t(0.5))), 0.0, 0.16)
    em(b, (seno(73.4, 2.0) + 0.5 * seno(146.8, 2.0)) * np.sin(np.pi * t(2.0) / 2.0) ** 1.5, 0.1, 0.35)
    for i, f in enumerate((293.7, 440.0, 740.0)):
        em(b, sino(f, 1.6), 0.35 + i * 0.16, 0.6)
    finaliza(sala(b, 0.8, 0.32, 4500), p / "expandir.wav", fecha=0.4, largura=0.001)
    b = np.zeros(int(SR * 1.2))
    em(b, sino(880.0, 0.9), 0.0, 0.7); em(b, sino(1174.7, 1.0), 0.14)
    finaliza(sala(b, 0.6, 0.28, 4500), p / "concluir.wav", fecha=0.3, largura=0.0009)
    finaliza(sala(sino(293.7, 1.0, ((1, 1.0), (1.414, 0.5), (2.76, 0.3))), 0.6, 0.3, 3000), p / "alerta.wav", fecha=0.3)
    # trilha chiptune (janela, workspace, dialogo, xp, elementos...): ver sons_grimorio.py
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import sons_grimorio
    sons_grimorio.gera(p / "chiptune")      # nunca escreve por cima dos de estudio
    import subprocess                       # reaplica o pacote ativo (chiptune ou estudio)
    ativo = (p / ".pacote").read_text().strip() if (p / ".pacote").exists() else "chiptune"
    if ativo == "estudio" and not list((p / "estudio").glob("*.wav")):
        ativo = "chiptune"
    subprocess.run([str(RAIZ / "bin" / "som-pacote"), ativo], check=True)


# -------------------------------------------------------------- SETOR 2814
def setor2814(p):
    def ping(f, dur=0.5):
        x = t(dur)
        vib = 1 + 0.004 * np.sin(2 * np.pi * 7 * x)
        s = np.sin(2 * np.pi * f * x * vib) + 0.35 * np.sin(2 * np.pi * 2 * f * x * vib)
        zumbido = filtra(np.sign(np.sin(2 * np.pi * f / 4 * x)), 80, 900) * 0.12
        return (s + zumbido) * decai(dur, 0.09, 0.012)
    finaliza(sala(ping(880.0), 0.4, 0.2), p / "notificar.wav", largura=0.0007)
    # carga do anel: zumbido subindo com tremor acelerando, e o acorde de la maior
    b = np.zeros(int(SR * 1.9))
    x = t(1.1)
    sub = varre(110, 440, 1.1, 1.4)
    serra = filtra(np.sign(sub) * 0.6 + sub, 60, 1800)
    trem = 0.6 + 0.4 * np.sin(2 * np.pi * np.cumsum(6 + 26 * (x / 1.1) ** 2) / SR)
    em(b, serra * trem * (x / 1.1) ** 1.5, 0.0, 0.5)
    for f in (440.0, 554.4, 659.3, 880.0):
        em(b, ping(f, 0.8), 1.08, 0.5)
    finaliza(sala(b, 0.6, 0.25), p / "expandir.wav", fecha=0.2, largura=0.0009)
    b = np.zeros(int(SR * 0.8))
    for i, f in enumerate((659.3, 880.0, 1108.7)):
        em(b, ping(f, 0.45), i * 0.085, 0.7)
    finaliza(sala(b, 0.4, 0.2), p / "concluir.wav", largura=0.0007)
    b = np.zeros(int(SR * 0.55))
    em(b, ping(622.3, 0.25), 0.0); em(b, ping(466.2, 0.3), 0.2)
    finaliza(b, p / "alerta.wav")


# ---------------------------------------------------------------- MALDICAO
def maldicao(p):
    finaliza(cowbell(1.0), p / "notificar.wav", pico_db=-9)
    # expansao: prato ao contrario crescendo, grave 808 e tres cowbells
    b = np.zeros(int(SR * 2.0))
    cresc = filtra(ruido(0.8), 3500, 14000) * (t(0.8) / 0.8) ** 3.5
    em(b, cresc, 0.0, 0.22)
    em(b, grave808(49, 1.1), 0.8, 1.0)
    for i, f in enumerate((1.0, 1.0, 1.19)):
        em(b, cowbell(f), 0.8 + i * 0.16, 0.42)
    finaliza(sala(b, 0.4, 0.12, 5000), p / "expandir.wav", fecha=0.25, largura=0.0005)
    b = np.zeros(int(SR * 0.6))
    em(b, cowbell(1.0), 0.0, 0.8); em(b, cowbell(1.335), 0.12)
    finaliza(b, p / "concluir.wav", pico_db=-9)
    finaliza(grave808(41, 0.6), p / "alerta.wav")


GERADORES = {"sistema": sistema, "grimorio": grimorio, "setor2814": setor2814, "maldicao": maldicao}

if __name__ == "__main__":
    for nome in (sys.argv[1:] or GERADORES):
        if nome not in GERADORES:       # dominio sem som (Neutro)
            print("sem sons para", nome)
            continue
        GERADORES[nome](RAIZ / "sons" / nome)
        print("sons de", nome)
