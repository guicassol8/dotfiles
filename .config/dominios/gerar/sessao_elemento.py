#!/usr/bin/env python3
"""Sessao do grimorio por elemento: niri (moldura e animacoes) e paleta do Noctalia.

Para cada um dos seis elementos grava em _build/grimorio/sessao/<elemento>/:
  niri.kdl             cores da moldura e shaders de abrir/fechar janela
                       (ganchos/elemento.d/65-niri copia para ~/.local/state/dominios/niri-elemento.kdl)
  noctalia-paleta.json paleta do Noctalia com o elemento como destaque
                       (ganchos/elemento.d/66-noctalia aponta a paleta dominio-grimorio para ela)

Mesmo contexto do terminal por elemento (gerar/terminal_elemento.py): primaria = elemento,
secundaria = elemento claro, fundo tingido de leve. Chamado por gerar/construir.py ao
construir o grimorio.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import construir as c            # noqa: E402
import terminal_elemento as te   # noqa: E402

DOMINIO = "grimorio"
MODELOS = {
    "niri.kdl": c.MODELOS / "_por_dominio" / DOMINIO / "niri-elemento.kdl",
    "noctalia-paleta.json": c.MODELOS / "noctalia-paleta.json",
}


def gera():
    base = c.BUILD / DOMINIO / "sessao"
    for el in te.ELEMENTOS:
        ctx = te.contexto_elemento(el, te.paleta(el))
        d = base / el
        d.mkdir(parents=True, exist_ok=True)
        for nome, arq in MODELOS.items():
            (d / nome).write_text(c.renderiza(arq.read_text(), ctx, DOMINIO, str(arq)))
    return len(te.ELEMENTOS)


if __name__ == "__main__":
    print(f"sessao por elemento: {gera()} elementos em {c.BUILD / DOMINIO / 'sessao'}")
