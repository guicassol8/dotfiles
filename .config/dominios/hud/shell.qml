import QtQuick
import Quickshell
import Quickshell.Io
import Quickshell.Wayland
import Quickshell.Niri
import qs.componentes
import qs.casca

// Casca do HUD do grimorio: UMA superficie em tela cheia na camada Bottom (acima do
// papel do Noctalia, abaixo das janelas). O clique atravessa onde nao ha widget.
// "Abrir o grimorio" (IPC `hud alternar`) traz a mesma superficie para a camada
// Overlay, com o fundo escurecido, sem duplicar nada.
// Paisagem (`hud paisagem`, Mod+Shift+G): os widgets somem, fica so o cenario, e a mesa
// deixa o clique passar inteiro. Contemplacao (`hud ocioso`/`voltou`, pelo ocioso do
// Noctalia, ou `hud contemplar`): o cenario sobe opaco por cima de tudo, sem pegar
// teclado nem clique; qualquer entrada desfaz.
//
//   qs -p ~/.config/dominios/hud                     sobe (ou use hud/hud ligar)
//   qs ipc -p ~/.config/dominios/hud call hud alternar
//
// Troca de workspace: o letreiro da sala (casca/Letreiro.qml), numa superficie pequena
// na camada Top que so existe enquanto aparece.
//
// Variaveis: HUD_DEV=1 (camada Overlay, fundo opaco, cena opaca, sem teclado: para foto;
// nunca mostra nada do dono), HUD_DEV_ABERTO=1 (com HUD_DEV: nasce com o grimorio aberto),
// HUD_MESA (outro mesa.json), HUD_NUCLEO (outro comando do nucleo, ou "nao"),
// HUD_ELEMENTO (fixa o elemento), DOMINIOS_TEMA (outro hud-tema.json).
ShellRoot {
    id: raiz

    // o workspace a vista esta sem janelas? (sem niri, considera que sim)
    readonly property bool devAberto: Hud.dev && Quickshell.env("HUD_DEV_ABERTO") === "1"
    readonly property bool mesaLivre: {
        if (Hud.dev)                        // foto: a mesa livre, ou janelas fingidas na frente
            return !devAberto;
        const lista = Niri.workspaces ? Niri.workspaces.values : [];
        for (let i = 0; i < lista.length; i++) {
            const w = lista[i];
            if (w.active && (!tela.screen || w.output === tela.screen.name))
                return !w.occupied;
        }
        return true;
    }
    Binding { target: Hud; property: "mesaLivre"; value: raiz.mesaLivre }
    // a mesa ficou livre ou foi coberta com o grimorio aberto: fecha, senao ele pularia
    // por cima da proxima janela aberta
    onMesaLivreChanged: if (Hud.aberto && !Hud.dev) Hud.fechar()
    Binding { target: Nucleo; property: "amostrar"; value: Hud.visivel && !Hud.recolhido }

    // ---- contemplacao: a mesma superficie sobe para Overlay com o cenario opaco
    property bool contemplaCima: false
    property bool _quietoVisto: false
    // regiao de entrada da mesa: os itens clicaveis, ou nada quando o clique tem de atravessar
    function refazEntrada() {
        const velhas = entrada.regions;
        const novas = [];
        const atravessa = Hud.contemplando || raiz.contemplaCima || (Hud.paisagem && !raiz.porCima);
        if (!atravessa)
            for (let i = 0; i < mesa.toques.length; i++)
                novas.push(pedaco.createObject(entrada, { item: mesa.toques[i] }));
        entrada.regions = novas;
        for (let i = 0; i < velhas.length; i++)
            velhas[i].destroy();
    }
    Connections {
        target: Hud
        function onContemplandoChanged() {
            if (Hud.contemplando) {
                largaContemplacao.stop();
                raiz._quietoVisto = false;
                if (!Hud.mesaLivre && !raiz.porCima) {
                    // janelas na frente: o cenario comeca invisivel e os widgets nao aparecem
                    mesa.ocultar = true;
                    mesa.cenario = false;
                }
                sobeContemplacao.restart();
            } else {
                sobeContemplacao.stop();
                if (Hud.mesaLivre && !raiz.porCima) {
                    mesa.cenario = true;            // a mesa esta a vista: o cenario fica
                    mesa.ocultar = false;
                }
                contempla.to = 0;
                contempla.duration = 220;           // volta rapida
                contempla.restart();
                largaContemplacao.restart();
            }
        }
    }
    Timer {
        id: sobeContemplacao
        interval: 50
        onTriggered: {
            raiz.contemplaCima = true;
            contempla.to = 1;
            contempla.duration = 1200;
            contempla.restart();
        }
    }
    Timer {
        id: largaContemplacao
        interval: 240
        onTriggered: {
            raiz.contemplaCima = false;
            if (!raiz.porCima)
                mesa.cenario = true;
            mesa.ocultar = false;
        }
    }
    NumberAnimation { id: contempla; target: mesa; property: "contemplar"; easing.type: Easing.InOutQuad }

    // a volta: qualquer entrada depois de um instante parado (vale tambem para `hud contemplar`,
    // que nao passa pelo ocioso do Noctalia). O `hud voltou` do Noctalia chega pelo IPC.
    IdleMonitor {
        enabled: Hud.contemplando && !Hud.dev
        timeout: 1.5
        respectInhibitors: false
        onIsIdleChanged: {
            if (isIdle)
                raiz._quietoVisto = true;
            else if (raiz._quietoVisto && Hud.contemplando)
                Hud.despertar();
        }
    }

    // ---- camada: sobe para Overlay so quando ha janelas na frente da mesa
    readonly property bool querSubir: Hud.aberto && !Hud.mesaLivre
    property bool porCima: false
    onQuerSubirChanged: {
        if (querSubir) {
            desce.stop();
            mesa.cenario = false;           // o cenario passa a seguir o veu (0) ANTES de trocar de camada
            sobe.restart();
        } else {
            sobe.stop();
            escurece.to = 0;
            escurece.restart();
            desce.restart();
        }
    }
    Timer {
        id: sobe
        interval: 50
        onTriggered: {
            raiz.porCima = true;
            escurece.to = 1;
            escurece.restart();
        }
    }
    Timer {
        id: desce
        interval: 240
        onTriggered: {
            raiz.porCima = false;
            mesa.cenario = true;
        }
    }
    NumberAnimation { id: escurece; target: mesa; property: "veu"; duration: 220; easing.type: Easing.OutQuad }

    PanelWindow {
        id: tela
        screen: {
            const lista = Quickshell.screens;
            for (let i = 0; i < lista.length; i++)
                if (lista[i].name === "eDP-1")
                    return lista[i];
            return lista[0];
        }
        anchors { top: true; bottom: true; left: true; right: true }
        exclusionMode: ExclusionMode.Ignore
        color: Hud.dev ? Tema.fundo : "transparent"
        WlrLayershell.namespace: "dominios-hud"
        WlrLayershell.layer: raiz.porCima || raiz.contemplaCima || Hud.dev ? WlrLayer.Overlay : WlrLayer.Bottom
        // por cima das janelas o grimorio pega o teclado enquanto esta aberto: Esc fecha de
        // primeira. Fechado, nunca pega (o atalho Mod+G e do niri e funciona sempre).
        // Na contemplacao, nunca: a primeira tecla do dono vai para a janela dele.
        WlrLayershell.keyboardFocus: raiz.porCima && !Hud.dev && !Hud.contemplando ? WlrKeyboardFocus.Exclusive : WlrKeyboardFocus.None
        // contemplacao e paisagem: o clique atravessa tudo. A mascara e sempre a MESMA regiao
        // (`entrada`), que fica vazia nesses modos (raiz.refazEntrada). Trocar a mascara por
        // outra Region vazia e voltar deixava a mesa sem clique ate reiniciar (visto em 12/11).
        mask: raiz.porCima && !Hud.contemplando && !raiz.contemplaCima ? null : entrada

        Region { id: entrada }
        Component { id: pedaco; Region {} }
        Connections {
            target: Hud
            function onPaisagemChanged() { raiz.refazEntrada(); }
            function onContemplandoChanged() { raiz.refazEntrada(); }
        }
        Connections {
            target: raiz
            function onContemplaCimaChanged() { raiz.refazEntrada(); }
            function onPorCimaChanged() { raiz.refazEntrada(); }
        }

        MouseArea {                         // clique no vazio fecha o grimorio (so recebe clique quando esta por cima)
            anchors.fill: parent
            enabled: raiz.porCima && !Hud.contemplando
            onClicked: Hud.fechar()
        }
        Mesa {
            id: mesa
            width: 1920
            height: 1080
            focus: true
            Keys.onEscapePressed: Hud.fechar()
            onToquesChanged: raiz.refazEntrada()
        }
    }

    // ---- letreiro de sala: ao trocar de workspace, "Sala 2" e as janelas dela no meio da
    // tela por uns 750 ms, por cima das janelas (casca/Letreiro.qml). Mora numa superficie
    // propria na camada Top, que so existe durante o letreiro e 20 s depois (trocas em
    // seguida reusam); parada nao custa nada. Nunca pega clique nem teclado.
    // Desliga com `letreiro_sala = false` em [grimorio.hud] no dominios.toml.
    readonly property bool letreiroLigado: Tema.ajustes.letreiro_sala !== false && !Hud.dev
    readonly property var salaAtiva: {
        const lista = Niri.workspaces ? Niri.workspaces.values : [];
        for (let i = 0; i < lista.length; i++) {
            const w = lista[i];
            if (w.active && (!tela.screen || w.output === tela.screen.name))
                return w;
        }
        return null;
    }
    property int _salaVista: -1
    onSalaAtivaChanged: {
        const w = salaAtiva;
        if (!w || w.id === _salaVista)
            return;
        const antes = _salaVista;
        _salaVista = w.id;
        if (antes >= 0)                     // na subida do HUD nao mostra
            mostrarLetreiro(false);
    }
    // Evento curto (como as animacoes do niri), entao vale tambem na bateria; a memoria
    // apertada e a paisagem seguram. `naMao` (hud letreiro): mostra mesmo em paisagem.
    // Devolve "" ou o motivo.
    function mostrarLetreiro(naMao) {
        const w = salaAtiva;
        if (!letreiroLigado)
            return "desligado em [grimorio.hud]";
        if (!w)
            return "sem workspace do niri";
        if (Hud.recolhido || Hud.contemplando || Hud.aberto || Hud.abertura || Niri.overviewActive)
            return "agora não (grimório aberto, contemplação, visão geral ou memória crítica)";
        if (Hud.apertado)
            return "memória apertada";
        if (!naMao && Hud.paisagem)
            return "modo paisagem";
        const jan = Niri.windows ? Niri.windows.values : [];
        let n = 0;
        for (let i = 0; i < jan.length; i++)
            if (jan[i].workspaceId === w.id)
                n++;
        _pedido = { sala: w.idx, nome: w.name || "", janelas: n };
        soltaPlaca.restart();
        if (placaSala.item)
            _entrega();
        else
            placaSala.active = true;        // _entrega quando a superficie nascer
        return "";
    }
    property var _pedido: null
    function _entrega() {
        const p = _pedido;
        _pedido = null;
        if (p && placaSala.item)
            placaSala.item.letreiro.mostrar(p.sala, p.nome, p.janelas);
    }
    Connections {
        target: Hud
        function onPaisagemChanged() { if (placaSala.item) placaSala.item.letreiro.esconder(); }
        function onContemplandoChanged() { if (placaSala.item) placaSala.item.letreiro.esconder(); }
        function onAbriu() { if (placaSala.item) placaSala.item.letreiro.esconder(); }
    }
    LazyLoader {
        id: placaSala
        active: false
        onItemChanged: if (item) raiz._entrega()
        PanelWindow {
            readonly property alias letreiro: letreiro
            screen: tela.screen
            visible: letreiro.ativo
            anchors.top: true
            margins.top: Tema.grade(540 - letreiro.implicitHeight / 2)
            implicitWidth: letreiro.implicitWidth
            implicitHeight: letreiro.implicitHeight
            exclusionMode: ExclusionMode.Ignore
            color: "transparent"
            WlrLayershell.namespace: "dominios-hud-sala"
            WlrLayershell.layer: WlrLayer.Top
            WlrLayershell.keyboardFocus: WlrKeyboardFocus.None
            // sem clique: a mascara e sempre esta mesma regiao vazia, nunca trocada
            mask: Region {}
            Letreiro { id: letreiro; anchors.fill: parent }
        }
    }
    Timer {
        id: soltaPlaca
        interval: 20000
        onTriggered: {
            if (placaSala.item && placaSala.item.letreiro.ativo)
                restart();
            else
                placaSala.active = false;
        }
    }

    Component.onCompleted: {
        if (devAberto)
            Hud.abrir();
        if (Quickshell.env("HUD_ABERTURA") !== "1")
            marca.running = true;           // com HUD_ABERTURA=1 a propria Mesa abre (teste)
    }

    // abertura do login: `hud sessao` deixa esta marca antes de subir o servico. Ela vale
    // uma vez e so por 2 min: reinicio por falha e `hud ligar` comum nao tem abertura.
    Process {
        id: marca
        command: ["sh", "-c", "f=\"${XDG_RUNTIME_DIR:-/tmp}/dominios-hud-abertura\"; [ -n \"$(find \"$f\" -mmin -2 2>/dev/null)\" ] && echo sim; rm -f \"$f\""]
        stdout: StdioCollector { onStreamFinished: if (text.trim() === "sim") mesa.abrirTitulo() }
    }

    // o qs recarrega sozinho quando um .qml muda; o aviso flutuante dele cobriria as
    // janelas do dono: fica so no registro (hud log)
    Connections {
        target: Quickshell
        function onReloadCompleted() { Quickshell.inhibitReloadPopup(); }
        function onReloadFailed(erro) { Quickshell.inhibitReloadPopup(); console.warn("hud: recarga falhou: " + erro); }
    }

    IpcHandler {
        target: "hud"
        function abrir(): void { Hud.abrir(); }
        function fechar(): void { Hud.fechar(); }
        function alternar(): void { Hud.alternar(); }
        function abertura(): void { mesa.abrirTitulo(); }
        function dizer(titulo: string, texto: string): void { Hud.dizer({ titulo: titulo, texto: texto, retrato: "grimorio" }); }
        // modo: "alternar" (ou vazio), "ligar", "desligar"; devolve "ligada" ou "desligada"
        function paisagem(modo: string): string {
            Hud.definirPaisagem(modo === "ligar" ? true : modo === "desligar" ? false : !Hud.paisagem);
            return Hud.paisagem ? "ligada" : "desligada";
        }
        // contemplacao na mao (teste): so o modo critico impede. Devolve "" ou o motivo.
        function contemplar(): string { return Hud.contemplar(false); }
        // pelo ocioso do Noctalia: na bateria e com a memoria apertada nao entra
        function ocioso(): string { return Hud.contemplar(true); }
        function voltou(): void { Hud.despertar(); }
        // o letreiro da sala atual agora (para conferir); devolve "" ou o motivo
        function letreiro(): string { return raiz.mostrarLetreiro(true); }
        function estado(): string {
            return JSON.stringify({
                aberto: Hud.aberto, por_cima: raiz.porCima, mesa_livre: Hud.mesaLivre, recolhido: Hud.recolhido,
                paisagem: Hud.paisagem, contemplando: Hud.contemplando,
                elemento: Tema.elemento, widgets: mesa.vagas.length, cenario: mesa.temPapel, nucleo: Nucleo.vivo
            });
        }
    }
}
