import QtQuick

// Texto: texto corrido, em fonte lisa (legivel por horas). A cor segue a janela:
// clara no vidro, escura no pergaminho.
Text {
    id: t

    property bool suave: false              // tom secundario
    property int tamanho: 18

    readonly property var _janela: Hud.janelaDe(t)

    color: _janela ? (suave ? _janela.tintaSuave : _janela.tinta) : (suave ? Tema.textoSuave : Tema.texto)
    font.family: Tema.fonteUi
    font.pixelSize: tamanho
    font.weight: Font.Medium
    wrapMode: Text.WordWrap
    textFormat: Text.PlainText
    lineHeight: 1.08
}
