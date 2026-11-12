"""Trilha chiptune do Grimorio: Re dorico, motivo de 4 notas (o "tema do grimorio").

Uso: sons_grimorio.py [nome ...]  ->  ../sons/grimorio/<nome>.wav
Interface em -12 dBFS de pico, eventos em -6. Sons frequentes sao curtos e suaves.
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from chip import (SR, acorde, eco, em, env, filtra, finaliza, hz, rng, ruido, sequencia,  # noqa: E402
                  tempo, trilha, voz)

def ev(dur, **kw):
    return env(int(SR * dur), **kw)


RAIZ = Path(__file__).resolve().parent.parent
TEMA = ["D5", "F5", "A5", "B5"]            # o motivo: Re, Fa, La e o Si dorico
DM = ["D5", "F5", "A5", "D6"]
INTERFACE, EVENTO = -12.0, -6.0


# ---------------------------------------------------------------- interface
def janela_abrir():
    b = trilha(0.09)
    em(b, voz("q", "A4", 0.09, duty=0.25, para="E5", a=0.002, tau=0.03, r=0.02))
    return b


def janela_fechar():
    b = trilha(0.08)
    em(b, voz("t", "E5", 0.08, para="A4", a=0.002, tau=0.035, r=0.02))
    return b


def workspace():
    b = trilha(0.075)
    em(b, voz("q", "A4", 0.03, duty=0.125, a=0.001, tau=0.02, r=0.008))
    em(b, voz("q", "D5", 0.045, duty=0.125, a=0.001, tau=0.03, r=0.015), 0.03)
    return b


def visao_abrir():
    b = trilha(0.3)
    sequencia(b, "q", [(0, "D4", 1), (1, "A4", 1), (2, "D5", 1), (3, "F5", 2)], 400, duty=0.25,
              a=0.002, tau=0.04, r=0.02)
    return b


def visao_fechar():
    b = trilha(0.28)
    sequencia(b, "q", [(0, "F5", 1), (1, "D5", 1), (2, "A4", 1), (3, "D4", 2)], 400, duty=0.25,
              a=0.002, tau=0.04, r=0.02)
    return b


def notificacao():
    b = trilha(0.5)
    em(b, voz("q", "A5", 0.12, duty=0.25, a=0.002, tau=0.05, r=0.02))
    em(b, voz("q", "D6", 0.34, duty=0.25, vib=(6, 0.004, 0.1), a=0.002, tau=0.09, r=0.06), 0.1)
    return eco(b, 0.14, 0.3, 2)


def notificacao_urgente():
    b = trilha(0.7)
    for i in range(3):
        em(b, voz("q", "B5", 0.09, duty=0.5, a=0.002, s=0.8, r=0.01), i * 0.22)
        em(b, voz("q", "F5", 0.09, duty=0.5, a=0.002, s=0.8, r=0.01), i * 0.22 + 0.1)
    return b


def grimorio_abrir():
    b = trilha(1.3)
    # pagina virando: chiados curtos subindo
    for i in range(5):
        em(b, filtra(ruido(int(SR * 0.07), 18000 + i * 700), 2000, 9000)
           * ev(0.07, a=0.01, s=1.0, r=0.04), i * 0.05, 0.28)
    # capa grave
    em(b, voz("t", "D2", 0.9, para="D3", a=0.05, s=0.9, r=0.3), 0.05, 0.55)
    # arpejo subindo, tema no final
    sequencia(b, "q", [(0, "D4", 1), (1, "F4", 1), (2, "A4", 1), (3, "C5", 1), (4, "D5", 1),
                       (5, "F5", 1), (6, "A5", 1), (7, "B5", 5)], 520, inicio=0.28, duty=0.125,
              a=0.002, tau=0.18, r=0.05, vib=(6, 0.003, 0.08))
    return eco(b, 0.16, 0.3, 2)


def grimorio_fechar():
    b = trilha(0.8)
    em(b, filtra(ruido(int(SR * 0.09), 2500), None, 1200) * ev(0.09, a=0.001, tau=0.03, r=0.03), 0.34, 0.9)
    sequencia(b, "q", [(0, "B5", 1), (1, "A5", 1), (2, "F5", 1), (3, "D5", 1), (4, "A4", 3)], 560,
              duty=0.125, a=0.002, tau=0.07, r=0.04)
    em(b, voz("t", "D3", 0.4, para="D2", a=0.003, tau=0.12, r=0.15), 0.3, 0.8)
    return b


def dialogo_letra():
    b = trilha(0.045)
    em(b, voz("q", "E6", 0.045, duty=0.125, a=0.001, tau=0.012, r=0.015))
    return b


def dialogo_avancar():
    b = trilha(0.13)
    em(b, voz("q", "E5", 0.05, duty=0.25, a=0.001, tau=0.025, r=0.01))
    em(b, voz("q", "A5", 0.08, duty=0.25, a=0.001, tau=0.04, r=0.03), 0.05)
    return b


# ------------------------------------------------------------------ eventos
def xp():
    b = trilha(0.4)
    em(b, voz("q", "A5", 0.07, duty=0.5, a=0.001, s=0.8, r=0.01))
    em(b, voz("q", "E6", 0.33, duty=0.5, a=0.001, tau=0.1, r=0.1), 0.07)
    return b


def oficio_concluido():
    b = trilha(1.1)
    sequencia(b, "q", [(0, "D5", 1), (1, "F5", 1), (2, "A5", 1), (3, "D6", 5)], 420, duty=0.25,
              a=0.002, tau=0.35, r=0.1, vib=(6, 0.003, 0.1))
    sequencia(b, "t", [(0, "D3", 3), (3, "A3", 5)], 420, a=0.003, s=0.9, r=0.08)
    em(b, voz("q", "F6", 0.5, duty=0.125, a=0.002, tau=0.2, r=0.1), 0.45, 0.35)
    return eco(b, 0.15, 0.25, 2)


def _pulso_bateria(b, inicio, n=8, passo=0.25):
    for i in range(n):
        em(b, filtra(ruido(int(SR * 0.05), 9000), 600) * ev(0.05, a=0.001, tau=0.015, r=0.01),
           inicio + i * passo, 0.35)


def dia_completo():
    b = trilha(2.7)
    bpm = 200                              # colcheia = 150 ms
    # chamada: tema, resposta e resolucao
    sequencia(b, "q", [(0, "D5", 1), (1, "F5", 1), (2, "A5", 1), (3, "B5", 3),
                       (6, "A5", 1), (7, "F5", 1), (8, "G5", 1), (9, "A5", 2)], bpm, duty=0.25,
              a=0.002, d=0.04, s=0.7, r=0.05, vib=(6, 0.003, 0.12))
    # final: acorde Dm longo, com subida de arpejo
    sequencia(b, "q", [(11, "F5", 1), (12, "A5", 1), (13, "D6", 5)], bpm, duty=0.125,
              a=0.002, tau=0.4, r=0.2, vib=(6, 0.004, 0.1))
    acorde(b, "q", ["D5", "F5", "A5"], 13 * 0.15, 1.2, 0.5, duty=0.5, a=0.01, tau=0.4, r=0.3)
    # contrabaixo triangular e batida
    sequencia(b, "t", [(0, "D3", 3), (3, "G3", 3), (6, "A3", 3), (9, "G3", 2), (11, "A3", 2), (13, "D3", 6)],
              bpm, a=0.004, s=0.9, r=0.06)
    for i in (0, 3, 6, 9, 12, 13):
        em(b, filtra(ruido(int(SR * 0.08), 5000), None, 3000) * ev(0.08, a=0.001, tau=0.02, r=0.02),
           i * 0.15, 0.4)
    return eco(b, 0.15, 0.22, 2, 0.8)


def nivel():
    b = trilha(3.2)
    bpm = 240                              # colcheia = 125 ms
    c = 0.125
    # escala dorica subindo em semicolcheias
    esc = ["D4", "E4", "F4", "G4", "A4", "B4", "C5", "D5", "E5", "F5", "G5", "A5"]
    for i, q in enumerate(esc):
        em(b, voz("q", q, 0.075, duty=0.25, a=0.002, d=0.03, s=0.7, r=0.02), i * 0.0625)
    t0 = len(esc) * 0.0625 + 0.05
    # tema do grimorio, oitava acima, e fanfarra
    sequencia(b, "q", [(0, "D6", 1), (1, "F6", 1), (2, "A6", 1), (3, "B6", 3), (6, "A6", 1),
                       (7, "F6", 1), (8, "D6", 4)], bpm, inicio=t0 + 0.1, duty=0.125,
              a=0.002, d=0.04, s=0.7, r=0.05, ganho=0.8, vib=(6, 0.003, 0.1))
    tf = t0 + 0.1 + 12 * c
    acorde(b, "q", ["D5", "F5", "A5", "D6"], tf, 1.0, 0.9, duty=0.25, a=0.01, tau=0.45, r=0.3,
           vib=(6, 0.004, 0.2))
    sequencia(b, "t", [(0, "D3", 3), (3, "F3", 3), (6, "A3", 3), (9, "B3", 3)], bpm, inicio=t0 + 0.1,
              a=0.004, s=0.9, r=0.06)
    em(b, voz("t", "D3", 1.2, a=0.004, tau=0.6, r=0.3), tf, 1.0)
    # brilho cintilante no final
    for i, q in enumerate(["A6", "F6", "D6", "A6", "E6", "D6"]):
        em(b, voz("q", q, 0.25, duty=0.125, a=0.001, tau=0.06, r=0.1), tf + 0.2 + i * 0.1, 0.25)
    return eco(b, 0.2, 0.25, 3, 0.7)


def titulo():
    b = trilha(1.7)
    sequencia(b, "q", [(0, "G4", 1), (1, "B4", 1), (2, "D5", 1), (3, "G5", 2)], 400, duty=0.25,
              a=0.002, tau=0.2, r=0.05)
    sequencia(b, "q", [(5, "D5", 1), (6, "F5", 1), (7, "A5", 1), (8, "D6", 6)], 400, duty=0.25,
              a=0.002, tau=0.5, r=0.2, vib=(6, 0.004, 0.1))
    em(b, voz("t", "G2", 0.5, a=0.004, s=0.9, r=0.1), 0.0)
    em(b, voz("t", "D3", 1.0, a=0.004, tau=0.5, r=0.2), 0.8)
    for i, q in enumerate(["A6", "D7", "F6", "A6", "D7"]):
        em(b, voz("q", q, 0.2, duty=0.125, a=0.001, tau=0.05, r=0.08), 1.0 + i * 0.09, 0.2)
    return eco(b, 0.17, 0.28, 3)


def penalidade():
    b = trilha(1.0)
    sequencia(b, "q", [(0, "A4", 1), (1, "F4", 1), (2, "D4", 1)], 300, duty=0.5, a=0.003, s=0.8, r=0.05)
    em(b, voz("q", "A3", 0.5, duty=0.5, para="D3", a=0.003, tau=0.3, r=0.2, vib=(5, 0.01, 0.0)), 0.5)
    em(b, voz("t", "D2", 0.5, a=0.003, tau=0.3, r=0.2), 0.5, 0.8)
    em(b, filtra(ruido(int(SR * 0.3), 1800), None, 900) * ev(0.3, a=0.001, tau=0.08, r=0.1), 0.5, 0.5)
    return b


def bateria_baixa():
    b = trilha(0.42)
    for i in range(2):
        em(b, voz("q", "C6", 0.09, duty=0.5, a=0.002, s=0.9, r=0.012), i * 0.16)
    return b


def tomada_ligada():
    b = trilha(0.4)
    em(b, filtra(ruido(int(SR * 0.02), 14000), 3000) * ev(0.02, a=0.0005, tau=0.006, r=0.005), 0.0, 0.6)
    em(b, voz("q", "D4", 0.14, duty=0.25, para="A4", a=0.002, s=0.8, r=0.02), 0.03)
    em(b, voz("q", "D5", 0.2, duty=0.25, a=0.002, tau=0.07, r=0.06), 0.17)
    return b


def tomada_desligada():
    b = trilha(0.4)
    em(b, voz("q", "D5", 0.12, duty=0.25, a=0.002, tau=0.06, r=0.03), 0.0)
    em(b, voz("q", "A4", 0.2, duty=0.25, para="D4", a=0.002, s=0.8, r=0.05), 0.1)
    em(b, filtra(ruido(int(SR * 0.02), 14000), 3000) * ev(0.02, a=0.0005, tau=0.006, r=0.005), 0.28, 0.6)
    return b


def erro():
    b = trilha(0.36)
    em(b, voz("q", "G#2", 0.12, duty=0.5, a=0.002, s=0.9, r=0.01), 0.0)
    em(b, voz("q", "D3", 0.2, duty=0.5, a=0.002, s=0.9, r=0.05), 0.14)
    em(b, voz("q", "G#3", 0.12, duty=0.125, a=0.002, s=0.9, r=0.01), 0.0, 0.5)
    return b


def familiar_invocado():
    b = trilha(1.6)
    # espiral de energia subindo, ruido crescendo, e flash
    em(b, voz("q", "D3", 0.7, duty=0.25, para="D5", curva=2.0, a=0.05, s=1.0, r=0.05,
              vib=(9, 0.01, 0.0)), 0.0, 0.7)
    em(b, filtra(ruido(int(SR * 0.7), 12000), 1500, 8000) * ev(0.7, a=0.6, s=1.0, r=0.03), 0.0, 0.25)
    sequencia(b, "q", [(0, "A5", 1), (1, "D6", 1), (2, "F6", 1), (3, "A6", 5)], 480, inicio=0.7,
              duty=0.125, a=0.002, tau=0.3, r=0.1, vib=(6, 0.004, 0.1))
    acorde(b, "t", ["D4", "A4"], 0.7, 0.8, 0.7, a=0.01, tau=0.4, r=0.2)
    return eco(b, 0.16, 0.3, 3)


def familiar_concluido():
    b = trilha(0.8)
    sequencia(b, "q", [(0, "F5", 1), (1, "A5", 1), (2, "D6", 4)], 400, duty=0.25,
              a=0.002, tau=0.25, r=0.1, vib=(6, 0.003, 0.1))
    em(b, voz("t", "D4", 0.6, a=0.004, tau=0.25, r=0.15), 0.0, 0.8)
    return eco(b, 0.14, 0.25, 2)


def login():
    b = trilha(4.4)
    bpm = 150                               # colcheia = 200 ms
    c = 0.2
    # pedal grave Re e arpejo de Dm suave por baixo
    em(b, voz("t", "D2", 4.2, a=0.3, s=1.0, r=1.0), 0.0, 0.8)
    for i in range(16):
        em(b, voz("t", ["D4", "A4", "F4", "A4"][i % 4], 0.19, a=0.003, s=0.8, r=0.03), 0.4 + i * c, 0.3)
    # tema e resposta
    sequencia(b, "q", [(2, "D5", 2), (4, "F5", 2), (6, "A5", 2), (8, "B5", 4)], bpm, duty=0.25,
              a=0.004, d=0.06, s=0.75, r=0.08, vib=(5.5, 0.004, 0.15), ganho=0.9)
    sequencia(b, "q", [(12, "A5", 1), (13, "G5", 1), (14, "F5", 2), (16, "E5", 2), (18, "D5", 1)],
              bpm, duty=0.25, a=0.004, d=0.06, s=0.75, r=0.08, vib=(5.5, 0.004, 0.15), ganho=0.9)
    # acorde final com brilho
    tf = 19 * c
    acorde(b, "q", ["D5", "F5", "A5"], tf, 0.5, 0.5, duty=0.5, a=0.01, tau=0.3, r=0.2)
    for i, q in enumerate(["D6", "A6", "F6", "A6", "D7", "A6"]):
        em(b, voz("q", q, 0.3, duty=0.125, a=0.001, tau=0.08, r=0.1), tf - 0.1 + i * 0.12, 0.25)
    return eco(b, 0.2, 0.25, 3, 0.8)


# ---------------------------------------------------------------- elementos
def _estalo(dur, n, grave=2500):
    return filtra(ruido(int(SR * dur), 20000), grave) * ev(dur, a=0.0005, tau=dur / 5, r=dur / 4) * 1.0


def elemento_fogo():
    b = trilha(1.0)
    # estalos de brasa e arpejo subindo em pulso fino
    for t0 in (0.0, 0.05, 0.11, 0.2, 0.26, 0.4):
        em(b, _estalo(0.02, 0), t0, rng.uniform(0.3, 0.6))
    sequencia(b, "q", [(0, "D4", 1), (1, "F4", 1), (2, "A4", 1), (3, "C5", 1), (4, "D5", 1), (5, "F5", 1),
                       (6, "A5", 4)], 560, inicio=0.05, duty=0.125, a=0.001, tau=0.2, r=0.08,
              vib=(8, 0.006, 0.1))
    em(b, voz("rm", 6000, 0.7, a=0.01, tau=0.18, r=0.2), 0.3, 0.12)
    em(b, voz("t", "D2", 0.8, a=0.003, tau=0.3, r=0.2), 0.0, 0.7)
    return b


def elemento_agua():
    b = trilha(1.3)
    # gotas: bipe com deslize ascendente, tema em notas de gota
    for t0, q, g in [(0.0, "D5", 1.0), (0.18, "F5", 0.8), (0.4, "A5", 0.7), (0.65, "B5", 0.6), (0.95, "D5", 0.35)]:
        em(b, voz("t", q, 0.12, para=hz(q) * 1.6, a=0.002, tau=0.04, r=0.04), t0, g)
        em(b, voz("t", hz(q) / 2, 0.1, para=hz(q) * 0.8, a=0.002, tau=0.03, r=0.03), t0, g * 0.3)
    return eco(b, 0.17, 0.45, 4)


def elemento_terra():
    b = trilha(1.2)
    for t0, f0, g in [(0.0, "D2", 1.0), (0.32, "A1", 0.9), (0.7, "D2", 0.8)]:
        em(b, voz("t", hz(f0) * 2.5, 0.35, para=hz(f0), a=0.002, tau=0.12, r=0.1, bits=3), t0, g)
        em(b, filtra(ruido(int(SR * 0.12), 1500), None, 500) * ev(0.12, a=0.001, tau=0.04, r=0.05),
           t0, 0.9 * g)
    em(b, filtra(ruido(int(SR * 0.9), 900), None, 220) * ev(0.9, a=0.1, tau=0.35, r=0.3), 0.5, 0.4)
    em(b, voz("q", "D3", 0.4, duty=0.5, a=0.003, tau=0.15, r=0.1), 0.0, 0.2)
    return b


def elemento_vento():
    b = trilha(1.4)
    n = int(SR * 1.3)
    r = ruido(n, 22000)
    faixas = [filtra(r, 300, 900), filtra(r, 1200, 3000), filtra(r, 400, 1400)]
    t = np.arange(n) / SR
    pesos = [np.clip(1 - t / 0.6, 0, 1) ** 1.2, np.sin(np.pi * np.clip(t / 1.3, 0, 1)) ** 2,
             np.clip((t - 0.6) / 0.7, 0, 1)]
    suave = np.sin(np.pi * t / 1.3) ** 1.6
    som = sum(f * p for f, p in zip(faixas, pesos)) * suave
    em(b, som / np.abs(som).max(), 0.0, 0.8)
    em(b, voz("t", "A5", 0.9, para="E6", a=0.3, s=1.0, r=0.4, vib=(5, 0.01, 0.0)), 0.25, 0.15)
    return b


def elemento_eletricidade():
    b = trilha(0.9)
    for t0, f0 in [(0.0, 4200), (0.17, 3600), (0.3, 2800)]:
        em(b, voz("q", f0, 0.13, duty=0.125, para=140, curva=0.7, a=0.001, tau=0.06, r=0.03), t0)
        em(b, voz("rm", 15000, 0.13, a=0.001, tau=0.04, r=0.02), t0, 0.5)
    # arco eletrico: duas notas alternando rapido
    em(b, voz("q", 1, 0.4, duty=0.25, arp=["D5", "A5", "D6", "F6"], arp_taxa=36, a=0.002,
              tau=0.2, r=0.1), 0.45, 0.7)
    return b


def elemento_mana_pura():
    b = trilha(1.7)
    notas = ["D5", "A5", "F5", "C6", "E6", "A5", "D6", "F6", "A6"]
    for i, q in enumerate(notas):
        em(b, voz("q", q, 0.5, duty=0.125 if i % 2 else 0.25, a=0.001, tau=0.12, r=0.15,
                  vib=(6, 0.005, 0.05)), i * 0.07, 0.35 + 0.04 * i)
    acorde(b, "t", ["D4", "A4", "F5", "A5"], 0.4, 1.1, 0.8, a=0.15, s=1.0, r=0.6, vib=(5, 0.004, 0.2))
    return eco(b, 0.2, 0.35, 3)


# nome -> (funcao, pico dBFS)
SONS = {
    "janela-abrir": (janela_abrir, INTERFACE),
    "janela-fechar": (janela_fechar, INTERFACE),
    "workspace": (workspace, INTERFACE),
    "visao-geral-abrir": (visao_abrir, INTERFACE),
    "visao-geral-fechar": (visao_fechar, INTERFACE),
    "notificacao": (notificacao, INTERFACE),
    "notificacao-urgente": (notificacao_urgente, EVENTO),
    "grimorio-abrir": (grimorio_abrir, EVENTO),
    "grimorio-fechar": (grimorio_fechar, INTERFACE),
    "dialogo-letra": (dialogo_letra, INTERFACE),
    "dialogo-avancar": (dialogo_avancar, INTERFACE),
    "xp": (xp, INTERFACE),
    "oficio-concluido": (oficio_concluido, EVENTO),
    "dia-completo": (dia_completo, EVENTO),
    "nivel": (nivel, EVENTO),
    "titulo": (titulo, EVENTO),
    "penalidade": (penalidade, EVENTO),
    "bateria-baixa": (bateria_baixa, EVENTO),
    "tomada-ligada": (tomada_ligada, INTERFACE),
    "tomada-desligada": (tomada_desligada, INTERFACE),
    "erro": (erro, EVENTO),
    "familiar-invocado": (familiar_invocado, EVENTO),
    "familiar-concluido": (familiar_concluido, EVENTO),
    "login": (login, EVENTO),
    "elemento-fogo": (elemento_fogo, EVENTO),
    "elemento-agua": (elemento_agua, EVENTO),
    "elemento-terra": (elemento_terra, EVENTO),
    "elemento-vento": (elemento_vento, EVENTO),
    "elemento-eletricidade": (elemento_eletricidade, EVENTO),
    "elemento-mana-pura": (elemento_mana_pura, EVENTO),
}


# duracao maxima (s): o eco que passar disso e cortado com fade
TETO = {"oficio-concluido": 1.1, "dia-completo": 2.6, "nivel": 3.2, "login": 4.2, "titulo": 2.0,
        "elemento-agua": 1.6, "elemento-mana-pura": 2.0, "notificacao": 0.55, "familiar-invocado": 1.9,
        "grimorio-abrir": 1.5, "familiar-concluido": 0.9}


def gera(pasta, nomes=None):
    for nome, (fn, pico) in SONS.items():
        if nomes and nome not in nomes:
            continue
        # semente por som: regerar um nao muda os outros
        rng.bit_generator.state = np.random.default_rng(abs(hash_estavel(nome))).bit_generator.state
        fecha = 0.25 if nome in ("login", "nivel", "titulo", "dia-completo") else 0.03
        x = fn()
        if nome in TETO:
            x = x[:int(SR * TETO[nome])]
            fecha = max(fecha, 0.12)
        finaliza(x, pasta / f"{nome}.wav", pico_db=pico, fecha=fecha)


def hash_estavel(s):
    return sum(ord(c) * 31 ** i for i, c in enumerate(s)) % (2 ** 31)


if __name__ == "__main__":
    gera(RAIZ / "sons" / "grimorio", sys.argv[1:] or None)
    print("trilha chiptune do grimorio:", len(SONS), "sons")
