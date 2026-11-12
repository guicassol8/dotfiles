import QtQuick

// Peça de pixel art em 9 fatias (cantos fixos, lados esticados), ampliada na grade
// sem suavizar. `borda` em pixels de arte; largura e altura múltiplas de `g`.
Item {
    id: fatias

    property url fonte
    property int borda: 0
    property int bordaEsquerda: borda
    property int bordaDireita: borda
    property int g: 3

    BorderImage {
        source: fatias.fonte
        smooth: false
        width: Math.round(fatias.width / fatias.g)
        height: Math.round(fatias.height / fatias.g)
        scale: fatias.g
        transformOrigin: Item.TopLeft
        border.left: fatias.bordaEsquerda
        border.right: fatias.bordaDireita
        border.top: fatias.borda
        border.bottom: fatias.borda
    }
}
