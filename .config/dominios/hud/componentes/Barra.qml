import QtQuick

// Barra: barra segmentada de RPG. Os gomos acendem um a um quando o valor muda.
//
//   Barra { tipo: "vida"; valor: 0.72; rotulo: "Vida"; texto: "72/100" }
//
// tipo: "vida" (fogo), "mana" (agua), "folego" (vento), "xp" (eletricidade); sem
// tipo, a cor e a do elemento ativo. Cada gomo ocupa 12 px: a barra desenha
// quantos couberem na largura (largura ideal = 12n + 3).
Item {
    id: barra

    property real valor: 0                  // 0 a 1
    property string tipo: ""
    property color cor: tipo === "vida" ? Tema.corDe("fogo") : tipo === "mana" ? Tema.corDe("agua")
        : tipo === "folego" ? Tema.corDe("vento") : tipo === "xp" ? Tema.corDe("eletricidade") : Tema.destaque
    property string rotulo: ""              // a esquerda, acima da barra
    property string texto: ""               // a direita, acima da barra

    readonly property int gomos: Math.max(1, Math.floor((width / Tema.px - 1) / 4))
    readonly property int _largura: (gomos * 4 + 1) * Tema.px
    readonly property bool _cabeca: rotulo !== "" || texto !== ""
    property real _mostrado: Math.max(0, Math.min(1, valor))
    Behavior on _mostrado { NumberAnimation { duration: 650; easing.type: Easing.OutCubic } }
    readonly property int _acesos: valor > 0 ? Math.max(1, Math.round(_mostrado * gomos)) : 0

    implicitWidth: 243
    implicitHeight: (_cabeca ? 24 : 0) + 7 * Tema.px

    Rotulo {
        visible: barra.rotulo !== ""
        text: barra.rotulo
        y: -7
    }
    Numero {
        visible: barra.texto !== ""
        text: barra.texto
        tamanho: 15
        suave: true
        x: barra._largura - width
        y: 0
    }

    Item {
        y: barra._cabeca ? 24 : 0
        width: barra._largura
        height: 7 * Tema.px

        Fatias { anchors.fill: parent; fonte: "barra-moldura"; bordaEsquerda: 3; bordaDireita: 3 }
        Rectangle {                         // a cor, lisa; a luz e os vaos vem da mascara por cima
            x: Tema.px
            y: Tema.px
            width: Math.max(0, barra._acesos * 4 - 1) * Tema.px
            height: 5 * Tema.px
            color: barra.cor
        }
        Image {
            x: Tema.px
            y: Tema.px
            source: Tema.peca("barra-luz")
            smooth: false
            fillMode: Image.TileHorizontally
            horizontalAlignment: Image.AlignLeft
            width: barra.gomos * 4 - 1
            height: 5
            scale: Tema.px
            transformOrigin: Item.TopLeft
        }
    }
}
