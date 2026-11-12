import QtQuick
import Quickshell
import qs.componentes
import qs.dev

// Bancada fora da tela: uma janela que nunca aparece (plataforma offscreen),
// fotografada pelo proprio Qt em $HUD_PROVA_SAIDA.
FloatingWindow {
    id: janela

    readonly property string saida: Quickshell.env("HUD_PROVA_SAIDA") || ""
    readonly property int espera: Number(Quickshell.env("HUD_PROVA_ESPERA") || 2500)
    readonly property int quadros: Number(Quickshell.env("HUD_PROVA_QUADROS") || 1)
    readonly property int intervalo: Number(Quickshell.env("HUD_PROVA_INTERVALO") || 400)

    implicitWidth: Number(Quickshell.env("HUD_PROVA_L") || 420) + 60
    implicitHeight: Number(Quickshell.env("HUD_PROVA_A") || 300) + 60
    color: Tema.fundo

    Bancada { id: bancada; anchors.fill: parent }
    Timer {
        property int n: 0
        interval: n === 0 ? janela.espera : janela.intervalo
        running: true
        repeat: true
        onTriggered: {
            n += 1;
            const nome = janela.quadros > 1 ? janela.saida.replace(/\.png$/, "-" + n + ".png") : janela.saida;
            const ultimo = n >= janela.quadros;
            if (ultimo)
                stop();
            bancada.grabToImage(function (r) {
                if (!r.saveToFile(nome))
                    console.error("prova: nao gravou " + nome);
                if (ultimo)
                    Qt.quit();
            });
        }
    }
}
