"""Falas do grimorio para a caixa de dialogo (canal `dialogo`).

Cada evento tem varias falas; a mesma fala nao se repete em menos de REPETE_S.
Fala(evento, **campos) devolve o dict do contrato ou None (todas as variantes recentes).
"""
import itertools
import re
import time

REPETE_S = 5 * 60

NOMES = {"fogo": "Fogo", "agua": "Água", "terra": "Terra", "vento": "Vento",
         "eletricidade": "Eletricidade", "mana-pura": "Mana pura"}

# evento -> (titulo, tipo, retrato, som, [textos]); {campos} vem de cada evento
FALAS = {
    "nivel": ("Nível {n}", "recompensa", "conjurador", "nivel", [
        "A mana transborda. Teu nível agora é {n}.",
        "Mais uma página do grimório se abre: nível {n}.",
        "O círculo se alarga. Nível {n}, conjurador.",
    ]),
    "titulo": ("Novo título", "recompensa", "grimorio", "titulo", [
        "O grimório te nomeia: {nome}.",
        "Um nome novo foi gravado na capa: {nome}.",
        "As runas se rearranjam e te chamam de {nome}.",
    ]),
    "oficio": ("Ofício cumprido", "recompensa", "conjurador", "oficio-concluido", [
        "{titulo}. Mais uma runa gravada.",
        "{titulo} está feito. A mana agradece.",
        "Ofício selado: {titulo}.",
    ]),
    "dia_completo": ("Dia de ofícios completo", "recompensa", "grimorio", "dia-completo", [
        "Todos os ofícios do dia foram selados. {seq}",
        "O grimório fecha o dia em ouro. {seq}",
        "Nenhuma runa ficou apagada hoje. {seq}",
    ]),
    "penalidade": ("A mana se dissipou", "perigo", "grimorio", "penalidade", [
        "Um dia terminou com ofícios em aberto. Parte da mana se perdeu.",
        "As runas do dia esmaeceram sem serem seladas. A mana recua.",
        "O dia virou e os ofícios ficaram pendentes. O preço foi cobrado.",
    ]),
    "familiar_invocado": ("Familiar invocado", "info", "familiar", "familiar-invocado", [
        "Um familiar despertou em {projeto}.",
        "O círculo brilha: há um familiar novo em {projeto}.",
        "Responde ao chamado um familiar de {projeto}.",
    ]),
    "familiar_retornou": ("Familiar de volta", "info", "familiar", "familiar-concluido", [
        "O familiar de {projeto} retornou do trabalho.",
        "Terminada a missão, o familiar de {projeto} volta ao grimório.",
        "O familiar de {projeto} se dissolve em luz e traz notícias.",
    ]),
    "bateria20": ("Fôlego baixo", "perigo", "grimorio", "bateria-baixa", [
        "O fôlego está em {pct}%. Procura uma tomada.",
        "A reserva de fôlego cai a {pct}%. Convém recarregar.",
    ]),
    "bateria10": ("Fôlego por um fio", "perigo", "grimorio", "alerta", [
        "Só restam {pct}% de fôlego. O grimório vai se apagar.",
        "Fôlego em {pct}%. Liga a tomada antes que a luz se vá.",
    ]),
    "tomada_ligada": ("Fonte de mana", "info", "grimorio", "tomada-ligada", [
        "A fonte de mana foi conectada. O fôlego volta a subir.",
        "Tomada ligada: a energia flui de novo.",
        "O cabo encontrou a fonte. A reserva se recompõe.",
    ]),
    "tomada_desligada": ("Fonte desconectada", "info", "grimorio", "tomada-desligada", [
        "A fonte de mana foi desconectada. Agora vives do fôlego guardado.",
        "Tomada desligada: o grimório segue com a reserva.",
        "O cabo se soltou. Segue o caminho com o fôlego que tens.",
    ]),
}

# elemento: titulo e texto vem do motor (motivo); so o titulo varia por elemento
TITULO_ELEMENTO = {
    "fogo": "O Fogo desperta", "agua": "A Água se ergue", "terra": "A Terra responde",
    "vento": "O Vento muda", "eletricidade": "A tempestade chama", "mana-pura": "A mana se aquieta",
}

_contador = itertools.count(1)


class Dialogos:
    def __init__(self):
        self.usadas = {}            # texto -> instante

    def _livre(self, texto, t):
        self.usadas = {k: v for k, v in self.usadas.items() if t - v < REPETE_S}
        return texto not in self.usadas

    def _monta(self, chave, titulo, texto, retrato, tipo, som, t):
        self.usadas[texto] = t
        return {"id": f"{chave}-{next(_contador)}", "titulo": titulo, "texto": texto,
                "retrato": retrato, "tipo": tipo, "som": som}

    def fala(self, evento, **campos):
        t = time.monotonic()
        if evento == "elemento":
            e = campos.get("elemento", "mana-pura")
            motivo = campos.get("motivo") or "A mana muda de forma."
            if not self._livre(motivo, t):      # mesma fala em menos de 5 min: nao repete
                return None
            return self._monta(f"elemento-{e}", TITULO_ELEMENTO.get(e, NOMES.get(e, e)), motivo,
                               f"elemento-{e}", "elemento", f"elemento-{e}", t)
        titulo, tipo, retrato, som, textos = FALAS[evento]
        campos = {k: ("" if v is None else v) for k, v in campos.items()}
        for tx in textos:
            texto = tx.format(**campos).strip()
            if self._livre(texto, t):
                return self._monta(evento, titulo.format(**campos), texto, retrato, tipo, som, t)
        return None


def numero_do_nivel(texto):
    m = re.search(r"Nível (\d+)", texto or "")
    return int(m.group(1)) if m else None
