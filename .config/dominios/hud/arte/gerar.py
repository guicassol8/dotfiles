#!/usr/bin/env python3
"""Desenha as pecas de pixel art do HUD do grimorio em hud/arte/*.png.

  gerar.py            gera tudo
  gerar.py --folha X  alem disso monta uma folha de conferencia ampliada em X.png

Tudo sai na grade 1x (1 pixel do PNG = 1 pixel de arte). Quem amplia 3x por vizinho
mais proximo e o QML (Tema.px). As excecoes sao sombra.png e brilho-*.png, que sao
luz lisa por cima do pixel e ja saem em pixels de tela.

As cores vem de [grimorio] no dominios.toml: nenhuma cor de base e inventada aqui,
so as rampas (claro e escuro de cada tom). Depois de mexer, rode de novo e confira
a folha. So biblioteca padrao e PIL.
"""
import sys
import tomllib
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent.parent
TOK = tomllib.loads((RAIZ / "dominios.toml").read_text())["grimorio"]
COR = TOK["cor"]
ELEMENTOS = TOK["elementos"]            # fogo, agua, terra, vento, eletricidade, mana-pura
FONTES = Path.home() / ".local/share/fonts/dominios"


# ------------------------------------------------------------------ cor
def rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def mix(a, b, t):
    a, b = (rgb(a) if isinstance(a, str) else a), (rgb(b) if isinstance(b, str) else b)
    return tuple(round(x + (y - x) * t) for x, y in zip(a[:3], b[:3]))


def al(c, a=255):
    c = rgb(c) if isinstance(c, str) else c
    return (*c[:3], a)


TINTA = mix(COR["fundo"], "#000000", 0.55)          # contorno escuro das pecas
VAZIO = (0, 0, 0, 0)


class Rampa:
    """Cinco tons de um metal ou de uma pedra: fundo, escuro, medio, claro, luz."""

    def __init__(self, fundo, escuro, medio, claro, luz):
        self.fundo, self.escuro, self.medio, self.claro, self.luz = (al(c) for c in (fundo, escuro, medio, claro, luz))


def rampa_de(cor, quente=0.0):
    """Rampa de pixel art a partir de uma cor: a sombra puxa para o violeta do
    grimorio e a luz para o branco quente (deslocamento de matiz, nao so de brilho)."""
    base = rgb(cor)
    sombra = mix(mix(base, "#241640", 0.50), "#000000", 0.10)
    fundo = mix(base, "#120C22", 0.78)
    claro = mix(base, "#FFF6E0", 0.32 + quente)
    luz = mix(base, "#FFFFFF", 0.72)
    return Rampa(fundo, sombra, base, claro, luz)


PRATA = Rampa(mix(COR["contorno"], COR["fundo"], 0.35), mix(COR["contorno"], COR["primaria"], 0.22),
              mix(COR["contorno"], COR["primaria"], 0.62), COR["primaria"], mix(COR["secundaria"], COR["texto"], 0.6))
OURO = Rampa("#3A2A14", mix(COR["terciaria"], "#3A2412", 0.58), mix(COR["terciaria"], "#6B4A22", 0.22),
             mix(COR["terciaria"], COR["aviso"], 0.30), mix(COR["aviso"], "#FFFFFF", 0.62))
PERIGO = rampa_de(COR["erro"])
PERIGO.fundo = al(mix(COR["erro"], "#1A0A0C", 0.80))
RAMPAS = {"normal": PRATA, "ouro": OURO, "perigo": PERIGO}
PEDRA = {nome: rampa_de(cor, 0.08 if nome in ("fogo", "terra", "eletricidade") else 0.0) for nome, cor in ELEMENTOS.items()}
PEDRA["apagada"] = Rampa(mix(COR["fundo"], "#000000", 0.3), mix(COR["contorno"], COR["fundo"], 0.4), COR["contorno"],
                         mix(COR["contorno"], COR["texto_suave"], 0.35), mix(COR["contorno"], COR["texto_suave"], 0.7))

# papel do pergaminho
PAPEL = {"luz": "#F3E7CB", "claro": "#E8D9B6", "medio": "#DAC79E", "escuro": "#BFA677", "borda": "#8E7446",
         "tinta": "#3A2C20", "suave": "#7C6748"}


# ------------------------------------------------------------------ desenho
def tela(w, h, cor=VAZIO):
    return Image.new("RGBA", (w, h), cor)


def de_texto(linhas, paleta):
    """Peca desenhada em texto: cada letra e uma cor da paleta, '.' e vazio."""
    linhas = [l for l in linhas.strip("\n").split("\n")]
    w = max(len(l) for l in linhas)
    im = tela(w, len(linhas))
    for y, l in enumerate(linhas):
        for x, ch in enumerate(l):
            if ch not in ". ":
                im.putpixel((x, y), paleta[ch])
    return im


def salva(im, nome):
    destino = AQUI / nome
    destino.parent.mkdir(parents=True, exist_ok=True)
    im.save(destino, optimize=True)
    FEITOS.append((nome, im))


FEITOS = []


def losango(im, cx, cy, raio, cor_de):
    """Pinta um losango (|dx|+|dy| <= raio); cor_de(dx, dy, d) devolve a cor ou None."""
    for dy in range(-raio, raio + 1):
        for dx in range(-raio, raio + 1):
            d = abs(dx) + abs(dy)
            if d <= raio:
                c = cor_de(dx, dy, d)
                if c is not None:
                    im.putpixel((cx + dx, cy + dy), c)


# ------------------------------------------------------------------ gemas
def gema(r, raio=2):
    """Pedra lapidada em losango. raio 2 = 5x5 (cantos das janelas), raio 4 = 9x9."""
    n = raio * 2 + 1
    im = tela(n, n)

    def cor(dx, dy, d):
        s = dx + dy                                    # negativo = lado da luz (cima, esquerda)
        if raio == 2:
            if (dx, dy) == (-1, -1):
                return r.luz
            if d == 2:
                return r.claro if s < 0 else (r.medio if s == 0 else r.escuro)
            if s > 0:
                return r.escuro if d == 1 else r.fundo
            return r.claro if s < 0 else r.medio
        if d == raio:                                  # aro: claro em cima, fundo embaixo
            return r.claro if s < 0 else (r.escuro if s == 0 else r.fundo)
        if (dx, dy) in ((-1, -2), (-2, -1)):
            return r.luz
        if (dx, dy) == (-1, -1):
            return (255, 255, 255, 255)
        if s < -1:
            return r.claro
        if s > 1:
            return r.escuro
        return r.medio

    losango(im, raio, raio, raio, cor)
    return im


# ------------------------------------------------------------------ molduras (9 fatias)
CANTO = 12          # fatia de canto, em pixels de arte
MEIO = 8
RECUO = 2           # a linha da moldura fica a 2 px da borda do PNG (o florao do canto passa para fora)


def moldura(r):
    t = 2 * CANTO + MEIO
    im = tela(t, t)
    a, b = RECUO, t - 1 - RECUO
    for i in range(a, b + 1):                           # contorno escuro
        for xy in ((i, a), (i, b), (a, i), (b, i)):
            im.putpixel(xy, al(TINTA))
    for i in range(a + 1, b):                           # filete claro: luz vem de cima e da esquerda
        im.putpixel((i, a + 1), r.luz)
        im.putpixel((a + 1, i), r.claro)
        im.putpixel((i, b - 1), r.medio)
        im.putpixel((b - 1, i), r.medio)
    im.putpixel((a + 1, a + 1), r.luz)
    for i in range(a + 2, b - 1):                       # filete escuro
        for xy in ((i, a + 2), (a + 2, i), (i, b - 2), (b - 2, i)):
            im.putpixel(xy, r.escuro)
    for i in range(a + 3, b - 2):                       # sombra da moldura caindo no vidro
        im.putpixel((i, a + 3), (0, 0, 0, 120))
        im.putpixel((a + 3, i), (0, 0, 0, 90))
        im.putpixel((i, b - 3), (0, 0, 0, 40))
        im.putpixel((b - 3, i), (0, 0, 0, 40))
    for cx, cy, sx, sy in ((4, 4, 1, 1), (t - 5, 4, -1, 1), (4, t - 5, 1, -1), (t - 5, t - 5, -1, -1)):
        # cantoneira interna: um L curto solto no vidro
        for k in range(4):
            im.putpixel((cx + sx * (4 + k), cy + sy * 4), r.escuro)
            im.putpixel((cx + sx * 4, cy + sy * (4 + k)), r.escuro)
        im.putpixel((cx + sx * 4, cy + sy * 4), r.medio)
        # florao: losango de metal com o engaste da gema no meio

        def cor(dx, dy, d):
            s = dx + dy
            if d == 4:
                return al(TINTA)
            if d == 3:
                return r.luz if s < -1 else (r.claro if s <= 0 else r.medio)
            return al(TINTA) if d == 2 else r.fundo
        losango(im, cx, cy, 4, cor)
    return im


def placa(r, fundo, fundo_luz, fundo_sombra):
    """Placa de titulo, 3 fatias na horizontal (5 + 6 + 5) por 11 de altura."""
    im = tela(16, 11)
    for y in range(11):
        for x in range(16):
            ex = min(x, 15 - x)                         # distancia da ponta mais proxima
            ey = min(y, 10 - y)
            chanfro = ex + ey
            if chanfro < 2:
                continue
            borda = chanfro == 2 or ex == 0 or ey == 0
            if borda:
                c = al(TINTA)
            elif chanfro == 3 or ex == 1 or ey == 1:
                c = r.luz if y <= 1 else (r.claro if x <= 2 and y < 8 else r.medio)
                if y >= 9 or (x >= 13 and y > 2):
                    c = r.escuro
            else:
                c = al(fundo_luz) if y == 2 else (al(fundo_sombra) if y == 8 else al(fundo))
            im.putpixel((x, y), c)
    return im


def moldura_pergaminho():
    """Pergaminho: folha clara com as bordas roidas e um bastao enrolado em cima e embaixo."""
    t = 2 * CANTO + MEIO
    im = tela(t, t)
    p = {k: al(v) for k, v in PAPEL.items()}
    roido = [0, 1, 0, 0, 1, 0, 1, 1, 0, 0, 1, 0]        # recorte irregular das laterais
    for y in range(5, t - 5):
        ke = roido[y % len(roido)]
        kd = roido[(y * 5 + 3) % len(roido)]
        x0, x1 = 3 + ke, t - 4 - kd
        for x in range(x0, x1 + 1):
            c = p["claro"]
            if x - x0 < 2:
                c = p["medio"] if x - x0 == 1 else p["escuro"]
            if x1 - x < 2:
                c = p["medio"] if x1 - x == 1 else p["escuro"]
            im.putpixel((x, y), c)
        im.putpixel((x0 - 1, y), p["borda"])
        im.putpixel((x1 + 1, y), p["borda"])
    for y0, de_cima in ((1, True), (t - 6, False)):      # bastoes
        for i, tom in enumerate(("borda", "luz", "claro", "medio", "borda")):
            for x in range(2, t - 2):
                im.putpixel((x, y0 + i), p[tom] if tom != "borda" else al(mix(PAPEL["borda"], "#000000", 0.25)))
        sombra = y0 + 5 if de_cima else y0 - 1           # sombra do rolo sobre a folha
        for x in range(4, t - 4):
            if im.getpixel((x, sombra))[3]:
                im.putpixel((x, sombra), p["escuro"] if de_cima else p["medio"])
        for x in (0, 1, t - 2, t - 1):                   # ponteiras de ouro
            for i in range(5):
                tom = (OURO.luz, OURO.claro, OURO.medio, OURO.escuro, OURO.fundo)[i]
                im.putpixel((x, y0 + i), tom)
        for x in (1, t - 2):
            im.putpixel((x, y0 - 1), al(TINTA)) if y0 > 0 else None
    return im


# ------------------------------------------------------------------ luz lisa (pixels de tela)
def sombra_macia(tam=96, borda=30, forca=150):
    """Sombra projetada, 9 fatias (30 px de borda), para dar profundidade atras da janela."""
    im = Image.new("L", (tam, tam), 0)
    ImageDraw.Draw(im).rectangle((borda - 6, borda - 6, tam - borda + 5, tam - borda + 5), fill=forca)
    im = im.filter(ImageFilter.GaussianBlur(9))
    saida = tela(tam, tam, (0, 0, 0, 0))
    saida.putalpha(im)
    return saida


def brilho_macio(cor, tam=64):
    """Halo radial liso na cor do elemento, para acender gemas e destaques."""
    c = rgb(cor)
    im = tela(tam, tam)
    m = (tam - 1) / 2
    for y in range(tam):
        for x in range(tam):
            d = ((x - m) ** 2 + (y - m) ** 2) ** 0.5 / m
            a = max(0.0, 1.0 - d) ** 2.2
            im.putpixel((x, y), (*mix(c, "#FFFFFF", 0.25 * a), round(255 * a * 0.85)))
    return im


# ------------------------------------------------------------------ barra, setas, divisor
def barra_moldura():
    """Calha da barra segmentada: 3 fatias (3 + 2 + 3) por 7."""
    im = de_texto("""
.oooooo.
occcccco
ottttttx
ottttttx
ottttttx
oxxxxxxx
.xxxxxx.
""", {"o": al(TINTA), "c": al(mix(COR["fundo"], "#000000", 0.45)), "t": al(mix(COR["fundo"], "#000000", 0.25)),
      "x": PRATA.escuro})
    return im


def barra_luz():
    """Mascara de um gomo (3 de cor + 1 de vao) por 5: luz em cima, sombra embaixo.
    Vai ladrilhada por cima de um retangulo liso na cor da barra."""
    im = tela(4, 5)
    for x in range(3):
        im.putpixel((x, 0), (255, 255, 255, 110))
        im.putpixel((x, 1), (255, 255, 255, 34))
        im.putpixel((x, 3), (0, 0, 0, 50))
        im.putpixel((x, 4), (0, 0, 0, 105))
    im.putpixel((0, 0), (255, 255, 255, 150))
    for y in range(5):
        im.putpixel((3, y), al(mix(COR["fundo"], "#000000", 0.25)))
    return im


def setas():
    p = {"o": al(TINTA), "c": al(COR["texto"]), "s": al(COR["texto_suave"])}
    baixo = de_texto("""
ooooooo
occcsso
.occso.
..oso..
...o...
""", p)
    direita = de_texto("""
oo...
oco..
occo.
occso
ocso.
oso..
oo...
""", p)
    return baixo, direita


def florao_divisor():
    im = tela(7, 5)

    def cor(dx, dy, d):
        if d == 2:
            return PRATA.claro if dx + dy < 0 else PRATA.medio
        return PRATA.luz if (dx, dy) == (0, 0) else PRATA.escuro
    losango(im, 3, 2, 2, cor)
    im.putpixel((0, 2), PRATA.escuro)
    im.putpixel((6, 2), PRATA.escuro)
    return im


# ------------------------------------------------------------------ orbe (medidor)
def orbe(n=33):
    """Aro de metal de 33x33 com o vidro vazado (o QML pinta o liquido linha a linha,
    com a mesma conta de raio) e, separado, o reflexo que vai por cima do liquido."""
    import math
    m = (n - 1) / 2
    dentro, aro_r, borda_r = m - 2.7, m - 0.7, m + 0.3
    aro, luz = tela(n, n), tela(n, n)
    for y in range(n):
        for x in range(n):
            dx, dy = x - m, y - m
            d = (dx * dx + dy * dy) ** 0.5
            lado = dx + dy                               # negativo = lado da luz
            if d <= dentro:
                ang = math.degrees(math.atan2(dy, dx))   # -180..180, -135 = cima e esquerda
                if dentro - 4.2 <= d <= dentro - 2.2 and -170 <= ang <= -110:
                    luz.putpixel((x, y), (255, 255, 255, 150 if -150 <= ang <= -125 else 80))
                elif lado >= dentro * 0.95:
                    luz.putpixel((x, y), (0, 0, 0, 80))
                elif dentro - 3.5 <= d <= dentro - 2.4 and 35 <= ang <= 60:
                    luz.putpixel((x, y), (255, 255, 255, 46))
            elif d <= aro_r:
                externo = d > aro_r - 1.0
                if lado < -m * 0.35:
                    c = PRATA.luz if externo else PRATA.claro
                elif lado < m * 0.45:
                    c = PRATA.claro if externo else PRATA.medio
                else:
                    c = PRATA.medio if externo else PRATA.escuro
                aro.putpixel((x, y), c)
            elif d <= borda_r:
                aro.putpixel((x, y), al(TINTA))
    return aro, luz


# ------------------------------------------------------------------ selo de rank
def fonte_pixel(arquivo, em):
    return ImageFont.truetype(str(FONTES / arquivo), em)


def texto_pixel(txt, arquivo, em, cor):
    """Texto de fonte de pixel desenhado 1x, sem suavizar (fica na grade)."""
    f = fonte_pixel(arquivo, em)
    x0, y0, x1, y1 = f.getbbox(txt)
    im = Image.new("1", (x1 - x0, y1 - y0), 0)
    d = ImageDraw.Draw(im)
    d.fontmode = "1"
    d.text((-x0, -y0), txt, font=f, fill=1)
    saida = tela(*im.size)
    saida.paste(al(cor), (0, 0), im)
    return saida


RANKS = {"E": "apagada", "D": "terra", "C": "vento", "B": "agua", "A": "mana-pura", "S": "eletricidade"}


def selo(letra, r):
    """Escudo de 15x17 com a letra do rank."""
    im = tela(15, 17)
    for y in range(17):
        meia = 7 if y < 9 else max(0, 7 - (y - 8))       # reto em cima, ponta embaixo
        for x in range(15):
            dx = abs(x - 7)
            if dx > meia:
                continue
            borda = dx == meia or y == 0 or (y >= 9 and dx == meia)
            if borda:
                c = al(TINTA)
            elif dx == meia - 1 or y == 1:
                c = r.luz if (x < 7 and y < 9) or y == 1 else r.escuro
            else:
                c = r.medio if x - 7 + (y - 8) * 0.5 < 0 else r.escuro
            im.putpixel((x, y), c)
    letra_im = texto_pixel(letra, "Silkscreen-Bold.ttf", 8, r.luz)
    sombra_im = texto_pixel(letra, "Silkscreen-Bold.ttf", 8, r.fundo)
    x = (15 - letra_im.width) // 2
    im.alpha_composite(sombra_im, (x + 1, 5))
    im.alpha_composite(letra_im, (x, 4))
    return im


# ------------------------------------------------------------------ simbolos dos elementos (11x11)
# Marca pequena e chapada de cada elemento, na grade. O emblema rico (34x34) e o
# `elemento-<nome>` do acervo em hud/sprites/.
ICONES_ELEMENTO = {
    "fogo": """
.....c.....
.....cc....
....ccc....
...sccc..c.
...schc.cc.
..scchhccc.
.sscchhhcc.
.scchhyhhc.
.scchyyyhc.
..sschyhc..
...sssss...
""",
    "agua": """
.....h.....
.....c.....
.....c.....
....hcs....
....hcs....
...hhccs...
..hhccccs..
.hhccccccs.
.hcyccccss.
..hccccss..
...sssss...
""",
    "terra": """
...........
...hhhh....
..hccccs...
.hhcccccs..
.hcccccsss.
hhccccccsss
hcccscccsss
hccccsccsss
.cccccsssss
..sssssss..
...........
""",
    "vento": """
...........
...hhhh....
..h....c...
.......c...
hhhhccc....
...........
hhhhhcccc..
.........c.
......s..c.
.......ss..
...........
""",
    "eletricidade": """
......hhc..
.....hhc...
....hhc....
...hhc.....
..hhhcccc..
.....hcs...
....hcs....
...hcs.....
..hcs......
..cs.......
..s........
""",
    "mana-pura": """
.....h.....
.....c.....
....hcs....
....hcs....
..hhhycss..
hccyyyyycss
..sscycss..
....hcs....
....hcs....
.....c.....
.....s.....
""",
}


def icone_elemento(nome, r):
    pal = {"h": r.luz if nome != "fogo" else r.claro, "c": r.medio, "s": r.escuro,
           "y": al(mix(ELEMENTOS["eletricidade"], "#FFFFFF", 0.45)) if nome == "fogo" else (255, 255, 255, 255)}
    return de_texto(ICONES_ELEMENTO[nome], pal)


# ------------------------------------------------------------------ moldura de retrato
def retrato_moldura():
    """Moldurinha do retrato, 9 fatias com 3 de borda."""
    im = tela(10, 10)
    for i in range(10):
        for xy in ((i, 0), (i, 9), (0, i), (9, i)):
            im.putpixel(xy, al(TINTA))
    for i in range(1, 9):
        im.putpixel((i, 1), PRATA.luz)
        im.putpixel((1, i), PRATA.claro)
        im.putpixel((i, 8), PRATA.medio)
        im.putpixel((8, i), PRATA.medio)
    for i in range(2, 8):
        im.putpixel((i, 2), (0, 0, 0, 110))
        im.putpixel((2, i), (0, 0, 0, 80))
    return im


# ------------------------------------------------------------------ clima em pixel
def clima_pixel(nome):
    """Os icones de clima do acervo sao lisos (100x100) e nao casam com o resto.
    Aqui eles viram pixel art de 34x34: reducao por vizinho, alfa duro, contorno
    escuro e sombreado em tres tons com as cores do grimorio."""
    origem = AQUI.parent / "sprites" / "fontes-livres" / "weather-icons" / f"{nome}.png"
    if not origem.exists():
        return None
    p = Image.open(origem).convert("RGBA").resize((30, 30), Image.NEAREST)
    im = tela(34, 34)
    im.alpha_composite(p, (2, 2))
    px = im.load()
    tipo = {}
    for y in range(34):
        for x in range(34):
            r, g, b, a = px[x, y]
            if a <= 110:
                px[x, y] = VAZIO
            else:
                tipo[x, y] = "gota" if b > r + 40 else ("raio" if r > b + 60 else "nuvem")
    nuvem = (al(mix(COR["texto"], COR["secundaria"], 0.3)), al(COR["texto_suave"]), al(mix(COR["texto_suave"], COR["contorno"], 0.55)))
    for (x, y), k in tipo.items():
        acima = sum(1 for d in (1, 2) if tipo.get((x, y - d)) == k)
        abaixo = sum(1 for d in (1, 2) if tipo.get((x, y + d)) == k)
        if k == "nuvem":
            px[x, y] = nuvem[0] if acima < 2 else (nuvem[2] if abaixo < 2 else nuvem[1])
        elif k == "gota":
            px[x, y] = PEDRA["agua"].claro if acima == 0 else PEDRA["agua"].medio
        else:
            px[x, y] = PEDRA["eletricidade"].luz if tipo.get((x - 1, y)) != k else PEDRA["eletricidade"].medio
    saida = im.copy()
    ps = saida.load()
    for y in range(34):
        for x in range(34):
            if (x, y) not in tipo and any((x + dx, y + dy) in tipo for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                ps[x, y] = al(TINTA)
    return saida


# ------------------------------------------------------------------ tudo
def gera():
    for nome, r in RAMPAS.items():
        salva(moldura(r), f"moldura-{nome}.png")
    f = COR["superficie2"]
    salva(placa(PRATA, f, mix(f, COR["primaria"], 0.18), mix(f, COR["fundo"], 0.35)), "placa-normal.png")
    salva(placa(OURO, mix(f, "#3A2A14", 0.45), mix(f, COR["terciaria"], 0.30), mix(f, "#1A1208", 0.55)), "placa-ouro.png")
    salva(placa(PERIGO, mix(f, "#3A1614", 0.55), mix(f, COR["erro"], 0.30), mix(f, "#1A0A0C", 0.6)), "placa-perigo.png")
    salva(moldura_pergaminho(), "moldura-pergaminho.png")
    salva(placa(OURO, PAPEL["medio"], PAPEL["luz"], PAPEL["escuro"]), "placa-pergaminho.png")
    for nome, r in PEDRA.items():
        salva(gema(r, 2), f"gema-{nome}.png")
        salva(gema(r, 4), f"gemao-{nome}.png")
    for nome, cor in ELEMENTOS.items():
        salva(icone_elemento(nome, PEDRA[nome]), f"simbolo-{nome}.png")
        salva(brilho_macio(cor), f"brilho-{nome}.png")
    salva(sombra_macia(), "sombra.png")
    salva(barra_moldura(), "barra-moldura.png")
    salva(barra_luz(), "barra-luz.png")
    baixo, direita = setas()
    salva(baixo, "seta-baixo.png")
    salva(direita, "seta-direita.png")
    salva(florao_divisor(), "florao.png")
    aro, luz = orbe()
    salva(aro, "orbe-aro.png")
    salva(luz, "orbe-luz.png")
    for letra, pedra in RANKS.items():
        salva(selo(letra, PEDRA[pedra] if pedra != "eletricidade" else OURO), f"selo-{letra.lower()}.png")
    salva(retrato_moldura(), "retrato-moldura.png")
    for nome, origem in (("nuvem", "cloudyWeather"), ("chuva", "rainyWeather"), ("tempestade", "stormyWeather")):
        im = clima_pixel(origem)
        if im is not None:
            salva(im, f"clima-{nome}.png")


def folha(destino, zoom=6):
    """Folha de conferencia: todas as pecas ampliadas sobre o fundo do grimorio."""
    lisas = ("sombra.png",) + tuple(f"brilho-{n}.png" for n in ELEMENTOS)
    x = y = 8
    alt_linha = 0
    larg = 1500
    itens = []
    for nome, im in FEITOS:
        z = 1 if nome in lisas else zoom
        g = im.resize((im.width * z, im.height * z), Image.NEAREST)
        if x + g.width + 8 > larg:
            x, y, alt_linha = 8, y + alt_linha + 22, 0
        itens.append((nome, g, x, y))
        x += max(g.width, 6 * len(nome)) + 14
        alt_linha = max(alt_linha, g.height)
    saida = Image.new("RGBA", (larg, y + alt_linha + 26), al(COR["fundo"]))
    d = ImageDraw.Draw(saida)
    for nome, g, gx, gy in itens:
        saida.alpha_composite(g, (gx, gy))
        d.text((gx, gy + g.height + 2), nome.replace(".png", ""), fill=al(COR["texto_suave"]))
    saida.convert("RGB").save(destino)


if __name__ == "__main__":
    gera()
    print(f"{len(FEITOS)} pecas em {AQUI}")
    if "--folha" in sys.argv:
        folha(sys.argv[sys.argv.index("--folha") + 1])
