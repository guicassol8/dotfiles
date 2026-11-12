import QtQuick

// TextoPixel: texto em fonte de pixel, cravado na grade (cada pixel da fonte vira
// Tema.px na tela, sem suavizar). Nao mude font.pixelSize na mao: escolha o `tipo`.
//
//   tipo          fonte         maiuscula   uso
//   "rotulo"      Silkscreen    15 px       rotulos (so maiusculas)
//   "titulo"      Silkscreen B  15 px       titulos de placa e de secao
//   "miudo"       Micro 5       15 px       nota estreita, tem minusculas
//   "medio"       Jersey 10     30 px       numeros e nomes de destaque
//   "grande"      Jersey 15     45 px       numero grande
//   "enorme"      Jersey 25     75 px       relogio
//   "gotico"      Jacquard 12   45 px       palavra de destaque (nao use em CAIXA ALTA)
//   "goticoGrande" Jacquard 24  93 px       uma palavra, no maximo
Text {
    id: t

    property string tipo: "rotulo"
    property int escala: 1                  // multiplo inteiro da grade
    property bool sombra: false             // sombra dura de 1 pixel de arte
    property color corSombra: Qt.rgba(0, 0, 0, 0.6)
    // contorno duro de 1 pixel de arte nos quatro lados: texto solto sobre a cena viva
    property bool contorno: false
    property color corContorno: Qt.rgba(0.04, 0.03, 0.07, 0.82)

    readonly property var _f: Tema.pixel[tipo] || Tema.pixel.rotulo
    readonly property var _janela: Hud.janelaDe(t)
    // altura da maiuscula na tela, para alinhar com sprites e barras
    readonly property int alta: _f.alta * Tema.px * escala

    color: _janela ? _janela.tinta : Tema.texto
    font.family: _f.familia
    font.pixelSize: Math.round(_f.em * Tema.px * Math.max(1, escala))
    font.bold: _f.negrito
    font.kerning: false
    font.hintingPreference: Font.PreferNoHinting
    font.letterSpacing: _f.aperto ? -_f.aperto * Tema.px * escala : 0
    renderType: Text.NativeRendering
    antialiasing: false
    textFormat: Text.PlainText

    Text {
        visible: t.sombra
        z: -1
        x: Tema.px * t.escala
        y: Tema.px * t.escala
        width: t.width
        height: t.height
        text: t.text
        font: t.font
        color: t.corSombra
        renderType: Text.NativeRendering
        antialiasing: false
        textFormat: Text.PlainText
        horizontalAlignment: t.horizontalAlignment
        verticalAlignment: t.verticalAlignment
        wrapMode: t.wrapMode
        elide: t.elide
    }
    Repeater {
        model: t.contorno ? [[-1, 0], [1, 0], [0, -1], [0, 1]] : []
        Text {
            required property var modelData
            z: -1
            x: modelData[0] * Tema.px * t.escala
            y: modelData[1] * Tema.px * t.escala
            width: t.width
            height: t.height
            text: t.text
            font: t.font
            color: t.corContorno
            renderType: Text.NativeRendering
            antialiasing: false
            textFormat: Text.PlainText
            horizontalAlignment: t.horizontalAlignment
            verticalAlignment: t.verticalAlignment
            wrapMode: t.wrapMode
            elide: t.elide
        }
    }
}
