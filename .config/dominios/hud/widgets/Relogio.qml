import QtQuick
import qs.componentes

// Relogio: a peca tipografica da mesa. Sem moldura: hora em pixel grande, dia da
// semana em gotico na cor do elemento, data e o capitulo (elemento) do momento.
Item {
    id: relogio

    implicitWidth: 720
    implicitHeight: 216

    readonly property var dias: ["Domingo", "Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira", "Sábado"]
    readonly property var meses: ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]
    readonly property date d: Hud.agora       // o relogio unico do HUD
    function dois(n) { return n < 10 ? "0" + n : "" + n; }

    Column {
        anchors.horizontalCenter: parent.horizontalCenter
        spacing: 0

        TextoPixel {
            anchors.horizontalCenter: parent.horizontalCenter
            tipo: "enorme"
            sombra: true
            contorno: true
            text: relogio.dois(relogio.d.getHours()) + ":" + relogio.dois(relogio.d.getMinutes())
        }
        // placa escura discreta atras do dia e da data: segura a leitura sobre o vitral claro
        Item {
            anchors.horizontalCenter: parent.horizontalCenter
            width: miolo.width
            height: miolo.height
            Rectangle {
                x: -24
                y: 3
                width: parent.width + 48
                height: parent.height - 3
                color: Tema.alfa(Tema.fundo, 0.5)
            }
            Column {
                id: miolo
                spacing: 0
                TextoPixel {
                    anchors.horizontalCenter: parent.horizontalCenter
                    tipo: "gotico"
                    sombra: true
                    contorno: true
                    corContorno: Qt.rgba(0.04, 0.03, 0.07, 0.95)
                    color: Tema.destaque
                    text: relogio.dias[relogio.d.getDay()]
                }
                Row {
                    anchors.horizontalCenter: parent.horizontalCenter
                    spacing: 12
                    Figura { fonte: "florao"; anchors.verticalCenter: parent.verticalCenter; anchors.verticalCenterOffset: 4 }
                    TextoPixel {
                        tipo: "rotulo"
                        sombra: true
                        contorno: true
                        corContorno: Qt.rgba(0.04, 0.03, 0.07, 0.95)
                        color: Tema.texto
                        font.capitalization: Font.AllUppercase
                        text: relogio.d.getDate() + " de " + relogio.meses[relogio.d.getMonth()] + " de " + relogio.d.getFullYear()
                    }
                    Figura { fonte: "florao"; anchors.verticalCenter: parent.verticalCenter; anchors.verticalCenterOffset: 4 }
                }
            }
        }
    }
}
