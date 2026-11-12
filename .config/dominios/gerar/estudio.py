#!/usr/bin/env python3
"""Pos-producao dos sons de estudio comprados (bruto -> sons/grimorio/estudio/<nome>.wav).

Uso: estudio.py [nome ...]. Le ~/.cache/dominios-dev/sons/bruto/<nome>-N/ (a ultima versao),
decodifica com ffmpeg, corta o silencio das pontas, limita a duracao com fade de saida,
tira DC, iguala a loudness (RMS dos trechos ativos) e fixa o pico em -6 dBFS.
Imprime metricas de aceitacao: silencio, planura espectral, energia na faixa de fala.
48 kHz, 16 bits, estereo, como os demais.
"""
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np

RAIZ = Path(__file__).resolve().parent.parent
BRUTO = Path.home() / ".cache/dominios-dev/sons/bruto"
SAIDA = RAIZ / "sons" / "grimorio" / "estudio"
SR = 48000
ALVO_RMS = -20.0      # dBFS, so nos trechos ativos
PICO = -6.0
# nome: (duracao maxima s, fade de saida s)
LIMITES = {"elemento-agua": (2.0, 0.5), "grimorio-fechar": (1.2, 0.4), "bateria-baixa": (1.2, 0.3), "login": (6.5, 1.3), "nivel": (3.5, 0.8), "dia-completo": (3.0, 0.7), "titulo": (2.2, 0.6)}
SFX = (2.5, 0.15)


def decodifica(arq):
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", str(arq), "-f", "f32le", "-ac", "2", "-ar", str(SR), "-"],
                       capture_output=True, check=True)
    return np.frombuffer(r.stdout, "<f4").reshape(-1, 2).astype(np.float64)


def db(v):
    return 20 * np.log10(max(v, 1e-9))


def corta_pontas(x, lim_db=-50.0):
    m = np.abs(x).max(axis=1)
    h = int(SR * 0.005)
    q = np.array([m[i:i + h].max() for i in range(0, len(m) - h, h)])
    ativo = np.where(q > 10 ** (lim_db / 20))[0]
    if len(ativo) == 0:
        return x
    a = max(0, ativo[0] * h - int(SR * 0.005))
    b = min(len(x), (ativo[-1] + 1) * h + int(SR * 0.02))
    return x[a:b]


def metricas(x):
    m = x.mean(axis=1)
    h = int(SR * 0.02)
    rms = np.array([np.sqrt((m[i:i + h] ** 2).mean()) for i in range(0, len(m) - h, h)])
    pico = np.abs(m).max()
    silencio = float((rms < pico * 10 ** (-50 / 20)).mean())
    n = 2048
    quadros = [m[i:i + n] * np.hanning(n) for i in range(0, len(m) - n, n)] or [np.pad(m, (0, n - len(m)))[:n] * np.hanning(n)]
    P = np.abs(np.fft.rfft(quadros, axis=1)) ** 2 + 1e-18
    plano = float(np.mean(np.exp(np.log(P).mean(1)) / P.mean(1)))
    f = np.fft.rfftfreq(n, 1 / SR)
    fala = float(P[:, (f > 300) & (f < 3000)].sum() / P.sum())
    env = rms - rms.mean()
    mod = 0.0
    if len(env) > 100:       # modulacao de silabas: 3 a 8 Hz (quadros de 20 ms -> 50 Hz)
        E = np.abs(np.fft.rfft(env * np.hanning(len(env))))
        fe = np.fft.rfftfreq(len(env), 0.02)
        mod = float(E[(fe > 3) & (fe < 8)].sum() / (E.sum() + 1e-12))
    return silencio, plano, fala, mod


def processa(nome):
    pasta = sorted(BRUTO.glob(f"{nome}-[0-9]*"))[-1]
    arq = next(p for p in pasta.iterdir() if p.suffix in (".mp3", ".wav"))
    x = decodifica(arq)
    bruto_dur = len(x) / SR
    x = corta_pontas(x)
    x = x - x.mean(axis=0)
    dur_max, fade = LIMITES.get(nome, SFX)
    x = x[:int(SR * dur_max)]
    n_f = min(int(SR * fade), len(x) // 2)
    n_a = min(int(SR * 0.004), len(x) // 4)
    x[:n_a] *= np.linspace(0, 1, n_a)[:, None]
    x[-n_f:] *= (np.linspace(1, 0, n_f) ** 2)[:, None]
    sil, plano, fala, mod = metricas(x)
    # loudness: RMS dos quadros ativos
    m = x.mean(axis=1)
    h = int(SR * 0.02)
    q = np.array([np.sqrt((m[i:i + h] ** 2).mean()) for i in range(0, len(m) - h, h)])
    ativos = q[q > q.max() * 10 ** (-30 / 20)]
    g = 10 ** ((ALVO_RMS - db(np.sqrt((ativos ** 2).mean()))) / 20)
    x = x * g
    k = 10 ** (-9 / 20)                       # limitador suave acima de -9 dBFS
    acima = np.abs(x) > k
    x[acima] = np.sign(x[acima]) * (k + (1 - k) * np.tanh((np.abs(x[acima]) - k) / (1 - k)))
    x = x - x.mean(axis=0)                    # o limitador assimetrico pode recriar DC
    x = x / np.abs(x).max() * 10 ** (PICO / 20)
    pcm = (x * 32767).round().astype("<i2")
    SAIDA.mkdir(parents=True, exist_ok=True)
    with wave.open(str(SAIDA / f"{nome}.wav"), "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    flags = []
    if sil > 0.4: flags.append("SILENCIO")
    if plano > 0.5: flags.append("SO-RUIDO")
    if mod > 0.35 and fala > 0.7: flags.append("VOZ?")
    print(f"{nome:24} bruto {bruto_dur:5.1f}s -> {len(x)/SR:5.2f}s  silencio {sil*100:3.0f}%  planura {plano:.3f}  "
          f"fala {fala*100:3.0f}%  mod {mod:.2f}  ganho {db(g):+5.1f} dB  {' '.join(flags)}")


if __name__ == "__main__":
    nomes = sys.argv[1:] or sorted({p.name.rsplit("-", 1)[0] for p in BRUTO.iterdir() if p.is_dir() and p.name[-1].isdigit()})
    for n in nomes:
        processa(n)
