import QtQuick

// Pixels: desenha um mapa de letras na grade, uma faixa por trecho de mesma cor.
//   Pixels { mapa: ["s.s", ".s.", "s.s"]; cores: ({ s: Tema.texto }) }
// Letra sem cor em `cores` (e o ".") fica vazia.
Item {
    id: px
    property var mapa: []
    property var cores: ({})
    implicitWidth: (mapa.length > 0 ? mapa[0].length : 0) * Tema.px
    implicitHeight: mapa.length * Tema.px
    readonly property var _trechos: {
        const r = [];
        for (let y = 0; y < mapa.length; y++) {
            const linha = mapa[y];
            let x = 0;
            while (x < linha.length) {
                const c = linha[x];
                let f = x;
                while (f < linha.length && linha[f] === c)
                    f++;
                if (c !== "." && cores[c] !== undefined)
                    r.push({ x: x, y: y, l: f - x, c: cores[c] });
                x = f;
            }
        }
        return r;
    }
    Repeater {
        model: px._trechos
        Rectangle {
            required property var modelData
            x: modelData.x * Tema.px
            y: modelData.y * Tema.px
            width: modelData.l * Tema.px
            height: Tema.px
            color: modelData.c
        }
    }
}
