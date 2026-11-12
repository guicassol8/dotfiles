import QtQuick

// Dialogo: a caixa de dialogo classica, embaixo no centro. E por onde o HUD fala
// com o dono (elemento mudou, subiu de nivel, oficio concluido, bateria baixa).
// A casca ja tem uma e liga nela o canal `dialogo` do Nucleo e o Hud.dizer():
// widget nenhum cria outra. Para falar: Hud.dizer({ titulo, texto, retrato, tipo }).
//
// Cada fala: texto em maquina de escrever, seta piscando quando termina, e passa
// para a proxima sozinha (ou no clique). tipo: "info", "recompensa", "perigo",
// "elemento". retrato: "conjurador", "familiar", "grimorio", "elemento-<nome>" ou
// qualquer nome de sprite do acervo.
Item {
    id: dialogo

    property var fila: []
    property var atual: null
    property int letras: 0
    property int pausa: 5200                // ms com a fala inteira na tela
    property int limite: 8                  // falas guardadas; acima disso descarta as mais velhas

    readonly property bool falando: atual !== null
    readonly property string _texto: atual ? String(atual.texto || "") : ""
    readonly property bool _completa: letras >= _texto.length
    readonly property string _tipo: atual && atual.tipo ? atual.tipo : "info"

    implicitWidth: 900
    implicitHeight: 126

    function enfileirar(f) {
        if (!f || !f.texto)
            return;
        if (f.id !== undefined && ((atual && atual.id === f.id) || fila.some(x => x.id === f.id)))
            return;
        const nova = fila.concat([f]);
        fila = nova.length > limite ? nova.slice(nova.length - limite) : nova;
        if (!falando)
            _proxima();
    }

    // clique: completa a fala; se ja estava completa, passa para a proxima
    function avancar() {
        if (!falando)
            return;
        if (!_completa)
            letras = _texto.length;
        else
            _proxima();
    }

    function _proxima() {
        if (fila.length === 0) {
            atual = null;
            return;
        }
        const f = fila[0];
        fila = fila.slice(1);
        letras = 0;
        atual = f;
        if (f.som)
            Nucleo.som(f.som);
    }

    Timer {                                 // maquina de escrever: 2 letras a cada 33 ms
        interval: 33
        repeat: true
        running: dialogo.falando && !dialogo._completa
        onTriggered: dialogo.letras = Math.min(dialogo._texto.length, dialogo.letras + 2)
    }
    Timer {
        interval: dialogo.pausa + dialogo._texto.length * 28
        running: dialogo.falando && dialogo._completa
        onTriggered: dialogo._proxima()
    }
    Timer {
        id: pisca
        property bool aceso: true
        interval: 480
        repeat: true
        running: dialogo.falando && dialogo._completa && Hud.animar
        onTriggered: aceso = !aceso
    }

    // retrato a esquerda, fora da caixa; a caixa de texto ocupa o resto
    Retrato {
        id: rosto
        readonly property string r: dialogo.atual && dialogo.atual.retrato ? dialogo.atual.retrato : "grimorio"
        visible: dialogo.falando && caixa.abertura >= 1
        // elemento-<nome>: o medalhao do elemento (64 px de arte, 1:1)
        readonly property bool emblema: r.startsWith("elemento-") && Tema.sprite("emblema-" + r.slice(9) + "-64") !== null
        fonte: r === "conjurador" ? "conjurador-32" : r === "familiar" ? "familiar-coruja-32"
             : emblema ? "emblema-" + r.slice(9) + "-64" : r
        ponto: emblema ? 1 : 0
        fps: 4
        y: parent.height - height
    }
    Janela {
        id: caixa
        x: rosto.width + 9
        y: 6
        width: parent.width - x
        height: parent.height - y
        aberta: dialogo.falando
        titulo: dialogo.atual && dialogo.atual.titulo ? dialogo.atual.titulo : ""
        variante: dialogo._tipo === "recompensa" ? "ouro" : dialogo._tipo === "perigo" ? "perigo" : "normal"
        respiro: 9

        Texto {
            width: parent.width - 30
            anchors.verticalCenter: parent.verticalCenter
            tamanho: 21
            text: dialogo._texto.slice(0, dialogo.letras)
            maximumLineCount: 2
            elide: Text.ElideRight
        }
        Figura {
            fonte: "seta-baixo"
            visible: dialogo._completa && pisca.aceso
            anchors.right: parent.right
            anchors.bottom: parent.bottom
        }
    }
    MouseArea {
        anchors.fill: parent
        enabled: dialogo.falando
        onClicked: dialogo.avancar()
    }
}
