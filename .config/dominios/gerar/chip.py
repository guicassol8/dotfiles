"""Mini sintetizador de chiptune (numpy), no espirito de console de 8/16 bits.

Canais: quadrada com largura de pulso variavel, triangular de 4 bits, ruido
(retido, como o LFSR do NES). Envelopes, arpejo, vibrato e deslize de frequencia.
Tudo a 48 kHz; os osciladores rodam em 4x e descem por media (menos serrilhado).
"""
import re

import numpy as np

SR = 48000
SOBRE = 4
rng = np.random.default_rng(1412)

_NOTAS = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}


def hz(nome):
    """'D5', 'F#4', 'Bb3' -> Hz (A4 = 440)."""
    m = re.fullmatch(r"([A-G])([#b]?)(-?\d)", nome)
    n = _NOTAS[m[1]] + {"#": 1, "b": -1, "": 0}[m[2]] + 12 * (int(m[3]) + 1)
    return 440.0 * 2 ** ((n - 69) / 12)


def tempo(dur):
    return np.arange(int(round(SR * dur))) / SR


def _arr(v, n):
    return np.full(n, float(v)) if np.isscalar(v) else np.asarray(v, dtype=float)


def _desce(x):
    return x.reshape(-1, SOBRE).mean(axis=1)


def _fase(f, n):
    f4 = np.repeat(_arr(f, n), SOBRE)
    return (np.cumsum(f4) / (SR * SOBRE)) % 1.0


def quadrada(f, n, duty=0.5):
    """Pulso: duty 0.125, 0.25, 0.5 sao os timbres classicos."""
    ph = _fase(f, n)
    d = np.repeat(_arr(duty, n), SOBRE)
    return _desce(np.where(ph < d, 1.0, -1.0) - (2 * d - 1))


def triangular(f, n, bits=4):
    ph = _fase(f, n)
    s = 4 * np.abs(ph - 0.5) - 1
    q = 2 ** bits / 2 - 0.5
    return _desce(np.round(s * q) / q)


def ruido(n, taxa=8000.0, curto=False):
    """Ruido retido a `taxa` Hz (baixa = granulado/grave, alta = chiado).
    `curto` repete uma sequencia curta: timbre metalico."""
    ph = np.cumsum(_arr(taxa, n)) / SR
    idx = np.floor(ph).astype(int)
    if curto:
        idx = idx % 93
    vals = rng.choice([-1.0, 1.0], idx.max() + 2)
    return vals[idx]


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


def env(n, a=0.003, d=0.05, s=0.6, r=0.03, tau=None):
    """ADSR em segundos sobre n amostras (o release termina em n).
    Com `tau`, o sustain vira queda exponencial de meia-vida tau."""
    x = np.arange(n) / SR
    fim = n / SR
    e = np.minimum(x / max(a, 1e-4), 1.0)
    dec = s + (1 - s) * np.exp(-np.maximum(x - a, 0) / max(d / 3, 1e-4))
    e = e * dec if tau is None else e * 0.5 ** (np.maximum(x - a, 0) / tau)
    e *= np.clip((fim - x) / max(r, 1e-4), 0, 1)
    return e


def voz(tipo, f, dur, vol=1.0, duty=0.5, a=0.003, d=0.05, s=0.6, r=0.03, tau=None,
        para=None, curva=1.0, vib=None, arp=None, arp_taxa=50.0, bits=4):
    """Uma nota. f em Hz ou nome ('D5').
    para: deslize ate essa frequencia; vib: (taxa Hz, profundidade, atraso s);
    arp: lista de notas percorridas a `arp_taxa` por segundo (f e ignorada)."""
    n = int(round(SR * dur))
    x = np.arange(n) / SR
    if arp:
        fs = np.array([hz(q) if isinstance(q, str) else q for q in arp])
        fr = fs[(x * arp_taxa).astype(int) % len(fs)]
    else:
        f0 = hz(f) if isinstance(f, str) else f
        if para is not None:
            f1 = hz(para) if isinstance(para, str) else para
            fr = f0 * (f1 / f0) ** ((x / dur) ** curva)
        else:
            fr = np.full(n, f0)
    if vib:
        taxa, prof, atraso = vib
        rampa = np.clip((x - atraso) / 0.08, 0, 1)
        fr = fr * (1 + prof * rampa * np.sin(2 * np.pi * taxa * x))
    if tipo == "q":
        o = quadrada(fr, n, duty)
    elif tipo == "t":
        o = triangular(fr, n, bits)
    elif tipo == "r":
        o = ruido(n, fr)
    elif tipo == "rm":
        o = ruido(n, fr, curto=True)
    else:
        raise ValueError(tipo)
    return o * env(n, a, d, s, r, tau) * vol


def trilha(dur):
    return np.zeros(int(round(SR * dur)))


def em(base, som, inicio=0.0, ganho=1.0):
    i = int(round(inicio * SR))
    m = min(len(som), len(base) - i)
    if m > 0:
        base[i:i + m] += som[:m] * ganho
    return base


def sequencia(base, tipo, notas, bpm, inicio=0.0, ganho=1.0, **kw):
    """notas: (tempo em colcheias, nome, duracao em colcheias). Colcheia = 60/bpm/2."""
    c = 60.0 / bpm / 2
    for t0, nome, d in notas:
        em(base, voz(tipo, nome, d * c, **kw), inicio + t0 * c, ganho)
    return base


def eco(x, atraso=0.18, fb=0.35, repete=3, mistura=1.0):
    y = x.copy()
    k = int(SR * atraso)
    for i in range(1, repete + 1):
        y = np.concatenate([y, np.zeros(max(0, k * i + len(x) - len(y)))])
        y[k * i:k * i + len(x)] += x * (fb ** i) * mistura
    return y


def acorde(base, tipo, nomes, inicio, dur, ganho=1.0, **kw):
    for q in nomes:
        em(base, voz(tipo, q, dur, **kw), inicio, ganho / len(nomes) ** 0.5)
    return base


def tira_dc(x):
    """Tira o nivel medio e o ronco abaixo de ~20 Hz."""
    x = x - x.mean()
    return x - filtra(x, None, 20)


def finaliza(x, caminho, pico_db=-12.0, abre=0.002, fecha=0.02, largura=0.0004):
    """Normaliza o pico, aplica fades, estereo por microatraso. 16 bits, 48 kHz."""
    import wave
    x = tira_dc(np.asarray(x, dtype=np.float64))
    n_a = min(int(SR * abre), len(x) // 4)
    n_f = min(int(SR * fecha), len(x) // 3)
    x[:n_a] *= np.linspace(0, 1, n_a)
    x[-n_f:] *= np.linspace(1, 0, n_f) ** 2
    x = x / max(1e-9, np.abs(x).max()) * 10 ** (pico_db / 20)
    d = int(SR * largura)
    dir_ = np.concatenate([np.zeros(d), x[:-d]]) if d else x
    pcm = (np.stack([x, dir_], axis=1) * 32767).round().astype("<i2")
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(caminho), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
