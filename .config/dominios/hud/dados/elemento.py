#!/usr/bin/env python3
"""elemento: o motor do elemento ativo do Grimório (fogo, água, terra, vento, eletricidade, mana pura).

  elemento                      mostra elemento, motivo, candidatos e clima (e atualiza o estado)
  elemento atualizar            um ciclo silencioso (grava ~/.local/state/dominios/elemento.json)
  elemento seguir [--intervalo 30]  laço leve; uma linha JSON a cada troca, e a cada minuto
  elemento travar <nome>        fixa o elemento na mão
  elemento soltar               volta ao automático (reavalia na hora)
  elemento proximo              passa ao próximo elemento e trava (demonstração)
  elemento simular --dia        simula 24 h com dados plausíveis, sem gravar nada

COMO ESCOLHE
  Cada sinal vota com um peso (0..100). O peso do elemento é o maior voto mais um quarto da soma
  dos outros votos dele (teto 100). Ganha o maior; empate decide pela ordem fogo, água, terra,
  vento, eletricidade, mana pura. "!" marca sinal urgente.

  água          chuva forte/pancada 90, chuva ou garoa 75 (garoa 70), umidade >= 90 com nuvens >= 70: 60,
                umidade >= 85 com nuvens >= 60: 45
  vento         vento >= 35 km/h 85, >= 25 65, dia claro com brisa (12 a 25 km/h) 50, manhã (6 a 10 h) 45
  fogo          bateria < 10% fora da tomada 100!, < 20% 80, CPU >= 85 °C 85!, >= 75 °C 60,
                sensação >= 32 °C 75, >= 28 °C 50, pôr do sol (40 min em volta) 65
  eletricidade  trovoada agora 100!, na previsão (próximas 2 h) 70, depois disso 45,
                CPU média de 2 min >= 90 e sustentada 95!, >= 70 70, agentes Claude >= 5: 70, 3 ou 4: 50
  terra         tarde (13 a 18 h) 45, tempo calmo e seco de dia 30 (55 na tarde), máquina ociosa
                (CPU média < 15%) 25, fim de semana 25
  mana pura     madrugada (0 a 5:30) 70, noite (sol posto) 55, padrão quando nada se destaca 20

HISTERESE
  O elemento fica no mínimo 20 min. Depois disso só cede se o líder passar o atual por 8 pontos.
  Sinal urgente (peso >= 90 marcado com "!") troca na hora.

CLIMA   Open-Meteo, Porto Alegre, 1 consulta a cada 15 min no máximo (inclusive tentativa que
        falhou), cache em disco, sem rede segue só com hora e máquina (cache velho > 3 h é ignorado).
GANCHOS ~/.config/dominios/ganchos/elemento.d/*: <novo> <anterior> em segundo plano, limite de 10 s.

Variáveis de teste: DOMINIOS_ESTADO (pasta de estado), ELEMENTO_CACHE (pasta do cache do clima),
ELEMENTO_API (URL base da API), ELEMENTO_AGORA (data e hora ISO fingidas),
ELEMENTO_GANCHOS (outra pasta de ganchos).
"""
import fcntl
import json
import math
import os
import shutil
import signal
import subprocess
import sys
import time
from datetime import datetime, timedelta

import herois   # titulos dos seis herois ([grimorio.herois] no dominios.toml)

CASA = os.path.expanduser("~")
RAIZ = os.path.expanduser("~/.config/dominios")
ESTADO_DIR = os.environ.get("DOMINIOS_ESTADO") or os.path.join(CASA, ".local/state/dominios")
CACHE_DIR = os.environ.get("ELEMENTO_CACHE") or os.path.join(CASA, ".cache/dominios")
GANCHOS_DIR = os.environ.get("ELEMENTO_GANCHOS") or os.path.join(RAIZ, "ganchos/elemento.d")
API = os.environ.get("ELEMENTO_API") or "https://api.open-meteo.com/v1/forecast"
LAT, LON = -30.03, -51.23

ELEMENTOS = ("fogo", "agua", "terra", "vento", "eletricidade", "mana-pura")
NOMES = {"fogo": "Fogo", "agua": "Água", "terra": "Terra", "vento": "Vento",
         "eletricidade": "Eletricidade", "mana-pura": "Mana pura"}
COR = {"fogo": "E8866E", "agua": "7FBBE0", "terra": "D3AE73", "vento": "74C5B0",
       "eletricidade": "FFD43B", "mana-pura": "B4A5DD"}

MOTIVO_POR = "O sol se deita em brasas no horizonte."
MOTIVO_FIXO = "Fixado pelo conjurador."
# elemento que segue pela histerese sem sinal proprio: o motivo fala dele, nunca de outro
MOTIVO_FICA = {"fogo": "As brasas ainda ardem.", "agua": "A maré ainda não baixou.",
               "terra": "A pedra segue firme.", "vento": "O vento ainda sopra.",
               "eletricidade": "O ar ainda estala.",
               "mana-pura": "Nada se destaca: a mana se mantém pura."}
MIN_FICA_S = 20 * 60
NAO_VOLTA_S = 60 * 60
MARGEM = 8
URGENTE = 90
CLIMA_CADA_S = 15 * 60
CLIMA_VALE_S = 3 * 3600
CPU_JANELA_S = 120
GANCHO_LIMITE_S = 10

WMO = {0: "Céu limpo", 1: "Quase limpo", 2: "Parcialmente nublado", 3: "Nublado",
       45: "Neblina", 48: "Neblina gelada", 51: "Garoa fraca", 53: "Garoa", 55: "Garoa forte",
       56: "Garoa gelada", 57: "Garoa gelada forte", 61: "Chuva fraca", 63: "Chuva",
       65: "Chuva forte", 66: "Chuva gelada", 67: "Chuva gelada forte", 71: "Neve fraca",
       73: "Neve", 75: "Neve forte", 77: "Grãos de neve", 80: "Pancadas fracas",
       81: "Pancadas de chuva", 82: "Pancadas fortes", 85: "Pancadas de neve",
       86: "Pancadas de neve fortes", 95: "Trovoada", 96: "Trovoada com granizo",
       99: "Trovoada com granizo forte"}
LUAS = ("Lua nova", "Lua crescente", "Quarto crescente", "Crescente gibosa",
        "Lua cheia", "Minguante gibosa", "Quarto minguante", "Lua minguante")


# ---------------------------------------------------------------- tempo e arquivos

def agora():
    f = os.environ.get("ELEMENTO_AGORA")
    if f:
        try:
            d = datetime.fromisoformat(f)
            return d if d.tzinfo else d.astimezone()
        except ValueError:
            pass
    return datetime.now().astimezone()


def iso(d):
    return d.isoformat(timespec="seconds")


def gravar_json(caminho, dados):
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    tmp = f"{caminho}.{os.getpid()}.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=1)
        f.write("\n")
    os.replace(tmp, caminho)


def ler_json(caminho):
    try:
        with open(caminho, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


# ---------------------------------------------------------------- lua

def lua(d):
    """Fase 0..1 (0 nova, 0.5 cheia) pelo período sinódico médio."""
    jd = d.timestamp() / 86400 + 2440587.5
    fase = ((jd - 2451550.1) / 29.530588853) % 1
    return round(fase, 3), LUAS[int(fase * 8 + 0.5) % 8]


# ---------------------------------------------------------------- máquina

_hw = {}


def _ler(caminho):
    try:
        with open(caminho) as f:
            return f.read().strip()
    except OSError:
        return None


def cpu_contadores():
    l = (_ler("/proc/stat") or "").split("\n", 1)[0].split()
    v = [int(x) for x in l[1:9]]
    return sum(v), v[3] + v[4]            # total, ocioso (idle + iowait)


def temp_cpu():
    if "temp" not in _hw:
        _hw["temp"] = None
        achados = {}
        try:
            for h in sorted(os.listdir("/sys/class/hwmon")):
                nome = _ler(f"/sys/class/hwmon/{h}/name")
                p = f"/sys/class/hwmon/{h}/temp1_input"
                if nome and os.path.exists(p):
                    achados[nome] = p
        except OSError:
            pass
        for nome in ("k10temp", "coretemp", "acpitz"):
            if nome in achados:
                _hw["temp"] = achados[nome]
                break
    v = _ler(_hw["temp"]) if _hw["temp"] else None
    try:
        return round(int(v) / 1000, 1)
    except (TypeError, ValueError):
        return None


def memoria_pct():
    tot = disp = None
    for l in (_ler("/proc/meminfo") or "").splitlines():
        if l.startswith("MemTotal:"):
            tot = int(l.split()[1])
        elif l.startswith("MemAvailable:"):
            disp = int(l.split()[1])
    return round(100 * (tot - disp) / tot, 1) if tot and disp is not None else None


def energia():
    """(bateria_pct, na_tomada). Sem bateria: (None, True)."""
    bat = tomada = None
    base = "/sys/class/power_supply"
    try:
        for n in os.listdir(base):
            tipo = _ler(f"{base}/{n}/type")
            if tipo == "Battery" and bat is None:
                try:
                    bat = int(_ler(f"{base}/{n}/capacity"))
                except (TypeError, ValueError):
                    pass
                if _ler(f"{base}/{n}/status") in ("Charging", "Full"):
                    tomada = True if tomada is None else tomada
            elif tipo == "Mains" and _ler(f"{base}/{n}/online") == "1":
                tomada = True
    except OSError:
        pass
    return bat, bool(tomada) if bat is not None else True


def contar_agentes():
    """Processos `claude` (comm), sem o host nativo do Chrome."""
    n = 0
    try:
        pids = [p for p in os.listdir("/proc") if p.isdigit()]
    except OSError:
        return 0
    for p in pids:
        try:
            if _ler(f"/proc/{p}/comm") != "claude":
                continue
            with open(f"/proc/{p}/cmdline", "rb") as f:
                if b"native-host" in f.read():
                    continue
            n += 1
        except OSError:
            pass
    return n


# ---------------------------------------------------------------- clima

def baixar(q):
    """Roda no processo filho: faz a consulta e imprime o JSON cru."""
    import urllib.parse
    import urllib.request
    req = urllib.request.Request(API + "?" + urllib.parse.urlencode(q),
                                 headers={"User-Agent": "dominios-elemento/1"})
    with urllib.request.urlopen(req, timeout=6) as r:
        sys.stdout.write(r.read().decode())


def buscar_clima(cache):
    """Consulta a API (respeitando 15 min entre tentativas). Devolve o cache atualizado."""
    t = time.time()
    if t - cache.get("tentado", 0) < CLIMA_CADA_S:
        return cache
    cache["tentado"] = t
    q = {"latitude": LAT, "longitude": LON, "timezone": "auto", "forecast_days": 2,
         "forecast_hours": 12, "wind_speed_unit": "kmh",
         "current": "temperature_2m,apparent_temperature,relative_humidity_2m,precipitation,"
                    "weather_code,wind_speed_10m,cloud_cover,is_day",
         "hourly": "weather_code", "daily": "sunrise,sunset"}
    try:
        # filho curto: o ssl/urllib sobem e morrem la, o laço fica magro
        r = subprocess.run([sys.executable, "-I", os.path.realpath(__file__), "_baixar", json.dumps(q)],
                           capture_output=True, text=True, timeout=15, check=True)
        d = json.loads(r.stdout)
        if "current" not in d:
            raise ValueError("resposta sem current")
        cache["dados"] = {"current": d["current"], "hourly": d.get("hourly", {}),
                          "daily": d.get("daily", {})}
        cache["buscado"] = t
        cache["erro"] = None
    except Exception as e:                       # nada derruba o laço
        cache["erro"] = f"{type(e).__name__}: {(getattr(e, 'stderr', '') or e)}"[-200:].strip()
    try:
        gravar_json(os.path.join(CACHE_DIR, "elemento-clima.json"), cache)
    except OSError:
        pass
    return cache


def montar_clima(cache, agora_):
    """Do cache bruto para (clima do contrato, extras internos) ou (None, {})."""
    d = cache.get("dados")
    if not d or agora_.timestamp() - cache.get("buscado", 0) > CLIMA_VALE_S:
        return None, {}
    c = d["current"]
    tz = agora_.tzinfo
    hoje = agora_.date().isoformat()
    nascer = por = None
    dia = d.get("daily", {})
    for i, dt in enumerate(dia.get("time", [])):
        if dt == hoje:
            try:
                nascer = datetime.fromisoformat(dia["sunrise"][i]).replace(tzinfo=tz)
                por = datetime.fromisoformat(dia["sunset"][i]).replace(tzinfo=tz)
            except (KeyError, IndexError, ValueError):
                pass
    e_dia = nascer <= agora_ < por if nascer and por else bool(c.get("is_day"))
    trov_h = None                                  # horas até a próxima trovoada prevista
    h = d.get("hourly", {})
    for ts, cod in zip(h.get("time", []), h.get("weather_code", [])):
        try:
            dh = (datetime.fromisoformat(ts).replace(tzinfo=tz) - agora_).total_seconds() / 3600
        except ValueError:
            continue
        if cod is not None and cod >= 95 and dh > -1:
            trov_h = max(dh, 0)
            break
    cod = int(c.get("weather_code", 0))
    fase, nome = lua(agora_)
    clima = {"temperatura_c": c.get("temperature_2m"), "sensacao_c": c.get("apparent_temperature"),
             "umidade": c.get("relative_humidity_2m"), "vento_kmh": c.get("wind_speed_10m"),
             "chuva_mm": c.get("precipitation"), "codigo": cod,
             "descricao": WMO.get(cod, "Tempo incerto"), "e_dia": e_dia,
             "nascer": iso(nascer) if nascer else None, "por": iso(por) if por else None,
             "lua_fase": fase, "lua_nome": nome,
             "atualizado": iso(datetime.fromtimestamp(cache["buscado"]).astimezone())}
    return clima, {"nuvens": c.get("cloud_cover") or 0, "trov_h": trov_h,
                   "nascer": nascer, "por": por}


# ---------------------------------------------------------------- regras

def sinais(ctx):
    """Devolve {elemento: [(peso, motivo, urgente), ...]}."""
    s = {e: [] for e in ELEMENTOS}
    cl, mq, ex = ctx["clima"], ctx["maquina"], ctx["extra"]
    h = ctx["hora"]
    por, nascer = ex.get("por"), ex.get("nascer")
    if cl:
        e_dia = cl["e_dia"]
    else:
        e_dia = 6 <= h < 18.5
    cod = cl["codigo"] if cl else 0
    vento = (cl["vento_kmh"] or 0) if cl else 0
    chuva = (cl["chuva_mm"] or 0) if cl else 0
    umid = (cl["umidade"] or 0) if cl else 0
    nuv = ex.get("nuvens", 0)
    sens = cl["sensacao_c"] if cl and cl["sensacao_c"] is not None else -99
    cpu, cpu_span = ctx["cpu_media"], ctx["cpu_span"]
    bat, tomada = mq["bateria_pct"], mq["na_tomada"]
    seco_calmo = bool(cl) and vento < 15 and chuva == 0 and cod <= 3 and umid < 80
    chove = cod in (61, 63, 65, 66, 67, 80, 81, 82) or (chuva >= 0.5 and cod not in (51, 53, 55))
    garoa = cod in (51, 53, 55, 56, 57)

    # agua
    if chove:
        s["agua"].append((90 if (chuva >= 2 or cod in (65, 67, 81, 82)) else 75, "Chove em Porto Alegre.", False))
    elif garoa or chuva > 0:
        s["agua"].append((70, "Garoa fina sobre Porto Alegre.", False))
    if umid >= 90 and nuv >= 70:
        s["agua"].append((60, f"O ar pesa: umidade em {umid:.0f}% e céu fechado.", False))
    elif umid >= 85 and nuv >= 60:
        s["agua"].append((45, f"Umidade em {umid:.0f}%: a água se anuncia.", False))

    # vento
    if vento >= 35:
        s["vento"].append((85, f"Ventania de {vento:.0f} km/h nos picos.", False))
    elif vento >= 25:
        s["vento"].append((65, f"O vento sopra a {vento:.0f} km/h.", False))
    elif cl and e_dia and cod <= 2 and 12 <= vento < 25:
        s["vento"].append((50, f"Dia claro e brisa de {vento:.0f} km/h.", False))
    if e_dia and 6 <= h < 10:
        s["vento"].append((45, "Manhã: o vento acorda os picos.", False))

    # fogo
    if bat is not None and not tomada:
        if bat < 10:
            s["fogo"].append((100, f"A chama morre: fôlego em {bat}%.", True))
        elif bat < 20:
            s["fogo"].append((80, f"O fôlego arde no fim: bateria em {bat}%.", False))
    t = mq["temp_c"]
    if t is not None:
        if t >= 85:
            s["fogo"].append((85, f"A forja está no limite: CPU a {t:.0f} °C.", True))
        elif t >= 75:
            s["fogo"].append((60, f"A forja esquenta: CPU a {t:.0f} °C.", False))
    if sens >= 32:
        s["fogo"].append((75, f"Calor de forja lá fora: sensação de {sens:.0f} °C.", False))
    elif sens >= 28:
        s["fogo"].append((50, f"O sol aperta: sensação de {sens:.0f} °C.", False))
    if por and abs((ctx["agora"] - por).total_seconds()) <= 40 * 60:
        s["fogo"].append((65, MOTIVO_POR, False))

    # eletricidade
    trov_h = ex.get("trov_h")
    if cl and cod >= 95:
        s["eletricidade"].append((100, "Trovoada sobre a cidade.", True))
    elif trov_h is not None:
        if trov_h <= 2:
            s["eletricidade"].append((70, "Trovoada a caminho nas próximas horas.", False))
        else:
            s["eletricidade"].append((45, "A previsão guarda uma trovoada.", False))
    if cpu is not None:
        if cpu >= 90 and cpu_span >= 100:
            s["eletricidade"].append((95, f"A torre estala: CPU no talo, {cpu:.0f}% por 2 min.", True))
        elif cpu >= 70:
            s["eletricidade"].append((70, f"Carga alta e sustentada: CPU em {cpu:.0f}%.", False))
    ag = ctx["agentes"]
    if ag >= 5:
        s["eletricidade"].append((70, f"{ag} familiares em campo: a torre vibra.", False))
    elif ag >= 3:
        s["eletricidade"].append((50, f"{ag} familiares invocados: faíscas no ar.", False))

    # terra
    if e_dia and 13 <= h < 18:
        s["terra"].append((45, "Tarde: as ruínas repousam ao sol.", False))
    if seco_calmo and e_dia:
        s["terra"].append((55 if 13 <= h < 18 else 30, "Tempo firme e seco: a terra descansa.", False))
    if cpu is not None and cpu < 15:
        s["terra"].append((25, "A máquina dorme: nada move a pedra.", False))
    if ctx["agora"].weekday() >= 5:
        s["terra"].append((25, "Fim de semana: dia de chão firme.", False))

    # mana pura
    if h < 5.5:
        s["mana-pura"].append((70, "Madrugada: a mana corre pura.", False))
    elif not e_dia and h >= 12:
        s["mana-pura"].append((55, "Noite: a biblioteca acende suas runas.", False))
    s["mana-pura"].append((20, "Nada se destaca: a mana se mantém pura.", False))
    return s


def candidatos(ctx):
    s = sinais(ctx)
    res = []
    for ordem, e in enumerate(ELEMENTOS):
        v = sorted(s[e], key=lambda x: -x[0])
        if not v:
            continue
        peso = min(100, v[0][0] + 0.25 * sum(x[0] for x in v[1:]))
        urg = any(x[2] for x in v) and peso >= URGENTE
        res.append({"elemento": e, "peso": round(peso, 1), "motivo": v[0][1], "_urg": urg, "_o": ordem})
    res.sort(key=lambda c: (-c["peso"], c["_o"]))
    return res


def decidir(est, cands, t, livre=False, por_ts=None):
    """Aplica histerese, regra contra retorno e pôr do sol grudento. Devolve o elemento escolhido."""
    atual = est.get("elemento")
    if atual not in ELEMENTOS:
        return cands[0]["elemento"]
    saiu = est.get("saiu", {})
    # sem voltar a um elemento que acabou de sair (menos de 1 h), salvo sinal urgente.
    # Soltar a mao volta ao automatico de verdade: ai a regra nao vale.
    ok = cands if livre else [c for c in cands if c["elemento"] == atual or c["_urg"]
                              or t - saiu.get(c["elemento"], 0) >= NAO_VOLTA_S]
    if not ok:
        return atual
    top = ok[0]
    if top["elemento"] == atual:
        return atual
    urg = next((c for c in ok if c["_urg"]), None)
    if urg and urg["elemento"] != atual:
        return urg["elemento"]
    if livre:
        return top["elemento"]
    if atual == "fogo" and est.get("por_grudado") and por_ts and t < por_ts:
        return atual                              # entrou pelo entardecer: fica até o sol se pôr
    if t - est.get("desde_ts", 0) < MIN_FICA_S:
        return atual
    peso = {c["elemento"]: c["peso"] for c in cands}
    if top["peso"] >= peso.get(atual, 0) + MARGEM:
        return top["elemento"]
    return atual


def trocar(est, novo, t, cands):
    """Registra a troca no estado (quem saiu, quando, e se o fogo veio do pôr do sol)."""
    antes = est.get("elemento")
    if antes in ELEMENTOS:
        est.setdefault("saiu", {})[antes] = t
    est["anterior"] = antes
    est["elemento"] = novo
    est["desde_ts"] = t
    mot = next((c["motivo"] for c in cands if c["elemento"] == novo), None)
    est["por_grudado"] = novo == "fogo" and mot == MOTIVO_POR


# ---------------------------------------------------------------- ciclo

class Motor:
    """Guarda o que vive entre ciclos: contadores de CPU e histórico."""

    def __init__(self):
        self.prev = None
        self.hist = []              # [(ts, pct)]
        self.agentes = (0, 0)       # (ts, n)
        self.cache = ler_json(os.path.join(CACHE_DIR, "elemento-clima.json")) or {}
        self.filhos = []

    def amostrar_cpu(self, t):
        tot, oc = cpu_contadores()
        if self.prev is None:
            time.sleep(0.3)
            self.prev = (tot, oc)
            tot, oc = cpu_contadores()
        dt, do = tot - self.prev[0], oc - self.prev[1]
        self.prev = (tot, oc)
        if dt > 0:
            self.hist.append((t, round(100 * (dt - do) / dt, 1)))
        self.hist = [x for x in self.hist if t - x[0] <= CPU_JANELA_S]

    def maquina(self, t):
        self.amostrar_cpu(t)
        if t - self.agentes[0] >= 60:
            self.agentes = (t, contar_agentes())
        bat, tomada = energia()
        cpu_pct = self.hist[-1][1] if self.hist else None
        return {"cpu_pct": cpu_pct, "temp_c": temp_cpu(), "mem_pct": memoria_pct(),
                "bateria_pct": bat, "na_tomada": tomada}

    def cpu_media(self):
        if not self.hist:
            return None, 0
        return (round(sum(p for _, p in self.hist) / len(self.hist), 1),
                self.hist[-1][0] - self.hist[0][0])

    def reaper(self):
        self.filhos = [p for p in self.filhos if p.poll() is None]

    def ganchos(self, novo, anterior):
        self.reaper()
        try:
            arqs = sorted(os.listdir(GANCHOS_DIR))
        except OSError:
            return
        tm = shutil.which("timeout")
        env = dict(os.environ, ELEMENTO=novo, ELEMENTO_ANTERIOR=anterior or "")
        for a in arqs:
            p = os.path.join(GANCHOS_DIR, a)
            if not (os.path.isfile(p) and os.access(p, os.X_OK)):
                continue
            cmd = [p, novo, anterior or ""]
            if tm:
                cmd = [tm, "-k", "2", str(GANCHO_LIMITE_S)] + cmd
            try:
                self.filhos.append(subprocess.Popen(
                    cmd, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL, start_new_session=True, env=env))
            except OSError:
                pass

    def ciclo(self, acao=None, nome=None):
        """Um ciclo completo. acao: None, 'travar', 'soltar'. Devolve o dict do contrato."""
        os.makedirs(ESTADO_DIR, exist_ok=True)
        with open(os.path.join(ESTADO_DIR, "elemento.lock"), "w") as lk:
            fcntl.flock(lk, fcntl.LOCK_EX)
            return self._ciclo(acao, nome)

    def _ciclo(self, acao, nome):
        d = agora()
        t = d.timestamp()
        est_path = os.path.join(ESTADO_DIR, "elemento-estado.json")
        est = ler_json(est_path) or {}
        if not self.hist:
            self.hist = [tuple(x) for x in est.get("hist", []) if t - x[0] <= CPU_JANELA_S and x[0] <= t]
        mq = self.maquina(t)
        self.cache = buscar_clima(self.cache) if not os.environ.get("ELEMENTO_SEM_CLIMA") else self.cache
        clima, extra = montar_clima(self.cache, d)
        cpu_m, span = self.cpu_media()
        ctx = {"agora": d, "hora": d.hour + d.minute / 60, "clima": clima, "extra": extra,
               "maquina": mq, "cpu_media": cpu_m, "cpu_span": span, "agentes": self.agentes[1]}
        cands = candidatos(ctx)
        antes = est.get("elemento")
        livre = False
        por_ts = extra["por"].timestamp() if extra.get("por") else None
        if acao == "travar":
            est["travado"] = True
            novo = nome
        elif acao == "soltar":
            est["travado"] = False
            livre = True
            novo = decidir(est, cands, t, livre=True, por_ts=por_ts)
        elif est.get("travado") and antes in ELEMENTOS:
            novo = antes
        else:
            novo = decidir(est, cands, t, por_ts=por_ts)
        mudou = novo != antes
        if mudou:
            trocar(est, novo, t, cands)
        est.setdefault("desde_ts", t)
        est.setdefault("travado", False)
        est["hist"] = [list(x) for x in self.hist]
        gravar_json(est_path, est)
        if est["travado"]:
            motivo = MOTIVO_FIXO
        else:
            motivo = next((c["motivo"] for c in cands if c["elemento"] == novo), None) \
                or MOTIVO_FICA.get(novo, MOTIVO_FICA["mana-pura"])
        out = {"elemento": novo, "motivo": motivo,
               "desde": iso(datetime.fromtimestamp(est["desde_ts"]).astimezone()),
               "travado": bool(est["travado"]), "anterior": est.get("anterior"),
               "candidatos": [{"elemento": c["elemento"], "peso": c["peso"], "motivo": c["motivo"]} for c in cands],
               "clima": clima,
               "maquina": {k: mq[k] for k in ("cpu_pct", "temp_c", "mem_pct", "bateria_pct", "na_tomada")},
               "atualizado": iso(d)}
        gravar_json(os.path.join(ESTADO_DIR, "elemento.json"), out)
        # ganchos so depois do elemento.json gravado (eles o leem). Travar e soltar sempre
        # avisam, mesmo sem trocar: o motivo e a trava mudam na nova aba e na barra.
        if mudou or acao in ("travar", "soltar"):
            self.ganchos(novo, antes if mudou else est.get("anterior"))
        return out


# ---------------------------------------------------------------- simulação

def bump(h, c, larg):
    return math.exp(-((h - c) / larg) ** 2)


def cenario(h):
    """Um dia plausível de novembro em Porto Alegre, dia útil, hora decimal h."""
    temp = 21 + 8 * math.sin((h - 9) / 24 * 2 * math.pi)
    sens = temp + 1.0
    umid = max(40, min(95, 90 - (temp - 13) * 2.7))
    vento = 7 + 6 * bump(h, 8, 1.5) + 9 * bump(h, 15.5, 3)
    cod, chuva, nuv = 1, 0.0, 30
    if 11 <= h < 12.5:
        cod, nuv = 2, 50
    if 20.5 <= h < 21.7:
        cod, chuva, nuv, umid = 53, 0.2, 90, 92
    if h < 5 or h >= 22.5:
        cod, nuv = 0, 15
    trov_h = None
    cpu = 22 + 20 * (9 <= h < 18) + 70 * (10.3 <= h < 10.8) + 55 * (15.5 <= h < 16.1)
    agentes = 1 + (h >= 9) + 2 * (10 <= h < 12) + (14 <= h < 17)
    na_tomada = not (18.2 <= h < 21.8)
    bat = 100 if na_tomada else max(8, round(100 - (h - 18.2) * 26))
    temp_cpu_ = 42 + 0.45 * (cpu - 22)
    return {"temp": temp, "sens": sens, "umid": umid, "vento": vento, "cod": cod, "chuva": chuva,
            "nuv": nuv, "trov_h": trov_h, "cpu": min(cpu, 100), "agentes": agentes,
            "na_tomada": na_tomada, "bat": bat, "tcpu": temp_cpu_}


def simular(passo_min=5):
    base = agora().replace(hour=0, minute=0, second=0, microsecond=0)
    nascer, por = base.replace(hour=5, minute=25), base.replace(hour=19, minute=25)
    est, linha, hist = {}, [], []
    for i in range(0, 24 * 60, passo_min):
        d = base + timedelta(minutes=i)
        h = i / 60
        c = cenario(h)
        e_dia = nascer <= d < por
        cl = {"temperatura_c": c["temp"], "sensacao_c": c["sens"], "umidade": c["umid"],
              "vento_kmh": c["vento"], "chuva_mm": c["chuva"], "codigo": c["cod"], "e_dia": e_dia}
        # CPU média de 2 min: amostras 'vizinhas' do cenário
        hist.append(c["cpu"])
        hist = hist[-(120 // (passo_min * 60) or 1):]
        ctx = {"agora": d, "hora": h, "clima": cl,
               "extra": {"nuvens": c["nuv"], "trov_h": c["trov_h"], "nascer": nascer, "por": por},
               "maquina": {"bateria_pct": c["bat"], "na_tomada": c["na_tomada"], "temp_c": c["tcpu"]},
               "cpu_media": c["cpu"], "cpu_span": 120, "agentes": c["agentes"]}
        cands = candidatos(ctx)
        novo = decidir(est, cands, d.timestamp(), por_ts=por.timestamp())
        if novo != est.get("elemento"):
            trocar(est, novo, d.timestamp(), cands)
            motivo = next(x["motivo"] for x in cands if x["elemento"] == novo)
            linha.append((d.strftime("%H:%M"), novo, motivo))
    return linha


# ---------------------------------------------------------------- terminal

def cor(e, txt, negrito=False):
    h = COR.get(e, "EDE7F6")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"\x1b[{'1;' if negrito else ''}38;2;{r};{g};{b}m{txt}\x1b[0m"


def suave(txt):
    return f"\x1b[38;2;176;167;196m{txt}\x1b[0m"


def barra(peso, e, n=20):
    k = round(n * peso / 100)
    return cor(e, "█" * k) + suave("░" * (n - k))


def mostrar(o):
    e = o["elemento"]
    print()
    print(f"  {cor(e, '◆ ' + NOMES[e].upper(), True)}" + (suave("   [travado]") if o["travado"] else ""))
    if herois.titulo(e):
        print(f"  {cor(e, herois.titulo(e))}")
    print(f"  {o['motivo']}")
    ant = f", antes {NOMES[o['anterior']]}" if o["anterior"] else ""
    print(suave(f"  desde {o['desde'][11:16]}{ant}"))
    print()
    print(suave("  Candidatos"))
    for c in o["candidatos"]:
        print(f"  {barra(c['peso'], c['elemento'])} {c['peso']:5.1f}  {cor(c['elemento'], NOMES[c['elemento']].ljust(12))} {suave(c['motivo'])}")
    cl = o["clima"]
    print()
    if cl:
        dia = "dia" if cl["e_dia"] else "noite"
        print(suave("  Clima em Porto Alegre"))
        print(f"  {cl['descricao']}, {cl['temperatura_c']:.1f} °C (sensação {cl['sensacao_c']:.1f}), "
              f"umidade {cl['umidade']}%, vento {cl['vento_kmh']:.0f} km/h, chuva {cl['chuva_mm']} mm")
        nas, por = (cl["nascer"] or "")[11:16], (cl["por"] or "")[11:16]
        print(suave(f"  {dia}, sol {nas} a {por}, {cl['lua_nome']} ({cl['lua_fase']:.2f}), consulta {cl['atualizado'][11:16]}"))
    else:
        print(suave("  Clima: sem rede, seguindo só com hora e máquina."))
    m = o["maquina"]
    bat = "sem bateria" if m["bateria_pct"] is None else \
        f"fôlego {m['bateria_pct']}% ({'na tomada' if m['na_tomada'] else 'na bateria'})"
    print()
    print(suave("  Máquina"))
    print(f"  CPU {m['cpu_pct']}%  {m['temp_c']} °C   mana {m['mem_pct']}%   {bat}")
    print()


def cmd_simular(args):
    linha = simular()
    print("\n  Simulação de 24 h (dia útil de novembro, sem gravar estado)\n")
    for h, e, m in linha:
        print(f"  {h}  {cor(e, '◆ ' + NOMES[e].ljust(13), True)} {suave(m)}")
    usados = sorted({e for _, e, _ in linha}, key=ELEMENTOS.index)
    print(f"\n  {len(usados)} elementos: " + ", ".join(cor(e, NOMES[e]) for e in usados))
    print("\n  " + " > ".join(f"{h} {e}" for h, e, _ in linha) + "\n")


def seguir(emitir, intervalo=30, parar=None):
    """Laço embutível: chama emitir(dict) a cada troca (e a cada minuto) até parar.is_set().
    Não usa stdout nem sinais. Erros de ciclo ou de emitir não derrubam o laço."""
    import threading
    parar = parar or threading.Event()
    m = Motor()
    ultimo_t, ultimo_chave = 0, None
    caminho = os.path.join(ESTADO_DIR, "elemento.json")

    def marca():
        try:
            return os.stat(caminho).st_mtime_ns
        except OSError:
            return None
    visto = None
    while not parar.is_set():
        try:
            o = m.ciclo()
            chave = (o["elemento"], o["travado"])
            t = time.time()
            if chave != ultimo_chave or t - ultimo_t >= 60:
                ultimo_chave, ultimo_t = chave, t
                emitir(o)
        except Exception as e:                      # nada derruba o laço
            try:
                sys.stderr.write(f"elemento: {type(e).__name__}: {e}\n")
                sys.stderr.flush()
            except Exception:
                pass
        visto = marca()
        # espera o intervalo, mas olha o elemento.json a cada 2 s: se outro processo o
        # gravou (`elemento travar` na linha de comando), reavalia na hora, para o HUD
        # nao ficar ate 30 s atras da barra e do terminal
        fim = time.monotonic() + max(1.0, intervalo)
        while not parar.is_set():
            resta = fim - time.monotonic()
            if resta <= 0:
                break
            parar.wait(min(2.0, resta))
            if marca() != visto:
                break
    return 0


def seguir_cli(intervalo):
    import threading
    parar = threading.Event()
    signal.signal(signal.SIGTERM, lambda *_: parar.set())
    signal.signal(signal.SIGINT, lambda *_: parar.set())

    def emitir(o):
        try:
            sys.stdout.write(json.dumps(o, ensure_ascii=False, separators=(",", ":")) + "\n")
            sys.stdout.flush()
        except BrokenPipeError:
            parar.set()
    return seguir(emitir, intervalo, parar)


def main(argv):
    cmd = argv[0] if argv else ""
    if cmd == "_baixar":
        baixar(json.loads(argv[1]))
        return 0
    if cmd in ("-h", "--help", "ajuda"):
        print(__doc__)
        return 0
    if cmd == "simular":
        cmd_simular(argv[1:])
        return 0
    if cmd == "seguir":
        iv = 30.0
        if "--intervalo" in argv:
            try:
                iv = max(2.0, float(argv[argv.index("--intervalo") + 1]))
            except (IndexError, ValueError):
                print("elemento: --intervalo pede um número de segundos", file=sys.stderr)
                return 2
        return seguir_cli(iv)
    m = Motor()
    if cmd in ("", "atualizar", "json"):
        o = m.ciclo()
        if cmd == "":
            mostrar(o)
        elif cmd == "json":
            print(json.dumps(o, ensure_ascii=False))
    elif cmd in ("travar", "proximo"):
        if cmd == "travar":
            nome = (argv[1] if len(argv) > 1 else "").lower().replace("á", "a").replace("_", "-")
            if nome == "mana":
                nome = "mana-pura"
            if nome not in ELEMENTOS:
                print("elemento: escolha entre " + ", ".join(ELEMENTOS), file=sys.stderr)
                return 2
        else:
            atual = (ler_json(os.path.join(ESTADO_DIR, "elemento.json")) or {}).get("elemento")
            nome = ELEMENTOS[(ELEMENTOS.index(atual) + 1) % len(ELEMENTOS)] if atual in ELEMENTOS else ELEMENTOS[0]
        mostrar(m.ciclo("travar", nome))
    elif cmd == "soltar":
        mostrar(m.ciclo("soltar"))
    else:
        print(__doc__)
        return 2
    time.sleep(0.05)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except BrokenPipeError:
        sys.exit(0)
