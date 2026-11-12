"""Estado da nova aba do Chrome (estado.json e cena.png), compartilhado pelo nucleo
e por bin/nova-aba-estado para os dois caminhos nao divergirem.
Ambiente de teste: NOVA_ABA_PASTA (destino), DOMINIOS_ESTADO (pasta de estado)."""
import json
import os
import shutil
from datetime import datetime

AQUI = os.path.dirname(os.path.realpath(__file__))
RAIZ = os.path.dirname(os.path.dirname(AQUI))
CENAS = os.path.join(RAIZ, "hud/papel/cenas")
ELEMENTOS = ("fogo", "agua", "terra", "vento", "eletricidade", "mana-pura")


def pasta():
    return os.environ.get("NOVA_ABA_PASTA") or os.path.join(RAIZ, "chrome-nova-aba")


def pasta_estado():
    return os.environ.get("DOMINIOS_ESTADO") or os.path.expanduser("~/.local/state/dominios")


def le(caminho):
    try:
        with open(caminho, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def dominio_atual():
    try:
        with open(os.path.join(pasta_estado(), "atual"), encoding="utf-8") as f:
            return f.read().strip()
    except OSError:
        return ""


def monta(antigo, el, jog, of, pg, elemento=None):
    """Dicionario do estado.json. Campo sem dado novo herda do arquivo anterior."""
    elemento = elemento or el.get("elemento") or antigo.get("elemento") or "mana-pura"
    if elemento not in ELEMENTOS:
        elemento = "mana-pura"
    motivo = el.get("motivo") if el.get("elemento") == elemento else None

    def pega(novo, chave, padrao=None):
        if novo is not None:
            return novo
        if chave == "motivo" and antigo.get("elemento") != elemento:
            return padrao
        return antigo.get(chave, padrao)

    return {
        "elemento": elemento,
        "motivo": pega(motivo, "motivo", ""),
        "nivel": pega(jog.get("nivel"), "nivel"),
        "xp": pega(jog.get("xp"), "xp"),
        "xp_proximo": pega(jog.get("xp_proximo"), "xp_proximo"),
        "titulo": pega(jog.get("titulo"), "titulo", ""),
        "oficios_feitos": pega(of.get("feitos"), "oficios_feitos"),
        "oficios_total": pega(of.get("total"), "oficios_total"),
        "frase": pega(pg.get("texto"), "frase", ""),
        "autor": pega(pg.get("autor"), "autor", ""),
        "atualizado": datetime.now().astimezone().isoformat(timespec="seconds"),
    }


def grava_atomico(destino, escreve):
    tmp = f"{destino}.tmp{os.getpid()}"
    try:
        escreve(tmp)
        os.replace(tmp, destino)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def grava(estado, copiar_cena=True):
    """Escreve estado.json (e cena.png se pedido) na pasta da nova aba."""
    dest = pasta()
    cena = os.path.join(CENAS, estado["elemento"] + ".png")
    if copiar_cena and os.path.isfile(cena):
        grava_atomico(os.path.join(dest, "cena.png"), lambda t: shutil.copyfile(cena, t))

    def escreve(t):
        with open(t, "w", encoding="utf-8") as f:
            json.dump(estado, f, ensure_ascii=False, indent=1)
    grava_atomico(os.path.join(dest, "estado.json"), escreve)


def atualiza_do_nucleo(dados, ultimo_elemento):
    """Caminho do nucleo: monta dos canais em memoria. Devolve (estado, mudou_conteudo)
    ou None se nao deve gravar (pasta ausente ou dominio diferente de grimorio)."""
    dest = pasta()
    if not os.path.isdir(dest) or dominio_atual() != "grimorio":
        return None
    antigo = le(os.path.join(dest, "estado.json"))
    est = monta(antigo, dados.get("elemento") or {}, dados.get("jogador") or {},
                dados.get("oficios") or {}, dados.get("pagina") or {})
    cena_falta = not os.path.isfile(os.path.join(dest, "cena.png"))
    est_cmp = {k: v for k, v in est.items() if k != "atualizado"}
    ant_cmp = {k: v for k, v in antigo.items() if k != "atualizado"}
    return est, est_cmp != ant_cmp, (est["elemento"] != ultimo_elemento or cena_falta)
