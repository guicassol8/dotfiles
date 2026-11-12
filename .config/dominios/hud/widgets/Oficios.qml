import QtQuick
import qs.componentes

// Oficios do Dia: o diario de missoes. Itens em duas colunas com caixa de marcar
// em pixel (clique alterna pelo Nucleo.oficio), a cor da caixa diz a categoria.
// Em cima a barra feitos/total e a sequencia de dias como chama; embaixo quanto
// falta para o dia acabar. Tudo feito: janela de ouro e selo "Dia completo".
// Dados: Nucleo.oficios.
Janela {
    id: diario

    titulo: "Ofícios do Dia"
    etiqueta: tem ? feitos + "/" + itens.length : ""
    variante: completo ? "ouro" : "normal"

    readonly property var o: Nucleo.oficios
    readonly property var itens: o && Array.isArray(o.itens) ? o.itens : []
    readonly property bool tem: itens.length > 0
    readonly property int sequencia: o ? (o.sequencia_dias || 0) : 0

    // clique ainda nao confirmado pelo nucleo: a caixa responde na hora
    property var marcas: ({})
    function feito(i) {
        const it = itens[i];
        if (!it)
            return false;
        return marcas[it.id] !== undefined ? marcas[it.id] : !!it.feito;
    }
    readonly property int feitos: {
        let n = 0;
        for (let i = 0; i < itens.length; i++)
            if (feito(i))
                n++;
        return n;
    }
    readonly property bool completo: tem && feitos === itens.length

    function alterna(i) {
        const it = itens[i];
        if (!it)
            return;
        const m = Object.assign({}, marcas);
        m[it.id] = !feito(i);
        marcas = m;
        Nucleo.oficio(it.id);
    }

    // categoria -> cor de elemento (ouro fica para a marca de feito)
    readonly property var categorias: ({ saude: "vento", estudo: "mana-pura", rotina: "agua" })
    function corCategoria(c) {
        return categorias[c] ? Tema.corDe(categorias[c]) : Tema.textoSuave;
    }

    // ---- contagem ate o fim do dia: o nucleo manda os segundos so quando muda
    property double recebido: Date.now()
    property double agora: Date.now()
    onOChanged: {
        marcas = ({});
        recebido = Date.now();
        agora = recebido;
    }
    Timer {
        interval: 30000
        repeat: true
        triggeredOnStart: true
        running: Hud.visivel && diario.o !== null
        onTriggered: diario.agora = Date.now()
    }
    readonly property real restante: o && o.termina_em_s !== undefined && o.termina_em_s !== null
        ? Math.max(0, o.termina_em_s - Math.max(0, agora - recebido) / 1000) : -1
    function duracao(s) {
        const min = Math.floor(s / 60), h = Math.floor(min / 60), m = min % 60;
        return h > 0 ? h + " h" + (m > 0 ? " " + m + " min" : "") : m + " min";
    }
    readonly property string fimDoDia: restante < 0 ? "" : restante < 60 ? "O dia está no fim"
        : "O dia termina em " + duracao(restante)

    // ---- peca: pixels de arte soltos (lista de [x, y] na grade)
    component Pixels: Item {
        id: px
        property var pontos: []
        property color cor
        Repeater {
            model: px.pontos
            Rectangle {
                required property var modelData
                x: modelData[0] * Tema.px
                y: modelData[1] * Tema.px
                width: Tema.px
                height: Tema.px
                color: px.cor
            }
        }
    }

    // ---- peca: caixa de marcar 7 x 7, cantos cortados, marca de ouro que transborda
    component Caixa: Item {
        id: cx
        property bool marcada: false
        property color cor: Tema.textoSuave
        property string categoria: ""
        // desenhos de 3 x 3 no meio: coracao (saude), cristal (estudo), anel (rotina)
        readonly property var simbolos: ({
            saude: [[0, 0], [2, 0], [0, 1], [1, 1], [2, 1], [1, 2]],
            estudo: [[1, 0], [0, 1], [1, 1], [2, 1], [1, 2]],
            rotina: [[0, 0], [1, 0], [2, 0], [0, 1], [2, 1], [0, 2], [1, 2], [2, 2]]
        })
        width: 7 * Tema.px
        height: 7 * Tema.px

        Image {                             // lampejo de ouro ao marcar
            id: lampejo
            source: Tema.peca("brilho-eletricidade")
            anchors.centerIn: parent
            width: 66
            height: 66
            opacity: 0
        }
        NumberAnimation { id: acende; target: lampejo; property: "opacity"; from: 0.95; to: 0; duration: 700; easing.type: Easing.OutQuad }
        onMarcadaChanged: if (marcada) acende.restart()

        Rectangle {                         // fundo fundo, como cavidade
            x: Tema.px; y: Tema.px; width: 5 * Tema.px; height: 5 * Tema.px
            color: cx.marcada ? Tema.alfa(Tema.ouro, 0.22) : Tema.alfa(Tema.fundo, 0.75)
        }
        Rectangle { x: Tema.px; y: Tema.px; width: 5 * Tema.px; height: Tema.px; color: Tema.alfa("#000000", 0.35) }
        Rectangle { x: Tema.px; y: 0; width: 5 * Tema.px; height: Tema.px; color: cx.cor }
        Rectangle { x: Tema.px; y: 6 * Tema.px; width: 5 * Tema.px; height: Tema.px; color: Tema.mistura(cx.cor, Tema.fundo, 0.35) }
        Rectangle { x: 0; y: Tema.px; width: Tema.px; height: 5 * Tema.px; color: cx.cor }
        Rectangle { x: 6 * Tema.px; y: Tema.px; width: Tema.px; height: 5 * Tema.px; color: Tema.mistura(cx.cor, Tema.fundo, 0.35) }

        Pixels {                            // simbolo da categoria, apagado, enquanto nao marca
            visible: !cx.marcada
            x: 2 * Tema.px; y: 2 * Tema.px
            opacity: 0.85
            cor: cx.cor
            pontos: cx.simbolos[cx.categoria] || []
        }
        Pixels {                            // sombra da marca
            visible: cx.marcada
            x: Tema.px; y: Tema.px
            cor: Tema.alfa("#000000", 0.55)
            pontos: [[6, -1], [5, 0], [6, 0], [4, 1], [5, 1], [1, 2], [3, 2], [4, 2], [1, 3], [2, 3], [3, 3], [2, 4]]
        }
        Pixels {                            // a marca, de ouro
            visible: cx.marcada
            cor: Tema.ouro
            pontos: [[6, -1], [7, -1], [5, 0], [6, 0], [4, 1], [5, 1], [1, 2], [3, 2], [4, 2], [1, 3], [2, 3], [3, 3], [2, 4]]
        }
        Pixels {                            // brilho na ponta
            visible: cx.marcada
            cor: Tema.mistura(Tema.ouro, "#ffffff", 0.6)
            pontos: [[7, -1], [1, 2]]
        }
    }

    // ================= com oficios
    Item {
        anchors.fill: parent
        visible: diario.tem

        // topo: progresso e sequencia de dias
        Barra {
            y: 2 * Tema.px
            width: Math.floor((parent.width - chama.width - 4 * Tema.px) / 12) * 12 + Tema.px
            valor: diario.tem ? diario.feitos / diario.itens.length : 0
            cor: diario.completo ? Tema.ouro : Tema.destaque
        }
        Row {
            id: chama
            anchors.right: parent.right
            height: 11 * Tema.px
            spacing: Tema.px
            Icone {
                nome: "fogo"
                opacity: diario.sequencia > 0 ? 1 : 0.4
            }
            TextoPixel {
                tipo: "medio"
                sombra: true
                color: diario.sequencia > 0 ? Tema.ouro : diario.tintaSuave
                text: String(diario.sequencia)
                anchors.verticalCenter: parent.verticalCenter
                anchors.verticalCenterOffset: -Tema.px
            }
            Rotulo {
                text: diario.sequencia === 1 ? "dia" : "dias"
                anchors.verticalCenter: parent.verticalCenter
                anchors.verticalCenterOffset: Tema.px
            }
        }

        // os itens, em duas colunas (rola se passar de oito)
        Flickable {
            id: rolo
            y: 13 * Tema.px
            width: parent.width
            height: 32 * Tema.px
            clip: contentHeight > height
            contentHeight: grade.height
            interactive: contentHeight > height
            boundsBehavior: Flickable.StopAtBounds

            Grid {
                id: grade
                width: rolo.width
                columns: 2
                rows: Math.ceil(diario.itens.length / 2)
                columnSpacing: 4 * Tema.px
                flow: Grid.TopToBottom
                Repeater {
                    model: diario.itens.length
                    Item {
                        id: linha
                        required property int index
                        readonly property var it: diario.itens[index] || ({})
                        readonly property bool marcada: diario.feito(index)

                        width: Tema.grade((grade.width - grade.columnSpacing) / 2)
                        height: 8 * Tema.px

                        Rectangle {
                            anchors.fill: parent
                            visible: area.containsMouse
                            color: Tema.alfa(diario.acento, 0.13)
                        }
                        Caixa {
                            x: Tema.px
                            y: Tema.grade((parent.height - height) / 2)
                            marcada: linha.marcada
                            cor: diario.corCategoria(linha.it.categoria)
                            categoria: linha.it.categoria || ""
                        }
                        Texto {
                            x: 11 * Tema.px
                            anchors.verticalCenter: parent.verticalCenter
                            width: parent.width - x - Tema.px
                            tamanho: 16
                            suave: linha.marcada
                            opacity: linha.marcada ? 0.7 : 1
                            font.strikeout: linha.marcada
                            text: linha.it.texto || ""
                            elide: Text.ElideRight
                            maximumLineCount: 1
                            wrapMode: Text.NoWrap
                        }
                        MouseArea {
                            id: area
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onClicked: diario.alterna(linha.index)
                        }
                    }
                }
            }
        }
        // rodape: quanto falta para o dia acabar e, com tudo feito, o selo
        Item {
            y: 45 * Tema.px
            width: parent.width
            height: parent.height - y

            Row {
                anchors.verticalCenter: parent.verticalCenter
                spacing: 2 * Tema.px
                visible: diario.fimDoDia !== ""
                Icone {
                    glifo: "\uf252"            // ampulheta
                    tamanho: 7
                    cor: diario.tintaSuave
                    anchors.verticalCenter: parent.verticalCenter
                }
                Texto {
                    anchors.verticalCenter: parent.verticalCenter
                    tamanho: 15
                    suave: true
                    text: diario.completo ? diario.fimDoDia.replace("O dia termina em", "Fim em") : diario.fimDoDia
                    maximumLineCount: 1
                    wrapMode: Text.NoWrap
                }
            }
            Figura {                        // tem mais embaixo: role a lista
                visible: rolo.interactive && rolo.contentY + rolo.height < rolo.contentHeight - 1
                fonte: "seta-baixo"
                anchors.right: selo.visible ? selo.left : parent.right
                anchors.rightMargin: selo.visible ? 3 * Tema.px : Tema.px
                anchors.verticalCenter: parent.verticalCenter
            }
            Item {
                id: selo
                visible: diario.completo
                anchors.right: parent.right
                anchors.verticalCenter: parent.verticalCenter
                width: Tema.grade(seloTexto.width) + 10 * Tema.px
                height: 11 * Tema.px
                Fatias { anchors.fill: parent; fonte: "placa-ouro"; bordaEsquerda: 5; bordaDireita: 5 }
                TextoPixel {
                    id: seloTexto
                    tipo: "titulo"
                    sombra: true
                    text: "DIA COMPLETO"
                    color: Tema.mistura(Tema.ouro, "#ffffff", 0.45)
                    x: 5 * Tema.px
                    y: selo.height / 2 - height / 2 - 1
                }
            }
        }
    }

    // ================= sem oficios
    Row {
        visible: !diario.tem
        anchors.centerIn: parent
        spacing: 6 * Tema.px
        Figura {
            fonte: "pergaminho"
            opacity: 0.75
            anchors.verticalCenter: parent.verticalCenter
        }
        Column {
            anchors.verticalCenter: parent.verticalCenter
            spacing: Tema.px
            Texto { text: "Nenhum ofício anotado"; tamanho: 19 }
            Texto {
                suave: true
                tamanho: 15
                text: diario.o === null ? "O diário de hoje ainda não abriu." : "As missões do dia aparecem aqui."
            }
        }
    }
}
