pragma ComponentBehavior: Bound
import QtQuick

// Moldura do painel. `t.estilo.moldura` escolhe o desenho:
//   "colchetes"  janela com colchetes nos cantos (Sistema)
//   "dupla"      filete duplo fino (Grimório)
//   "bloco"      contorno grosso com sombra dura deslocada (Maldição)
//   "nenhuma"    sem painel, o conteúdo fica solto sobre o papel (Setor 2814)
Item {
    id: moldura

    required property var t
    readonly property string tipo: t.estilo.moldura
    readonly property bool tem: tipo === "colchetes" || tipo === "dupla" || tipo === "bloco"

    // sombra dura
    Rectangle {
        visible: moldura.tipo === "bloco"
        x: moldura.t.px(12)
        y: moldura.t.px(12)
        width: moldura.width
        height: moldura.height
        color: moldura.t.cor.contorno
    }

    // brilho discreto em volta da janela
    Rectangle {
        visible: moldura.tipo === "colchetes" && moldura.t.estilo.brilho
        anchors.fill: parent
        anchors.margins: -moldura.t.px(4)
        radius: moldura.t.raio + moldura.t.px(4)
        color: Qt.alpha(moldura.t.cor.primaria, 0.0)
        border.width: moldura.t.px(4)
        border.color: Qt.alpha(moldura.t.cor.primaria, 0.10)
    }

    // corpo
    Rectangle {
        visible: moldura.tem
        anchors.fill: parent
        radius: moldura.t.raio
        color: Qt.alpha(moldura.t.cor.superficie, moldura.t.estilo.painel_alfa)
        border.width: moldura.t.borda
        border.color: moldura.tipo === "bloco" ? moldura.t.cor.primaria : moldura.t.cor.contorno
    }

    // filete interno
    Rectangle {
        readonly property int folga: moldura.t.px(7)

        visible: moldura.tipo === "dupla"
        anchors.fill: parent
        anchors.margins: folga
        radius: Math.max(0, moldura.t.raio - folga)
        color: Qt.alpha(moldura.t.cor.superficie, 0.0)
        border.width: moldura.t.borda
        border.color: Qt.alpha(moldura.t.cor.primaria, 0.45)
    }

    // colchetes: 0 alto-esquerda, 1 alto-direita, 2 baixo-direita, 3 baixo-esquerda
    Repeater {
        model: moldura.tipo === "colchetes" ? 4 : 0

        Item {
            id: canto

            required property int index
            readonly property bool direita: index === 1 || index === 2
            readonly property bool baixo: index >= 2
            readonly property int folga: moldura.t.px(8)
            readonly property int braco: moldura.t.px(26)
            readonly property int traco: moldura.t.borda + 1

            width: braco
            height: braco
            x: direita ? moldura.width + folga - braco : -folga
            y: baixo ? moldura.height + folga - braco : -folga

            Rectangle {
                width: canto.braco
                height: canto.traco
                y: canto.baixo ? canto.braco - canto.traco : 0
                color: moldura.t.cor.primaria
            }

            Rectangle {
                width: canto.traco
                height: canto.braco
                x: canto.direita ? canto.braco - canto.traco : 0
                color: moldura.t.cor.primaria
            }
        }
    }
}
