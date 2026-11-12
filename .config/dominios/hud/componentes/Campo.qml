import QtQuick

// Campo: linha de ficha, rotulo em pixel a esquerda e valor liso a direita.
//   Campo { rotulo: "Classe"; valor: "Invocador" }
Item {
    id: campo

    property string rotulo: ""
    property string valor: ""
    property bool numero: false             // valor em mono
    property color corValor: _janela ? _janela.tinta : Tema.texto
    readonly property var _janela: Hud.janelaDe(campo)

    implicitWidth: 240
    implicitHeight: 24

    Rotulo { text: campo.rotulo; y: -4 }
    Text {
        text: campo.valor
        color: campo.corValor
        anchors.right: parent.right
        y: campo.numero ? 4 : 0
        font.family: campo.numero ? Tema.fonteMono : Tema.fonteUi
        font.pixelSize: campo.numero ? 17 : 19
        font.weight: Font.Medium
        textFormat: Text.PlainText
    }
}
