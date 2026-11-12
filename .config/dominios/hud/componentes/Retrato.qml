import QtQuick

// Retrato: sprite numa moldurinha de pixel, sobre um fundo escuro com a luz do
// elemento. Qualquer `fonte` de Figura serve; os do acervo tem 32 a 34 px de arte
// e cabem no miolo padrao (34). 114 x 114 px.
//
//   Retrato { fonte: "mago"; fps: 4 }
Item {
    id: retrato

    property string fonte: "mago"
    property real fps: 0
    property int ponto: 0                   // 1: arte fina desenhada 1:1 (o emblema de 64 do elemento)
    property int lado: 34                   // lado do miolo em pixels de arte
    property color luz: Tema.destaque

    implicitWidth: (lado + 4) * Tema.px
    implicitHeight: (lado + 4) * Tema.px

    Rectangle {
        x: Tema.px
        y: Tema.px
        width: parent.width - 2 * Tema.px
        height: parent.height - 2 * Tema.px
        gradient: Gradient {
            GradientStop { position: 0; color: Tema.mistura(Tema.superficie2, retrato.luz, 0.26) }
            GradientStop { position: 1; color: Tema.mistura(Tema.fundo, "#000000", 0.3) }
        }
    }
    Figura {
        fonte: retrato.fonte
        fps: retrato.fps
        ponto: retrato.ponto
        x: Tema.grade((parent.width - width) / 2)
        y: Tema.grade((parent.height - height) / 2)
    }
    Fatias { anchors.fill: parent; fonte: "retrato-moldura"; borda: 3 }
}
