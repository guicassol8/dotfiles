import QtQuick
import Quickshell
import Quickshell.Wayland
import qs.componentes
import qs.dev

// Bancada na tela de verdade: camada overlay, tela cheia, fundo opaco.
PanelWindow {
    anchors { top: true; bottom: true; left: true; right: true }
    exclusionMode: ExclusionMode.Ignore
    color: Tema.fundo
    WlrLayershell.layer: WlrLayer.Overlay
    WlrLayershell.namespace: "dominios-hud-prova"
    WlrLayershell.keyboardFocus: WlrKeyboardFocus.None
    Bancada { anchors.fill: parent }
}
