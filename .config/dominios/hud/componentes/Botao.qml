import QtQuick

// Botao: placa de pixel clicavel. So funciona onde a casca deixa o clique passar
// (dentro da area de um widget da mesa).
//   Botao { texto: "Concluir"; onClicado: Nucleo.oficio(id) }
Item {
    id: botao

    property string texto: ""
    property string icone: ""               // nome de Icone, opcional
    property bool ativo: true
    property bool marcado: false            // estado ligado
    signal clicado()

    readonly property bool _dentro: toque.containsMouse && ativo
    implicitWidth: Tema.grade(linha.width) + 10 * Tema.px
    implicitHeight: 11 * Tema.px
    opacity: ativo ? 1 : 0.45

    Item {
        width: parent.width
        height: parent.height
        y: toque.pressed && botao.ativo ? Tema.px : 0
        Fatias { anchors.fill: parent; fonte: botao.marcado ? "placa-ouro" : "placa-normal"; bordaEsquerda: 5; bordaDireita: 5 }
        Rectangle {
            visible: botao._dentro
            x: 2 * Tema.px
            y: 2 * Tema.px
            width: parent.width - 4 * Tema.px
            height: parent.height - 4 * Tema.px
            color: Tema.alfa(Tema.destaque, 0.22)
        }
        Row {
            id: linha
            anchors.centerIn: parent
            anchors.verticalCenterOffset: -1
            spacing: 2 * Tema.px
            Icone {
                visible: botao.icone !== ""
                nome: botao.icone
                tamanho: 7
                cor: Tema.texto
                anchors.verticalCenter: parent.verticalCenter
                anchors.verticalCenterOffset: 1
            }
            TextoPixel {
                visible: botao.texto !== ""
                tipo: "rotulo"
                text: botao.texto
                color: botao._dentro ? Tema.mistura(Tema.destaque, "#ffffff", 0.5) : Tema.texto
                font.capitalization: Font.AllUppercase
            }
        }
    }
    MouseArea {
        id: toque
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: botao.ativo ? Qt.PointingHandCursor : Qt.ArrowCursor
        onClicked: if (botao.ativo) botao.clicado()
    }
}
