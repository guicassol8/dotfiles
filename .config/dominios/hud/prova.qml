import QtQuick
import Quickshell
import qs.componentes     // sem estes imports o qs nao registra os modulos
import qs.dev             // para o arquivo carregado pelo LazyLoader

// prova.qml: bancada de teste de UM widget. Nao rode direto: use hud/dev/prova.
// Cada modo mora num arquivo porque o PanelWindow nem carrega fora do Wayland.
ShellRoot {
    LazyLoader {
        active: true
        source: Quickshell.env("HUD_PROVA_SAIDA") ? "dev/ProvaFora.qml" : "dev/ProvaTela.qml"
    }
}
