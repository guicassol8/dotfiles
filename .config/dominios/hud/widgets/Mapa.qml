import QtQuick
import Quickshell
import Quickshell.Niri
import qs.componentes

// Mapa: os workspaces da tela como salas de uma masmorra, de cima para baixo (como o
// niri empilha), ligadas por corredores. Cada sala mostra um bauzinho por janela (ate
// quatro, depois "+N"); a ativa fica acesa na cor do elemento, com o conjurador ao lado;
// a vazia fica escura. Clique numa sala foca aquele workspace.
// Dados: Quickshell.Niri (workspaces e janelas).
//
// `amostra` troca os dados de verdade por um exemplo (teste fora da tela):
//   HUD_AMOSTRA_MAPA='[{"idx": 1, "janelas": 3, "ativa": true}, {"idx": 2, "janelas": 0}]'
//   (campos opcionais: "nome", "urgente")
Janela {
    id: mapa

    titulo: "Mapa"

    // ================================================================ dados
    readonly property string saida: "eDP-1"

    property var amostra: {
        const t = Quickshell.env("HUD_AMOSTRA_MAPA");
        if (!t)
            return null;
        try {
            return JSON.parse(t);
        } catch (e) {
            console.warn("Mapa: HUD_AMOSTRA_MAPA nao e JSON (" + e + ")");
            return null;
        }
    }
    // sem niri (foto fora da sessao): um exemplo para a mesa nao nascer vazia
    readonly property var exemplo: [
        { idx: 1, nome: "", janelas: 2, ativa: true, urgente: false },
        { idx: 2, nome: "", janelas: 0, ativa: false, urgente: false }
    ]

    readonly property var doNiri: {
        const ws = Niri.workspaces ? Niri.workspaces.values : [];
        const jan = Niri.windows ? Niri.windows.values : [];
        const conta = {};
        for (let i = 0; i < jan.length; i++) {
            const k = String(jan[i].workspaceId);
            conta[k] = (conta[k] || 0) + 1;
        }
        let l = [];
        for (let i = 0; i < ws.length; i++)
            if (ws[i].output === saida)
                l.push(ws[i]);
        if (l.length === 0)
            l = ws.slice();                 // outra tela com outro nome: mostra o que houver
        l.sort((a, b) => a.idx - b.idx);
        return l.map(w => ({
            idx: w.idx, nome: w.name || "", janelas: conta[String(w.id)] || 0,
            ativa: w.active, urgente: w.urgent
        }));
    }

    readonly property var salas: amostra ? amostra : (doNiri.length > 0 ? doNiri : exemplo)
    readonly property int ativa: {
        for (let i = 0; i < salas.length; i++)
            if (salas[i].ativa)
                return i;
        return 0;
    }

    // focar um workspace: so por clique do dono (nunca em teste)
    function focar(sala) {
        if (amostra || doNiri.length === 0 || sala.ativa)
            return;
        Quickshell.execDetached(["niri", "msg", "action", "focus-workspace", String(sala.idx)]);
    }

    // ================================================================ desenho
    readonly property int salaL: 44 * Tema.px
    readonly property int salaA: 12 * Tema.px     // tres salas cabem nos 120 px
    readonly property int corredor: 2 * Tema.px
    readonly property int passo: salaA + corredor
    readonly property int desvio: corpo.width - salaL          // as salas alternam de lado
    readonly property int maxBaus: 4

    function xSala(i) { return i % 2 === 0 ? 0 : desvio; }

    Item {
        id: vista
        anchors.fill: parent
        clip: true

        readonly property int total: mapa.salas.length * mapa.passo - mapa.corredor
        readonly property int alvo: {
            const y = mapa.ativa * mapa.passo - Tema.grade((height - mapa.salaA) / 2);
            return Math.max(0, Math.min(Math.max(0, total - height), y));
        }

        Item {
            id: trilho
            width: parent.width
            height: vista.total
            // poucas salas: a masmorra fica no meio; muitas: rola ate a ativa
            y: vista.total <= vista.height ? Tema.grade((vista.height - vista.total) / 2) : -vista.alvo
            Behavior on y { NumberAnimation { duration: 260; easing.type: Easing.OutCubic } }

            // luz lisa atras da sala ativa
            Image {
                source: Tema.peca("brilho-" + Tema.elemento)
                x: mapa.xSala(mapa.ativa) - 18 * Tema.px
                y: mapa.ativa * mapa.passo - 12 * Tema.px
                width: mapa.salaL + 36 * Tema.px
                height: mapa.salaA + 24 * Tema.px
                opacity: 0.5
                Behavior on x { NumberAnimation { duration: 260; easing.type: Easing.OutCubic } }
                Behavior on y { NumberAnimation { duration: 260; easing.type: Easing.OutCubic } }
            }

            // salas
            Repeater {
                model: mapa.salas
                Sala {
                    required property var modelData
                    required property int index
                    sala: modelData
                    x: mapa.xSala(index)
                    y: index * mapa.passo
                }
            }

            // corredores, por cima das paredes (abrem as portas)
            Repeater {
                model: Math.max(0, mapa.salas.length - 1)
                Item {
                    required property int index
                    readonly property bool aceso: index === mapa.ativa || index + 1 === mapa.ativa
                    x: Tema.grade((mapa.desvio + mapa.salaL) / 2) - 2 * Tema.px
                    y: index * mapa.passo + mapa.salaA - Tema.px
                    width: 4 * Tema.px
                    height: mapa.corredor + 2 * Tema.px
                    Rectangle { width: Tema.px; height: parent.height; color: Tema.contorno }
                    Rectangle { x: 3 * Tema.px; width: Tema.px; height: parent.height; color: Tema.contorno }
                    Rectangle {
                        x: Tema.px
                        width: 2 * Tema.px
                        height: parent.height
                        color: Tema.mistura(Tema.fundo, "#000000", 0.25)
                    }
                    Rectangle {                     // pegadas de luz no corredor da sala ativa
                        visible: parent.aceso
                        x: Tema.px
                        y: Tema.grade(parent.height / 2) - Tema.px
                        width: 2 * Tema.px
                        height: Tema.px
                        color: Tema.alfa(Tema.destaque, 0.55)
                    }
                }
            }

            // o conjurador, de pe ao lado da sala ativa, com a luz dele
            Image {
                source: Tema.peca("brilho-" + Tema.elemento)
                width: 20 * Tema.px
                height: 20 * Tema.px
                x: conjurador.x + conjurador.width / 2 - width / 2
                y: conjurador.y + conjurador.height / 2 - height / 2
                opacity: 0.6
            }
            Rectangle {                         // chao aceso sob os pes
                width: 7 * Tema.px
                height: Tema.px
                x: conjurador.x + Tema.grade((conjurador.width - width) / 2)
                y: conjurador.y + conjurador.height
                color: Tema.alfa(Tema.destaque, 0.6)
            }
            Figura {
                id: conjurador
                fonte: Qt.resolvedUrl("../sprites/conjurador-32.png")
                ponto: 1
                x: mapa.ativa % 2 === 0 ? mapa.salaL + Tema.grade((mapa.desvio - width) / 2) : Tema.grade((mapa.desvio - width) / 2)
                y: mapa.ativa * mapa.passo + mapa.salaA - height
                Behavior on x { NumberAnimation { duration: 260; easing.type: Easing.OutCubic } }
                Behavior on y { NumberAnimation { duration: 260; easing.type: Easing.OutCubic } }
            }
        }

        // ha salas fora da vista: seta no lado livre da sala da ponta
        Seta {
            readonly property int ponta: Math.min(mapa.salas.length - 1, Math.floor((vista.alvo + vista.height) / mapa.passo))
            visible: vista.total > vista.height && vista.alvo + vista.height < vista.total
            x: ponta % 2 === 0 ? mapa.salaL + Tema.grade((mapa.desvio - width) / 2) : Tema.grade((mapa.desvio - width) / 2)
            y: parent.height - height
        }
        Seta {
            readonly property int ponta: Math.min(mapa.salas.length - 1, Math.ceil(vista.alvo / mapa.passo))
            visible: vista.total > vista.height && vista.alvo > 0
            paraCima: true
            x: ponta % 2 === 0 ? mapa.salaL + Tema.grade((mapa.desvio - width) / 2) : Tema.grade((mapa.desvio - width) / 2)
            y: 0
        }
    }

    // ================================================================ pecas

    // uma sala: paredes, piso, numero e bauzinhos
    component Sala: Item {
        id: s
        property var sala: ({})
        readonly property bool ativa: !!sala.ativa
        readonly property bool vazia: (sala.janelas || 0) === 0
        readonly property bool urgente: !!sala.urgente
        readonly property int n: sala.janelas || 0
        readonly property int mostrados: n > mapa.maxBaus ? 3 : n
        property bool _pisca: false                         // urgente: a parede pisca
        Timer {
            interval: 500
            repeat: true
            running: s.urgente && Hud.animar
            onTriggered: s._pisca = !s._pisca
            onRunningChanged: if (!running) s._pisca = false
        }
        readonly property bool _dentro: toque.containsMouse && !ativa

        width: mapa.salaL
        height: mapa.salaA

        readonly property color parede: urgente ? (_pisca ? Tema.contorno : Tema.perigo) : ativa ? Tema.destaque
            : _dentro ? Tema.mistura(Tema.contorno, Tema.texto, 0.35) : Tema.contorno
        readonly property color piso: ativa ? Tema.mistura(Tema.fundo, Tema.destaque, 0.24)
            : vazia ? Tema.mistura(Tema.fundo, "#000000", 0.3) : Tema.mistura(Tema.superficie, Tema.superficie2, 0.5)

        Rectangle {                         // sombra dura embaixo
            x: Tema.px
            y: Tema.px
            width: parent.width
            height: parent.height
            color: Qt.rgba(0, 0, 0, 0.45)
        }
        Rectangle { anchors.fill: parent; color: s.parede }
        Rectangle {
            x: Tema.px
            y: Tema.px
            width: parent.width - 2 * Tema.px
            height: parent.height - 2 * Tema.px
            color: s.piso
        }
        Repeater {                          // lajotas: um pixel mais claro a cada 6, em xadrez
            model: Math.floor((mapa.salaL / Tema.px - 4) / 6) * 2
            Rectangle {
                required property int index
                readonly property int col: Math.floor(index / 2)
                readonly property int lin: index % 2
                x: (4 + col * 6 + lin * 3) * Tema.px
                y: (3 + lin * 5) * Tema.px
                width: Tema.px
                height: Tema.px
                color: s.ativa ? Tema.alfa(Tema.destaque, 0.22) : Qt.rgba(1, 1, 1, s.vazia ? 0.025 : 0.05)
            }
        }
        Rectangle {                         // luz de cima
            x: Tema.px
            y: Tema.px
            width: parent.width - 2 * Tema.px
            height: Tema.px
            color: s.ativa ? Tema.alfa(Tema.mistura(Tema.destaque, "#ffffff", 0.4), 0.3) : Qt.rgba(1, 1, 1, s.vazia ? 0.03 : 0.07)
        }

        TextoPixel {
            tipo: "titulo"
            sombra: true
            x: 4 * Tema.px
            y: Tema.grade((parent.height - height) / 2)
            text: s.sala.nome ? s.sala.nome.slice(0, 1) : String(s.sala.idx || "")
            font.capitalization: Font.AllUppercase
            color: s.ativa ? Tema.mistura(Tema.destaque, "#ffffff", 0.55) : s.vazia ? Tema.alfa(Tema.textoSuave, 0.55) : Tema.texto
        }

        Row {
            visible: !s.vazia
            spacing: 2 * Tema.px
            anchors.right: parent.right
            anchors.rightMargin: 3 * Tema.px
            anchors.verticalCenter: parent.verticalCenter
            Repeater {
                model: s.mostrados
                Bau { ativa: s.ativa; anchors.verticalCenter: parent.verticalCenter }
            }
            TextoPixel {
                visible: s.n > mapa.maxBaus
                tipo: "miudo"
                text: "+" + (s.n - s.mostrados)
                color: s.ativa ? Tema.mistura(Tema.destaque, "#ffffff", 0.55) : Tema.textoSuave
                anchors.verticalCenter: parent.verticalCenter
            }
        }
        TextoPixel {
            visible: s.vazia
            tipo: "rotulo"
            text: "vazia"
            font.capitalization: Font.AllUppercase
            color: Tema.alfa(Tema.textoSuave, 0.5)
            anchors.right: parent.right
            anchors.rightMargin: 3 * Tema.px
            y: Tema.grade((parent.height - height) / 2)
        }

        MouseArea {
            id: toque
            anchors.fill: parent
            hoverEnabled: true
            cursorShape: s.ativa ? Qt.ArrowCursor : Qt.PointingHandCursor
            onClicked: mapa.focar(s.sala)
        }
    }

    // bauzinho 5 x 4 pixels de arte: tampa clara, aro escuro, fecho de ouro
    component Bau: Item {
        property bool ativa: false
        readonly property color corpo: ativa ? Tema.destaque : Tema.mistura(Tema.textoSuave, Tema.fundo, 0.3)
        width: 5 * Tema.px
        height: 4 * Tema.px
        Rectangle { width: parent.width; height: parent.height; color: Tema.mistura(parent.corpo, "#000000", 0.25) }
        Rectangle { width: parent.width; height: Tema.px; color: Tema.mistura(parent.corpo, "#ffffff", 0.45) }
        Rectangle { y: Tema.px; width: parent.width; height: Tema.px; color: parent.corpo }
        Rectangle { y: 2 * Tema.px; width: parent.width; height: Tema.px; color: Tema.mistura(Tema.fundo, "#000000", 0.3) }
        Rectangle { x: 2 * Tema.px; y: Tema.px; width: Tema.px; height: 2 * Tema.px; color: Tema.ouro }
    }

    component Seta: Image {
        property bool paraCima: false
        source: Tema.peca("seta-baixo")
        mirrorVertically: paraCima
        smooth: false
        width: 7 * Tema.px
        height: 5 * Tema.px
    }
}
