import QtQuick

// Texto em fonte de pixel cravado na grade (sem dica de fonte nem suavização), com
// sombra dura de 1 pixel de arte e, se pedir, contorno de 1 pixel nos quatro lados.
// O tamanho em px de tela é múltiplo da grade: passe `corpo` em pixels de arte.
Text {
    id: texto

    property int g: 3
    property real corpo: 8
    property real aperto: 0                 // entreletra em pixels de arte
    property bool sombra: true
    property bool contorno: false
    property color corSombra: Qt.rgba(0, 0, 0, 0.6)
    property color corContorno: Qt.rgba(0.04, 0.03, 0.07, 0.85)

    font.pixelSize: Math.round(corpo * g)
    font.kerning: false
    font.hintingPreference: Font.PreferNoHinting
    font.letterSpacing: aperto * g
    renderType: Text.NativeRendering
    antialiasing: false
    textFormat: Text.PlainText

    Repeater {
        model: texto.contorno ? [[-1, 0], [1, 0], [0, -1], [0, 1], [1, 1]] : []

        Text {
            required property var modelData

            z: -1
            x: modelData[0] * texto.g
            y: modelData[1] * texto.g
            width: texto.width
            height: texto.height
            text: texto.text
            font: texto.font
            color: texto.corContorno
            renderType: Text.NativeRendering
            antialiasing: false
            textFormat: Text.PlainText
            horizontalAlignment: texto.horizontalAlignment
        }
    }

    Text {
        visible: texto.sombra
        z: -1
        x: texto.g
        y: texto.g
        width: texto.width
        height: texto.height
        text: texto.text
        font: texto.font
        color: texto.corSombra
        renderType: Text.NativeRendering
        antialiasing: false
        textFormat: Text.PlainText
        horizontalAlignment: texto.horizontalAlignment
    }
}
