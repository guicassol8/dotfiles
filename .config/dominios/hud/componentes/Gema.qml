import QtQuick

// Gema: pedra do elemento (por padrao o ativo). Troca de cor com uma passagem
// suave quando o elemento muda. `brilho` e a forca do halo liso atras dela.
Item {
    id: gema

    property string elemento: Tema.elemento     // ou "apagada"
    property bool grande: false                 // 9x9 em vez de 5x5
    property real brilho: 0.0                   // 0 = sem halo
    property int escala: 1

    readonly property string _peca: grande ? "gemao-" : "gema-"
    property string _anterior: elemento

    implicitWidth: (grande ? 9 : 5) * Tema.px * escala
    implicitHeight: implicitWidth

    Image {
        visible: gema.brilho > 0 && gema.elemento !== "apagada"
        source: visible ? Tema.peca("brilho-" + gema.elemento) : ""
        anchors.centerIn: parent
        width: parent.width * 3.4
        height: width
        opacity: gema.brilho
    }
    Figura { id: nova; fonte: gema._peca + gema.elemento; escala: gema.escala }
    Figura { id: velha; fonte: gema._peca + gema._anterior; escala: gema.escala; opacity: 0 }

    onElementoChanged: {
        passagem.stop();
        velha.opacity = 1;
        passagem.start();
    }
    SequentialAnimation {
        id: passagem
        NumberAnimation { target: velha; property: "opacity"; to: 0; duration: 900 }
        ScriptAction { script: gema._anterior = gema.elemento }
    }
}
