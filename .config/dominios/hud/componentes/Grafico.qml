import QtQuick

// Grafico: historico em colunas de pixel (1 coluna = 1 valor, 3 px de largura mais
// 3 px de vao; com `colado: true` nao ha vao).
//
//   Grafico { valores: [12, 40, 33, 80]; maximo: 100 }
//   tipo: "colunas" (cheio) ou "linha" (so o topo aceso sobre um corpo apagado)
Item {
    id: grafico

    property var valores: []
    property real minimo: 0
    property real maximo: 0                 // 0 = o maior valor da lista
    property string tipo: "colunas"
    property bool colado: false
    property color cor: Tema.destaque

    readonly property int _passo: (colado ? 1 : 2) * Tema.px
    readonly property int _cabem: Math.max(1, Math.floor((width + (colado ? 0 : Tema.px)) / _passo))
    readonly property var _vista: valores.length > _cabem ? valores.slice(valores.length - _cabem) : valores
    readonly property real _topo: {
        if (maximo > minimo)
            return maximo;
        let m = minimo + 1e-9;
        for (let i = 0; i < _vista.length; i++) m = Math.max(m, _vista[i]);
        return m;
    }

    implicitWidth: 240
    implicitHeight: 60

    Rectangle {                             // chao
        y: parent.height - Tema.px
        width: parent.width
        height: Tema.px
        color: Tema.alfa(grafico.cor, 0.22)
    }
    Repeater {
        model: grafico._vista.length
        Item {
            required property int index
            readonly property real fr: Math.max(0, Math.min(1, (grafico._vista[index] - grafico.minimo) / (grafico._topo - grafico.minimo)))
            readonly property int alt: Math.max(Tema.px, Tema.grade(fr * (grafico.height - Tema.px)))
            x: grafico.width - (grafico._vista.length - index) * grafico._passo + (grafico.colado ? 0 : Tema.px)
            y: grafico.height - Tema.px - alt
            width: Tema.px
            height: alt
            Rectangle {
                width: Tema.px
                height: parent.height
                color: grafico.tipo === "linha" ? Tema.alfa(grafico.cor, 0.28) : Tema.mistura(grafico.cor, "#120c22", 0.25)
            }
            Rectangle {                     // topo aceso
                width: Tema.px
                height: Tema.px
                color: Tema.mistura(grafico.cor, "#ffffff", 0.35)
            }
        }
    }
}
