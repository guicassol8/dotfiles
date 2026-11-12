#!/usr/bin/env python3
"""nucleo: o processo unico de dados do HUD (contrato em hud/dados/CONTRATO.md).

  nucleo                  roda: uma linha JSON {"canal", "dados"} por mensagem no stdout
  nucleo --uma-vez        emite o estado de todos os canais e sai (sem som, sem gravar o jogador)
  nucleo --canal <nome>   so um canal (repetivel); sem som; com --uma-vez, uma vez so

Entrada (stdin, uma linha por comando): maquina 1|0, som <nome>, oficio <id>,
elemento travar <nome>, elemento soltar, sair. EOF e SIGTERM tambem encerram.
Canais: elemento jogador maquina familiares oficios cronica pagina dialogo pressao.

Ambiente de teste: DOMINIOS_ESTADO, DOMINIOS_MISSOES, DOMINIOS_AGORA, ELEMENTO_*, JOGADOR_*,
SOM_EVENTOS_TOCADOR (registro no lugar do audio), CRONICA_CACHE, CRONICA_GH (outro `gh`).
"""
import json
import os
import re
import signal
import sys
import threading
import time
from datetime import date, datetime, timedelta

AQUI = os.path.dirname(os.path.realpath(__file__))
RAIZ = os.path.dirname(os.path.dirname(AQUI))
CASA = os.path.expanduser("~")
sys.path.insert(0, AQUI)

CANAIS = ("elemento", "jogador", "maquina", "familiares", "oficios", "cronica", "pagina",
          "dialogo", "pressao")
LENTO_S = 5.0
MAQUINA_S = 2.0
OFICIOS_REEMITE_S = 600
DESCRICAO_CADA_S = 20.0
# pressao: (entra abaixo de, sai acima de) em MB de memoria disponivel
APERTADO = (900, 1100)
CRITICO = (500, 650)
NOVA_ABA_CANAIS = ("oficios", "jogador", "elemento", "pagina")
NOVA_ABA_DEBOUNCE_S = 2.0


def aviso(msg):
    try:
        sys.stderr.write(f"nucleo: {msg}\n")
        sys.stderr.flush()
    except Exception:
        pass


def carrega_script(nome, caminho):
    from importlib.machinery import SourceFileLoader
    from importlib.util import module_from_spec, spec_from_loader
    ld = SourceFileLoader(nome, caminho)
    mod = module_from_spec(spec_from_loader(nome, ld))
    ld.exec_module(mod)
    return mod


class Nucleo:
    def __init__(self, filtro=None, com_som=True):
        self.filtro = set(filtro) if filtro else None
        self.com_som = com_som
        self.parar = threading.Event()
        self.acorda_jogador = threading.Event()
        self.lig = threading.Event()                 # amostragem da maquina
        self.trava_saida = threading.Lock()
        self.trava = threading.RLock()                # estado compartilhado dos dialogos
        self.ultimo = {}
        self.filhos = []                              # Popen (gh)
        self.niri = []                                # pid do `niri msg`
        self.threads = []
        self.missao_mod = None
        self.ctx_agentes = None
        self.elem_prev = None
        self.jog_vistos = None
        self.fam = None                               # pid -> {...}; None antes da 1a leitura
        self.fam_cache = {}
        self.jsonl = {}
        self.energia_prev = None
        self.arma20 = self.arma10 = True
        self.pressao_nivel = None
        self.pagina_dia = None
        self.oficios_chave = None
        self.oficios_t = 0.0
        self.mtimes = {}
        self.nova_aba_prazo = None                    # monotonic em que a nova aba deve gravar
        self.nova_aba_ligada = False
        self.nova_aba_acorda = threading.Event()
        self.nova_aba_elem = None                     # elemento da ultima cena copiada
        from dialogo import Dialogos
        self.dialogos = Dialogos()

    # ------------------------------------------------------------ saida
    def quer(self, canal):
        return self.filtro is None or canal in self.filtro

    def precisa(self, canal):
        """Fontes que precisam rodar: as pedidas e as que alimentam o dialogo."""
        if self.quer(canal):
            return True
        return self.quer("dialogo") and canal in ("elemento", "jogador", "familiares", "energia")

    def emitir(self, canal, dados):
        self.ultimo[canal] = dados
        if canal in NOVA_ABA_CANAIS and self.nova_aba_ligada:
            self.nova_aba_prazo = time.monotonic() + NOVA_ABA_DEBOUNCE_S
            self.nova_aba_acorda.set()
        if not self.quer(canal):
            return
        linha = json.dumps({"canal": canal, "dados": dados}, ensure_ascii=False, separators=(",", ":"))
        with self.trava_saida:
            try:
                sys.stdout.write(linha + "\n")
                sys.stdout.flush()
            except (BrokenPipeError, ValueError):
                self.parar.set()
            except OSError:
                self.parar.set()

    def protegido(self, nome, fn, *a):
        try:
            return fn(*a)
        except Exception as ex:
            aviso(f"{nome}: {type(ex).__name__}: {ex}")
            return None

    # ------------------------------------------------------------ som e dialogo
    def mudo(self):
        rt = os.environ.get("XDG_RUNTIME_DIR")
        return bool(rt) and os.path.exists(os.path.join(rt, "dominios-silencio"))

    def toca(self, nome):
        if not self.com_som or not nome or self.mudo():
            return
        try:
            import som
            som.toca(nome)
        except Exception as ex:
            aviso(f"som {nome}: {ex}")

    def dizer(self, evento, **campos):
        with self.trava:
            d = self.dialogos.fala(evento, **campos)
        if d:
            self.emitir("dialogo", d)
            self.toca(d["som"])
        return d

    # ------------------------------------------------------------ elemento
    def on_elemento(self, o):
        prev, self.elem_prev = self.elem_prev, o
        self.emitir("elemento", o)
        if prev is not None and prev.get("elemento") != o.get("elemento"):
            self.dizer("elemento", elemento=o.get("elemento"), motivo=o.get("motivo"))

    # ------------------------------------------------------------ jogador
    def on_jogador(self, f):
        self.emitir("jogador", f)
        eventos = f.get("eventos") or []
        chaves = [(e.get("quando"), e.get("tipo"), e.get("texto")) for e in eventos]
        if self.jog_vistos is None:                   # arranque: nao despeja falas atrasadas
            self.jog_vistos = set(chaves)
            return
        novos = [e for e, c in zip(eventos, chaves) if c not in self.jog_vistos]
        self.jog_vistos |= set(chaves)
        if len(self.jog_vistos) > 2000:
            self.jog_vistos = set(chaves)
        falou = False
        for e in list(reversed(novos))[:4]:           # do mais antigo ao mais novo
            tipo, texto = e.get("tipo"), e.get("texto") or ""
            d = None
            if tipo == "nivel" and "reconheceu" not in texto:
                d = self.dizer("nivel", n=_nivel_do_texto(texto, f.get("nivel")))
            elif tipo == "titulo":
                d = self.dizer("titulo", nome=texto.split(":", 1)[-1].strip())
            elif tipo == "penalidade":
                d = self.dizer("penalidade")
            elif tipo == "missao" and texto.startswith("Dia de ofícios completo"):
                m = re.search(r"(\d+) em sequência", texto)
                d = self.dizer("dia_completo", seq=f"Sequência de {m.group(1)} dia(s)." if m else "")
            elif tipo == "missao" and texto.startswith("Ofício concluído"):
                d = self.dizer("oficio", titulo=texto.split(":", 1)[-1].strip())
            falou = falou or bool(d)
        if not falou and any((e.get("xp") or 0) > 0 and e.get("tipo") not in ("xp",) for e in novos):
            self.toca("xp")

    # ------------------------------------------------------------ oficios
    def missao(self):
        if self.missao_mod is None:
            self.missao_mod = carrega_script("dominios_missao", os.path.join(RAIZ, "bin", "missao"))
        return self.missao_mod

    def monta_oficios(self):
        m = self.missao()
        cfg = m.carrega_config()
        momento = m.agora()
        hoje = m.dia_da_missao(momento, cfg["virada"])
        estado = m.carrega_estado()
        feitas = m.feitas_em(estado, hoje)
        lista = m.do_dia(cfg, hoje)
        seq, _ = m.sequencias(cfg, estado, hoje)
        saude = ("acordar", "academia", "alongamento", "fruta", "mindfulness", "celular")
        estudo = ("leitura", "diario")
        itens = [{"id": x["id"], "texto": x["titulo"], "feito": x["id"] in feitas,
                  "categoria": "saude" if x["id"] in saude else "estudo" if x["id"] in estudo else "rotina"}
                 for x in lista]
        virada = datetime.combine(hoje + timedelta(days=1), datetime.min.time()) + timedelta(minutes=cfg["virada"])
        return {"titulo": "Ofícios do dia", "itens": itens, "feitos": sum(i["feito"] for i in itens),
                "total": len(itens), "sequencia_dias": seq,
                "termina_em_s": max(0, int((virada - momento).total_seconds()))}

    def confere_oficios(self, forcar=False):
        try:
            o = self.monta_oficios()
        except Exception as ex:
            aviso(f"oficios: {type(ex).__name__}: {ex}")
            return
        chave = json.dumps({k: v for k, v in o.items() if k != "termina_em_s"}, sort_keys=True)
        t = time.monotonic()
        if forcar or chave != self.oficios_chave or t - self.oficios_t >= OFICIOS_REEMITE_S:
            self.oficios_chave, self.oficios_t = chave, t
            self.emitir("oficios", o)

    def comando_oficio(self, ident):
        m = self.missao()
        cfg = m.carrega_config()
        hoje = m.dia_da_missao(m.agora(), cfg["virada"])
        alvo = m.resolve(ident, m.do_dia(cfg, hoje), cfg["missoes"])
        m.aplica(cfg, hoje, [alvo["id"]], "alternar")     # caminho oficial; sem celebra() (o dialogo cuida)
        self.confere_oficios(forcar=True)
        self.acorda_jogador.set()

    # ------------------------------------------------------------ familiares
    def sessoes(self):
        import jogador
        if self.ctx_agentes is None:
            self.ctx_agentes = jogador.Contexto()
        return jogador.sessoes_vivas(self.ctx_agentes)

    def _jsonl_da_sessao(self, cwd, agora_):
        enc = re.sub(r"[^A-Za-z0-9]", "-", cwd or "")
        pasta = os.path.join(CASA, ".claude", "projects", enc)
        c = self.jsonl.get(pasta)
        if c is None or agora_ - c[0] > 15:
            melhor = None
            try:
                with os.scandir(pasta) as it:
                    for e in it:
                        if e.name.endswith(".jsonl"):
                            mt = e.stat().st_mtime
                            if melhor is None or mt > melhor[0]:
                                melhor = (mt, e.path)
            except OSError:
                pass
            c = (agora_, melhor[1] if melhor else None)
            self.jsonl[pasta] = c
        return c[1]

    @staticmethod
    def _titulo_ai(caminho):
        try:
            with open(caminho, "rb") as f:
                f.seek(0, 2)
                tam = f.tell()
                f.seek(max(0, tam - 262144))
                dados = f.read()
        except OSError:
            return None
        i = dados.rfind(b'"type":"ai-title"')
        if i < 0:
            return None
        ini = dados.rfind(b"\n", 0, i) + 1
        fim = dados.find(b"\n", i)
        try:
            return json.loads(dados[ini:fim if fim >= 0 else None]).get("aiTitle")
        except ValueError:
            return None

    def monta_familiares(self):
        vivas = self.sessoes()
        if vivas is None:
            return None
        agora_ = time.time()
        lista = []
        for s in vivas:
            pid = str(s["pid"])
            c = self.fam_cache.get(pid)
            if c is None:
                c = self.fam_cache[pid] = {"desde": datetime.fromtimestamp(agora_ - s.get("tempo_s", 0))
                                           .astimezone().isoformat(timespec="seconds"),
                                           "desc": None, "desc_t": 0.0, "desc_m": 0.0}
            arq = self._jsonl_da_sessao(s.get("cwd"), agora_)
            idade = None
            if arq:
                try:
                    mt = os.stat(arq).st_mtime
                    idade = agora_ - mt
                    if mt != c["desc_m"] and agora_ - c["desc_t"] >= DESCRICAO_CADA_S:
                        c["desc_m"], c["desc_t"] = mt, agora_
                        c["desc"] = self._titulo_ai(arq) or c["desc"]
                except OSError:
                    pass
            estado = ("ocioso" if idade is None or idade > 900 else
                      "conjurando" if idade <= 45 else "aguardando")
            cwd = (s.get("cwd") or "").replace(CASA, "~", 1)
            lista.append({"id": pid, "projeto": s.get("projeto", "?"), "estado": estado,
                          "desde": c["desde"], "descricao": c["desc"] or cwd or s.get("projeto", "?"),
                          "_vive": s.get("tempo_s", 0)})
        for pid in [p for p in self.fam_cache if p not in {x["id"] for x in lista}]:
            del self.fam_cache[pid]
        lista.sort(key=lambda x: (x["desde"], x["id"]))
        return lista

    def confere_familiares(self):
        lista = self.monta_familiares()
        if lista is None:
            return
        atuais = {x["id"]: x for x in lista}
        if self.fam is not None:
            for pid, x in atuais.items():
                if pid not in self.fam:
                    self.dizer("familiar_invocado", projeto=x["projeto"])
            for pid, x in self.fam.items():
                if pid not in atuais and x["_vive"] >= 120:
                    self.dizer("familiar_retornou", projeto=x["projeto"])
        publico = [{k: v for k, v in x.items() if k != "_vive"} for x in lista]
        if self.fam is None or publico != self.ultimo_publico:
            self.emitir("familiares", publico)
            self.ultimo_publico = publico
        self.fam = atuais

    ultimo_publico = None

    # ------------------------------------------------------------ pressao, energia, pagina
    def confere_pressao(self, disp_mb):
        if disp_mb is None:
            return
        atual = self.pressao_nivel or "ok"
        if atual == "critico":
            novo = "critico" if disp_mb < CRITICO[1] else "apertado" if disp_mb < APERTADO[1] else "ok"
        elif atual == "apertado":
            novo = "critico" if disp_mb < CRITICO[0] else "apertado" if disp_mb < APERTADO[1] else "ok"
        else:
            novo = "critico" if disp_mb < CRITICO[0] else "apertado" if disp_mb < APERTADO[0] else "ok"
        if novo != self.pressao_nivel:
            self.pressao_nivel = novo
            self.emitir("pressao", {"nivel": novo})

    def confere_energia(self, bat):
        pct, tomada = bat["pct"], bat["tomada"]
        if pct is None:
            return
        prev, primeira = self.energia_prev, self.energia_prev is None
        self.energia_prev = (pct, tomada)
        if not primeira and prev[1] != tomada:
            self.dizer("tomada_ligada" if tomada else "tomada_desligada")
        if tomada or pct >= 25:
            self.arma20 = True
        if tomada or pct >= 15:
            self.arma10 = True
        if tomada:
            return
        if pct < 10 and self.arma10:
            self.arma10 = self.arma20 = False
            if not primeira:                      # no arranque so arma, sem fala atrasada
                self.dizer("bateria10", pct=pct)
        elif pct < 20 and self.arma20:
            self.arma20 = False
            if not primeira:
                self.dizer("bateria20", pct=pct)

    def confere_pagina(self, forcar=False):
        hoje = date.today()
        if forcar or hoje != self.pagina_dia:
            self.pagina_dia = hoje
            self.emitir("pagina", frase_do_dia(hoje))

    def muda_arquivo(self, caminho):
        try:
            m = os.stat(caminho).st_mtime_ns
        except OSError:
            m = None
        velho = self.mtimes.get(caminho, 0)
        self.mtimes[caminho] = m
        return velho != 0 and m != velho

    # ------------------------------------------------------------ threads
    def laco_lento(self):
        import maquina
        estado_dir = os.environ.get("DOMINIOS_ESTADO") or os.path.join(CASA, ".local/state/dominios")
        arq_missoes = os.path.join(estado_dir, "missoes.json")
        arq_toml = os.environ.get("DOMINIOS_MISSOES") or os.path.join(RAIZ, "missoes.toml")
        self.mtimes[arq_missoes] = self.mtimes[arq_toml] = 0
        self.muda_arquivo(arq_missoes)
        self.muda_arquivo(arq_toml)
        primeira = True
        while not self.parar.is_set():
            if self.precisa("familiares"):
                self.protegido("familiares", self.confere_familiares)
            if self.precisa("pressao"):
                self.protegido("pressao", lambda: self.confere_pressao(maquina.disponivel_mb()))
            if self.precisa("energia") or self.quer("dialogo"):
                self.protegido("energia", lambda: self.confere_energia(maquina.energia()))
            if self.quer("pagina"):
                self.protegido("pagina", self.confere_pagina)
            if self.quer("oficios"):
                mudou = self.muda_arquivo(arq_missoes) | self.muda_arquivo(arq_toml)
                if primeira or mudou:
                    self.protegido("oficios", self.confere_oficios)
                    if mudou:
                        self.acorda_jogador.set()
                else:
                    self.protegido("oficios", self.confere_oficios)
            primeira = False
            self.parar.wait(LENTO_S)

    def laco_nova_aba(self):
        """Mantem chrome-nova-aba/estado.json em dia (so no dominio grimorio), com debounce."""
        import nova_aba
        primeira = True
        while not self.parar.is_set():
            if primeira:
                self.parar.wait(NOVA_ABA_DEBOUNCE_S + 1)   # deixa os canais emitirem a 1a vez
                self.nova_aba_prazo = None
            else:
                self.nova_aba_acorda.wait()
                self.nova_aba_acorda.clear()
                while self.nova_aba_prazo and not self.parar.is_set():
                    falta = self.nova_aba_prazo - time.monotonic()
                    if falta <= 0:
                        break
                    self.parar.wait(falta)
                self.nova_aba_prazo = None
            if self.parar.is_set():
                break
            r = self.protegido("nova_aba", nova_aba.atualiza_do_nucleo, dict(self.ultimo), self.nova_aba_elem)
            if r and (primeira or r[1] or r[2]):
                est, _, copiar = r
                self.protegido("nova_aba", nova_aba.grava, est, copiar)
                if copiar:
                    self.nova_aba_elem = est["elemento"]
            primeira = False

    def laco_maquina(self):
        import maquina
        m = maquina.Maquina()
        while not self.parar.is_set():
            if not self.lig.wait(0.5):
                continue
            m.zera()
            self.protegido("maquina", m.amostra)            # base das diferencas
            if self.parar.wait(0.6):
                break
            while self.lig.is_set() and not self.parar.is_set():
                d = self.protegido("maquina", m.amostra)
                if d:
                    self.emitir("maquina", d)
                    self.confere_pressao(d["mem_disponivel_mb"])
                self.parar.wait(MAQUINA_S)
            m.zera()

    def laco_cronica(self):
        from cronica import Cronica
        c = Cronica(self.filhos.append)
        self.emitir("cronica", c.dados)
        while not self.parar.is_set():
            if self.parar.wait(max(1.0, c.quando_vence() - time.time())):
                break
            if self.protegido("cronica", c.atualiza):
                self.emitir("cronica", c.dados)

    def laco_elemento(self):
        import elemento
        elemento.seguir(self.on_elemento, 30, self.parar)

    def laco_jogador(self):
        import jogador
        jogador.seguir(self.on_jogador, 60, self.parar, self.acorda_jogador)

    def laco_niri(self):
        import som
        som.embutido(self.parar, self.niri)

    def laco_stdin(self):
        try:
            for linha in sys.stdin:
                self.protegido("comando", self.comando, linha.strip())
                if self.parar.is_set():
                    return
        except (OSError, ValueError):
            pass
        self.parar.set()                                     # EOF

    def comando(self, linha):
        p = linha.split()
        if not p:
            return
        c = p[0].lower()
        if c == "sair":
            self.parar.set()
        elif c == "maquina" and len(p) > 1:
            if p[1] == "1":
                self.lig.set()
            elif p[1] == "0":
                self.lig.clear()
        elif c == "som" and len(p) > 1:
            self.toca(p[1])
        elif c == "oficio" and len(p) > 1:
            self.comando_oficio(p[1])
        elif c == "elemento" and len(p) > 1:
            import elemento
            if p[1] == "travar" and len(p) > 2:
                nome = p[2].lower().replace("á", "a").replace("_", "-")
                nome = "mana-pura" if nome == "mana" else nome
                if nome in elemento.ELEMENTOS:
                    self.on_elemento(elemento.Motor().ciclo("travar", nome))
            elif p[1] == "soltar":
                self.on_elemento(elemento.Motor().ciclo("soltar"))
        else:
            aviso(f"comando desconhecido: {linha[:40]}")

    # ------------------------------------------------------------ ciclo de vida
    def inicia(self, alvo, nome):
        t = threading.Thread(target=lambda: self.protegido(nome, alvo), name=nome, daemon=True)
        t.start()
        self.threads.append(t)

    def roda(self):
        for sig in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
            signal.signal(sig, lambda *_: self.parar.set())
        if self.precisa("elemento"):
            self.inicia(self.laco_elemento, "elemento")
        if self.precisa("jogador"):
            self.inicia(self.laco_jogador, "jogador")
        self.inicia(self.laco_lento, "lento")
        if self.filtro is None:
            self.nova_aba_ligada = True
            self.inicia(self.laco_nova_aba, "nova_aba")
        if self.quer("maquina"):
            self.inicia(self.laco_maquina, "maquina")
            if self.filtro is not None:
                self.lig.set()                              # depurando o canal: liga sozinho
        if self.quer("cronica"):
            self.inicia(self.laco_cronica, "cronica")
        if self.filtro is None and self.com_som:
            self.inicia(self.laco_niri, "niri")
        self.inicia(self.laco_stdin, "stdin")
        self.parar.wait()
        self.encerra()
        return 0

    def encerra(self):
        self.parar.set()
        self.acorda_jogador.set()
        for p in list(self.filhos):
            try:
                if p.poll() is None:
                    os.killpg(p.pid, signal.SIGTERM)
            except (OSError, ProcessLookupError):
                pass
        try:
            import som
            som.mata(self.niri)
        except Exception:
            pass
        for t in self.threads:
            if t.name != "stdin":
                t.join(timeout=1.5)
        try:
            sys.stdout.flush()
        except Exception:
            pass

    # ------------------------------------------------------------ --uma-vez
    def uma_vez(self):
        import elemento
        import jogador
        import maquina
        from cronica import Cronica
        if self.precisa("elemento") or self.quer("dialogo"):
            o = self.protegido("elemento", elemento.Motor().ciclo)
            if o:
                self.emitir("elemento", o)
        if self.quer("jogador"):
            f = self.protegido("jogador", lambda: jogador.ciclo(jogador.Contexto(), gravar=False))
            if f:
                self.emitir("jogador", f)
        if self.quer("maquina"):
            m = maquina.Maquina()
            m.amostra()
            time.sleep(1.1)
            self.emitir("maquina", m.amostra())
        if self.quer("familiares"):
            lista = self.protegido("familiares", self.monta_familiares)
            if lista is not None:
                self.emitir("familiares", [{k: v for k, v in x.items() if k != "_vive"} for x in lista])
        if self.quer("oficios"):
            self.confere_oficios(True)
        if self.quer("cronica"):
            c = Cronica(self.filhos.append)
            self.protegido("cronica", c.atualiza)
            self.emitir("cronica", c.dados)
        if self.quer("pagina"):
            self.confere_pagina(True)
        if self.quer("pressao"):
            self.confere_pressao(maquina.disponivel_mb())
            if "pressao" not in self.ultimo:
                self.emitir("pressao", {"nivel": "ok"})
        if self.quer("dialogo"):
            e = self.ultimo.get("elemento") or {}
            self.com_som = False
            self.dizer("elemento", elemento=e.get("elemento", "mana-pura"),
                       motivo=e.get("motivo") or "A mana se mantém pura.")
        self.encerra()
        return 0


def _nivel_do_texto(texto, padrao):
    from dialogo import numero_do_nivel
    return numero_do_nivel(texto) or padrao


_frases = []


def frase_do_dia(dia):
    import tomllib
    if not _frases:
        try:
            with open(os.path.join(AQUI, "frases.toml"), "rb") as f:
                _frases.extend(x for x in tomllib.load(f).get("frase", []) if isinstance(x, dict) and x.get("texto"))
        except (OSError, ValueError):
            pass
    if not _frases:
        return {"texto": "O obstáculo é o caminho.", "autor": "Marco Aurélio", "obra": "Meditações"}
    f = _frases[(dia.timetuple().tm_yday - 1) % len(_frases)]
    return {"texto": f["texto"], "autor": f.get("autor") or "", "obra": f.get("obra") or None}


def main(argv):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    if "-h" in argv or "--help" in argv:
        print(__doc__)
        return 0
    filtro = []
    i = 0
    while i < len(argv):
        if argv[i] == "--canal":
            if i + 1 >= len(argv) or argv[i + 1] not in CANAIS:
                aviso("--canal pede um destes: " + " ".join(CANAIS))
                return 2
            filtro.append(argv[i + 1])
            i += 1
        elif argv[i] != "--uma-vez":
            aviso(f"argumento desconhecido: {argv[i]}")
            return 2
        i += 1
    n = Nucleo(filtro or None, com_som=not filtro and "--uma-vez" not in argv)
    return n.uma_vez() if "--uma-vez" in argv else n.roda()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
