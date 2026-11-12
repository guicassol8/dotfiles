#!/usr/bin/env python3
"""jogador: o motor do Conjurador (nível, XP, atributos, títulos e eventos).

  jogador                       ficha no terminal
  jogador atualizar             recalcula e grava ~/.local/state/dominios/jogador.json
  jogador seguir [--intervalo 60]  laço: imprime uma linha JSON a cada mudança
  jogador conceder <xp> <motivo>   XP manual (vira evento)
  jogador gastar <atributo> [n]    gasta pontos livres num atributo
  jogador eventos               eventos recentes
  jogador json                  imprime o JSON da ficha (sem gravar)
  jogador nome <texto>          nome mostrado na ficha (sem texto: mostra o atual; "auto" volta ao git config)
  jogador classe <texto>        classe mostrada na ficha (padrão Invocador; "auto" volta ao padrão)
  jogador titulo                lista os títulos (conquistados e por conquistar) com a condição de cada um
  jogador titulo <nome|número>  escolhe qual título conquistado aparece na ficha
  jogador titulo auto           volta ao mais prestigioso conquistado
  (preferências em jogador-prefs.json na pasta de estado; nível e XP não se escolhem, só vêm de atividade e de `conceder`)

FONTES DE XP (tudo idempotente, o estado fica em jogador-estado.json)
  commit do dono (autor = git config --global user.email)   20 XP, 1x por hash
  missão diária concluída (lê missoes.json do `missao`)     20 XP, 1x por dia+id
  dia com todas as missões                                  60 XP + 5 por dia de sequência (até 10)
  dia perdido (missão pendente após a virada)               -40 XP (não rebaixa o nível) e zera a sequência
  familiar invocado (sessão nova do Claude Code, via `agentes`) 10 XP
  familiar de volta (sessão que durou 2 min ou mais)        15 XP
  histórico na 1ª execução: todos os commits + 10 XP por sessão em ~/.claude/projects
  Curva: xp_proximo(n) = round(50 * n^1.4). Com ~5 mil commits o dono cai perto do nível 35.

ATRIBUTOS (base 10, mais o que o contador real der, mais pontos gastos)
  força        + dias distintos com commit / 5           (volume de trabalho)
  agilidade    + 4 * recorde de agentes em paralelo + familiares invocados / 25
  inteligência + commits totais / 60                     (código escrito)
  vitalidade   + 2 * recorde de sequência + missões de saúde / 4
               (acordar, academia, alongamento, fruta, mindfulness, celular)
  percepção    + commits de revisão/refatoração / 15 + missões de estudo / 3
               (leitura, diário, mindfulness)

RANK: E 1-9, D 10-19, C 20-29, B 30-44, A 45-69, S 70+.
PONTOS LIVRES: 3 por nível ganho desde a abertura do grimório, menos os gastos.

Variáveis de teste: DOMINIOS_ESTADO (pasta de estado, a mesma do `missao`),
DOMINIOS_MISSOES (outro missoes.toml), DOMINIOS_AGORA (data e hora ISO fingidas),
JOGADOR_RAIZES (pastas separadas por ':' onde procurar repositórios),
JOGADOR_SEM_AGENTES=1 (ignora as sessões vivas), JOGADOR_SEM_HISTORICO=1.
"""
import json
import os
import re
import sys
import time
from datetime import datetime, timedelta

CASA = os.path.expanduser("~")
AQUI = os.path.dirname(os.path.realpath(__file__))
RAIZ = os.path.dirname(os.path.dirname(AQUI))          # ~/.config/dominios

XP_COMMIT, XP_MISSAO, XP_DIA, XP_DIA_SEQ, XP_PENALIDADE = 20, 20, 60, 5, 40
XP_SOMBRA, XP_SOMBRA_VOLTA, SOMBRA_MIN_S, XP_SESSAO_HIST = 10, 15, 120, 10
GUARDA_EVENTOS, MOSTRA_EVENTOS = 300, 30
REPOS_CADA_S = 1800
PROFUNDIDADE = 5
PULA = {"node_modules", "__pycache__", "venv", "env", "target", "dist", "build", "vendor",
        "site-packages", "Downloads", "snap", "go", "proc"}
SAUDE = ("acordar", "academia", "alongamento", "fruta", "mindfulness", "celular")
ESTUDO = ("leitura", "diario", "mindfulness")
REVISAO = ("review", "revis", "refactor", "refator")
ATRIBUTOS = ("forca", "agilidade", "inteligencia", "vitalidade", "percepcao")
DIAS = ("seg", "ter", "qua", "qui", "sex", "sab", "dom")

# paleta do dominio `grimorio`
COR = {"fundo": "17141D", "sup": "1F1A28", "sup2": "2C2440", "contorno": "3A3348",
       "texto": "EDE7F6", "suave": "B0A7C4", "prim": "A99BD9", "sec": "7FBBE0",
       "terc": "74C5B0", "erro": "E8866E", "ouro": "FFD43B", "terra": "D3AE73"}

# (nome, descricao, funcao(estado, derivados) -> bool), do menos ao mais prestigioso
TITULOS = [
    ("Aprendiz de Grimório", "Abriu o grimório pela primeira vez.", lambda e, d: True),
    ("Fiel ao Ofício", "Cumpriu todos os ofícios de um dia.", lambda e, d: len(e["bonus_dia"]) >= 1),
    ("Vontade de Aço", "7 dias seguidos com todos os ofícios.", lambda e, d: e["seq_max"] >= 7),
    ("Quem se Ergueu da Queda", "Perdeu um dia, deixou a mana se dissipar e voltou com 3 dias de sequência.",
     lambda e, d: e["penalidades"] >= 1 and d["sequencia"] >= 3),
    ("Chama Inextinguível", "30 dias seguidos com todos os ofícios.", lambda e, d: e["seq_max"] >= 30),
    ("Chamador de Familiares", "3 familiares trabalhando ao mesmo tempo.", lambda e, d: e["paralelo_max"] >= 3),
    ("Mestre Invocador", "5 familiares invocados ao mesmo tempo.", lambda e, d: e["paralelo_max"] >= 5),
    ("Senhor do Bestiário", "100 familiares invocados.", lambda e, d: e["sombras_total"] >= 100),
    ("Escriba Incansável", "Runas gravadas em 7 dias seguidos.", lambda e, d: d["run_commits"] >= 7),
    ("Cartógrafo de Masmorras", "Runas gravadas em 10 masmorras (repositórios).", lambda e, d: d["repos_ativos"] >= 10),
    ("Corpo de Ferro", "20 treinos na academia.", lambda e, d: e["missao_cont"].get("academia", 0) >= 20),
    ("Mente Serena", "20 sessões de mindfulness.", lambda e, d: e["missao_cont"].get("mindfulness", 0) >= 20),
    ("Leitor de Grimórios", "20 dias de leitura.", lambda e, d: e["missao_cont"].get("leitura", 0) >= 20),
    ("Mil Runas Gravadas", "1000 commits gravados.", lambda e, d: e["commits_total"] >= 1000),
    ("Arcanista de Rank B", "Chegou ao nível 30 na guilda.", lambda e, d: d["nivel"] >= 30),
    ("Arquimago de Rank A", "Chegou ao nível 45 na guilda.", lambda e, d: d["nivel"] >= 45),
]


# ------------------------------------------------------------ utilidades
def aviso(msg):
    print(f"jogador: {msg}", file=sys.stderr)


def agora():
    f = os.environ.get("DOMINIOS_AGORA")
    if f:
        try:
            return datetime.fromisoformat(f).replace(tzinfo=None)
        except ValueError:
            pass
    return datetime.now()


def iso(d):
    return d.isoformat(timespec="seconds")


def pasta_estado():
    p = os.environ.get("DOMINIOS_ESTADO")
    if p:
        return p
    base = os.environ.get("XDG_STATE_HOME") or os.path.join(CASA, ".local", "state")
    return os.path.join(base, "dominios")


def arq(nome):
    return os.path.join(pasta_estado(), nome)


def grava_atomico(caminho, obj):
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    tmp = f"{caminho}.{os.getpid()}.tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False, indent=1)
            f.write("\n")
        os.replace(tmp, caminho)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def le_json(caminho, padrao):
    try:
        with open(caminho, "rb") as f:
            return json.loads(f.read().decode("utf-8"))
    except FileNotFoundError:
        return padrao
    except (OSError, ValueError) as e:
        aviso(f"não consegui ler {caminho}: {e}")
        return padrao


def com_trava(fn):
    import fcntl
    os.makedirs(pasta_estado(), exist_ok=True)
    fd = os.open(arq("jogador.lock"), os.O_RDWR | os.O_CREAT, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        return fn()
    finally:
        os.close(fd)


def git(args, timeout=60):
    import subprocess
    try:
        r = subprocess.run(["git", *args], capture_output=True, text=True, timeout=timeout,
                           errors="replace", env={**os.environ, "GIT_OPTIONAL_LOCKS": "0"})
        return r.stdout if r.returncode == 0 else ""
    except (OSError, subprocess.SubprocessError):
        return ""


SILENCIO = [False]      # true durante o XP retroativo (sem evento de nivel)


# ------------------------------------------------------------ curva
def xp_proximo(n):
    return round(50 * n ** 1.4)


def nivel_de(total):
    """(nivel, xp dentro do nivel, tamanho do nivel)."""
    n = 1
    while total >= xp_proximo(n):
        total -= xp_proximo(n)
        n += 1
    return n, total, xp_proximo(n)


def inicio_do_nivel(total):
    n, dentro, _ = nivel_de(total)
    return total - dentro


def rank_de(n):
    for lim, r in ((70, "S"), (45, "A"), (30, "B"), (20, "C"), (10, "D")):
        if n >= lim:
            return r
    return "E"


# ------------------------------------------------------------ estado
def estado_novo():
    return {"versao": 1, "inicio": None, "nome": None, "xp_total": 0, "eventos": [],
            "commits_total": 0, "commits_revisao": 0, "hashes": [], "repos": {}, "dias_commit": {},
            "xp_dia": {}, "missoes_pagas": {}, "missao_cont": {}, "bonus_dia": [], "fechados": [],
            "penalidades": 0, "seq_max": 0, "sombras_total": 0, "paralelo_max": 0, "ativos": {},
            "titulos": {}, "gastos": {a: 0 for a in ATRIBUTOS}, "nivel_inicial": 1,
            "historico_feito": False}


RENOMEAR_TITULOS = {'Despertado': 'Aprendiz de Grimório', 'Cumpridor das Regras': 'Fiel ao Ofício', 'Vontade Inabalável': 'Vontade de Aço', 'O Que Superou a Adversidade': 'Quem se Ergueu da Queda', 'Inquebrável': 'Chama Inextinguível', 'Soldado da Sombra': 'Chamador de Familiares', 'Monarca das Sombras': 'Mestre Invocador', 'Exército de Sombras': 'Senhor do Bestiário', 'Caçador Incansável': 'Escriba Incansável', 'Mil Cortes': 'Mil Runas Gravadas', 'Caçador de Rank B': 'Arcanista de Rank B', 'Caçador de Rank A': 'Arquimago de Rank A'}
REESCREVER = [("Missão cumprida: ", "Ofício concluído: "), ("Dia completo, ", "Dia de ofícios completo, "),
              ("Sombra invocada em", "Familiar invocado em"), ("Sombra de volta de", "Familiar retornou de"),
              ("sombras já tinham sido invocadas antes do despertar", "familiares já tinham sido invocados antes do grimório se abrir"),
              ("Despertar: ", "Grimório aberto: "), ("O Sistema te escolheu.", "O grimório te reconheceu."),
              ("O Sistema reconhece o teu avanço.", "A mana responde ao teu avanço."),
              ("A sequência voltou a zero.", "a mana se dissipou."), ("Dia perdido (", "Dia perdido ("),
              ("Rank B", "Rank B")]


def migra_tema(e):
    """Estado gravado com o tema antigo: renomeia títulos e reescreve eventos (XP intacto)."""
    for a, b in RENOMEAR_TITULOS.items():
        if a in e["titulos"] and b not in e["titulos"]:
            e["titulos"][b] = e["titulos"].pop(a)
    for ev in e["eventos"]:
        t = ev.get("texto", "")
        for a, b in REESCREVER:
            t = t.replace(a, b)
        for a, b in RENOMEAR_TITULOS.items():
            t = t.replace(a, b)
        t = re.sub(r"(Dia perdido \(\d\d/\d\d\))[.:] [Aa] mana", r"\1: a mana", t)
        ev["texto"] = t


def carrega_estado():
    e = le_json(arq("jogador-estado.json"), None)
    base = estado_novo()
    if not isinstance(e, dict):
        return base
    for k, v in base.items():
        if k not in e or type(e[k]) is not type(v) and v is not None:
            e[k] = v
    for a in ATRIBUTOS:
        e["gastos"].setdefault(a, 0)
    migra_tema(e)
    return e


def evento(e, momento, tipo, texto, xp=0):
    e["eventos"].insert(0, {"quando": iso(momento), "tipo": tipo, "texto": texto, "xp": int(xp)})
    del e["eventos"][GUARDA_EVENTOS:]


def ganha(e, momento, tipo, texto, xp):
    """Soma XP, registra evento e avisa subida de nivel."""
    antes = nivel_de(e["xp_total"])[0]
    e["xp_total"] += xp
    dia = momento.date().isoformat()
    if xp > 0:
        e["xp_dia"][dia] = e["xp_dia"].get(dia, 0) + xp
    evento(e, momento, tipo, texto, xp)
    depois = nivel_de(e["xp_total"])[0]
    if depois > antes and not SILENCIO[0]:
        evento(e, momento, "nivel", f"Nível {depois}. A mana responde ao teu avanço.", 0)


# ------------------------------------------------------------ git
def emails_dono():
    saida = git(["config", "--global", "--get-all", "user.email"])
    return [x.strip() for x in saida.splitlines() if x.strip()]


def nome_dono():
    nome = git(["config", "--global", "user.name"]).strip().split()
    return (nome[0] if nome else os.environ.get("USER", "JOGADOR")).upper()


def _gitdir(caminho):
    """(gitdir, commondir) de um '.git' que pode ser pasta ou arquivo de worktree."""
    try:
        if os.path.isdir(caminho):
            return caminho, caminho
        with open(caminho, encoding="utf-8", errors="replace") as f:
            linha = f.readline().strip()
        if not linha.startswith("gitdir:"):
            return None
        gd = linha[7:].strip()
        if not os.path.isabs(gd):
            gd = os.path.join(os.path.dirname(caminho), gd)
        gd = os.path.realpath(gd)
        common = gd
        try:
            with open(os.path.join(gd, "commondir"), encoding="utf-8") as f:
                common = os.path.realpath(os.path.join(gd, f.read().strip()))
        except OSError:
            pass
        return gd, common
    except OSError:
        return None


def acha_repos():
    """{commondir: {'nome', 'gitdirs': [...]}} dentro de ~ (profundidade limitada)."""
    raizes = os.environ.get("JOGADOR_RAIZES")
    raizes = [r for r in raizes.split(":") if r] if raizes else [CASA]
    achados = {}

    def anota(gd_cd, dono):
        gd, cd = gd_cd
        r = achados.setdefault(cd, {"nome": None, "gitdirs": []})
        if gd not in r["gitdirs"]:
            r["gitdirs"].append(gd)
        if gd == cd:
            r["nome"] = os.path.basename(dono.rstrip("/")) if not cd.endswith("/.git") \
                else os.path.basename(os.path.dirname(cd))

    def anda(pasta, prof):
        try:
            itens = list(os.scandir(pasta))
        except OSError:
            return
        nomes = {i.name for i in itens}
        if ".git" in nomes:
            r = _gitdir(os.path.join(pasta, ".git"))
            if r:
                anota(r, pasta)
            return
        if prof >= PROFUNDIDADE:
            return
        for i in itens:
            if i.name.startswith(".") or i.name in PULA:
                continue
            try:
                if i.is_dir(follow_symlinks=False):
                    anda(i.path, prof + 1)
            except OSError:
                pass

    for r in raizes:
        anda(r, 0)
    dot = os.path.join(CASA, ".dotfiles")
    if not os.environ.get("JOGADOR_RAIZES") and os.path.isfile(os.path.join(dot, "HEAD")):
        anota((dot, dot), dot)
    for cd, r in achados.items():           # worktree sem o repo principal varrido
        if not r["nome"]:
            r["nome"] = os.path.basename(os.path.dirname(cd)) if cd.endswith("/.git") else os.path.basename(cd)
    return achados


def assinatura(repo):
    """mtimes que mudam quando algo commita: baratos de checar a cada volta."""
    s = []
    for gd in repo["gitdirs"]:
        for sub in ("logs/HEAD", "HEAD"):
            try:
                s.append(os.stat(os.path.join(gd, sub)).st_mtime_ns)
            except OSError:
                s.append(0)
    return s


class Contexto:
    """Cache em memoria do modo seguir: lista de repos e assinaturas."""
    def __init__(self):
        self.repos = None
        self.repos_em = 0.0
        self.assinaturas = {}
        self.emails = None
        self.sessoes_mod = None


def coleta_commits(e, momento, ctx, primeira):
    emails = ctx.emails or emails_dono()
    if not emails:
        return
    ctx.emails = emails
    if ctx.repos is None or time.monotonic() - ctx.repos_em > REPOS_CADA_S:
        ctx.repos = acha_repos()
        ctx.repos_em = time.monotonic()
    vistos = set(e["hashes"])
    padrao = "|".join(x.replace(".", "[.]") for x in emails)
    novos_por_repo = {}
    for cd, rep in ctx.repos.items():
        sig = assinatura(rep)
        estado_repo = e["repos"].setdefault(cd, {"cursor": 0, "nome": rep["nome"], "commits": 0})
        if not primeira and ctx.assinaturas.get(cd) == sig and cd in ctx.assinaturas:
            continue
        ctx.assinaturas[cd] = sig
        args = ["--git-dir", cd, "log", "--all", "--no-merges", "-E", f"--author=({padrao})",
                "--format=%H%x09%ct%x09%s"]
        if estado_repo["cursor"]:
            args.append(f"--since=@{estado_repo['cursor'] - 86400}")
        for linha in git(args).splitlines():
            partes = linha.split("\t", 2)
            if len(partes) < 3 or partes[0] in vistos:
                continue
            try:
                ct = int(partes[1])
            except ValueError:
                continue
            h = partes[0]
            vistos.add(h)
            e["hashes"].append(h)
            e["commits_total"] += 1
            estado_repo["commits"] += 1
            estado_repo["cursor"] = max(estado_repo["cursor"], ct)
            estado_repo["nome"] = rep["nome"]
            dia = datetime.fromtimestamp(ct).date().isoformat()
            e["dias_commit"][dia] = e["dias_commit"].get(dia, 0) + 1
            if any(k in partes[2].lower() for k in REVISAO):
                e["commits_revisao"] += 1
            novos_por_repo[rep["nome"]] = novos_por_repo.get(rep["nome"], 0) + 1
    n = sum(novos_por_repo.values())
    if not n:
        return
    xp = n * XP_COMMIT
    if primeira:
        ganha(e, momento, "xp", f"Grimório aberto: {n} commits em {len(novos_por_repo)} {"repositório" if len(novos_por_repo) == 1 else "repositórios"} viraram o teu nível inicial", xp)
        e["xp_dia"].pop(momento.date().isoformat(), None)      # historico nao e XP de hoje
        return
    for nome, k in sorted(novos_por_repo.items(), key=lambda x: -x[1]):
        ganha(e, momento, "xp", f"{k} commit{'s' if k > 1 else ''} em {nome}", k * XP_COMMIT)


# ------------------------------------------------------------ missoes
def _virada(v):
    try:
        h, m = str(v).split(":")
        return int(h) * 60 + int(m)
    except ValueError:
        return 240


def carrega_missoes():
    import tomllib
    caminho = os.environ.get("DOMINIOS_MISSOES") or os.path.join(RAIZ, "missoes.toml")
    try:
        with open(caminho, "rb") as f:
            cfg = tomllib.load(f)
    except (OSError, ValueError):
        return None
    missoes = []
    for m in cfg.get("missao", []) if isinstance(cfg.get("missao"), list) else []:
        if not isinstance(m, dict) or not isinstance(m.get("id"), str):
            continue
        d = m.get("dias", "todos")
        dias = set(range(7)) if d == "todos" else {DIAS.index(x) for x in d if x in DIAS} \
            if isinstance(d, list) else set(range(7))
        missoes.append({"id": m["id"], "titulo": str(m.get("titulo", m["id"])), "dias": dias})
    return {"virada": _virada(cfg.get("virada", "04:00")), "missoes": missoes}


def le_missoes_estado():
    dados = le_json(arq("missoes.json"), {})
    dias = dados.get("dias") if isinstance(dados, dict) else None
    saida = {}
    for k, reg in (dias or {}).items():
        try:
            datetime.fromisoformat(k)
        except ValueError:
            continue
        if isinstance(reg, list):
            reg = {"feitas": reg}
        if isinstance(reg, dict):
            saida[k] = {"feitas": [x for x in reg.get("feitas", []) if isinstance(x, str)]
                        if isinstance(reg.get("feitas"), list) else [],
                        "agendadas": reg.get("agendadas") if isinstance(reg.get("agendadas"), list) else None}
    return saida


def coleta_missoes(e, momento, cfg, primeira):
    """Atualiza XP de missoes e devolve a sequencia atual."""
    if not cfg:
        return e.get("seq_atual", 0)
    dados = le_missoes_estado()
    hoje = (momento - timedelta(minutes=cfg["virada"])).date()
    por_id = {m["id"]: m for m in cfg["missoes"]}
    inicio_dia = e.setdefault("inicio_dia", hoje.isoformat())

    def agendadas(d):
        reg = dados.get(d.isoformat())
        if d != hoje and reg and reg["agendadas"] is not None:
            return reg["agendadas"]
        return [m["id"] for m in cfg["missoes"] if d.weekday() in m["dias"]]

    # recompensa por missao concluida
    for dia, reg in sorted(dados.items()):
        pagas = e["missoes_pagas"].setdefault(dia, [])
        for mid in reg["feitas"]:
            if mid in pagas:
                continue
            pagas.append(mid)
            e["missao_cont"][mid] = e["missao_cont"].get(mid, 0) + 1
            titulo = por_id[mid]["titulo"] if mid in por_id else mid
            ganha(e, momento, "missao", f"Ofício concluído: {titulo}", XP_MISSAO)
    limite = (hoje - timedelta(days=450)).isoformat()
    for k in [k for k in e["missoes_pagas"] if k < limite]:
        del e["missoes_pagas"][k]

    # dias: bonus, penalidade, sequencia (mesma regra do `missao`)
    if not dados:
        return 0
    d = min(datetime.fromisoformat(k).date() for k in dados)
    seq = 0
    while d <= hoje:
        ag = agendadas(d)
        feitas = set(dados.get(d.isoformat(), {}).get("feitas", ()))
        completo = bool(ag) and all(i in feitas for i in ag)
        chave = d.isoformat()
        if completo:
            seq += 1
            e["seq_max"] = max(e["seq_max"], seq)
            if chave not in e["bonus_dia"]:
                e["bonus_dia"].append(chave)
                ganha(e, momento, "missao", f"Dia de ofícios completo, {seq} em sequência", XP_DIA + XP_DIA_SEQ * min(seq, 10))
        elif ag and d != hoje:
            seq = 0
            if chave not in e["fechados"] and chave >= inicio_dia:
                piso = inicio_do_nivel(e["xp_total"])
                perda = min(XP_PENALIDADE, e["xp_total"] - piso)
                e["xp_total"] -= perda
                e["penalidades"] += 1
                evento(e, momento, "penalidade", f"Dia perdido ({d.day:02d}/{d.month:02d}): a mana se dissipou.", -perda)
            e["fechados"].append(chave) if chave not in e["fechados"] else None
        d += timedelta(days=1)
    e["bonus_dia"] = e["bonus_dia"][-500:]
    e["fechados"] = e["fechados"][-500:]
    e["seq_atual"] = seq
    return seq


# ------------------------------------------------------------ agentes
def sessoes_vivas(ctx):
    if os.environ.get("JOGADOR_SEM_AGENTES"):
        return []
    try:
        if ctx.sessoes_mod is None:
            from importlib.machinery import SourceFileLoader
            from importlib.util import module_from_spec, spec_from_loader
            caminho = os.path.join(RAIZ, "bin", "agentes")
            ld = SourceFileLoader("dominios_agentes", caminho)
            spec = spec_from_loader("dominios_agentes", ld)
            ctx.sessoes_mod = module_from_spec(spec)
            ld.exec_module(ctx.sessoes_mod)
        return ctx.sessoes_mod.acha_sessoes()
    except Exception as ex:                      # nunca derruba o laco
        aviso(f"agentes indisponível: {ex}")
        return None


def coleta_agentes(e, momento, ctx):
    vivas = sessoes_vivas(ctx)
    if vivas is None:
        return
    t = time.time()
    atuais = {}
    for s in vivas:
        atuais[str(s["pid"])] = {"projeto": s.get("projeto", "?"), "inicio": t - s.get("tempo_s", 0)}
    for pid, s in atuais.items():
        velho = e["ativos"].get(pid)
        if velho and abs(velho["inicio"] - s["inicio"]) < 120:
            continue
        e["sombras_total"] += 1
        ganha(e, momento, "xp", f"Familiar invocado em {s['projeto']}", XP_SOMBRA)
    for pid, v in list(e["ativos"].items()):
        nova = atuais.get(pid)
        if nova and abs(v["inicio"] - nova["inicio"]) < 120:
            continue
        if v.get("visto", 0) - v["inicio"] >= SOMBRA_MIN_S:
            ganha(e, momento, "xp", f"Familiar retornou de {v['projeto']}", XP_SOMBRA_VOLTA)
    e["ativos"] = {pid: {**s, "visto": t} for pid, s in atuais.items()}
    e["paralelo_max"] = max(e["paralelo_max"], len(atuais))


def historico_sessoes(e, momento):
    if os.environ.get("JOGADOR_SEM_HISTORICO"):
        return
    base = os.path.join(os.environ.get("CLAUDE_CONFIG_DIR") or os.path.join(CASA, ".claude"), "projects")
    n = 0
    try:
        for p in os.scandir(base):
            if p.is_dir():
                try:
                    n += sum(1 for f in os.scandir(p.path) if f.name.endswith(".jsonl"))
                except OSError:
                    pass
    except OSError:
        return
    if n:
        e["sombras_total"] += n
        ganha(e, momento, "xp", f"{n} familiares já tinham sido invocados antes do grimório se abrir", n * XP_SESSAO_HIST)
        e["xp_dia"].pop(momento.date().isoformat(), None)


# ------------------------------------------------------------ derivados
def maior_sequencia_commits(dias):
    ds = sorted(datetime.fromisoformat(k).date() for k in dias)
    melhor = atual = 0
    ant = None
    for d in ds:
        atual = atual + 1 if ant and (d - ant).days == 1 else 1
        melhor = max(melhor, atual)
        ant = d
    return melhor


def atributos(e):
    cont = e["missao_cont"]
    saude = sum(cont.get(i, 0) for i in SAUDE)
    estudo = sum(cont.get(i, 0) for i in ESTUDO)
    base = {
        "forca": len(e["dias_commit"]) // 5,
        "agilidade": 4 * e["paralelo_max"] + e["sombras_total"] // 25,
        "inteligencia": e["commits_total"] // 60,
        "vitalidade": 2 * e["seq_max"] + saude // 4,
        "percepcao": e["commits_revisao"] // 15 + estudo // 3,
    }
    return {a: 10 + base[a] + e["gastos"].get(a, 0) for a in ATRIBUTOS}


def atualiza_titulos(e, momento, derivados):
    for nome, _desc, cond in TITULOS:
        if nome in e["titulos"]:
            continue
        try:
            ok = cond(e, derivados)
        except Exception:
            ok = False
        if ok:
            e["titulos"][nome] = iso(momento)
            evento(e, momento, "titulo", f"Título conquistado: {nome}", 0)


PADRAO_CLASSE = "Invocador"


def le_prefs():
    p = le_json(arq("jogador-prefs.json"), {})
    return p if isinstance(p, dict) else {}


def grava_prefs(chave, valor):
    p = le_prefs()
    if valor is None:
        p.pop(chave, None)
    else:
        p[chave] = valor
    grava_atomico(arq("jogador-prefs.json"), p)


def monta_ficha(e, momento, seq):
    nivel, dentro, tam = nivel_de(e["xp_total"])
    deriv = {"nivel": nivel, "sequencia": seq, "run_commits": maior_sequencia_commits(e["dias_commit"]),
             "repos_ativos": sum(1 for r in e["repos"].values() if r["commits"] > 0)}
    atualiza_titulos(e, momento, deriv)
    ganhos = nivel - e["nivel_inicial"]
    livres = max(0, 3 * ganhos - sum(e["gastos"].values()))
    ativo = "Aprendiz de Grimório"
    for nome, _d, _c in TITULOS:
        if nome in e["titulos"]:
            ativo = nome
    prefs = le_prefs()
    escolhido = prefs.get("titulo")
    if isinstance(escolhido, str) and escolhido in e["titulos"]:
        ativo = escolhido
    nome = prefs.get("nome") if isinstance(prefs.get("nome"), str) and prefs.get("nome").strip() else e["nome"]
    classe = prefs.get("classe") if isinstance(prefs.get("classe"), str) and prefs.get("classe").strip() else PADRAO_CLASSE
    return {
        "nome": nome, "titulo": ativo, "classe": classe, "nivel": nivel,
        "rank": rank_de(nivel), "xp": dentro, "xp_proximo": tam, "xp_total": e["xp_total"],
        "xp_hoje": e["xp_dia"].get(momento.date().isoformat(), 0),
        "atributos": atributos(e), "pontos_livres": livres, "sequencia_dias": seq,
        "eventos": e["eventos"][:MOSTRA_EVENTOS],
        "titulos": [{"nome": n, "descricao": d, "conquistado": n in e["titulos"],
                     "quando": e["titulos"].get(n)} for n, d, _c in TITULOS],
        "atualizado": iso(momento),
    }


# ------------------------------------------------------------ ciclo
def ciclo(ctx, gravar=True):
    """Um recalculo completo. Devolve a ficha."""
    def tudo():
        momento = agora()
        e = carrega_estado()
        primeira = e["inicio"] is None
        SILENCIO[0] = primeira
        if primeira:
            e["inicio"] = iso(momento)
            e["nome"] = nome_dono()
        if not e["nome"]:
            e["nome"] = nome_dono()
        try:
            coleta_commits(e, momento, ctx, primeira)
        except Exception as ex:
            aviso(f"git: {ex}")
        if primeira:
            historico_sessoes(e, momento)
        try:
            seq = coleta_missoes(e, momento, carrega_missoes(), primeira)
        except Exception as ex:
            aviso(f"missões: {ex}")
            seq = e.get("seq_atual", 0)
        try:
            coleta_agentes(e, momento, ctx)
        except Exception as ex:
            aviso(f"agentes: {ex}")
        SILENCIO[0] = False
        if primeira:
            e["nivel_inicial"] = nivel_de(e["xp_total"])[0]
            evento(e, momento, "nivel", f"O grimório te reconheceu. Nível inicial {e['nivel_inicial']}.", 0)
        ficha = monta_ficha(e, momento, seq)
        e["xp_dia"] = {k: v for k, v in e["xp_dia"].items() if k >= (momento.date() - timedelta(days=60)).isoformat()}
        if gravar:
            grava_atomico(arq("jogador-estado.json"), e)
            grava_atomico(arq("jogador.json"), ficha)
        return ficha
    return com_trava(tudo)


# ------------------------------------------------------------ comandos
def tc(hexa, fundo=False):
    return f"\x1b[{48 if fundo else 38};2;{int(hexa[0:2], 16)};{int(hexa[2:4], 16)};{int(hexa[4:6], 16)}m"


RESET = "\x1b[0m"


def barra(frac, larg, cor, cor_vazia="223A66"):
    cheio = max(0, min(larg, round(frac * larg)))
    return tc(cor) + "█" * cheio + tc(cor_vazia) + "░" * (larg - cheio) + RESET


def cmd_ficha(f):
    cor = sys.stdout.isatty() or os.environ.get("FORCE_COLOR")
    c = (lambda k: tc(COR[k])) if cor else (lambda k: "")
    r = RESET if cor else ""
    rank_cor = {"E": "suave", "D": "terc", "C": "sec", "B": "prim", "A": "terra", "S": "ouro"}[f["rank"]]
    L = 56
    out = []
    out.append(f"{c('contorno')}╭{'─' * 3} {c('prim')}GRIMÓRIO{c('contorno')} {'─' * (L - 16)} {c('suave')}CONJURADOR{c('contorno')} ─╮{r}")

    def linha(txt):
        out.append(f"{c('contorno')}│{r} {txt}")
    linha(f"{c('texto')}\x1b[1m{f['nome']}{r}  {c('suave')}{f['classe']}{r}")
    linha(f"{c('ouro')}« {f['titulo']} »{r}")
    linha("")
    linha(f"{c('suave')}NÍVEL{r} {c('prim')}\x1b[1m{f['nivel']}{r}    {c('suave')}RANK{r} {c(rank_cor)}\x1b[1m{f['rank']}{r}    {c('suave')}XP total{r} {c('texto')}{f['xp_total']:,}{r}".replace(",", "."))
    if cor:
        linha(f"{barra(f['xp'] / f['xp_proximo'], 30, COR['prim'])} {c('texto')}{f['xp']}{c('suave')}/{f['xp_proximo']}{r}")
    else:
        linha(f"{f['xp']}/{f['xp_proximo']}")
    linha(f"{c('suave')}hoje{r} {c('terc')}+{f['xp_hoje']} XP{r}    {c('suave')}sequência{r} {c('ouro')}{f['sequencia_dias']} {'dia' if f['sequencia_dias'] == 1 else 'dias'}{r}    {c('suave')}pontos livres{r} {c('texto')}{f['pontos_livres']}{r}")
    linha("")
    nomes = {"forca": "Força", "agilidade": "Agilidade", "inteligencia": "Inteligência",
             "vitalidade": "Vitalidade", "percepcao": "Percepção"}
    cores = {"forca": "erro", "agilidade": "terc", "inteligencia": "prim", "vitalidade": "ouro", "percepcao": "sec"}
    topo = max(max(f["atributos"].values()), 30)
    for a, v in f["atributos"].items():
        b = barra(v / topo, 24, COR[cores[a]]) if cor else "#" * round(24 * v / topo)
        linha(f"{c('suave')}{nomes[a]:<13}{r}{b} {c('texto')}{v}{r}")
    linha("")
    ganhos = [t for t in f["titulos"] if t["conquistado"]]
    linha(f"{c('suave')}Títulos {len(ganhos)}/{len(f['titulos'])}{r}")
    for t in ganhos[-6:]:
        linha(f"  {c('ouro')}◆{r} {c('texto')}{t['nome']}{r}")
    linha("")
    linha(f"{c('suave')}Eventos recentes{r}")
    for ev in f["eventos"][:5]:
        sinal = f"{ev['xp']:+d}" if ev["xp"] else "  "
        hora = ev["quando"][5:16].replace("T", " ")
        corx = "erro" if ev["tipo"] == "penalidade" else "terc" if ev["tipo"] in ("nivel", "titulo") else "prim"
        txt = ev["texto"] if len(ev["texto"]) <= 44 else ev["texto"][:43] + "…"
        linha(f"{c('suave')}{hora}{r} {c(corx)}{sinal:>6}{r} {c('texto')}{txt}{r}")
    out.append(f"{c('contorno')}╰{'─' * (L + 2)}╯{r}")
    print("\n".join(out))


def seguir(emitir, intervalo=60, parar=None, acordar=None):
    """Laço embutível: chama emitir(ficha) a cada mudança (a 1ª ficha sai sempre) até parar.is_set().
    `acordar` (threading.Event, opcional) antecipa o próximo ciclo; quem para o laço aciona
    `parar` e `acordar`. Não usa stdout nem sinais; erros de ciclo ou de emitir não derrubam o laço."""
    import threading
    parar = parar or threading.Event()
    acordar = acordar or threading.Event()
    ctx = Contexto()
    ultimo = None
    while not parar.is_set():
        try:
            f = ciclo(ctx)
            chave = json.dumps({k: v for k, v in f.items() if k != "atualizado"}, sort_keys=True)
            if chave != ultimo:
                ultimo = chave
                emitir(f)
        except Exception as ex:
            aviso(f"falha no ciclo: {ex}")
        acordar.wait(max(1.0, intervalo))
        acordar.clear()
    return 0


def cmd_seguir(intervalo):
    import signal
    import threading
    parar = threading.Event()
    signal.signal(signal.SIGTERM, lambda *_: parar.set())
    signal.signal(signal.SIGINT, lambda *_: parar.set())

    def emitir(f):
        try:
            print(json.dumps(f, ensure_ascii=False, separators=(",", ":")), flush=True)
        except BrokenPipeError:
            parar.set()
    # acordar fica fora da parada: sem ele o laço dorme o intervalo inteiro mesmo parado
    acordar = threading.Event()
    threading.Thread(target=lambda: (parar.wait(), acordar.set()), daemon=True).start()
    return seguir(emitir, intervalo, parar, acordar)


def cmd_conceder(args):
    if len(args) < 2:
        aviso("uso: jogador conceder <xp> <motivo>")
        return 2
    try:
        xp = int(args[0])
    except ValueError:
        aviso("xp precisa ser inteiro")
        return 2
    motivo = " ".join(args[1:])

    def f():
        e = carrega_estado()
        if e["inicio"] is None:
            return False
        ganha(e, agora(), "xp", motivo, xp)
        grava_atomico(arq("jogador-estado.json"), e)
        return True
    if not com_trava(f):
        ciclo(Contexto())
        com_trava(f)
    ciclo(Contexto())
    return 0


def cmd_gastar(args):
    if not args or args[0] not in ATRIBUTOS:
        aviso("uso: jogador gastar <" + "|".join(ATRIBUTOS) + "> [n]")
        return 2
    n = int(args[1]) if len(args) > 1 and args[1].isdigit() else 1
    ficha = ciclo(Contexto())
    if ficha["pontos_livres"] < n:
        aviso(f"só tens {ficha['pontos_livres']} pontos livres")
        return 1

    def f():
        e = carrega_estado()
        e["gastos"][args[0]] += n
        evento(e, agora(), "xp", f"{n} ponto(s) em {args[0]}", 0)
        grava_atomico(arq("jogador-estado.json"), e)
    com_trava(f)
    ciclo(Contexto())
    return 0


def cmd_texto_pref(chave, args, rotulo):
    if not args:
        print(le_prefs().get(chave) or "(padrão)")
        return 0
    texto = " ".join(args).strip()
    grava_prefs(chave, None if texto.lower() == "auto" or not texto else texto)
    f = ciclo(Contexto())
    print(f"{rotulo}: {f[chave]}")
    return 0


def cmd_titulo(args):
    f = ciclo(Contexto())
    lista = f["titulos"]
    if not args:
        for i, t in enumerate(lista, 1):
            marca = "x" if t["conquistado"] else " "
            atual = "  <- na ficha" if t["nome"] == f["titulo"] else ""
            print(f"{i:>2} [{marca}] {t['nome']}: {t['descricao']}{atual}")
        return 0
    q = " ".join(args).strip()
    if q.lower() == "auto":
        grava_prefs("titulo", None)
    else:
        alvo = None
        if q.isdigit() and 1 <= int(q) <= len(lista):
            alvo = lista[int(q) - 1]
        else:
            alvo = next((t for t in lista if t["nome"].lower() == q.lower()), None) or \
                next((t for t in lista if q.lower() in t["nome"].lower()), None)
        if alvo is None:
            aviso(f"título desconhecido: {q}")
            return 2
        if not alvo["conquistado"]:
            aviso(f"ainda não conquistado: {alvo['nome']} ({alvo['descricao']})")
            return 2
        grava_prefs("titulo", alvo["nome"])
    f = ciclo(Contexto())
    print(f"título: {f['titulo']}")
    return 0


def main(argv):
    cmd = argv[0] if argv else "ficha"
    resto = argv[1:]
    try:
        if cmd in ("ficha", ""):
            cmd_ficha(ciclo(Contexto()))
        elif cmd == "atualizar":
            f = ciclo(Contexto())
            print(f"nível {f['nivel']} ({f['rank']}) xp_total {f['xp_total']}")
        elif cmd == "json":
            print(json.dumps(ciclo(Contexto(), gravar=False), ensure_ascii=False))
        elif cmd == "seguir":
            iv = 60.0
            if "--intervalo" in resto:
                i = resto.index("--intervalo")
                try:
                    iv = max(1.0, float(resto[i + 1]))
                except (IndexError, ValueError):
                    aviso("--intervalo precisa de um número")
                    return 2
            return cmd_seguir(iv)
        elif cmd == "conceder":
            return cmd_conceder(resto)
        elif cmd == "nome":
            return cmd_texto_pref("nome", resto, "nome")
        elif cmd == "classe":
            return cmd_texto_pref("classe", resto, "classe")
        elif cmd == "titulo":
            return cmd_titulo(resto)
        elif cmd == "gastar":
            return cmd_gastar(resto)
        elif cmd == "eventos":
            f = ciclo(Contexto())
            for ev in f["eventos"]:
                print(f"{ev['quando']}  {ev['tipo']:<10} {ev['xp']:>+6}  {ev['texto']}")
        elif cmd in ("ajuda", "-h", "--help"):
            print(__doc__)
        else:
            aviso(f"comando desconhecido: {cmd}")
            return 2
    except KeyboardInterrupt:
        return 130
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
