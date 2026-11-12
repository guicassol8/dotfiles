import Quickshell
import Quickshell.Wayland
import QtQuick

// Shell de teste do papel vivo: tela cheia, camada overlay, fundo opaco.
// Papel.qml, o .qsb e cenas/ entram aqui por link simbolico (o qs nao le fora da pasta do shell).
// Variaveis: PAPEL_ELEMENTO, PAPEL_HORA (0..24), PAPEL_CHUVA, PAPEL_FPS (12), PAPEL_NITIDO (1),
// PAPEL_TEMPO (inicio da cena), PAPEL_PULSO, PAPEL_TROCA_PARA + PAPEL_TROCA_EM (s),
// PAPEL_SURTO_EM (s), PAPEL_HORA_PARA + PAPEL_HORA_EM (s): muda a hora (fusao entre fases).
ShellRoot {
    PanelWindow {
        anchors { top: true; bottom: true; left: true; right: true }
        exclusionMode: ExclusionMode.Ignore
        WlrLayershell.layer: WlrLayer.Overlay
        WlrLayershell.keyboardFocus: WlrKeyboardFocus.None
        WlrLayershell.namespace: "dominios-papel-dev"
        color: "#17141D"

        Papel {
            id: papel
            elemento: Quickshell.env("PAPEL_ELEMENTO") || "mana-pura"
            fps: Number(Quickshell.env("PAPEL_FPS") || 12)
            nitido: (Quickshell.env("PAPEL_NITIDO") || "1") === "1"
            tempo: Number(Quickshell.env("PAPEL_TEMPO") || 40)
            pulso: Number(Quickshell.env("PAPEL_PULSO") || 0)
            chuva: Number(Quickshell.env("PAPEL_CHUVA") || 0)
            Component.onCompleted: {
                const h = Quickshell.env("PAPEL_HORA");
                if (h) hora = Number(h);
            }
        }

        Timer {
            interval: Number(Quickshell.env("PAPEL_TROCA_EM") || 0) * 1000
            running: interval > 0 && !!Quickshell.env("PAPEL_TROCA_PARA")
            onTriggered: papel.elemento = Quickshell.env("PAPEL_TROCA_PARA")
        }
        Timer {
            interval: Number(Quickshell.env("PAPEL_HORA_EM") || 0) * 1000
            running: interval > 0 && !!Quickshell.env("PAPEL_HORA_PARA")
            onTriggered: papel.hora = Number(Quickshell.env("PAPEL_HORA_PARA"))
        }
        Timer {
            interval: Number(Quickshell.env("PAPEL_SURTO_EM") || 0) * 1000
            running: interval > 0
            onTriggered: papel.surto()
        }
    }
}
