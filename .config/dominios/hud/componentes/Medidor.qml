import QtQuick

// Medidor: orbe de vidro com liquido ate o nivel `valor` (o medidor radial do
// grimorio). 99 x 99 px, mais a legenda embaixo se houver `rotulo`.
//
//   Medidor { valor: 0.62; texto: "62%"; rotulo: "Mana"; cor: Tema.corDe("agua") }
Item {
    id: medidor

    property real valor: 0                  // 0 a 1
    property color cor: Tema.destaque
    property string texto: ""               // no meio do orbe
    property string rotulo: ""              // embaixo

    readonly property int lado: 33          // pixels de arte (igual ao orbe-aro.png)
    readonly property real _raio: (lado - 1) / 2 - 2.7
    readonly property int _linhas: 2 * Math.floor(_raio) + 1
    property real _mostrado: Math.max(0, Math.min(1, valor))
    Behavior on _mostrado { NumberAnimation { duration: 800; easing.type: Easing.OutCubic } }
    readonly property int _cheias: Math.round(_mostrado * _linhas)

    implicitWidth: lado * Tema.px
    implicitHeight: lado * Tema.px + (rotulo !== "" ? 30 : 0)

    Item {
        id: vidro
        width: medidor.lado * Tema.px
        height: width
        anchors.horizontalCenter: parent.horizontalCenter

        Repeater {
            model: medidor._linhas
            Rectangle {
                required property int index
                readonly property int dy: index - Math.floor(medidor._raio)
                readonly property int meia: Math.floor(Math.sqrt(medidor._raio * medidor._raio - dy * dy))
                readonly property int deBaixo: medidor._linhas - 1 - index
                readonly property bool cheia: deBaixo < medidor._cheias
                x: ((medidor.lado - 1) / 2 - meia) * Tema.px
                y: ((medidor.lado - 1) / 2 + dy) * Tema.px
                width: (2 * meia + 1) * Tema.px
                height: Tema.px
                color: !cheia ? Qt.rgba(0, 0, 0, 0.5)
                    : deBaixo === medidor._cheias - 1 ? Tema.mistura(medidor.cor, "#ffffff", 0.45)
                    : Tema.mistura(medidor.cor, "#120c22", 0.42 * (1 - deBaixo / medidor._linhas))
            }
        }
        Figura { fonte: "orbe-luz" }
        Figura { fonte: "orbe-aro" }
        TextoPixel {
            visible: medidor.texto !== ""
            anchors.centerIn: parent
            anchors.verticalCenterOffset: 3
            tipo: "medio"
            sombra: true
            color: Tema.texto
            text: medidor.texto
        }
    }
    Rotulo {
        visible: medidor.rotulo !== ""
        text: medidor.rotulo
        anchors.horizontalCenter: parent.horizontalCenter
        y: vidro.height + 1
    }
}
