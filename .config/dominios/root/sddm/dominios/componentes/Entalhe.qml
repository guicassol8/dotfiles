import QtQuick

// Retângulo de pixel art: cantos entalhados de 1 pixel de arte (3 px de tela),
// sem arredondar nem suavizar. `g` é o pixel de arte em px de tela.
Item {
    id: entalhe

    property color cor: "black"
    property int g: 3

    Rectangle {
        x: entalhe.g
        width: entalhe.width - 2 * entalhe.g
        height: entalhe.height
        color: entalhe.cor
    }

    Rectangle {
        y: entalhe.g
        width: entalhe.width
        height: entalhe.height - 2 * entalhe.g
        color: entalhe.cor
    }
}
