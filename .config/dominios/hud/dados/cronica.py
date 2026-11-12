"""Cronica: calendario de contribuicoes do GitHub (`gh api graphql`) fundido com os commits locais
(`dias_commit` do jogador): cada dia vale o maior dos dois. Sem rede ou sem `gh`, so os locais.

Cache em ~/.cache/dominios/cronica.json (CRONICA_CACHE troca o arquivo, para teste). No maximo
uma consulta a cada 30 min; falha de rede tenta de novo em 3 min (o GitHub nem foi consultado).
Nada de token: o `gh` usa a propria credencial e aqui so passa a consulta e as datas.
"""
import json
import os
import subprocess
import time
from datetime import datetime, timedelta, timezone

CACHE = os.environ.get("CRONICA_CACHE") or os.path.expanduser("~/.cache/dominios/cronica.json")
CADA_S = 30 * 60
REDE_CADA_S = 3 * 60
LOCAL_CADA_S = 2 * 60
SEMANAS = 26
LIMITE_S = 25
GH = os.environ.get("CRONICA_GH") or "gh"

CONSULTA = ("query($from:DateTime!,$to:DateTime!){viewer{contributionsCollection(from:$from,to:$to)"
            "{contributionCalendar{totalContributions weeks{contributionDays{contributionCount date}}}}}}")


def le_cache():
    try:
        with open(CACHE, encoding="utf-8") as f:
            c = json.load(f)
        return c if isinstance(c, dict) else {}
    except (OSError, ValueError):
        return {}


def grava_cache(c):
    try:
        os.makedirs(os.path.dirname(CACHE), exist_ok=True)
        tmp = f"{CACHE}.{os.getpid()}.tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(c, f, ensure_ascii=False)
        os.replace(tmp, CACHE)
    except OSError:
        pass


def le_local():
    """Commits por dia (todos os ramos, todos os repositorios) que o `jogador` ja conta em
    jogador-estado.json (`dias_commit`: {"AAAA-MM-DD": n}). Vazio se nao houver."""
    caminho = os.environ.get("CRONICA_LOCAL")
    if not caminho:
        base = os.environ.get("DOMINIOS_ESTADO") or os.path.join(
            os.environ.get("XDG_STATE_HOME") or os.path.expanduser("~/.local/state"), "dominios")
        caminho = os.path.join(base, "jogador-estado.json")
    try:
        with open(caminho, encoding="utf-8") as f:
            d = json.load(f).get("dias_commit")
        return {k: int(v) for k, v in d.items() if isinstance(v, int)} if isinstance(d, dict) else {}
    except (OSError, ValueError, AttributeError):
        return {}


def monta(gh, local, agora_=None):
    """Funde as duas fontes no dict do canal `cronica`: cada dia vale o MAIOR entre as
    contribuicoes do GitHub (`gh`, {data: n} ou None) e os commits locais (`local`).
    `total_ano` e a soma dos dias fundidos do ano corrente. None sem nenhuma fonte."""
    if gh is None and not local:
        return None
    agora_ = agora_ or datetime.now()
    dias = dict(local or {})
    for k, v in (gh or {}).items():
        dias[k] = max(dias.get(k, 0), v)
    hoje = agora_.date()
    # semanas de domingo a sabado, terminando na semana de hoje; dia futuro conta 0
    inicio = hoje - timedelta(days=(hoje.weekday() + 1) % 7) - timedelta(weeks=SEMANAS - 1)
    semanas = [[dias.get((inicio + timedelta(weeks=s, days=d)).isoformat(), 0) for d in range(7)]
               for s in range(SEMANAS)]
    n, d = 0, hoje
    if dias.get(d.isoformat(), 0) == 0:
        d -= timedelta(days=1)          # hoje ainda pode estar em aberto
    while dias.get(d.isoformat(), 0) > 0:
        n += 1
        d -= timedelta(days=1)
    ano = f"{hoje.year}-"
    return {"semanas": semanas, "total_ano": sum(v for k, v in dias.items() if k.startswith(ano) and k <= hoje.isoformat()),
            "hoje": dias.get(hoje.isoformat(), 0), "sequencia": n,
            "fontes": {"github": gh is not None, "local": bool(local)},
            "atualizado": agora_.astimezone().isoformat(timespec="seconds")}


def consulta(registra_filho=None):
    """Chama o gh. Devolve ({data: contribuicoes}, motivo) ou (None, motivo), e motivo 'rede' | 'auth' | 'outro'."""
    fim = datetime.now(timezone.utc).replace(microsecond=0, tzinfo=None)
    ini = fim - timedelta(days=364)
    cmd = [GH, "api", "graphql", "-f", f"query={CONSULTA}",
           "-f", f"from={ini.isoformat()}Z", "-f", f"to={fim.isoformat()}Z"]
    env = dict(os.environ, GH_PROMPT_DISABLED="1", NO_COLOR="1", GH_SPINNER_DISABLED="1")
    try:
        p = subprocess.Popen(cmd, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE, env=env, text=True, start_new_session=True)
    except OSError:
        return None, "outro"
    if registra_filho:
        registra_filho(p)
    try:
        saida, erro = p.communicate(timeout=LIMITE_S)
    except subprocess.TimeoutExpired:
        p.kill()
        p.communicate()
        return None, "rede"
    if p.returncode != 0:
        e = (erro or "").lower()
        if "auth" in e or "login" in e or "token" in e or "401" in e:
            return None, "auth"
        if any(x in e for x in ("connect", "dial", "resolve", "timeout", "network", "unreachable", "eof")):
            return None, "rede"
        return None, "outro"
    try:
        cal = json.loads(saida)["data"]["viewer"]["contributionsCollection"]["contributionCalendar"]
        return {d["date"]: int(d["contributionCount"]) for sem in cal["weeks"]
                for d in sem["contributionDays"]}, None
    except (ValueError, KeyError, TypeError):
        return None, "outro"


class Cronica:
    """Estado do canal: `atual()` devolve o ultimo valor bom, None sem nenhuma fonte.
    O GitHub e consultado no maximo a cada 30 min (cache em `gh`); os commits locais sao lidos
    do arquivo do jogador a cada LOCAL_CADA_S (barato) e o canal e remontado com os dois."""

    def __init__(self, registra_filho=None):
        c = le_cache()
        gh = c.get("gh")
        self.gh = {k: v for k, v in gh.items() if isinstance(v, int)} if isinstance(gh, dict) else None
        self.tentativa = float(c.get("tentativa", 0) or 0) if self.gh is not None else 0.0
        self.proxima = self.tentativa + CADA_S
        self.registra = registra_filho
        self.local_em = time.time()
        self.dados = monta(self.gh, le_local())

    def quando_vence(self):
        return min(self.proxima, self.local_em + LOCAL_CADA_S)

    def atualiza(self, forcar=False):
        """Reconsulta o GitHub se ja passou o tempo e remonta. Devolve True se os dados mudaram."""
        agora_ = time.time()
        if not forcar and agora_ < self.quando_vence():
            return False
        motivo = None
        if forcar or agora_ >= self.proxima:
            gh, motivo = consulta(self.registra)
            self.tentativa = agora_
            self.proxima = agora_ + (REDE_CADA_S if motivo == "rede" else CADA_S)
            if gh is not None:
                self.gh = gh
            if motivo != "rede":            # a tentativa de verdade conta para o limite de 30 min
                grava_cache({"tentativa": agora_, "gh": self.gh})
        self.local_em = agora_
        novo = monta(self.gh, le_local())
        sem = lambda x: {k: v for k, v in (x or {}).items() if k != "atualizado"}
        mudou = sem(novo) != sem(self.dados)
        self.dados = novo
        return mudou
