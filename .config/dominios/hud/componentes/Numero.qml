import QtQuick

// Numero: valores em fonte mono lisa, para as colunas nao dancarem.
Text {
    id: t

    property bool suave: false
    property int tamanho: 17

    readonly property var _janela: Hud.janelaDe(t)

    color: _janela ? (suave ? _janela.tintaSuave : _janela.tinta) : (suave ? Tema.textoSuave : Tema.texto)
    font.family: Tema.fonteMono
    font.pixelSize: tamanho
    font.features: { "tnum": 1 }
    textFormat: Text.PlainText
}
