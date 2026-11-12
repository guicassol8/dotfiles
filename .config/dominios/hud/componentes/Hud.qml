pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Io

// Hud: estado vivo do HUD, visivel para a casca e para qualquer widget.
Singleton {
    id: hud

    // o grimorio esta aberto por cima das janelas (Mod+G)
    property bool aberto: false
    // o workspace atual esta sem janelas: a mesa aparece inteira (a casca atualiza)
    property bool mesaLivre: true
    // modo paisagem (Mod+Shift+G): os widgets somem e fica so o cenario. Guardado em
    // ~/.local/state/dominios/hud.json (lido na subida, sem animar). $HUD_PAISAGEM=1 nasce
    // ligado (teste); na prova e com HUD_DEV o arquivo nao e lido nem gravado.
    property bool paisagem: Quickshell.env("HUD_PAISAGEM") === "1" || _guardado().paisagem === true
    readonly property bool _guarda: (!dev && !Quickshell.env("HUD_PROVA")) || !!Quickshell.env("DOMINIOS_ESTADO")
    function _guardado() {
        if (!_guarda)
            return {};
        try { return JSON.parse(estadoArq.text()) || {}; } catch (e) { return {}; }
    }
    FileView {
        id: estadoArq
        path: hud._guarda ? Nucleo.pastaEstado + "/hud.json" : ""
        blockAllReads: true
        printErrors: false
    }
    // contemplacao (protetor de tela): o cenario em tela cheia por cima de tudo, sem widgets.
    // Entra pelo ocioso do Noctalia (`hud ocioso`) ou na mao (`hud contemplar`).
    property bool contemplando: Quickshell.env("HUD_CONTEMPLAR") === "1"
    // ha alguma chance de o dono estar vendo o cenario
    readonly property bool cenaVisivel: aberto || mesaLivre || contemplando
    // ... e os widgets (em paisagem e na contemplacao eles somem)
    readonly property bool visivel: (aberto || mesaLivre) && !paisagem && !contemplando
    // memoria no limite: a casca descarrega cenario e widgets
    readonly property bool recolhido: Nucleo.pressao !== null && Nucleo.pressao.nivel === "critico"
    // memoria apertada: tudo para (o cenario congela), mas continua carregado
    readonly property bool apertado: Nucleo.pressao !== null && Nucleo.pressao.nivel === "apertado"
    // na bateria tudo congela num quadro (decisao do dono em 12/11: animacao so carregando).
    // Com a amostragem ligada vale o canal `maquina` (2 s); sem ela, o resumo que vem no
    // `elemento` (1 min).
    readonly property bool naBateria: {
        const m = Nucleo.amostrar && Nucleo.maquina ? Nucleo.maquina : (Nucleo.elemento ? Nucleo.elemento.maquina : null);
        return !!m && m.na_tomada === false;
    }
    // o cenario vivo anda (10 fps) so se isto for true
    readonly property bool animarCena: cenaVisivel && !recolhido && !apertado && !naBateria
    // animacao ociosa dos widgets (gema que pisca, seta, sprite animado, visualizador)
    // so roda se isto for true
    readonly property bool animar: visivel && animarCena

    // abertura do login (tela de titulo): a mesa espera, sem widgets nem dialogo
    property bool abertura: false

    // grave da musica, 0..1: o Bardo escreve, o cenario pulsa com ele
    property real pulso: 0

    // relogio unico do HUD (minutos): o Relogio mostra, o cenario tira a luz da hora
    readonly property date agora: relogio.date
    // $HUD_HORA (0..24) fixa a hora do cenario: teste das variantes de aurora, dia, entardecer
    readonly property real hora: Quickshell.env("HUD_HORA") ? Number(Quickshell.env("HUD_HORA")) : agora.getHours() + agora.getMinutes() / 60
    SystemClock { id: relogio; precision: SystemClock.Minutes }

    // $HUD_DEV=1: modo de teste. A casca nasce aberta, com fundo opaco e sem pegar
    // teclado, para poder ser fotografada sem mostrar nada do dono.
    readonly property bool dev: Quickshell.env("HUD_DEV") === "1"

    signal abriu()
    signal fechou()
    function abrir() { if (!aberto) { aberto = true; abriu(); } }
    function fechar() { if (aberto) { aberto = false; fechou(); } }
    function alternar() { aberto ? fechar() : abrir(); }

    // paisagem: aviso curto no canto ao entrar e sair (a Mesa mostra)
    signal paisagemMudou(bool ligada)
    function definirPaisagem(v) {
        if (paisagem === v)
            return;
        paisagem = v;
        paisagemMudou(v);
        if (_guarda)
            estadoArq.setText(JSON.stringify({ paisagem: v }) + "\n");
    }

    // contemplacao. `automatica`: veio do ocioso, e so entra se a maquina deixa (na tomada,
    // memoria folgada); na mao (`hud contemplar`) so o modo critico impede.
    // Devolve "" se entrou, senao o motivo.
    function contemplar(automatica) {
        if (contemplando)
            return "";
        if (recolhido)
            return "memória crítica";
        if (abertura)
            return "abertura do login";
        if (automatica && naBateria)
            return "na bateria";
        if (automatica && apertado)
            return "memória apertada";
        contemplando = true;
        return "";
    }
    function despertar() { contemplando = false; }
    onRecolhidoChanged: if (recolhido) contemplando = false

    // fala na caixa de dialogo: Hud.dizer({ titulo: "Grimório", texto: "...",
    // retrato: "grimorio", tipo: "info" }). So `texto` e obrigatorio.
    signal fala(var f)
    function dizer(f) {
        fala(typeof f === "string" ? { texto: f } : f);
    }

    // a Janela que contem um item (ou null): os textos usam para saber a cor da tinta
    function janelaDe(item) {
        let p = item ? item.parent : null;
        while (p) {
            if (p.ehJanela === true)
                return p;
            p = p.parent;
        }
        return null;
    }
}
