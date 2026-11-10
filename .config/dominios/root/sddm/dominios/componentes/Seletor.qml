import QtQuick

// Seletor cíclico (sessão). Setas, Enter ou Espaço trocam; com uma opção só, vira rótulo.
Item {
    id: seletor

    required property var t
    property string rotulo: ""
    property var nomes: []
    property int indice: 0
    readonly property bool varios: nomes.length > 1
    readonly property bool aceso: activeFocus || toque.containsMouse
    readonly property string atual: indice >= 0 && indice < nomes.length ? nomes[indice] : ""

    function proximo() {
        if (varios)
            indice = (indice + 1) % nomes.length
    }

    function anterior() {
        if (varios)
            indice = (indice + nomes.length - 1) % nomes.length
    }

    implicitWidth: linha.implicitWidth + t.px(30)
    implicitHeight: t.px(40)
    activeFocusOnTab: varios
    enabled: varios

    Keys.onLeftPressed: seletor.anterior()
    Keys.onUpPressed: seletor.anterior()
    Keys.onRightPressed: seletor.proximo()
    Keys.onDownPressed: seletor.proximo()
    Keys.onReturnPressed: seletor.proximo()
    Keys.onEnterPressed: seletor.proximo()
    Keys.onSpacePressed: seletor.proximo()

    Rectangle {
        anchors.fill: parent
        radius: Math.min(seletor.t.raio, height / 2)
        color: Qt.alpha(seletor.t.cor.superficie, seletor.aceso ? 0.85 : 0.0)
        border.width: seletor.t.borda
        border.color: seletor.activeFocus ? seletor.t.cor.primaria
                    : Qt.alpha(seletor.t.cor.contorno, toque.containsMouse ? 1.0 : 0.0)
    }

    Row {
        id: linha

        anchors.centerIn: parent
        spacing: seletor.t.px(10)

        Text {
            anchors.verticalCenter: parent.verticalCenter
            text: seletor.rotulo
            color: seletor.t.cor.texto_suave
            font.family: seletor.t.fonteRotulos
            font.weight: seletor.t.pesoRotulos
            font.variableAxes: seletor.t.eixosRotulos
            font.pixelSize: seletor.t.px(seletor.t.estilo.rotulos_tamanho + 1)
            font.letterSpacing: seletor.t.px(seletor.t.estilo.rotulos_tamanho + 1) * seletor.t.estilo.rotulos_espaco
        }

        Text {
            anchors.verticalCenter: parent.verticalCenter
            visible: seletor.varios
            text: seletor.t.txt.anterior
            color: seletor.t.cor.primaria
            font.family: seletor.t.ui
            font.pixelSize: seletor.t.px(seletor.t.estilo.texto_tamanho)
        }

        Text {
            anchors.verticalCenter: parent.verticalCenter
            text: seletor.atual
            color: seletor.aceso ? seletor.t.cor.primaria : seletor.t.cor.texto
            font.family: seletor.t.ui
            font.weight: seletor.t.pesoForte
            font.pixelSize: seletor.t.px(seletor.t.estilo.texto_tamanho - 2)
        }

        Text {
            anchors.verticalCenter: parent.verticalCenter
            visible: seletor.varios
            text: seletor.t.txt.proximo
            color: seletor.t.cor.primaria
            font.family: seletor.t.ui
            font.pixelSize: seletor.t.px(seletor.t.estilo.texto_tamanho)
        }
    }

    MouseArea {
        id: toque

        anchors.fill: parent
        hoverEnabled: true
        onClicked: {
            seletor.forceActiveFocus()
            seletor.proximo()
        }
    }
}
