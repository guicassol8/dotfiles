import QtQuick

// Fatias: peca de pixel art em 9 fatias (cantos fixos, lados esticados), ampliada
// na grade sem suavizar. As bordas sao em pixels de ARTE. Use largura e altura
// multiplas de Tema.px, senao a ultima coluna sai cortada.
Item {
    id: fatias

    property string fonte: ""               // nome da peca em arte/ (sem .png)
    property int borda: 0
    property int bordaEsquerda: borda
    property int bordaDireita: borda
    property int bordaTopo: borda
    property int bordaBase: borda

    BorderImage {
        source: Tema.peca(fatias.fonte)
        smooth: false
        width: Math.round(fatias.width / Tema.px)
        height: Math.round(fatias.height / Tema.px)
        scale: Tema.px
        transformOrigin: Item.TopLeft
        border.left: fatias.bordaEsquerda
        border.right: fatias.bordaDireita
        border.top: fatias.bordaTopo
        border.bottom: fatias.bordaBase
    }
}
