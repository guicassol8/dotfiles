import QtQuick
import qs.componentes

// Ficha do Conjurador: retrato, nome, titulo, classe e rank; nivel e experiencia;
// folego (bateria), mana (memoria livre) e foco (folga da CPU); os cinco atributos
// e o ultimo feito. Dados: Nucleo.jogador e Nucleo.maquina.
Janela {
    id: ficha

    titulo: Tema.textos.ficha_titulo

    // exemplo usado ate o nucleo responder (ou se ele nao existir)
    readonly property var exemplo: ({
        nome: "CONJURADOR", titulo: "Aprendiz de Grimório", classe: "Invocador", nivel: 1, rank: "E",
        xp: 0, xp_proximo: 50, xp_hoje: 0, sequencia_dias: 0, pontos_livres: 0,
        atributos: { forca: 10, agilidade: 10, inteligencia: 10, vitalidade: 10, percepcao: 10 }, eventos: []
    })
    readonly property var j: Nucleo.jogador || exemplo
    readonly property var m: Nucleo.maquina
    readonly property var feito: j.eventos && j.eventos.length > 0 ? j.eventos[0] : null

    function nomeProprio(s) {               // "GUILHERME" -> "Guilherme" (gotico nao se le em caixa alta)
        return String(s || "").toLowerCase().replace(/(^|\s)\S/g, c => c.toUpperCase());
    }
    function milhar(n) {
        return String(Math.round(n || 0)).replace(/\B(?=(\d{3})+(?!\d))/g, ".");
    }

    Column {
        anchors.fill: parent
        spacing: 6

        Item {                              // cabecalho: retrato com o selo de rank, nome, titulo, classe e nivel
            width: parent.width
            height: rosto.height
            Retrato { id: rosto; fonte: "conjurador-32" }
            Selo { rank: ficha.j.rank || "E"; x: rosto.width - width + 9; y: rosto.height - height + 6 }
            Item {
                x: rosto.width + 21
                width: parent.width - x
                height: parent.height
                TextoPixel {
                    tipo: "gotico"
                    sombra: true
                    color: Tema.destaque
                    width: parent.width
                    elide: Text.ElideRight
                    text: ficha.nomeProprio(ficha.j.nome)
                    y: -12
                }
                Texto { y: 42; width: parent.width - 66; text: ficha.j.titulo || ""; elide: Text.ElideRight; maximumLineCount: 1; wrapMode: Text.NoWrap }
                Rotulo { y: 63; text: "Classe" }
                Texto { y: 93; text: ficha.j.classe || ""; tamanho: 17 }
                Rotulo { y: 57; text: "Nível"; anchors.right: parent.right }
                TextoPixel { tipo: "medio"; sombra: true; color: Tema.ouro; text: String(ficha.j.nivel || 1); anchors.right: parent.right; y: 66 }
            }
        }

        Barra {
            width: parent.width
            tipo: "xp"
            valor: ficha.j.xp_proximo > 0 ? ficha.j.xp / ficha.j.xp_proximo : 0
            rotulo: "Experiência"
            texto: ficha.milhar(ficha.j.xp) + " / " + ficha.milhar(ficha.j.xp_proximo)
        }
        Barra {
            width: parent.width
            tipo: "folego"
            valor: ficha.m ? ficha.m.bateria_pct / 100 : 0
            rotulo: Tema.textos.ficha_bateria
            texto: ficha.m ? Math.round(ficha.m.bateria_pct) + "%" + (ficha.m.na_tomada ? " na tomada" : "") : "..."
        }
        Barra {
            width: parent.width
            tipo: "mana"
            valor: ficha.m ? ficha.m.mem_disponivel_mb / ficha.m.mem_total_mb : 0
            rotulo: Tema.textos.ficha_memoria
            texto: ficha.m ? (ficha.m.mem_disponivel_mb / 1024).toFixed(1).replace(".", ",") + " GB livres" : "..."
        }
        Barra {
            width: parent.width
            cor: Tema.corDe("mana-pura")
            valor: ficha.m ? 1 - ficha.m.cpu_pct / 100 : 0
            rotulo: Tema.textos.ficha_cpu
            texto: ficha.m ? Math.round(ficha.m.cpu_pct) + "% em uso, " + Math.round(ficha.m.temp_c) + " °C" : "..."
        }

        Divisor { width: parent.width; rotulo: "Atributos" }
        Grid {
            columns: 2
            columnSpacing: 24
            rowSpacing: 0
            Repeater {
                model: [["Força", "forca"], ["Agilidade", "agilidade"], ["Inteligência", "inteligencia"],
                        ["Vitalidade", "vitalidade"], ["Percepção", "percepcao"], ["Sequência", ""]]
                Campo {
                    required property var modelData
                    width: (ficha.corpo.width - 24) / 2
                    rotulo: modelData[0]
                    numero: true
                    valor: modelData[1] !== "" ? String(ficha.j.atributos ? ficha.j.atributos[modelData[1]] : 0)
                        : (ficha.j.sequencia_dias || 0) + (ficha.j.sequencia_dias === 1 ? " dia" : " dias")
                    corValor: modelData[1] === "" ? Tema.ouro : ficha.tinta
                }
            }
        }
    }

    // ultimo feito, no rodape
    Texto {
        visible: ficha.feito !== null
        anchors.bottom: parent.bottom
        width: parent.width
        suave: true
        tamanho: 16
        elide: Text.ElideRight
        maximumLineCount: 1
        wrapMode: Text.NoWrap
        text: ficha.feito ? ficha.feito.texto + (ficha.feito.xp ? "  (+" + ficha.feito.xp + " XP)" : "") : ""
    }
}
