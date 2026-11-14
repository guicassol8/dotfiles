"""Titulos dos seis herois ([grimorio.herois] do dominios.toml), a fonte unica.

titulo(elemento) -> "O Espadachim da Brasa", ou "" se nao houver. Relê o arquivo so
quando o mtime muda (o nucleo vive dias), para renomear sem reiniciar nada.
"""
import os
import tomllib

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
ARQUIVO = os.environ.get("DOMINIOS_TOML") or os.path.join(RAIZ, "dominios.toml")
_cache = {"mtime": None, "herois": {}}


def todos():
    try:
        m = os.stat(ARQUIVO).st_mtime
        if m != _cache["mtime"]:
            with open(ARQUIVO, "rb") as f:
                _cache.update(mtime=m, herois=tomllib.load(f).get("grimorio", {}).get("herois", {}))
    except (OSError, ValueError):
        pass
    return _cache["herois"]


def titulo(elemento):
    return str(todos().get(elemento) or "")
