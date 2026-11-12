import QtQuick
import Quickshell
import Quickshell.Io
import qs.componentes

// Mesa: tudo o que a casca desenha, de baixo para cima: o cenario vivo
// (papel/Papel.qml, se existir), o veu que escurece o fundo quando o grimorio abre
// por cima das janelas, os widgets de mesa.json e a caixa de dialogo.
// Fica separada do shell.qml para poder ser desenhada fora da tela:
//   hud/dev/prova casca/Mesa.qml --tamanho 1920x1080
Item {
    id: mesa

    property bool cenario: true             // false: o cenario segue o veu (grimorio por cima das janelas)
    property real veu: 0                    // 0 a 1, escurecimento atras dos widgets
    property real contemplar: 0             // 0 a 1, o cenario opaco por cima das janelas (contemplacao)
    // widgets, dialogo e a calma do cenario: somem em paisagem e na contemplacao (esmaecer de 500 ms)
    property real mostrar: Hud.paisagem || Hud.contemplando ? 0 : 1
    Behavior on mostrar { NumberAnimation { duration: 500; easing.type: Easing.InOutQuad } }
    // a casca liga isto enquanto o cenario cobre janelas sem o grimorio aberto: os widgets
    // nao podem aparecer por cima delas nem um quadro
    property bool ocultar: false
    readonly property real _widgets: ocultar ? 0 : mostrar
    readonly property string pasta: Quickshell.shellDir
    readonly property string caminhoMesa: Quickshell.env("HUD_MESA") || pasta + "/mesa.json"

    property var vagas: []                  // vagas de mesa.json cujo widget existe
    property bool temPapel: false
    readonly property alias dialogo: dialogo
    readonly property alias papel: papel
    // itens que recebem clique: a casca monta a mascara de entrada com eles
    property var toques: []
    signal vagasProntas()

    implicitWidth: 1920
    implicitHeight: 1080

    // ---- layout: mesa.json + o que existe em widgets/
    Arquivo {
        id: layout
        caminho: mesa.caminhoMesa
        onAtualizado: lista.running = true
        onErroChanged: if (erro !== "") console.warn("mesa: " + erro)
    }
    Process {
        id: lista
        command: ["sh", "-c", "cd \"$1\" && ls -1 widgets 2>/dev/null; [ -f papel/Papel.qml ] && echo @papel", "sh", mesa.pasta]
        stdout: StdioCollector {
            onStreamFinished: {
                const nomes = text.split("\n");
                mesa.temPapel = nomes.indexOf("@papel") >= 0;
                const lidas = layout.dados && Array.isArray(layout.dados.vagas) ? layout.dados.vagas : [];
                const boas = [];
                for (const v of lidas) {
                    if (!v || !v.widget || v.ativo === false)
                        continue;
                    if (nomes.indexOf(v.widget + ".qml") < 0)
                        continue;           // vaga reservada: o widget ainda nao foi escrito
                    boas.push(v);
                }
                mesa.vagas = boas;
            }
        }
    }

    // ---- cenario vivo (de outro agente): so carrega se o arquivo existir
    Loader {
        id: papel
        anchors.fill: parent
        active: mesa.temPapel && !Hud.recolhido
        // por cima das janelas (grimorio aberto) o cenario entra junto com o veu, quase opaco:
        // o mundo do grimorio toma a tela e as janelas ficam so como sombra atras
        opacity: mesa.cenario ? 1 : Math.max(0.92 * mesa.veu, mesa.contemplar)
        visible: opacity > 0
        source: active ? Qt.resolvedUrl("../papel/Papel.qml") : ""
        onStatusChanged: if (status === Loader.Error) console.warn("mesa: papel/Papel.qml nao carregou; seguindo sem cenario")
    }
    // entradas do cenario: elemento do Nucleo, chuva e sol do clima, grave do Bardo, hora do relogio.
    // Congela (rodando false) escondido, na bateria e com a memoria apertada: Hud.animarCena.
    readonly property var _clima: Nucleo.elemento && Nucleo.elemento.clima ? Nucleo.elemento.clima : null
    readonly property real chuva: {
        const c = _clima;
        if (!c)
            return 0;
        // intensidade pelo codigo WMO (garoa, chuva, pancada, temporal) ou pelos milimetros
        const k = c.codigo || 0;
        const porCodigo = ({ 51: 0.25, 53: 0.35, 55: 0.45, 56: 0.35, 57: 0.45, 61: 0.45, 63: 0.65, 65: 0.9,
                             66: 0.5, 67: 0.7, 80: 0.5, 81: 0.7, 82: 0.95, 95: 0.85, 96: 0.9, 99: 1 })[k] || 0;
        const mm = c.chuva_mm || 0;
        return Math.max(porCodigo, mm > 0 ? Math.min(1, 0.3 + mm / 4) : 0);
    }
    function _horaIso(t, padrao) {          // "2026-11-11T05:22:00-03:00" -> 5.37
        const m = /T(\d\d):(\d\d)/.exec(t || "");
        return m ? Number(m[1]) + Number(m[2]) / 60 : padrao;
    }
    Binding { target: papel.item; when: papel.status === Loader.Ready; property: "elemento"; value: Hud.abertura ? "titulo" : Tema.elemento }
    Binding { target: papel.item; when: papel.status === Loader.Ready; property: "rodando"; value: (mesa.cenario || mesa.veu > 0 || mesa.contemplar > 0) && Hud.animarCena }
    // em paisagem e na contemplacao a calma atras dos widgets e o poco do relogio somem junto
    Binding { target: papel.item; when: papel.status === Loader.Ready; property: "mesa"; value: mesa.mostrar }
    // $HUD_FPS troca o ritmo do cenario (medicao de CPU); o padrao fica no Papel
    readonly property int fps: Number(Quickshell.env("HUD_FPS") || 0)
    Binding { target: papel.item; when: papel.status === Loader.Ready && mesa.fps > 0; property: "fps"; value: mesa.fps }
    Binding { target: papel.item; when: papel.status === Loader.Ready; property: "chuva"; value: mesa.chuva }
    Binding { target: papel.item; when: papel.status === Loader.Ready; property: "pulso"; value: Hud.pulso }
    Binding { target: papel.item; when: papel.status === Loader.Ready; property: "hora"; value: Hud.hora }
    Binding { target: papel.item; when: papel.status === Loader.Ready; property: "nascer"; value: mesa._horaIso(mesa._clima ? mesa._clima.nascer : "", 5.5) }
    Binding { target: papel.item; when: papel.status === Loader.Ready; property: "por"; value: mesa._horaIso(mesa._clima ? mesa._clima.por : "", 19) }
    // surto de luz no cenario quando o elemento troca de verdade (nao na subida)
    Connections {
        target: Tema
        function onElementoChanged() { if (papel.item && mesa.vagas.length > 0 && !Hud.abertura) papel.item.surto(); }
    }

    Rectangle {
        anchors.fill: parent
        color: Qt.rgba(0.03, 0.02, 0.06, 0.62)
        opacity: mesa.veu * (papel.status === Loader.Ready ? 0.45 : 1) * mesa.mostrar   // com o cenario atras, so um toque
        visible: opacity > 0
    }

    // ---- widgets
    Repeater {
        id: pecas
        model: Hud.recolhido || Hud.abertura ? [] : mesa.vagas
        Loader {
            id: vaga
            required property var modelData
            required property int index
            x: modelData.x
            y: modelData.y
            width: modelData.largura
            height: modelData.altura
            opacity: mesa._widgets
            visible: opacity > 0
            source: Qt.resolvedUrl("../widgets/" + modelData.widget + ".qml")
            onLoaded: {
                if (item.atraso !== undefined)
                    item.atraso = 90 + index * 70;          // cascata de abertura
                const p = modelData.props;
                if (p)
                    for (const k in p) item[k] = p[k];
                mesa._refazToques();
            }
            onStatusChanged: if (status === Loader.Error) console.warn("mesa: widgets/" + modelData.widget + ".qml nao carregou; a vaga fica vazia")
            // grimorio aberto por cima das janelas: clique no corpo de um widget fica nele
            // (sem isto atravessaria ate o fundo da casca, que fecha o grimorio)
            MouseArea {
                z: -1
                anchors.fill: parent
                enabled: Hud.aberto
                acceptedButtons: Qt.AllButtons
            }
        }
        onCountChanged: mesa._refazToques()
    }

    function _refazToques() {
        const l = [];
        for (let i = 0; i < pecas.count; i++) {
            const it = pecas.itemAt(i);
            if (it && it.status === Loader.Ready)
                l.push(it);
        }
        if (dialogo.falando)
            l.push(dialogo);
        toques = l;
    }

    // ---- caixa de dialogo: a voz do grimorio
    Dialogo {
        id: dialogo
        width: 900
        height: 126
        x: Tema.grade((parent.width - width) / 2)
        y: parent.height - 234 - height - 18
        z: 10
        opacity: mesa._widgets
        visible: opacity > 0 && !Hud.recolhido && !Hud.abertura
        onFalandoChanged: mesa._refazToques()
    }
    Connections {
        target: Nucleo
        function onDialogo(fala) { dialogo.enfileirar(fala); }
    }
    Connections {
        target: Hud
        function onFala(f) { dialogo.enfileirar(f); }
    }

    // ---- cartela ao abrir o grimorio (Mod+G): o nome em gotico, aparece, segura e some
    Column {
        id: cartela
        x: Tema.grade(mesa.width / 2 - width / 2)
        y: Tema.grade(558 - height / 2)
        z: 5
        spacing: 12
        opacity: 0
        visible: opacity > 0 && !Hud.recolhido && !Hud.abertura
        TextoPixel { tipo: "goticoGrande"; sombra: true; contorno: true; color: Tema.destaque; text: "Grimório"; anchors.horizontalCenter: parent.horizontalCenter }
        TextoPixel { tipo: "rotulo"; sombra: true; contorno: true; color: Tema.texto; text: Tema.textos.rotulo || ""; anchors.horizontalCenter: parent.horizontalCenter }
        SequentialAnimation {
            id: mostraCartela
            NumberAnimation { target: cartela; property: "opacity"; to: 1; duration: 260; easing.type: Easing.OutQuad }
            PauseAnimation { duration: 1100 }
            NumberAnimation { target: cartela; property: "opacity"; to: 0; duration: 700; easing.type: Easing.InQuad }
        }
    }
    Connections {
        target: Hud
        function onAbriu() { cartela.opacity = 0; mostraCartela.restart(); }
        function onFechou() { mostraCartela.stop(); cartela.opacity = 0; }
    }

    // ---- abertura do login: a cena de titulo (papel/cenas/titulo.png pelo shader), o nome
    // do jogo em gotico no terco de cima e o capitulo do elemento ativo. Uns 3 s; depois a
    // cena varre para o lugar do elemento e os widgets desdobram em cascata.
    // So a casca chama, quando o HUD sobe pelo `hud sessao` (nunca em reinicio).
    function abrirTitulo() {
        if (Hud.recolhido)
            return;
        Hud.abertura = true;
        letreiro.opacity = 0;
        roteiro.restart();
        if (Nucleo.vivo)
            Nucleo.som("login");
        else
            somPendente = true;
    }
    property bool somPendente: false
    Component.onCompleted: if (Quickshell.env("HUD_ABERTURA") === "1") abrirTitulo()
    Connections {
        target: Nucleo
        function onVivoChanged() { if (Nucleo.vivo && mesa.somPendente) { mesa.somPendente = false; Nucleo.som("login"); } }
    }
    Column {
        id: letreiro
        x: Tema.grade(mesa.width / 2 - width / 2)
        y: 72
        z: 6
        spacing: 18
        opacity: 0
        visible: opacity > 0
        TextoPixel { tipo: "goticoGrande"; sombra: true; contorno: true; color: Tema.texto; text: "Despertar da Mana"; anchors.horizontalCenter: parent.horizontalCenter }
        Row {
            anchors.horizontalCenter: parent.horizontalCenter
            spacing: 12
            Figura { fonte: "florao"; anchors.verticalCenter: parent.verticalCenter; anchors.verticalCenterOffset: 4 }
            TextoPixel {
                tipo: "gotico"
                sombra: true
                contorno: true
                color: Tema.destaque
                readonly property var nomes: ({ fogo: "do Fogo", agua: "da Água", terra: "da Terra", vento: "do Vento",
                                                 eletricidade: "da Eletricidade", "mana-pura": "da Mana Pura" })
                text: "Capítulo " + (nomes[Tema.elemento] || "da Mana")
            }
            Figura { fonte: "florao"; anchors.verticalCenter: parent.verticalCenter; anchors.verticalCenterOffset: 4 }
        }
    }
    SequentialAnimation {
        id: roteiro
        PauseAnimation { duration: 350 }
        NumberAnimation { target: letreiro; property: "opacity"; to: 1; duration: 600; easing.type: Easing.OutQuad }
        PauseAnimation { duration: 1500 }
        NumberAnimation { target: letreiro; property: "opacity"; to: 0; duration: 500; easing.type: Easing.InQuad }
        ScriptAction { script: Hud.abertura = false }
    }

    // ---- paisagem (Mod+Shift+G): um letreiro no canto ao entrar e ao sair, some em 2 s
    Item {
        id: avisoPaisagem
        x: mesa.width - width - 24
        y: mesa.height - height - 24
        z: 8
        width: Tema.grade(textoPaisagem.width) + 30
        height: 33
        opacity: 0
        visible: opacity > 0 && !Hud.recolhido && !Hud.contemplando
        Fatias { anchors.fill: parent; fonte: "placa-normal"; bordaEsquerda: 5; bordaDireita: 5 }
        TextoPixel {
            id: textoPaisagem
            x: 15
            y: parent.height / 2 - height / 2 - 1
            tipo: "rotulo"
            color: Tema.texto
            text: Hud.paisagem ? "SÓ O CENÁRIO · MOD+SHIFT+G VOLTA" : "A MESA VOLTOU"
        }
        SequentialAnimation {
            id: mostraAvisoPaisagem
            NumberAnimation { target: avisoPaisagem; property: "opacity"; to: 1; duration: 200; easing.type: Easing.OutQuad }
            PauseAnimation { duration: 1400 }
            NumberAnimation { target: avisoPaisagem; property: "opacity"; to: 0; duration: 400; easing.type: Easing.InQuad }
        }
    }
    Connections {
        target: Hud
        function onPaisagemMudou(ligada) { avisoPaisagem.opacity = 0; mostraAvisoPaisagem.restart(); }
    }

    // ---- contemplacao: so o cenario, com a hora e o lugar pequenos no canto de baixo
    Column {
        id: placaLugar
        x: 36
        y: mesa.height - height - 33
        z: 7
        spacing: 6
        opacity: 0                          // entra devagar depois do cenario, sai na hora
        visible: opacity > 0 && !Hud.recolhido
        SequentialAnimation {
            id: entraLugar
            PauseAnimation { duration: 900 }
            NumberAnimation { target: placaLugar; property: "opacity"; to: 1; duration: 1200; easing.type: Easing.InOutQuad }
        }
        NumberAnimation { id: saiLugar; target: placaLugar; property: "opacity"; to: 0; duration: 150 }
        Connections {
            target: Hud
            function onContemplandoChanged() {
                if (Hud.contemplando) { saiLugar.stop(); entraLugar.restart(); }
                else { entraLugar.stop(); saiLugar.restart(); }
            }
        }
        Component.onCompleted: if (Hud.contemplando) opacity = 1     // teste (HUD_CONTEMPLAR=1)
        readonly property var lugares: ({ fogo: "Forja", agua: "Santuário Submerso", terra: "Ruínas na Floresta",
                                          vento: "Picos no Céu", eletricidade: "Torre da Tempestade",
                                          "mana-pura": "Biblioteca Arcana" })
        readonly property var nomes: ({ fogo: "Fogo", agua: "Água", terra: "Terra", vento: "Vento",
                                        eletricidade: "Eletricidade", "mana-pura": "Mana Pura" })
        TextoPixel {
            tipo: "grande"
            sombra: true
            contorno: true
            color: Tema.texto
            text: Qt.formatTime(Hud.agora, "HH:mm")
        }
        Row {
            spacing: 9
            Icone { nome: Tema.elemento; anchors.verticalCenter: parent.verticalCenter }
            TextoPixel {
                anchors.verticalCenter: parent.verticalCenter
                tipo: "rotulo"
                sombra: true
                contorno: true                  // so contorno, sem sombra, some fora da tela
                color: Tema.destaque
                text: ((placaLugar.lugares[Tema.elemento] || "Grimório") + " · " + (placaLugar.nomes[Tema.elemento] || "Mana")).toUpperCase()
            }
        }
    }

    // ---- memoria no limite: so um aviso pequeno
    Item {
        visible: Hud.recolhido
        x: parent.width - width - 24
        y: parent.height - height - 24
        width: Tema.grade(aviso.width) + 30
        height: 33
        Fatias { anchors.fill: parent; fonte: "placa-perigo"; bordaEsquerda: 5; bordaDireita: 5 }
        TextoPixel {
            id: aviso
            x: 15
            y: parent.height / 2 - height / 2 - 1
            tipo: "rotulo"
            color: Tema.perigo
            text: "MEMÓRIA NO LIMITE: O GRIMÓRIO SE RECOLHEU"
        }
    }
}
