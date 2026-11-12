"""Coletor da maquina: le /proc e /sys direto, sem subprocessos.

Maquina.amostra() devolve o dict do canal `maquina` do CONTRATO. CPU, rede e processos saem
de diferencas entre duas amostras, entao a primeira chamada depois de `zera()` so serve de base.
Os processos (top 5 por CPU, agrupados pelo nome) sao recalculados a cada PROC_CADA_S.
"""
import os
import time

PROC_CADA_S = 6.0
PAGINA_MB = (os.sysconf("SC_PAGE_SIZE") if hasattr(os, "sysconf") else 4096) / 1048576
TICKS = os.sysconf("SC_CLK_TCK")
PULA_REDE = ("lo", "docker", "veth", "br-", "virbr")


def _le(caminho):
    try:
        with open(caminho) as f:
            return f.read()
    except OSError:
        return None


def _int(caminho):
    v = _le(caminho)
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def meminfo():
    """(total_kb, disponivel_kb, swap_total_kb, swap_livre_kb)."""
    d = {}
    for l in (_le("/proc/meminfo") or "").splitlines():
        k, _, v = l.partition(":")
        if k in ("MemTotal", "MemAvailable", "SwapTotal", "SwapFree"):
            try:
                d[k] = int(v.split()[0])
            except (ValueError, IndexError):
                pass
    return d.get("MemTotal"), d.get("MemAvailable"), d.get("SwapTotal", 0), d.get("SwapFree", 0)


def disponivel_mb():
    t, d, _, _ = meminfo()
    return None if d is None else d / 1024


def energia():
    """{pct, tomada, min} da primeira bateria. Sem bateria: pct None e tomada True."""
    base = "/sys/class/power_supply"
    pct = minutos = None
    tomada = None
    try:
        nomes = sorted(os.listdir(base))
    except OSError:
        nomes = []
    for n in nomes:
        p = f"{base}/{n}"
        tipo = (_le(f"{p}/type") or "").strip()
        if tipo == "Battery" and pct is None:
            pct = _int(f"{p}/capacity")
            estado = (_le(f"{p}/status") or "").strip()
            if estado == "Discharging":
                tomada = False if tomada is None else tomada
                for agora_, taxa in (("energy_now", "power_now"), ("charge_now", "current_now")):
                    a, t = _int(f"{p}/{agora_}"), _int(f"{p}/{taxa}")
                    if a and t:
                        minutos = int(a / t * 60)
                        break
            elif estado in ("Charging", "Full"):
                tomada = True
        elif tipo == "Mains" and (_le(f"{p}/online") or "").strip() == "1":
            tomada = True
    if pct is None:
        return {"pct": None, "tomada": True, "min": None}
    return {"pct": pct, "tomada": bool(tomada) if tomada is not None else True, "min": minutos}


def _acha_sensor():
    cand = {}
    try:
        for h in sorted(os.listdir("/sys/class/hwmon")):
            nome = (_le(f"/sys/class/hwmon/{h}/name") or "").strip()
            p = f"/sys/class/hwmon/{h}/temp1_input"
            if os.path.exists(p):
                cand.setdefault(nome, p)
    except OSError:
        pass
    for nome in ("k10temp", "coretemp", "acpitz"):
        if nome in cand:
            return cand[nome]
    return None


class Maquina:
    def __init__(self):
        self._sensor = False          # False = ainda nao procurou
        self.zera()

    def zera(self):
        """Esquece as bases: a proxima amostra reinicia as diferencas."""
        self.cpu_prev = None
        self.rede_prev = None
        self.proc_prev = None
        self.proc_t = 0.0
        self.processos = []

    # ------------------------------------------------------------ leituras
    @staticmethod
    def _cpus():
        saida = []
        for l in (_le("/proc/stat") or "").splitlines():
            if not l.startswith("cpu"):
                break
            c = l.split()
            v = [int(x) for x in c[1:9]]
            saida.append((c[0], sum(v), v[3] + v[4]))
        return saida                  # [("cpu", total, ocioso), ("cpu0", ...), ...]

    @staticmethod
    def _rede():
        rx = tx = 0
        for l in (_le("/proc/net/dev") or "").splitlines()[2:]:
            nome, _, resto = l.partition(":")
            nome = nome.strip()
            if not resto or nome.startswith(PULA_REDE):
                continue
            c = resto.split()
            rx += int(c[0])
            tx += int(c[8])
        return rx, tx

    def _temp(self):
        if self._sensor is False:
            self._sensor = _acha_sensor()
        v = _int(self._sensor) if self._sensor else None
        return None if v is None else round(v / 1000, 1)

    @staticmethod
    def _tabela():
        """pid -> (nome, ticks de CPU, rss em paginas)."""
        t = {}
        try:
            it = os.scandir("/proc")
        except OSError:
            return t
        with it:
            for e in it:
                if not e.name.isdigit():
                    continue
                try:
                    with open(f"/proc/{e.name}/stat") as f:
                        s = f.read()
                    a, b = s.index("("), s.rindex(")")
                    c = s[b + 2:].split()
                    with open(f"/proc/{e.name}/statm") as f:
                        rss = int(f.read().split()[1])
                    t[int(e.name)] = (s[a + 1:b], int(c[11]) + int(c[12]), rss)
                except (OSError, ValueError, IndexError):
                    pass
        return t

    def _processos(self, agora_):
        tab = self._tabela()
        if self.proc_prev is not None and agora_ > self.proc_t:
            dt = agora_ - self.proc_t
            grupos = {}
            for pid, (nome, ticks, rss) in tab.items():
                ant = self.proc_prev.get(pid)
                d = ticks - ant if ant is not None else 0
                g = grupos.setdefault(nome, [0.0, 0.0])
                g[0] += 100.0 * d / TICKS / dt
                g[1] += rss * PAGINA_MB
            top = sorted(grupos.items(), key=lambda kv: (-kv[1][0], -kv[1][1]))[:5]
            self.processos = [{"nome": n, "cpu_pct": round(c, 1), "mem_mb": round(m)} for n, (c, m) in top]
        self.proc_prev = {pid: v[1] for pid, v in tab.items()}
        self.proc_t = agora_

    # ------------------------------------------------------------ amostra
    def amostra(self):
        agora_ = time.monotonic()
        cpus = self._cpus()
        cpu_pct, nucleos = None, []
        if self.cpu_prev is not None and len(cpus) == len(self.cpu_prev):
            pcts = []
            for (_, t1, o1), (_, t0, o0) in zip(cpus, self.cpu_prev):
                dt = t1 - t0
                pcts.append(round(100 * (dt - (o1 - o0)) / dt, 1) if dt > 0 else 0.0)
            cpu_pct, nucleos = pcts[0], pcts[1:]
        self.cpu_prev = cpus

        rede_b = rede_s = None
        rx, tx = self._rede()
        if self.rede_prev is not None:
            dt = agora_ - self.rede_prev[2]
            if dt > 0:
                rede_b = round(max(0, rx - self.rede_prev[0]) * 8 / 1000 / dt, 1)
                rede_s = round(max(0, tx - self.rede_prev[1]) * 8 / 1000 / dt, 1)
        self.rede_prev = (rx, tx, agora_)

        if self.proc_prev is None or agora_ - self.proc_t >= (PROC_CADA_S if self.processos else 1.0):
            self._processos(agora_)

        total, disp, st, sl = meminfo()
        usada = (total - disp) if total and disp is not None else None
        try:
            carga = float((_le("/proc/loadavg") or "").split()[0])
        except (IndexError, ValueError):
            carga = None
        try:
            v = os.statvfs("/")
            disco = round(100 * (1 - v.f_bavail / v.f_blocks), 1) if v.f_blocks else None
        except OSError:
            disco = None
        bat = energia()
        return {
            "cpu_pct": cpu_pct, "nucleos": nucleos, "carga1": carga,
            "mem_pct": round(100 * usada / total, 1) if usada is not None and total else None,
            "mem_usada_mb": round(usada / 1024) if usada is not None else None,
            "mem_total_mb": round(total / 1024) if total else None,
            "mem_disponivel_mb": round(disp / 1024) if disp is not None else None,
            "swap_pct": round(100 * (st - sl) / st, 1) if st else 0.0,
            "temp_c": self._temp(),
            "bateria_pct": bat["pct"], "na_tomada": bat["tomada"], "bateria_min": bat["min"],
            "rede_baixa_kbps": rede_b, "rede_sobe_kbps": rede_s,
            "disco_pct": disco, "processos": list(self.processos),
        }
