import QtQuick

// Divisor: filete de pixel com um florao no meio. Com `rotulo`, vira cabecalho de
// secao: o texto fica a esquerda e o filete segue ate a borda.
Item {
    id: divisor

    property string rotulo: ""
    readonly property var _janela: Hud.janelaDe(divisor)
    readonly property color _cor: Tema.alfa(_janela ? _janela.tintaSuave : Tema.textoSuave, 0.38)

    implicitWidth: 240
    implicitHeight: rotulo !== "" ? 24 : 15

    Rotulo {
        id: r
        visible: divisor.rotulo !== ""
        text: divisor.rotulo
        y: -4
    }
    Rectangle {
        x: divisor.rotulo !== "" ? Tema.grade(r.width + 9) : 0
        y: Tema.grade((parent.height - Tema.px) / 2)
        width: (divisor.rotulo !== "" ? parent.width : Tema.grade(parent.width / 2 - 15)) - x
        height: Tema.px
        color: divisor._cor
    }
    Rectangle {
        visible: divisor.rotulo === ""
        x: Tema.grade(parent.width / 2 + 15)
        y: Tema.grade((parent.height - Tema.px) / 2)
        width: parent.width - x
        height: Tema.px
        color: divisor._cor
    }
    Figura {
        visible: divisor.rotulo === ""
        fonte: "florao"
        x: Tema.grade(parent.width / 2 - width / 2)
        y: Tema.grade((parent.height - height) / 2)
    }
}
