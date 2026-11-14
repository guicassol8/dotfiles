#!/usr/bin/env python3
"""Paletas do terminal por elemento (so o dominio grimorio).

Para cada um dos seis elementos grava em _build/grimorio/terminal/<elemento>/:
  kitty.conf       cores do kitty (incluido por ~/.local/state/dominios/kitty-elemento.conf)
  starship.toml    prompt com a cor, o glifo e a inicial do elemento
  fastfetch.jsonc  ficha com a moldura, o capitulo e o titulo do heroi do elemento
  contraste.txt    razoes WCAG de cada cor sobre o fundo tingido

Uso: terminal_elemento.py [--folha saida.png]
Chamado tambem por gerar/construir.py ao construir o grimorio.
"""
import colorsys
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import construir as c   # noqa: E402

DOMINIO = "grimorio"
ELEMENTOS = ["fogo", "agua", "terra", "vento", "eletricidade", "mana-pura"]
# Glifos Nerd Font (Material Design) e inicial de cada elemento
GLIFOS = {"fogo": "󰈸", "agua": "󰖌", "terra": "󰌪", "vento": "󰖝", "eletricidade": "󱐋", "mana-pura": "✦"}
NOMES = {"fogo": "Fogo", "agua": "Água", "terra": "Terra", "vento": "Vento", "eletricidade": "Eletricidade", "mana-pura": "Mana Pura"}
TINGE_FUNDO = 0.06     # fracao do elemento misturada no fundo
ALVO_CONTRASTE = 7.0   # texto normal e cores de destaque


def lum(h):
    def f(v):
        v /= 255
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = (f(x) for x in c._rgb(h))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contraste(a, b):
    la, lb = sorted((lum(a), lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def gira(h, graus, dl=0.0):
    r, g, b = (v / 255 for v in c._rgb(h))
    hh, ll, ss = colorsys.rgb_to_hls(r, g, b)
    hh = (hh + graus / 360) % 1
    ll = min(1, max(0, ll + dl))
    return c._hex([v * 255 for v in colorsys.hls_to_rgb(hh, ll, ss)])


def legivel(cor, fundo, alvo=ALVO_CONTRASTE):
    """Clareia a cor ate o contraste com o fundo chegar no alvo."""
    t = 0.0
    while contraste(cor, fundo) < alvo and t < 1:
        t += 0.02
        cor = c._mix(cor, "#FFFFFF", 0.02 / (1 - (t - 0.02)) if t < 1 else 1)
    return cor


def paleta(el):
    t = c.TOKENS[DOMINIO]
    cor, ansi = t["cor"], t["ansi"]
    e = t["elementos"][el]
    fundo = c._mix(cor["fundo"], e, TINGE_FUNDO)
    superf = c._mix(cor["superficie"], e, TINGE_FUNDO)
    claro = c._mix(e, "#FFFFFF", 0.28)
    p = {
        "fundo": fundo, "superficie": superf, "elemento": e, "claro": claro,
        "moldura": c._mix(fundo, e, 0.5),
        "contorno": c._mix(cor["contorno"], e, 0.12),
        "selecao_fundo": c._mix(fundo, e, 0.82),
    }
    r, g, b = (v / 255 for v in c._rgb(e))
    matiz = colorsys.rgb_to_hls(r, g, b)[0] * 360
    # amarelos e dourados giram para verde-limao quando se soma matiz: ficam no proprio tom, so mais claros
    magenta = legivel(c._mix(e, "#FFFFFF", 0.15) if 30 <= matiz <= 65 else gira(e, 14), fundo)
    azul = legivel(gira(e, -14), fundo)
    a = dict(ansi)
    a["preto"] = c._mix(ansi["preto"], e, TINGE_FUNDO)
    a["preto_claro"] = c._mix(ansi["preto_claro"], e, 0.18)
    a["azul"], a["magenta"] = azul, magenta
    a["azul_claro"] = legivel(c._mix(azul, "#FFFFFF", 0.28), fundo)
    a["magenta_claro"] = legivel(c._mix(magenta, "#FFFFFF", 0.28), fundo)
    p["ansi"] = a
    return p


def kitty_conf(el, p, t):
    cor = t["cor"]
    L = [f"# Elemento {NOMES[el]}. Gerado por gerar/terminal_elemento.py (nao edite).",
         f"background            {p['fundo']}",
         f"selection_background  {p['elemento']}",
         f"selection_foreground  {cor['sobre_primaria']}",
         f"cursor                {p['elemento']}",
         f"cursor_text_color     {p['fundo']}",
         f"cursor_trail_color    {p['claro']}",
         f"url_color             {p['claro']}",
         f"active_border_color   {p['elemento']}",
         f"inactive_border_color {p['contorno']}",
         f"active_tab_background   {p['elemento']}",
         f"active_tab_foreground   {cor['sobre_primaria']}",
         f"inactive_tab_background {c._mix(p['superficie'], p['elemento'], 0.05)}",
         f"inactive_tab_foreground {cor['texto_suave']}",
         f"tab_bar_background      {p['fundo']}",
         f"tab_bar_margin_color    {p['fundo']}",
         f"scrollbar_handle_color  {p['elemento']}",
         f"scrollbar_track_color   {p['contorno']}",
         f"mark1_background {p['elemento']}", f"mark1_foreground {cor['sobre_primaria']}",
         f"mark2_background {p['claro']}", f"mark2_foreground {cor['sobre_primaria']}"]
    nomes = ["preto", "vermelho", "verde", "amarelo", "azul", "magenta", "ciano", "branco"]
    for i, n in enumerate(nomes):
        L.append(f"color{i:<2} {p['ansi'][n]}")
    for i, n in enumerate(nomes):
        L.append(f"color{i + 8:<2} {p['ansi'][n + '_claro']}")
    return "\n".join(L) + "\n"


def modulo_heroi(el, ctx):
    """Linha da ficha com o titulo do heroi, na cor do elemento (vazio sem titulo em [grimorio.herois])."""
    titulo = ctx["herois"].get(el)
    if not titulo:
        return ""
    chave = f"{{#{c._filtra(ctx['cor']['moldura'], 'ansi', ctx)}}}┃ {{#{c._filtra(ctx['elemento']['cor'], 'ansi', ctx)}}}{ctx['ficha']['heroi']}"
    cor = c._filtra(ctx["elemento"]["cor"], "ansi", ctx)
    return json.dumps({"type": "custom", "key": chave, "format": f"{{#{cor}}}{{#1}}{titulo}{{#}}"}, ensure_ascii=False) + ","


def contexto_elemento(el, p):
    ctx = c.contexto(DOMINIO)
    ctx["cor"] = {**ctx["cor"], "primaria": p["elemento"], "secundaria": p["claro"], "moldura": p["moldura"],
                  "fundo": p["fundo"]}
    ctx["elemento"] = {"cor": p["elemento"], "rgb": c._filtra(p["elemento"], "rgb", ctx), "nome": NOMES[el],
                       "glifo": GLIFOS[el], "inicial": NOMES[el][0]}
    ctx["heroi"] = {"modulo": modulo_heroi(el, ctx)}
    return ctx


def relatorio(el, p, t):
    fundo = p["fundo"]
    itens = [("texto", t["cor"]["texto"]), ("texto_suave", t["cor"]["texto_suave"]), ("elemento", p["elemento"]),
             ("claro", p["claro"]), ("vermelho", p["ansi"]["vermelho"]), ("verde", p["ansi"]["verde"]),
             ("amarelo", p["ansi"]["amarelo"]), ("azul", p["ansi"]["azul"]), ("magenta", p["ansi"]["magenta"]),
             ("azul_claro", p["ansi"]["azul_claro"]), ("magenta_claro", p["ansi"]["magenta_claro"]),
             ("ciano", p["ansi"]["ciano"]), ("branco", p["ansi"]["branco"]),
             ("sobre_selecao", None)]
    L = [f"{el}: fundo {fundo}"]
    for n, h in itens:
        if h is None:
            L.append(f"  selecao ({t['cor']['sobre_primaria']} sobre {p['elemento']}): {contraste(t['cor']['sobre_primaria'], p['elemento']):.1f}:1")
        else:
            L.append(f"  {n:14} {h} {contraste(h, fundo):5.1f}:1")
    return "\n".join(L) + "\n"


def gera():
    t = c.TOKENS[DOMINIO]
    base = c.BUILD / DOMINIO / "terminal"
    modelos = {n: (c.MODELOS / "_por_dominio" / DOMINIO / n) for n in ("starship.toml", "fastfetch.jsonc")}
    saida = {}
    for el in ELEMENTOS:
        p = paleta(el)
        d = base / el
        d.mkdir(parents=True, exist_ok=True)
        c.grava(d / "kitty.conf", kitty_conf(el, p, t))
        ctx = contexto_elemento(el, p)
        for nome, arq in modelos.items():
            c.grava(d / nome, c.renderiza(arq.read_text(), ctx, DOMINIO, str(arq)))
        c.grava(d / "contraste.txt", relatorio(el, p, t))
        saida[el] = p
    return saida


def folha(paletas, destino):
    from PIL import Image, ImageDraw, ImageFont
    t = c.TOKENS[DOMINIO]
    f = ImageFont.truetype("/usr/share/fonts/TTF/DejaVuSansMono.ttf", 15)
    fb = ImageFont.truetype("/usr/share/fonts/TTF/DejaVuSansMono-Bold.ttf", 17)
    W, H = 560, 330
    img = Image.new("RGB", (W * 3, H * 2), "#000000")
    d = ImageDraw.Draw(img)
    for i, el in enumerate(ELEMENTOS):
        p = paletas[el]
        x0, y0 = (i % 3) * W, (i // 3) * H
        d.rectangle([x0, y0, x0 + W - 1, y0 + H - 1], fill=p["fundo"])
        d.text((x0 + 16, y0 + 12), f"{NOMES[el].upper()}  fundo {p['fundo']}", font=fb, fill=p["elemento"])
        d.text((x0 + 16, y0 + 40), "$ git status  # texto normal", font=f, fill=t["cor"]["texto"])
        d.text((x0 + 16, y0 + 62), "texto suave: comentario, dica", font=f, fill=t["cor"]["texto_suave"])
        a = p["ansi"]
        nomes = ["preto", "vermelho", "verde", "amarelo", "azul", "magenta", "ciano", "branco"]
        for k, n in enumerate(nomes):
            for linha, suf in enumerate(("", "_claro")):
                h = a[n + suf]
                x, y = x0 + 16 + k * 66, y0 + 92 + linha * 62
                d.rectangle([x, y, x + 58, y + 30], fill=h, outline=p["contorno"])
                cc = contraste(h, p["fundo"])
                d.text((x, y + 34), f"{cc:.1f}", font=f, fill=t["cor"]["texto_suave"])
        y = y0 + 226
        # acentos: cursor, selecao, aba ativa, url, borda
        d.rectangle([x0 + 16, y, x0 + 24, y + 22], fill=p["elemento"])
        d.text((x0 + 32, y + 2), "cursor", font=f, fill=t["cor"]["texto"])
        d.rectangle([x0 + 110, y, x0 + 214, y + 22], fill=p["elemento"])
        d.text((x0 + 116, y + 2), "selecao", font=f, fill=t["cor"]["sobre_primaria"])
        d.rectangle([x0 + 224, y, x0 + 300, y + 22], fill=p["elemento"])
        d.text((x0 + 232, y + 2), "✦ aba", font=f, fill=t["cor"]["sobre_primaria"])
        d.text((x0 + 312, y + 2), "https://url", font=f, fill=p["claro"])
        d.line([x0 + 312, y + 21, x0 + 412, y + 21], fill=p["claro"])
        d.rectangle([x0 + 428, y, x0 + 540, y + 22], outline=p["elemento"], width=2)
        d.text((x0 + 436, y + 2), "borda", font=f, fill=t["cor"]["texto"])
        d.text((x0 + 16, y0 + 262), f"╭─ {GLIFOS[el]} {NOMES[el][0]}  ~/projeto  em  main", font=f, fill=p["elemento"])
        d.text((x0 + 16, y0 + 284), "╰─ ✦", font=f, fill=p["elemento"])
        d.text((x0 + 16, y0 + 306), "numeros: contraste dos 16 sobre o fundo", font=f, fill=p["contorno"] if False else t["cor"]["texto_suave"])
    img.save(destino)


if __name__ == "__main__":
    pal = gera()
    if "--folha" in sys.argv:
        folha(pal, sys.argv[sys.argv.index("--folha") + 1])
    print(f"terminal por elemento: {len(pal)} paletas em {c.BUILD / DOMINIO / 'terminal'}")
