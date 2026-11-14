import QtQuick
import Quickshell
import qs.componentes

// Letreiro de sala: quando o foco troca de workspace, o nome da sala aparece no meio da
// tela como a placa de area de um RPG ao entrar num lugar novo. Uma faixa de vidro
// escuro abre do centro numa varredura de pixels (degraus de 4 pixels de arte, com o
// fio de luz na borda), o titulo acende no elemento e esfria, segura um instante e a
// faixa fecha de volta. Uns 750 ms, so por evento: parado nao anima nada.
// A casca (shell.qml) poe isto numa superficie propria na camada Top, sem clique nem
// teclado, visivel so enquanto `ativo`, e chama `mostrar()`. Em rajada (rolar por varios
// workspaces) a placa ja aberta so troca o texto, reacende e segura mais um pouco.
//
//   HUD_AMOSTRA_LETREIRO='{"sala": 3, "janelas": 5, "aberto": 1}' \
//       hud/dev/prova casca/Letreiro.qml --tamanho 612x180 --fundo '#5a6170'
//   (campos opcionais "nome" e "faisca" 0..1; sem "aberto", a animacao inteira em laco,
//   para --quadros 22 --intervalo 0.04)
Item {
    id: letreiro

    property int sala: 1
    property string nome: ""                // workspace com nome no niri: vira o titulo
    property int janelas: 0
    // 0 fechado, 1 aberto: a faixa abre do centro para fora
    property real aberto: 0
    // 1 logo que a placa abre ou troca de sala, 0 assentado: o titulo esfria do elemento
    property real faisca: 0
    readonly property bool ativo: aberto > 0 || abre.running || segura.running || fecha.running

    // tempos (ms)
    readonly property int tAbre: 170
    readonly property int tSegura: 560      // contado do pedido: abrir + ficar lido
    readonly property int tFecha: 190

    function mostrar(sala, nome, janelas) {
        letreiro.sala = sala;
        letreiro.nome = nome || "";
        letreiro.janelas = Math.max(0, janelas || 0);
        fecha.stop();
        if (aberto < 1 && !abre.running) {
            abre.duration = Math.max(40, Math.round(tAbre * (1 - aberto)));
            abre.restart();
        }
        esfria.restart();
        segura.restart();
    }
    // some na hora (paisagem, contemplacao, grimorio aberto)
    function esconder() {
        abre.stop();
        segura.stop();
        esfria.stop();
        if (aberto > 0) {
            fecha.duration = 120;
            fecha.restart();
        }
    }

    NumberAnimation { id: abre; target: letreiro; property: "aberto"; to: 1; easing.type: Easing.OutCubic }
    NumberAnimation { id: esfria; target: letreiro; property: "faisca"; from: 1; to: 0; duration: 340; easing.type: Easing.InQuad }
    Timer {
        id: segura
        interval: letreiro.tSegura
        onTriggered: {
            fecha.duration = letreiro.tFecha;
            fecha.restart();
        }
    }
    NumberAnimation { id: fecha; target: letreiro; property: "aberto"; to: 0; easing.type: Easing.InCubic }

    implicitWidth: 612
    implicitHeight: 180

    // ================================================================ desenho
    // faixa de 168 x 44 pixels de arte; as gemas das pontas passam 4 para fora
    readonly property int faixaL: 504
    readonly property int faixaA: 132
    readonly property int sobra: 4 * Tema.px
    readonly property int faixaY: Tema.grade((height - faixaA) / 2)
    readonly property int centro: Tema.grade(width / 2)
    // meia abertura em degraus de 4 pixels de arte: a varredura anda na grade
    readonly property int meia: Math.round(aberto * (faixaL / 2 + sobra) / (4 * Tema.px)) * 4 * Tema.px
    readonly property bool varrendo: aberto > 0 && aberto < 1

    readonly property color luz: Tema.mistura(Tema.destaque, "#ffffff", 0.55)
    readonly property color escuro: Tema.mistura(Tema.fundo, "#000000", 0.55)
    // nome de workspace com minuscula vai em gotico como "Sala"; tudo maiusculo, em pixel
    readonly property bool gotico: nome === "" || nome !== nome.toUpperCase()

    opacity: Math.min(1, aberto * 5)        // o fim do fechar some junto, sem resto de pixel
    visible: aberto > 0

    // texto em pixel com o topo da maiuscula numa linha da grade da faixa
    function topo(t, linha) { return linha * Tema.px - (t.baselineOffset - t.alta); }

    // luz lisa atras (HD-2D): acende com a faixa e brilha mais na faisca
    Image {
        source: Tema.peca("brilho-" + Tema.elemento)
        x: letreiro.centro - width / 2
        y: 0
        width: letreiro.faixaL + 72
        height: letreiro.height
        opacity: 0.38 * letreiro.aberto + 0.3 * letreiro.faisca
    }

    // a faixa e o que mora nela, recortados pela abertura
    Item {
        id: recorte
        x: letreiro.centro - letreiro.meia
        y: letreiro.faixaY - 3 * Tema.px
        width: 2 * letreiro.meia
        height: letreiro.faixaA + 6 * Tema.px
        clip: true

        Item {                              // o conteudo fica parado; so o recorte anda
            id: faixa
            x: letreiro.centro - letreiro.faixaL / 2 - recorte.x
            y: 3 * Tema.px
            width: letreiro.faixaL
            height: letreiro.faixaA

            // sombra dura de 2 pixels de arte embaixo
            Rectangle { x: 2 * Tema.px; y: 2 * Tema.px; width: parent.width; height: parent.height; color: Qt.rgba(0.02, 0.01, 0.04, 0.55) }
            // contorno escuro, filete do elemento, vidro
            Rectangle { anchors.fill: parent; color: letreiro.escuro }
            Rectangle {
                x: Tema.px; y: Tema.px; width: parent.width - 2 * Tema.px; height: parent.height - 2 * Tema.px
                color: Tema.mistura(Tema.destaque, letreiro.escuro, 0.2)
            }
            Rectangle {
                x: 2 * Tema.px; y: 2 * Tema.px; width: parent.width - 4 * Tema.px; height: parent.height - 4 * Tema.px
                color: Tema.alfa(Tema.mistura(Tema.superficie2, Tema.fundo, 0.55), 0.94)
            }
            Rectangle {                     // reflexo de cima do vidro
                x: 2 * Tema.px; y: 2 * Tema.px; width: parent.width - 4 * Tema.px; height: Tema.px
                color: Qt.rgba(1, 1, 1, 0.07)
            }
            // filetes de dentro; o de baixo com o florao no meio
            Rectangle { x: 9 * Tema.px; y: 5 * Tema.px; width: parent.width - 18 * Tema.px; height: Tema.px; color: Tema.alfa(Tema.destaque, 0.3) }
            Rectangle { x: 9 * Tema.px; y: 38 * Tema.px; width: Tema.grade(parent.width / 2) - 15 - x; height: Tema.px; color: Tema.alfa(Tema.destaque, 0.3) }
            Rectangle { x: Tema.grade(parent.width / 2) + 15; y: 38 * Tema.px; width: parent.width - 9 * Tema.px - x; height: Tema.px; color: Tema.alfa(Tema.destaque, 0.3) }
            Figura { fonte: "florao"; x: Tema.grade(parent.width / 2 - width / 2); y: 36 * Tema.px }

            // titulo: "Sala" em gotico e o numero em pixel, no elemento (ou o nome do workspace)
            Row {
                x: Tema.grade((parent.width - width) / 2)
                spacing: 5 * Tema.px
                TextoPixel {
                    id: nomeSala
                    y: letreiro.topo(nomeSala, 10)
                    tipo: letreiro.gotico ? "gotico" : "grande"
                    sombra: true
                    text: letreiro.nome !== "" ? letreiro.nome.slice(0, 18) : "Sala"
                    color: Tema.mistura(Tema.texto, letreiro.luz, letreiro.faisca)
                }
                TextoPixel {
                    id: numeroSala
                    visible: letreiro.nome === ""
                    y: letreiro.topo(numeroSala, 10)
                    tipo: "grande"
                    sombra: true
                    text: String(letreiro.sala)
                    color: Tema.mistura(Tema.mistura(Tema.destaque, "#ffffff", 0.2), "#ffffff", 0.6 * letreiro.faisca)
                }
            }

            // linha de baixo: um bau por janela (como no Mapa) e a contagem
            Row {
                x: Tema.grade((parent.width - width) / 2)
                y: 29 * Tema.px
                height: 5 * Tema.px
                spacing: 3 * Tema.px
                Row {
                    visible: letreiro.janelas > 0
                    y: Tema.px
                    spacing: 2 * Tema.px
                    Repeater {
                        model: Math.min(letreiro.janelas, 5)
                        Bau {}
                    }
                }
                TextoPixel {
                    id: contagem
                    y: letreiro.topo(contagem, 0)
                    tipo: "rotulo"
                    color: Tema.textoSuave
                    text: (letreiro.nome !== "" ? "SALA " + letreiro.sala + " · " : "")
                          + (letreiro.janelas === 0 ? "VAZIA" : letreiro.janelas === 1 ? "1 JANELA" : letreiro.janelas + " JANELAS")
                }
            }
        }
        // gemas nas pontas: as ultimas a aparecer na varredura
        Repeater {
            model: 2
            Gema {
                required property int index
                grande: true
                brilho: 0.35 + 0.4 * letreiro.faisca
                x: faixa.x + (index === 0 ? -letreiro.sobra : faixa.width + letreiro.sobra - width)
                y: faixa.y + Tema.grade((faixa.height - height) / 2)
            }
        }
    }

    // fio de luz nas duas bordas da varredura, so enquanto abre ou fecha
    Repeater {
        model: letreiro.varrendo && letreiro.meia > 0 ? [-1, 1] : []
        Item {
            required property var modelData
            x: letreiro.centro + modelData * letreiro.meia - (modelData > 0 ? Tema.px : 0)
            y: letreiro.faixaY - 3 * Tema.px
            width: Tema.px
            height: letreiro.faixaA + 6 * Tema.px
            Rectangle { anchors.fill: parent; color: letreiro.luz }
            Rectangle {                     // rastro de 2 pixels de arte, mais fraco, para dentro
                x: parent.modelData > 0 ? -2 * Tema.px : Tema.px
                y: 2 * Tema.px
                width: 2 * Tema.px
                height: parent.height - 4 * Tema.px
                color: Tema.alfa(Tema.destaque, 0.45)
            }
        }
    }

    // bauzinho 5 x 4 pixels de arte (o mesmo do Mapa), aceso no elemento
    component Bau: Item {
        readonly property color corpo: Tema.destaque
        width: 5 * Tema.px
        height: 4 * Tema.px
        Rectangle { width: parent.width; height: parent.height; color: Tema.mistura(parent.corpo, "#000000", 0.25) }
        Rectangle { width: parent.width; height: Tema.px; color: Tema.mistura(parent.corpo, "#ffffff", 0.45) }
        Rectangle { y: Tema.px; width: parent.width; height: Tema.px; color: parent.corpo }
        Rectangle { y: 2 * Tema.px; width: parent.width; height: Tema.px; color: Tema.mistura(Tema.fundo, "#000000", 0.3) }
        Rectangle { x: 2 * Tema.px; y: Tema.px; width: Tema.px; height: 2 * Tema.px; color: Tema.ouro }
    }

    // ================================================================ teste fora da tela
    readonly property var amostra: {
        const t = Quickshell.env("HUD_AMOSTRA_LETREIRO");
        if (!t)
            return null;
        try {
            return JSON.parse(t);
        } catch (e) {
            console.warn("Letreiro: HUD_AMOSTRA_LETREIRO nao e JSON (" + e + ")");
            return null;
        }
    }
    Timer {                                 // sem "aberto": repete a animacao inteira
        running: !!letreiro.amostra && letreiro.amostra.aberto === undefined
        interval: 1100
        repeat: true
        triggeredOnStart: true
        onTriggered: letreiro.mostrar(letreiro.amostra.sala || 2, letreiro.amostra.nome, letreiro.amostra.janelas || 0)
    }
    Component.onCompleted: {
        const a = amostra;
        if (a && a.aberto !== undefined) {
            sala = a.sala || 2;
            nome = a.nome || "";
            janelas = a.janelas || 0;
            aberto = a.aberto;
            faisca = a.faisca || 0;
        }
    }
}
