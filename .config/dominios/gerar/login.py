#!/usr/bin/env python3
"""Gera o tema de login (SDDM) e o de boot (Plymouth) a partir de dominios.toml.

Uso: login.py [sddm] [plymouth]        (sem argumento: os dois)

SDDM, em root/sddm/dominios/ (um tema so com os dominios todos):
  dominios.js            tokens dos dominios para o QML (cor, fonte, forma, texto, estilo)
  arte/<d>-fundo.jpg     papel desfocado em JPEG
  arte/<d>-emblema.png   emblema (logo do papel, ou selo de texto: ver "selo")
  arte/grao.png          ruido fino ladrilhado sobre o papel (ver "grao")
  fontes/*.ttf           so as fontes usadas (o greeter roda como usuario sddm e nao le a home)
  Main.qml, componentes/, metadata.desktop e theme.conf sao escritos a mao e nao
  tem cor nem fonte literal: tudo vem de dominios.js.

Plymouth, em root/plymouth/dominios/:
  dominios.script        gerar/login/dominios.script.modelo + tabela de cores dos dominios
  <d>-emblema.png, <d>-rotulo.png, <d>-trilho.png, <d>-barra.png, <d>-campo.png, <d>-ponto.png
  dominios.plymouth e escrito a mao.

A "personalidade" de cada dominio na tela de login fica em ESTILO, logo abaixo. Um
dominio novo em dominios.toml funciona com ESTILO_PADRAO; para ajustar sem mexer
aqui, crie a tabela [<dominio>.login] em dominios.toml com as mesmas chaves.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

RAIZ = Path(__file__).resolve().parent.parent
TOKENS = tomllib.loads((RAIZ / "dominios.toml").read_text())
ORDEM = TOKENS["ordem"]["lista"]                               # ciclo: os emblemas sorteados no boot
TODOS = ORDEM + TOKENS["ordem"].get("extras", [])               # a tela de login conhece todos
PAPEIS = RAIZ / "papeis"
SDDM = RAIZ / "root/sddm/dominios"
PLY = RAIZ / "root/plymouth/dominios"
MODELO_PLY = Path(__file__).resolve().parent / "login/dominios.script.modelo"
PASTAS_FONTES = [Path.home() / ".local/share/fonts/dominios",
                 Path.home() / ".local/share/fonts/despertar-da-mana",
                 Path("/usr/share/fonts/Adwaita")]               # fonte de interface do Neutro

# ----------------------------------------------------------------- estilo
# Nada aqui e cor ou fonte: sao so escolhas de composicao.
#   painel_x         centro horizontal do painel, fracao da largura da tela
#   painel_dy        deslocamento vertical do painel em px (tela de 1080)
#   painel_largura   largura do painel em px (tela de 1080)
#   painel_alfa      opacidade do fundo do painel
#   alinhamento      "centro" | "esquerda"
#   moldura          "colchetes" | "dupla" | "bloco" | "nenhuma"
#   emblema          "topo" | "cabecalho" | "lado" | "nenhum"
#   emblema_tamanho  lado do emblema em px
#   selo             nome de um token de texto curto (ex.: "notificacao") para usar
#                    como emblema desenhado em vez do logo; "" usa o logo do papel
#   titulo_caixa     "alta" | "versalete" | "normal"   (idem rotulos_caixa)
#   titulo_espaco    entreletra do titulo, em fracao do tamanho da fonte
#   rotulos_fonte    "ui" | "destaque"
#   relogio          "esquerda" (alinhado ao painel) | "centro"
#   veu              quanto escurecer o papel (0 a 1)
#   grao             opacidade do grao fino por cima do papel (0 desliga); ele esconde
#                    as faixas que um degrade escuro mostra em tela de 8 bits
ESTILO_PADRAO = {
    "painel_x": 0.5, "painel_dy": 30, "painel_largura": 460, "painel_alfa": 0.86,
    "alinhamento": "centro", "moldura": "nenhuma",
    "emblema": "topo", "emblema_tamanho": 170, "selo": "",
    "titulo_caixa": "alta", "titulo_espaco": 0.2, "titulo_tamanho": 28,
    "frase_tamanho": 21, "frase_caixa": "normal", "frase_espaco": 0.0,
    "rotulos_fonte": "ui", "rotulos_caixa": "alta", "rotulos_espaco": 0.18, "rotulos_tamanho": 14,
    "texto_tamanho": 21, "campo_altura": 48,
    "relogio": "centro", "relogio_tamanho": 92, "data_caixa": "normal", "data_espaco": 0.04,
    "veu": 0.25, "brilho": False, "grao": 1.0,
}
ESTILO = {
    # janela do Sistema: painel a esquerda com colchetes nos cantos, portal livre a direita
    "sistema": {
        "painel_x": 0.27, "painel_largura": 500, "painel_alfa": 0.84, "alinhamento": "esquerda",
        "moldura": "colchetes", "emblema": "cabecalho", "emblema_tamanho": 46, "brilho": True,
        "titulo_espaco": 0.28, "titulo_tamanho": 25, "frase_tamanho": 23,
        "rotulos_espaco": 0.22, "texto_tamanho": 22,
        "relogio": "esquerda", "relogio_tamanho": 86, "data_caixa": "alta", "data_espaco": 0.16,
    },
    # pagina do grimorio: sigilo ao centro, versalete, filete duplo fino
    "grimorio": {
        "painel_largura": 470, "painel_alfa": 0.90, "moldura": "dupla",
        "emblema": "topo", "emblema_tamanho": 150,
        "titulo_caixa": "versalete", "titulo_espaco": 0.12, "titulo_tamanho": 27,
        "frase_tamanho": 21, "rotulos_fonte": "destaque", "rotulos_caixa": "versalete",
        "rotulos_espaco": 0.10, "rotulos_tamanho": 15, "texto_tamanho": 21,
        "relogio": "centro", "relogio_tamanho": 78, "veu": 0.72,
    },
    # Setor 2814: emblema e juramento soltos sobre o espaco, campos em pilula
    "setor2814": {
        "painel_largura": 440, "painel_dy": 10, "moldura": "nenhuma", "brilho": True,
        "emblema": "topo", "emblema_tamanho": 200,
        "titulo_espaco": 0.5, "titulo_tamanho": 30,
        "frase_tamanho": 14, "frase_caixa": "alta", "frase_espaco": 0.22,
        "rotulos_espaco": 0.3, "rotulos_tamanho": 13, "texto_tamanho": 20,
        "relogio": "centro", "relogio_tamanho": 80, "data_caixa": "alta", "data_espaco": 0.3,
        "veu": 0.32,
    },
    # Maldicao: bloco de sangue com o kanji, cantos vivos, tipo pesado
    "maldicao": {
        "painel_x": 0.29, "painel_largura": 690, "painel_alfa": 0.94, "alinhamento": "esquerda",
        "moldura": "bloco", "emblema": "lado", "emblema_tamanho": 190, "selo": "notificacao",
        "titulo_espaco": 0.14, "titulo_tamanho": 34,
        "frase_tamanho": 21, "frase_caixa": "alta", "frase_espaco": 0.04,
        "rotulos_espaco": 0.2, "rotulos_tamanho": 16, "texto_tamanho": 23,
        "relogio": "esquerda", "relogio_tamanho": 120, "data_caixa": "alta", "data_espaco": 0.1,
        "veu": 0.35,
    },
}

# Textos fixos da tela de login (os de cada dominio vem de dominios.toml).
TEXTOS = {
    "senha": "Senha",
    "usuario": "Usuário",
    "sessao": "Sessão",
    "suspender": "Suspender",
    "reiniciar": "Reiniciar",
    "desligar": "Desligar",
    "entrando": "Entrando...",
    "bem_vindo": "Entrou. Abrindo a sessão...",
    "senha_errada": "Senha errada. Tenta de novo.",
    "sem_usuario": "Digita o usuário.",
    "sem_senha": "Digita a senha.",
    "caps": "Caps Lock ligado",
    "ajuda": "Enter entra  ·  Tab navega  ·  Esc limpa",
    "separador": "  ·  ",
    "anterior": "‹",
    "proximo": "›",
    "ponto_senha": "•",
    "formato_hora": "HH:mm",
    "formato_data": "dddd, d 'de' MMMM",
    "localidade": "pt_BR",
}

# Pesos pedidos (escala CSS). O gerador pega o arquivo mais proximo que existir.
PESO_UI, PESO_FORTE, PESO_DESTAQUE = 500, 600, 700
MINUSCULAS = {"da", "de", "do", "das", "dos", "e", "a", "o", "em", "na", "no"}
FC_PESO = {100: 0, 200: 40, 300: 50, 400: 80, 500: 100, 600: 180, 700: 200, 800: 205, 900: 210}


# ------------------------------------------------------------------ cores
def rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def mistura(a, b, t):
    return tuple(round(x * (1 - t) + y * t) for x, y in zip(rgb(a), rgb(b)))


def unidade(c):
    """Cor (hex ou tupla 0-255) como tres numeros de 0 a 1 para o script do Plymouth."""
    if isinstance(c, str):
        c = rgb(c)
    return [f"{v / 255:.4f}" for v in c]


# ----------------------------------------------------------------- fontes
_indice = None


def indice_fontes():
    """Faces dos arquivos em PASTAS_FONTES, lidas com fc-scan."""
    global _indice
    if _indice is None:
        _indice = []
        for pasta in PASTAS_FONTES:
            for arq in sorted(pasta.glob("*.[to]tf")):
                out = subprocess.run(["fc-scan", "--format", "%{family[0]}|%{weight}|%{slant}|%{variable}\n", str(arq)],
                                     capture_output=True, text=True).stdout
                for linha in out.splitlines():
                    familia, peso, inclinacao, variavel = linha.split("|")
                    faixa = [float(v) for v in re.findall(r"[\d.]+", peso)]
                    if not faixa:
                        continue
                    _indice.append({"arquivo": arq, "familia": familia, "italico": inclinacao.strip() not in ("", "0"),
                                    "variavel": variavel.strip() == "True", "min": min(faixa), "max": max(faixa)})
    return _indice


def escolhe_fonte(familia, peso, italico=False):
    """(arquivo, peso CSS que o QML deve pedir, e variavel?) da face mais proxima, ou None."""
    faces = [f for f in indice_fontes() if f["familia"] == familia and f["italico"] == italico]
    if not faces:
        return None
    alvo = FC_PESO[peso]
    for f in faces:
        if f["variavel"] and f["min"] <= alvo <= f["max"]:
            return f["arquivo"], peso, True
    fixas = [f for f in faces if not f["variavel"]] or faces
    melhor = min(fixas, key=lambda f: abs(f["min"] - alvo))
    css = min(FC_PESO, key=lambda k: abs(FC_PESO[k] - melhor["min"]))
    return melhor["arquivo"], css, False


def fonte_cjk():
    """Arquivo e indice de uma fonte japonesa pesada do sistema (a mesma ideia de papeis.py)."""
    for consulta in ("Noto Sans CJK JP:style=Black", ":lang=ja:weight=black"):
        out = subprocess.run(["fc-match", "-f", "%{file}\t%{index}\t%{lang}", consulta], capture_output=True, text=True).stdout
        partes = out.split("\t")
        if len(partes) == 3 and "ja" in partes[2].split("|") and Path(partes[0]).exists():
            return partes[0], int(partes[1])
    return None


def precisa_cjk(texto):
    return any(ord(c) >= 0x2E80 for c in texto)


def fonte_pil(familia, peso, tamanho, texto=""):
    """ImageFont para desenhar texto nos assets do Plymouth."""
    if precisa_cjk(texto):
        cjk = fonte_cjk()
        if cjk:
            return ImageFont.truetype(cjk[0], int(tamanho), index=cjk[1])
    achada = escolhe_fonte(familia, peso)
    if not achada:
        out = subprocess.run(["fc-match", "-f", "%{file}|%{index}", familia], capture_output=True, text=True).stdout
        arq, idx = out.split("|")
        return ImageFont.truetype(arq, int(tamanho), index=int(idx))
    arq, css, variavel = achada
    f = ImageFont.truetype(str(arq), int(tamanho))
    if variavel:
        try:
            eixos = f.get_variation_axes()
            f.set_variation_by_axes([css if e.get("name") in ("Weight", b"Weight") or len(eixos) == 1 else e["default"]
                                     for e in eixos])
        except Exception:
            pass
    return f


def nome_limpo(arq):
    return re.sub(r"[^A-Za-z0-9._-]", "", Path(arq).name)


# ------------------------------------------------------------------ texto
def caixa(texto, modo):
    if modo == "alta":
        return texto.upper()
    if modo == "versalete":
        palavras = texto.lower().split(" ")
        return " ".join(p if (p in MINUSCULAS and i) else p[:1].upper() + p[1:] for i, p in enumerate(palavras))
    return texto


def estilo_de(dominio):
    e = dict(ESTILO_PADRAO)
    e.update(ESTILO.get(dominio, {}))
    e.update(TOKENS[dominio].get("login", {}))
    return e


def textos_de(dominio):
    d, e = TOKENS[dominio], estilo_de(dominio)
    rotulo, bloqueio, lema = d.get("rotulo", d["nome"]), d.get("bloqueio", ""), d.get("lema", "")
    rotulo = d.get("login", {}).get("titulo", rotulo)       # [<dominio>.login] titulo = "..." troca o titulo
    frase = bloqueio if bloqueio and bloqueio != rotulo else lema
    base = lema.rstrip(".").lower()
    rodape = "" if (not lema or lema == frase or (base and frase.lower().startswith(base))) else lema
    return {
        "titulo": caixa(rotulo, e["titulo_caixa"]),
        "frase": caixa(frase, e["frase_caixa"]),
        "rodape": rodape,
        "usuario": caixa(d.get("ficha", {}).get("usuario", TEXTOS["usuario"]), e["rotulos_caixa"]),
        "senha": caixa(TEXTOS["senha"], e["rotulos_caixa"]),
        "sessao": caixa(TEXTOS["sessao"], e["rotulos_caixa"]),
    }


# ------------------------------------------------------------------- arte
def emblema(dominio, lado):
    """Logo do papel reduzido. Sem o arquivo, um disco na cor primaria (nunca falha)."""
    origem = PAPEIS / f"{dominio}-logo.png"
    if origem.exists():
        return Image.open(origem).convert("RGBA").resize((lado, lado), Image.LANCZOS)
    im = Image.new("RGBA", (lado, lado), (0, 0, 0, 0))
    ImageDraw.Draw(im).ellipse((lado * 0.2, lado * 0.2, lado * 0.8, lado * 0.8),
                               outline=rgb(TOKENS[dominio]["cor"]["primaria"]) + (255,), width=max(2, lado // 40))
    return im


def selo(texto, cor_hex, lado):
    """Texto curto (um kanji, por exemplo) centrado num quadrado transparente."""
    cjk = fonte_cjk() if precisa_cjk(texto) else None
    if not cjk:
        return None
    im = Image.new("RGBA", (lado, lado), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    tam = int(lado * 0.86)
    while tam > 8:
        fnt = ImageFont.truetype(cjk[0], tam, index=cjk[1])
        x0, y0, x1, y1 = d.textbbox((0, 0), texto, font=fnt)
        if x1 - x0 <= lado * 0.9 and y1 - y0 <= lado * 0.9:
            break
        tam -= 4
    d.text(((lado - (x1 - x0)) / 2 - x0, (lado - (y1 - y0)) / 2 - y0), texto, font=fnt, fill=rgb(cor_hex) + (255,))
    return im


def fundo_jpeg(dominio, destino):
    origem = PAPEIS / f"{dominio}-desfocado.png"
    if origem.exists():
        im = Image.open(origem).convert("RGB")
    else:
        im = Image.new("RGB", (64, 36), rgb(TOKENS[dominio]["cor"]["fundo"]))
    im.save(destino, "JPEG", quality=90, subsampling=0, optimize=True)


def grao(lado=256, forca=4, semente=2814):
    """Ruido fino e neutro (branco quase transparente) para ladrilhar sobre o papel."""
    import random
    rng = random.Random(semente)
    alfa = bytes(rng.randint(0, forca) for _ in range(lado * lado))
    im = Image.new("RGBA", (lado, lado), (255, 255, 255, 0))
    im.putalpha(Image.frombytes("L", (lado, lado), alfa))
    return im


def retangulo(larg, alt, raio, preenchimento, contorno=None, borda=0):
    """PNG com cantos arredondados e antisserrilhado (desenha em 4x e reduz)."""
    k = 4
    im = Image.new("RGBA", (larg * k, alt * k), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    r = min(raio, alt // 2, larg // 2) * k
    d.rounded_rectangle((0, 0, larg * k - 1, alt * k - 1), radius=r, fill=preenchimento,
                        outline=contorno, width=borda * k if contorno else 0)
    return im.resize((larg, alt), Image.LANCZOS)


def rotulo_png(texto, fnt, cor_hex, espaco):
    """Texto numa linha com entreletra, recortado no tamanho justo."""
    d = ImageDraw.Draw(Image.new("RGBA", (8, 8)))
    larguras = [d.textlength(c, font=fnt) for c in texto]
    larg = int(sum(larguras) + espaco * (len(texto) - 1)) + 8
    sobe, desce = fnt.getmetrics()
    im = Image.new("RGBA", (larg, sobe + desce + 8), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    x = 4.0
    for c, w in zip(texto, larguras):
        d.text((x, 4), c, font=fnt, fill=rgb(cor_hex) + (255,))
        x += w + espaco
    return im


# ------------------------------------------------------------------- SDDM
def gera_sddm():
    # Tudo e montado num rascunho e so entra no lugar no fim: se algo falhar no meio,
    # o tema que ja estava pronto continua inteiro.
    SDDM.mkdir(parents=True, exist_ok=True)
    rascunho = SDDM / ".gerando"
    if rascunho.exists():
        shutil.rmtree(rascunho)
    arte, fontes = rascunho / "arte", rascunho / "fontes"
    arte.mkdir(parents=True)
    fontes.mkdir()
    dados = {}
    for dom in TODOS:
        d, e = TOKENS[dom], estilo_de(dom)
        fundo_jpeg(dom, arte / f"{dom}-fundo.jpg")
        imagem = None
        if e["selo"]:
            imagem = selo(str(d.get(e["selo"], "")), d["cor"]["sobre_primaria"], 384)
        if imagem is None:
            e["selo"] = ""
            imagem = emblema(dom, 384)
        imagem.save(arte / f"{dom}-emblema.png", optimize=True)

        fonte = {"ui": d["fonte"]["ui"], "destaque": d["fonte"]["destaque"], "arquivos": {}, "eixos": {}}
        for papel, familia, peso in (("ui", fonte["ui"], PESO_UI), ("forte", fonte["ui"], PESO_FORTE),
                                     ("destaque", fonte["destaque"], PESO_DESTAQUE)):
            achada = escolhe_fonte(familia, peso)
            if achada:
                arq, css, variavel = achada
                shutil.copyfile(arq, fontes / nome_limpo(arq))
                fonte["arquivos"][papel] = f"fontes/{nome_limpo(arq)}"
                # Fonte variavel: o peso vai pelo eixo wght e o QML pede o peso normal,
                # senao o Qt engrossa o traco por cima (negrito sintetico em dobro).
                fonte[f"peso_{papel}"] = 400 if variavel else css
                fonte["eixos"][papel] = {"wght": css} if variavel else {}
            else:
                print(f"  aviso: fonte '{familia}' nao encontrada em {', '.join(map(str, PASTAS_FONTES))}", file=sys.stderr)
                fonte["arquivos"][papel] = ""
                fonte[f"peso_{papel}"] = peso
                fonte["eixos"][papel] = {}
        # Titulo em kanji cai numa fonte japonesa do sistema: pede o peso maximo para acompanhar o destaque.
        fonte["peso_titulo"] = 900 if precisa_cjk(textos_de(dom)["titulo"]) else fonte["peso_destaque"]
        dados[dom] = {
            "chave": dom, "nome": d["nome"], **textos_de(dom),
            "cor": d["cor"], "forma": {"raio": d["forma"]["raio"], "borda": d["forma"]["borda"]},
            "fonte": fonte, "estilo": e,
            "arte": {"fundo": f"arte/{dom}-fundo.jpg", "emblema": f"arte/{dom}-emblema.png"},
        }
    grao().save(arte / "grao.png", optimize=True)
    padrao = "sistema" if "sistema" in ORDEM else ORDEM[0]
    js = [".pragma library", "// GERADO por gerar/login.py a partir de dominios.toml. Nao edite a mao.", ""]
    for nome, valor in (("padrao", padrao), ("ordem", TODOS), ("grao", "arte/grao.png"), ("textos", TEXTOS), ("dominios", dados)):
        js.append(f"var {nome} = {json.dumps(valor, ensure_ascii=True, indent=2)};")
        js.append("")
    (rascunho / "dominios.js").write_text("\n".join(js))
    for nome in ("arte", "fontes"):
        if (SDDM / nome).exists():
            shutil.rmtree(SDDM / nome)
        (rascunho / nome).rename(SDDM / nome)
    os.replace(rascunho / "dominios.js", SDDM / "dominios.js")
    rascunho.rmdir()
    total = sum(f.stat().st_size for f in SDDM.rglob("*") if f.is_file())
    print(f"sddm: {len(TODOS)} dominios, {len(list((SDDM / 'fontes').iterdir()))} fontes, {total / 1e6:.1f} MB em {SDDM}")


# --------------------------------------------------------------- Plymouth
def gera_plymouth():
    modelo = MODELO_PLY.read_text()
    if "@@DADOS@@" not in modelo:
        sys.exit(f"{MODELO_PLY}: falta o marcador @@DADOS@@")
    PLY.mkdir(parents=True, exist_ok=True)
    destino, rascunho = PLY, PLY / ".gerando"
    if rascunho.exists():
        shutil.rmtree(rascunho)
    rascunho.mkdir()
    linhas = [f"dominios.total = {len(ORDEM)};"]
    for i, dom in enumerate(ORDEM):
        d, c, forma = TOKENS[dom], TOKENS[dom]["cor"], TOKENS[dom]["forma"]
        e = estilo_de(dom)
        raio, borda = int(forma["raio"]), int(forma["borda"])
        emblema(dom, 340).save(rascunho / f"{dom}-emblema.png", optimize=True)
        titulo = caixa(d.get("rotulo", d["nome"]), "alta")
        fnt = fonte_pil(d["fonte"]["destaque"], PESO_DESTAQUE, 30, titulo)
        rotulo_png(titulo, fnt, c["texto"], 30 * min(e["titulo_espaco"], 0.4)).save(rascunho / f"{dom}-rotulo.png", optimize=True)
        alt = max(3, borda * 2)
        retangulo(300, alt, raio, rgb(c["contorno"]) + (255,)).save(rascunho / f"{dom}-trilho.png", optimize=True)
        retangulo(300, alt, raio, rgb(c["primaria"]) + (255,)).save(rascunho / f"{dom}-barra.png", optimize=True)
        retangulo(340, 46, raio, rgb(c["superficie2"]) + (255,), rgb(c["primaria"]) + (255,), borda).save(
            rascunho / f"{dom}-campo.png", optimize=True)
        retangulo(12, 12, raio, rgb(c["texto"]) + (255,)).save(rascunho / f"{dom}-ponto.png", optimize=True)
        linhas.append(f'dominios[{i}].chave = "{dom}";')
        for nome, valor in (("topo", c["fundo"]), ("base", mistura(c["fundo"], c["superficie"], 0.85)),
                            ("texto", c["texto"]), ("suave", c["texto_suave"])):
            r, g, b = unidade(valor)
            linhas.append(f"dominios[{i}].{nome}.r = {r}; dominios[{i}].{nome}.g = {g}; dominios[{i}].{nome}.b = {b};")
    cabecalho = "# GERADO por gerar/login.py (modelo: gerar/login/dominios.script.modelo). Nao edite a mao.\n"
    (rascunho / "dominios.script").write_text(cabecalho + modelo.replace("@@DADOS@@", "\n".join(linhas)))
    for velho in destino.glob("*.png"):
        velho.unlink()
    for novo in sorted(rascunho.iterdir()):
        os.replace(novo, destino / novo.name)
    rascunho.rmdir()
    total = sum(f.stat().st_size for f in PLY.iterdir() if f.is_file())
    print(f"plymouth: {len(ORDEM)} dominios, {total / 1e3:.0f} kB em {PLY}")


if __name__ == "__main__":
    alvos = sys.argv[1:] or ["sddm", "plymouth"]
    for alvo in alvos:
        if alvo == "sddm":
            gera_sddm()
        elif alvo == "plymouth":
            gera_plymouth()
        else:
            sys.exit(f"alvo desconhecido: {alvo} (use sddm e/ou plymouth)")
