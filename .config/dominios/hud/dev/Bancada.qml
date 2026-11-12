import QtQuick
import Quickshell
import qs.componentes

// Bancada: um widget sozinho, centralizado sobre fundo opaco. Usada por prova.qml.
Item {
    id: bancada

    readonly property string alvo: Quickshell.env("HUD_PROVA") || ""
    readonly property int largura: Number(Quickshell.env("HUD_PROVA_L") || 0)
    readonly property int altura: Number(Quickshell.env("HUD_PROVA_A") || 0)
    readonly property string fundo: Quickshell.env("HUD_PROVA_FUNDO") || "cena"
    readonly property alias carga: carga
    readonly property url origem: {
        if (alvo === "")
            return "";
        if (alvo.startsWith("/"))
            return "file://" + alvo;
        if (alvo.endsWith(".qml"))
            return Qt.resolvedUrl("../" + alvo);
        return Qt.resolvedUrl("../widgets/" + alvo + ".qml");
    }

    Rectangle { anchors.fill: parent; color: fundo === "cena" ? Tema.fundo : fundo }

    // cena falsa, so para julgar o vidro: faixas de cor atras da peca
    Item {
        anchors.fill: parent
        visible: bancada.fundo === "cena"
        Rectangle {
            anchors.fill: parent
            gradient: Gradient {
                GradientStop { position: 0; color: "#241c3d" }
                GradientStop { position: 0.55; color: "#3a2a55" }
                GradientStop { position: 1; color: "#1b1630" }
            }
        }
        Repeater {
            model: 14
            Rectangle {
                required property int index
                x: (index * 197) % Math.max(1, bancada.width)
                y: (index * 131 + 40) % Math.max(1, bancada.height)
                width: 60 + (index * 37) % 120
                height: 24 + (index * 53) % 90
                color: Tema.corDe(Tema.nomesElementos[index % 6])
                opacity: 0.5
            }
        }
    }

    Loader {
        id: carga
        anchors.centerIn: parent
        source: bancada.origem
        width: bancada.largura > 0 ? bancada.largura : (item ? item.implicitWidth : 0)
        height: bancada.altura > 0 ? bancada.altura : (item ? item.implicitHeight : 0)
        onStatusChanged: if (status === Loader.Error) console.error("prova: nao carregou " + bancada.origem)
    }
}
