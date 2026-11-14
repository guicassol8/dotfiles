import QtQuick
import qs.componentes

// Elemento: os seis elementos em roda, com o heroi do ativo no meio. O ativo fica aceso e maior; os outros ficam
// apagados, com a intensidade do peso que tiveram como candidatos. Clique trava num
// elemento; clique no ativo travado solta. Quando o ativo muda, a luz passa de um
// para o outro (animacao por evento, nada roda parado). Dados: Nucleo.elemento.
Janela {
    id: elemento

    titulo: "Elemento"
    respiro: 0

    readonly property var e: Nucleo.elemento
    readonly property string ativo: Tema.elemento
    readonly property bool travado: e ? e.travado === true : false
    readonly property var candidatos: e && e.candidatos ? e.candidatos : []
    readonly property real maiorPeso: {
        let m = 0;
        for (let i = 0; i < candidatos.length; i++)
            m = Math.max(m, candidatos[i].peso || 0);
        return m;
    }
    function pesoDe(nome) {
        for (let i = 0; i < candidatos.length; i++)
            if (candidatos[i].elemento === nome)
                return candidatos[i].peso || 0;
        return 0;
    }
    function clicou(nome) {
        if (nome === ativo && travado)
            Nucleo.soltarElemento();
        else
            Nucleo.travarElemento(nome);
    }

    // posicao dos seis na roda (hexagono deitado), a partir do centro
    readonly property var posicoes: [[-45, -33], [45, -33], [78, 0], [45, 33], [-45, 33], [-78, 0]]

    Item {
        id: roda
        width: parent.width
        height: 96

        // aro do hexagono, em pontos de pixel entre os seis lugares
        Repeater {
            model: 6
            Item {
                required property int index
                readonly property var a: elemento.posicoes[index]
                readonly property var b: elemento.posicoes[(index + 1) % 6]
                Repeater {
                    model: 4
                    Rectangle {
                        required property int index
                        readonly property real t: (index + 1) / 5
                        x: Tema.grade(roda.width / 2 + parent.a[0] + (parent.b[0] - parent.a[0]) * t - Tema.px / 2)
                        y: Tema.grade(roda.height / 2 + parent.a[1] + (parent.b[1] - parent.a[1]) * t - Tema.px / 2)
                        width: Tema.px
                        height: Tema.px
                        color: Tema.alfa(elemento.tintaSuave, 0.35)
                    }
                }
            }
        }

        // heroi do ativo no meio da roda (corpo de 64 px de arte, 1:1), com a luz do elemento atras;
        // sem a arte dele, o medalhao do elemento
        Item {
            id: centro
            width: 66
            height: 66
            x: Tema.grade(roda.width / 2 - width / 2)
            y: Tema.grade(roda.height / 2 - height / 2)
            Image {
                source: Tema.peca("brilho-" + elemento.ativo)
                anchors.centerIn: parent
                width: 150
                height: 150
                opacity: 0.55
            }
            Figura {
                id: medalhao
                fonte: (Tema.temHeroi(elemento.ativo) ? "heroi-" : "emblema-") + elemento.ativo + "-64"
                ponto: 1
                anchors.centerIn: parent
                onFonteChanged: { opacity = 0; surge.restart(); }
                NumberAnimation { id: surge; target: medalhao; property: "opacity"; to: 1; duration: 600; easing.type: Easing.OutQuad }
            }
            MouseArea {
                anchors.fill: parent
                cursorShape: elemento.travado ? Qt.PointingHandCursor : Qt.ArrowCursor
                onClicked: if (elemento.travado) Nucleo.soltarElemento()
            }
        }

        Repeater {
            model: Tema.nomesElementos
            Item {
                id: lugar
                required property int index
                required property string modelData
                readonly property bool ativo: modelData === elemento.ativo
                readonly property real base: 0.28 + 0.45 * (elemento.maiorPeso > 0 ? elemento.pesoDe(modelData) / elemento.maiorPeso : 0)
                // luz: 1 no ativo, 0 nos outros; muda com uma passagem
                property real luz: ativo ? 1 : 0
                Behavior on luz { NumberAnimation { duration: 700; easing.type: Easing.InOutQuad } }

                width: 48
                height: 42
                x: Tema.grade(roda.width / 2 + elemento.posicoes[index][0] - width / 2)
                y: Tema.grade(roda.height / 2 + elemento.posicoes[index][1] - height / 2)
                z: ativo ? 2 : 1

                Image {                         // halo liso atras do aceso
                    visible: lugar.luz > 0.01
                    source: visible ? Tema.peca("brilho-" + lugar.modelData) : ""
                    anchors.centerIn: parent
                    width: 72
                    height: 72
                    opacity: 0.6 * lugar.luz
                }
                Figura {                        // simbolo da casa: apagado com a intensidade do peso, aceso no ativo
                    fonte: "simbolo-" + lugar.modelData
                    anchors.centerIn: parent
                    opacity: Math.min(1, (lugar.base + (alvo.containsMouse ? 0.25 : 0)) * (1 - lugar.luz) + lugar.luz)
                    visible: opacity > 0.01
                }
                MouseArea {
                    id: alvo
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: elemento.clicou(lugar.modelData)
                }
            }
        }
    }

    // nome e motivo
    Item {
        y: roda.height + 3
        width: parent.width
        height: parent.height - y

        Item {
            id: nome
            anchors.horizontalCenter: parent.horizontalCenter
            width: tituloNome.width + (elemento.travado ? 27 : 0)
            height: 18
            TextoPixel {
                id: tituloNome
                tipo: text.length > 9 ? "rotulo" : "titulo"
                sombra: true
                color: Tema.destaque
                text: Tema.rotulosElementos[elemento.ativo] || ""
                y: 0
            }
            Icone {
                visible: elemento.travado
                glifo: ""
                tamanho: 6
                cor: Tema.ouro
                x: tituloNome.width + 9
                y: -3
            }
        }
        Texto {
            y: 24
            width: parent.width
            horizontalAlignment: Text.AlignHCenter
            tamanho: 13
            suave: true
            maximumLineCount: 2
            elide: Text.ElideRight
            lineHeight: 1.0
            text: Tema.motivoElemento
        }
    }
}
