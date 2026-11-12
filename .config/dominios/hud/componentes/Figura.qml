import QtQuick

// Figura: imagem de pixel art, sem suavizar (o "Sprite" da base: o QtQuick ja tem
// um tipo chamado Sprite e ele ganha a disputa de nomes, por isso o nome e outro). `fonte` pode ser:
//   - um nome do acervo (hud/sprites/indice.json): "mago", "moeda", "monstro-slime"...
//   - uma peca da casa (hud/arte/*.png): "gema-fogo", "simbolo-agua", "florao"...
//   - um caminho de PNG ("~/...", "/..."), com `quadros` se for folha de quadros
// Com `quadros` > 1 a imagem e uma tira de quadros lado a lado e `fps` anima (por
// relogio, nunca a 60 fps; para sozinha quando a mesa nao esta a vista).
//
// Tamanho: `escala` multiplica a grade (1 = 3 px de tela por pixel de arte). Os
// sprites do acervo sao grandes (32 a 34 px de arte): na grade viram ilustracao de
// ~100 px. Para usa-los como icone pequeno, `ponto: 1` (1 px de tela por pixel).
//
//   Figura { fonte: "mago"; fps: 4 }             retrato animado, 96 px
//   Figura { fonte: "moeda"; ponto: 1 }          icone de 34 px
Item {
    id: sprite

    property string fonte: ""
    property int quadros: _ref ? _ref.quadros : 1
    property int quadro: 0
    property real fps: 0                // 0 = parado
    property bool rodando: true
    property int escala: 1              // multiplo inteiro da grade
    property int ponto: 0               // px de tela por pixel de arte; 0 = Tema.px * escala

    readonly property var _ref: Tema.sprite(fonte)
    readonly property int fator: ponto > 0 ? ponto : Tema.px * Math.max(1, escala)
    readonly property bool pronto: img.status === Image.Ready
    readonly property int _tira: _ref ? _ref.l * Math.max(1, quadros) : img.implicitWidth
    readonly property int _alta: _ref ? _ref.a : img.implicitHeight

    implicitWidth: _tira / Math.max(1, quadros) * fator
    implicitHeight: _alta * fator
    clip: quadros > 1

    Image {
        id: img
        source: sprite._ref ? sprite._ref.url : Tema.peca(sprite.fonte)
        sourceClipRect: sprite._ref ? Qt.rect(sprite._ref.x, sprite._ref.y, sprite._ref.l * Math.max(1, sprite.quadros), sprite._ref.a) : undefined
        smooth: false
        mipmap: false
        x: -(sprite.quadro % Math.max(1, sprite.quadros)) * sprite.width
        width: sprite._tira * sprite.fator
        height: sprite._alta * sprite.fator
    }

    Timer {
        interval: sprite.fps > 0 ? Math.max(40, 1000 / sprite.fps) : 1000
        repeat: true
        running: sprite.fps > 0 && sprite.quadros > 1 && sprite.rodando && sprite.visible && Hud.animar
        onTriggered: sprite.quadro = (sprite.quadro + 1) % sprite.quadros
    }
}
