#!/usr/bin/env python3
"""Renderiza modelos/ em _build/<dominio>/ com os valores de dominios.toml.

Sintaxe dos modelos:
  {{cor.primaria}}              valor do token (ponto navega nas tabelas)
  {{cor.primaria|sem#}}         sem o # inicial
  {{cor.primaria|rgb}}          "79, 195, 255"
  {{cor.primaria|rgba:0.5}}     "rgba(79, 195, 255, 0.5)"
  {{cor.primaria|alfa:0.5}}     "#4FC3FF80"
  {{cor.primaria|glsl}}         "0.3098, 0.7647, 1.0000"
  {{cor.primaria|ansi}}         "38;2;79;195;255" (codigo SGR truecolor)
  {{cor.primaria|claro:0.2}}    mistura com branco (0 a 1)
  {{cor.primaria|escuro:0.2}}   mistura com preto
  {{cor.fundo|mistura:cor.primaria:0.3}}  mistura com outro token
  {{forma.raio|soma:4}}         aritmetica simples em numeros (soma, vezes)
  {{>arquivo}}                  inclui modelos/_por_dominio/<dominio>/arquivo (renderizado)
  {{dominio}} {{casa}} {{raiz}} chave do dominio, $HOME e ~/.config/dominios
  {{modo.saudacao}}             chaves de [<dominio>.modo], ja com os padroes

Arquivos de modelos/ (fora de _por_dominio/) viram _build/<dominio>/<mesmo nome>.
Um arquivo em modelos/_por_dominio/<dominio>/ com o mesmo nome de um modelo
geral substitui o geral para aquele dominio.
"""
import json
import re
import shutil
import sys
import tomllib
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
MODELOS = RAIZ / "modelos"
BUILD = RAIZ / "_build"
TOKENS = tomllib.loads((RAIZ / "dominios.toml").read_text())
ORDEM = TOKENS["ordem"]["lista"] + TOKENS["ordem"].get("extras", [])   # ciclo + fora do ciclo
MODO_PADRAO = {"apresentacao": False, "saudacao": True}
BINARIOS = {".png", ".jpg", ".wav", ".ogg", ".ttf", ".ico", ".webp"}


def _rgb(h):
    h = h.lstrip("#")
    return [int(h[i:i + 2], 16) for i in (0, 2, 4)]


def _hex(rgb):
    return "#" + "".join(f"{max(0, min(255, round(v))):02X}" for v in rgb)


def _mix(a, b, t):
    return _hex([x * (1 - t) + y * t for x, y in zip(_rgb(a), _rgb(b))])


def _busca(ctx, caminho):
    no = ctx
    for parte in caminho.split("."):
        if not isinstance(no, dict) or parte not in no:
            raise KeyError(caminho)
        no = no[parte]
    return no


def _filtra(valor, filtro, ctx):
    nome, *args = filtro.split(":")
    if nome == "sem#":
        return str(valor).lstrip("#")
    if nome == "rgb":
        return ", ".join(str(v) for v in _rgb(valor))
    if nome == "rgba":
        return f"rgba({', '.join(str(v) for v in _rgb(valor))}, {args[0]})"
    if nome == "alfa":
        return f"{valor}{round(float(args[0]) * 255):02X}"
    if nome == "ansi":
        return "38;2;" + ";".join(str(v) for v in _rgb(valor))
    if nome == "glsl":
        return ", ".join(f"{v / 255:.4f}" for v in _rgb(valor))
    if nome == "claro":
        return _mix(valor, "#FFFFFF", float(args[0]))
    if nome == "escuro":
        return _mix(valor, "#000000", float(args[0]))
    if nome == "mistura":
        return _mix(valor, _busca(ctx, args[0]), float(args[1]))
    if nome == "soma":
        r = float(valor) + float(args[0])
        return int(r) if r == int(r) else r
    if nome == "vezes":
        r = float(valor) * float(args[0])
        return int(r) if r == int(r) else round(r, 3)
    if nome == "minusculo":
        return str(valor).lower()
    if nome == "json":
        return json.dumps(valor, ensure_ascii=False)
    raise ValueError(f"filtro desconhecido: {nome}")


PADRAO = re.compile(r"\{\{\s*(>?)\s*([^}|\s]+)\s*((?:\|[^}|]+)*)\s*\}\}")


def renderiza(texto, ctx, dominio, origem="?", nivel=0):
    def troca(m):
        inclui, chave, filtros = m.group(1), m.group(2), m.group(3)
        if inclui:
            arq = MODELOS / "_por_dominio" / dominio / chave
            if not arq.exists():
                raise FileNotFoundError(f"{origem}: parcial ausente {arq}")
            if nivel > 4:
                raise RecursionError(f"{origem}: inclusao em ciclo ({chave})")
            return renderiza(arq.read_text(), ctx, dominio, str(arq), nivel + 1).rstrip("\n")
        try:
            valor = _busca(ctx, chave)
        except KeyError:
            raise KeyError(f"{origem}: token inexistente '{chave}' no dominio {dominio}") from None
        for f in filter(None, filtros.split("|")):
            valor = _filtra(valor, f.strip(), ctx)
        return str(valor)
    return PADRAO.sub(troca, texto)


def contexto(dominio):
    ctx = dict(TOKENS[dominio])
    ctx.update(dominio=dominio, casa=str(Path.home()), raiz=str(RAIZ),
               indice=ORDEM.index(dominio) + 1, total=len(ORDEM),
               modo={**MODO_PADRAO, **TOKENS[dominio].get("modo", {})})
    return ctx


def constroi(dominio):
    ctx = contexto(dominio)
    destino = BUILD / dominio
    destino.mkdir(parents=True, exist_ok=True)
    proprio = MODELOS / "_por_dominio" / dominio
    feitos = 0
    for arq in sorted(MODELOS.rglob("*")):
        if arq.is_dir() or "_por_dominio" in arq.parts:
            continue
        rel = arq.relative_to(MODELOS)
        fonte = proprio / rel if (proprio / rel).exists() else arq
        saida = destino / rel
        saida.parent.mkdir(parents=True, exist_ok=True)
        if fonte.suffix.lower() in BINARIOS:
            shutil.copyfile(fonte, saida)
        else:
            saida.write_text(renderiza(fonte.read_text(), ctx, dominio, str(fonte)))
            shutil.copymode(fonte, saida)
        feitos += 1
    # tokens prontos para quem nao le TOML
    plano = {"dominio": dominio, **{k: v for k, v in TOKENS[dominio].items()}}
    (destino / "tokens.json").write_text(json.dumps(plano, ensure_ascii=False, indent=2) + "\n")
    linhas = [f"  --{grupo}-{k.replace('_', '-')}: {v};" for grupo in ("cor", "ansi") for k, v in TOKENS[dominio][grupo].items()]
    linhas += [f"  --fonte-{k.replace('_', '-')}: {json.dumps(v) if isinstance(v, str) else v};" for k, v in TOKENS[dominio]["fonte"].items()]
    linhas += [f"  --forma-{k.replace('_', '-')}: {v if isinstance(v, str) else str(v) + ('px' if k in ('raio', 'borda', 'vaos') else '')};"
               for k, v in TOKENS[dominio]["forma"].items()]
    (destino / "tokens.css").write_text(":root {\n" + "\n".join(linhas) + "\n}\n")
    # arte e sons gerados
    for nome, alvo in ((f"papeis/{dominio}.png", "papel.png"), (f"papeis/{dominio}-logo.png", "logo.png"),
                       (f"papeis/{dominio}-desfocado.png", "papel-desfocado.png")):
        origem = RAIZ / nome
        if origem.exists():
            link = destino / alvo
            link.unlink(missing_ok=True)
            link.symlink_to(origem)
    sons = RAIZ / "sons" / dominio
    if sons.is_dir():
        link = destino / "sons"
        if link.is_symlink() or link.exists():
            link.unlink()
        link.symlink_to(sons)
    return feitos


if __name__ == "__main__":
    alvo = sys.argv[1:] or ORDEM
    for d in alvo:
        if d not in ORDEM:
            sys.exit(f"dominio desconhecido: {d} (existem: {', '.join(ORDEM)})")
        print(f"{d}: {constroi(d)} arquivos em {BUILD / d}")
        if d == "grimorio":   # paletas do terminal por elemento
            import terminal_elemento
            terminal_elemento.gera()
            import sessao_elemento     # niri e Noctalia por elemento
            sessao_elemento.gera()
