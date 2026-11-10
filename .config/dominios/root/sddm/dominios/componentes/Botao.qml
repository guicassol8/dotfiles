import QtQuick

// Botão de texto com foco de teclado (Enter ou Espaço acionam).
Item {
    id: botao

    required property var t
    property string rotulo: ""
    readonly property bool aceso: activeFocus || toque.containsMouse

    signal acionado()

    implicitWidth: texto.implicitWidth + t.px(30)
    implicitHeight: t.px(40)
    activeFocusOnTab: true
    opacity: enabled ? 1.0 : 0.38

    Keys.onReturnPressed: botao.acionado()
    Keys.onEnterPressed: botao.acionado()
    Keys.onSpacePressed: botao.acionado()

    Rectangle {
        anchors.fill: parent
        radius: Math.min(botao.t.raio, height / 2)
        color: Qt.alpha(botao.t.cor.superficie, botao.aceso ? 0.85 : 0.0)
        border.width: botao.t.borda
        border.color: botao.activeFocus ? botao.t.cor.primaria
                    : Qt.alpha(botao.t.cor.contorno, toque.containsMouse ? 1.0 : 0.0)
    }

    Text {
        id: texto

        anchors.centerIn: parent
        text: botao.rotulo
        color: botao.aceso ? botao.t.cor.primaria : botao.t.cor.texto_suave
        font.family: botao.t.fonteRotulos
        font.weight: botao.t.pesoRotulos
        font.variableAxes: botao.t.eixosRotulos
        font.pixelSize: botao.t.px(botao.t.estilo.rotulos_tamanho + 1)
        font.letterSpacing: botao.t.px(botao.t.estilo.rotulos_tamanho + 1) * botao.t.estilo.rotulos_espaco
    }

    MouseArea {
        id: toque

        anchors.fill: parent
        hoverEnabled: true
        onClicked: {
            botao.forceActiveFocus()
            botao.acionado()
        }
    }
}
