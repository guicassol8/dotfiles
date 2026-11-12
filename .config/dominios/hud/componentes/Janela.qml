import QtQuick

// Janela: a janela de menu do grimorio. Vidro escuro translucido, moldura de pixel
// em 9 fatias com um florao em cada canto (a gema e da cor do elemento ativo) e a
// placa de titulo em pixel. Todo widget da mesa tem uma Janela na raiz.
//
//   Janela {
//       titulo: "Ofícios do Dia"
//       etiqueta: "3/7"
//       Column { anchors.fill: parent; spacing: 9; ... }     // vai para dentro de `corpo`
//   }
//
// variante: "normal", "pergaminho" (papel claro, para citacao), "ouro"
// (recompensa) ou "perigo". No pergaminho a tinta e escura: os componentes de
// texto ja se ajustam sozinhos; se pintar algo a mao, use janela.tinta,
// janela.tintaSuave e janela.acento.
Item {
    id: janela

    property string titulo: ""
    property string etiqueta: ""            // texto curto na placa da direita
    property string variante: "normal"
    property bool gemas: !papel
    property int respiro: Tema.respiro      // folga entre a moldura e o conteudo
    property bool aberta: true              // false: dobra e some
    property int atraso: 0                  // ms antes de abrir (cascata)

    default property alias conteudo: corpo.data
    readonly property alias corpo: corpo

    readonly property bool ehJanela: true
    readonly property bool papel: variante === "pergaminho"
    readonly property string _var: ["normal", "pergaminho", "ouro", "perigo"].indexOf(variante) >= 0 ? variante : "normal"
    readonly property color tinta: papel ? Tema.tintaPapel : Tema.texto
    readonly property color tintaSuave: papel ? Tema.tintaPapelSuave : Tema.textoSuave
    readonly property color acento: _var === "ouro" ? Tema.ouro : _var === "perigo" ? Tema.perigo
        : papel ? Tema.mistura(Tema.destaque, Tema.tintaPapel, 0.5) : Tema.destaque

    signal abriu()

    implicitWidth: 420
    implicitHeight: 240

    // ---- abrir e fechar: a janela desdobra do meio em degraus, como menu de RPG
    readonly property int _topo: titulo !== "" ? 2 * Tema.px : 0
    property real abertura: 0
    readonly property int _altura: Math.max(30 * Tema.px, Tema.grade((height - _topo) * abertura / 2) * 2)
    readonly property bool _pronta: abertura >= 1

    function _move() {
        anim.stop();
        anim.to = aberta ? 1 : 0;
        espera.duration = aberta ? atraso : 0;
        anim.duration = aberta ? 260 : 140;
        seq.start();
    }
    onAbertaChanged: _move()
    Component.onCompleted: {
        if (aberta)
            Qt.callLater(_move);
    }
    Connections {                           // o grimorio abriu por cima das janelas: desdobra de novo, em cascata
        target: Hud
        function onAbriu() {
            if (janela.aberta) {
                janela.abertura = 0;
                janela._move();
            }
        }
    }
    SequentialAnimation {
        id: seq
        PauseAnimation { id: espera; duration: 0 }
        NumberAnimation { id: anim; target: janela; property: "abertura"; easing.type: Easing.OutCubic }
        ScriptAction { script: if (janela.aberta) janela.abriu() }
    }

    Item {
        id: quadro
        visible: janela.abertura > 0
        x: 0
        y: janela._topo + Tema.grade((janela.height - janela._topo - janela._altura) / 2)
        width: janela.width
        height: janela._altura

        BorderImage {                       // sombra projetada, lisa: profundidade atras do pixel
            source: Tema.peca("sombra")
            x: -18
            y: -9
            width: parent.width + 36
            height: parent.height + 36
            border { left: 30; right: 30; top: 30; bottom: 30 }
            opacity: janela.papel ? 0.55 : 0.7
        }
        Rectangle {                         // vidro
            visible: !janela.papel
            anchors.fill: parent
            anchors.margins: 2 * Tema.px
            gradient: Gradient {
                GradientStop {
                    position: 0
                    color: Tema.alfa(Tema.mistura(Tema.superficie2, janela._var === "normal" ? Tema.fundo : janela.acento, janela._var === "normal" ? 0.45 : 0.16), 0.84)
                }
                GradientStop {
                    position: 1
                    color: Tema.alfa(Tema.mistura(Tema.fundo, janela._var === "normal" ? Tema.fundo : janela.acento, 0.06), 0.9)
                }
            }
        }
        Fatias {
            anchors.fill: parent
            fonte: "moldura-" + janela._var
            borda: 12
        }
        Repeater {                          // gemas dos quatro cantos
            model: janela.gemas ? 4 : 0
            Gema {
                required property int index
                x: index % 2 === 0 ? 2 * Tema.px : quadro.width - 7 * Tema.px
                y: index < 2 ? 2 * Tema.px : quadro.height - 7 * Tema.px
                brilho: janela._pronta ? 0.5 : 0.9
            }
        }
    }

    // ---- placa de titulo, montada na linha de cima da moldura
    Item {
        id: placa
        visible: janela.titulo !== "" && janela.abertura > 0
        x: 10 * Tema.px
        y: quadro.y - 2 * Tema.px
        width: Tema.grade(nome.width) + 10 * Tema.px
        height: 11 * Tema.px
        Fatias { anchors.fill: parent; fonte: "placa-" + janela._var; bordaEsquerda: 5; bordaDireita: 5 }
        TextoPixel {
            id: nome
            tipo: "titulo"
            sombra: !janela.papel
            text: janela.titulo
            font.capitalization: Font.AllUppercase
            color: janela.papel ? Tema.tintaPapel : janela._var === "normal" ? Tema.texto : Tema.mistura(janela.acento, "#ffffff", 0.55)
            x: 5 * Tema.px
            y: placa.height / 2 - height / 2 - 1
        }
    }
    Item {
        id: placaDireita
        // some se o titulo for comprido demais para caber os dois
        visible: janela.etiqueta !== "" && janela.abertura > 0 && (janela.titulo === "" || x > placa.x + placa.width + 2 * Tema.px)
        x: janela.width - width - 10 * Tema.px
        y: quadro.y - 2 * Tema.px
        width: Tema.grade(marca.width) + 8 * Tema.px
        height: 11 * Tema.px
        Fatias { anchors.fill: parent; fonte: "placa-" + janela._var; bordaEsquerda: 5; bordaDireita: 5 }
        TextoPixel {
            id: marca
            tipo: "rotulo"
            text: janela.etiqueta
            font.capitalization: Font.AllUppercase
            color: janela.papel ? Tema.tintaPapelSuave : janela.acento
            x: 4 * Tema.px
            y: placaDireita.height / 2 - height / 2 - 1
        }
    }

    // ---- conteudo
    Item {
        id: corpo
        x: 6 * Tema.px + janela.respiro
        y: janela._topo + (janela.titulo !== "" || janela.etiqueta !== "" ? 10 : 6) * Tema.px + janela.respiro
        width: janela.width - 2 * x
        height: janela.height - y - 6 * Tema.px - janela.respiro
        visible: janela._pronta
    }
}
