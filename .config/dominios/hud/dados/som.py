"""Logica de sons do Dominios: toca sons/<nome>.wav do dominio ativo e traduz eventos do niri.

Usado pelo `bin/som-eventos` (daemon e comando `tocar`) e embutido no hud/dados/nucleo.py.
Respeita `dominio som on|off` (estado/preferencias.json). Debounce: um som do mesmo tipo a
cada 120 ms e no maximo 3 tocando ao mesmo tempo.
Ambiente: SOM_EVENTOS_VOLUME, SOM_EVENTOS_TOCADOR=<arquivo> (registro "tempo nome volume",
sem tocar audio).
"""
import json
import os
import signal
import sys
import threading
import time
from pathlib import Path

CASA = Path.home()
RAIZ = CASA / ".config/dominios"
ATUAL = RAIZ / "atual"
PREFS = CASA / ".local/state/dominios/preferencias.json"
CONFIG = RAIZ / "som-eventos.json"
VOLUME_PADRAO = 0.35
DEBOUNCE = 0.12
MAX_SIMULTANEOS = 3

_tocando = []          # processos pw-play vivos
_ultimo = {}           # nome -> instante do ultimo som
_cache = {"pref": (None, True), "cfg": (None, {})}
_trava = threading.RLock()   # o nucleo toca de varias threads


def _json_com_cache(chave, caminho, padrao):
    """Le um JSON pequeno so quando o mtime muda."""
    try:
        m = caminho.stat().st_mtime_ns
    except OSError:
        return padrao
    if _cache[chave][0] != m:
        try:
            dado = json.loads(caminho.read_text())
        except (OSError, ValueError):
            dado = padrao
        _cache[chave] = (m, dado)
    return _cache[chave][1]


def spawn(prog, argv, saida=None):
    """posix_spawn: bem mais leve que importar subprocess. Entrada e erro vao para /dev/null."""
    acoes = [(os.POSIX_SPAWN_OPEN, 0, os.devnull, os.O_RDONLY, 0),
             (os.POSIX_SPAWN_OPEN, 2, os.devnull, os.O_WRONLY, 0)]
    if saida is None:
        acoes.append((os.POSIX_SPAWN_OPEN, 1, os.devnull, os.O_WRONLY, 0))
    else:
        acoes.append((os.POSIX_SPAWN_DUP2, saida, 1))
    return os.posix_spawnp(prog, argv, os.environ, file_actions=acoes, setsid=True)


def terminou(pid):
    try:
        return os.waitpid(pid, os.WNOHANG)[0] != 0
    except ChildProcessError:
        return True


def som_ligado():
    p = _json_com_cache("pref", PREFS, {"som": True})
    return bool(p.get("som", True)) if isinstance(p, dict) else True


def volume_de(nome, explicito=None):
    if explicito is not None:
        return explicito
    env = os.environ.get("SOM_EVENTOS_VOLUME")
    if env:
        return float(env)
    cfg = _json_com_cache("cfg", CONFIG, {})
    return float(cfg.get("volumes", {}).get(nome, cfg.get("volume", VOLUME_PADRAO)))


def toca(nome, volume=None, forcar=False, debounce=True):
    """Dispara o som sem bloquear. Devolve True se disparou."""
    with _trava:
        return _toca(nome, volume, forcar, debounce)


def _toca(nome, volume, forcar, debounce):
    if "/" in nome or nome.startswith("."):
        return False
    if not forcar and not som_ligado():
        return False
    arq = ATUAL / "sons" / f"{nome}.wav"
    if not arq.is_file():
        return False
    agora = time.monotonic()
    if debounce:
        if agora - _ultimo.get(nome, -1e9) < DEBOUNCE:
            return False
        _tocando[:] = [p for p in _tocando if not terminou(p)]
        if len(_tocando) >= MAX_SIMULTANEOS:
            return False
    _ultimo[nome] = agora
    v = volume_de(nome, volume)
    registro = os.environ.get("SOM_EVENTOS_TOCADOR")
    if registro:
        with open(registro, "a") as f:
            f.write(f"{time.time():.3f} {nome} {v:.2f}\n")
        return True
    try:
        pid = spawn("pw-play", ["pw-play", "--volume", f"{v:.2f}", str(arq)])
    except OSError:
        return False
    _tocando.append(pid)
    return True


class Eventos:
    """Traduz eventos do niri em sons. O despejo inicial so alimenta o estado."""

    def __init__(self):
        self.janelas = set()
        self.ws_saida = {}        # id do workspace -> saida
        self.ws_ativo = {}        # saida -> id do workspace ativo
        self.visao = None         # None ate o estado inicial chegar

    def trata(self, linha):
        try:
            ev = json.loads(linha)
        except ValueError:
            return
        if not isinstance(ev, dict) or len(ev) != 1:
            return
        tipo, d = next(iter(ev.items()))
        if tipo == "WindowsChanged":
            self.janelas = {j["id"] for j in d.get("windows", [])}
        elif tipo == "WindowOpenedOrChanged":
            i = d.get("window", {}).get("id")
            if i is not None and i not in self.janelas:
                self.janelas.add(i)
                toca("janela-abrir")
        elif tipo == "WindowClosed":
            if d.get("id") in self.janelas:
                self.janelas.discard(d["id"])
                toca("janela-fechar")
        elif tipo == "WorkspacesChanged":
            self.ws_saida = {w["id"]: w.get("output") for w in d.get("workspaces", [])}
            self.ws_ativo = {w.get("output"): w["id"] for w in d.get("workspaces", []) if w.get("is_active")}
        elif tipo == "WorkspaceActivated":
            i = d.get("id")
            saida = self.ws_saida.get(i)
            if self.ws_ativo.get(saida) != i:
                self.ws_ativo[saida] = i
                toca("workspace")
        elif tipo == "OverviewOpenedOrClosed":
            aberta = bool(d.get("is_open"))
            antes, self.visao = self.visao, aberta
            if antes is not None and antes != aberta:
                toca("visao-geral-abrir" if aberta else "visao-geral-fechar")


def le_fluxo(fonte, ev):
    for linha in fonte:
        ev.trata(linha)


def daemon(usa_stdin):
    ev = Eventos()
    if usa_stdin:
        le_fluxo(sys.stdin, ev)
        return
    filho = []
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))
    try:
        _laco(ev, filho)
    finally:                  # nao deixa o `niri msg` orfao
        mata(filho)


def mata(filho):
    if filho:
        try:
            os.kill(filho[0], signal.SIGTERM)
        except OSError:
            pass
        terminou(filho[0])


def _laco(ev, filho, parar=None):
    """Mantem um `niri msg event-stream` vivo e alimenta `ev`. Com `parar` (threading.Event),
    sai quando ele for acionado (o chamador mata o filho)."""
    while not (parar and parar.is_set()):
        leitura, escrita = os.pipe()
        try:
            filho[:] = [spawn("niri", ["niri", "msg", "--json", "event-stream"], escrita)]
        except OSError:
            os.close(leitura)
            os.close(escrita)
            if parar:
                parar.wait(5)
            else:
                time.sleep(5)
            continue
        os.close(escrita)
        ev.visao = None
        with os.fdopen(leitura, "r", buffering=1) as f:
            le_fluxo(f, ev)
        try:
            os.waitpid(filho[0], 0)
        except ChildProcessError:
            pass
        if parar:
            parar.wait(3)
        else:
            time.sleep(3)         # niri saiu ou ainda nao esta de pe: tenta de novo


def embutido(parar, filho):
    """Para o nucleo: corpo de uma thread que toca os eventos do niri ate `parar`."""
    try:
        _laco(Eventos(), filho, parar)
    except Exception:
        pass
