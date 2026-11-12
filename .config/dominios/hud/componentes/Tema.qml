pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Io

// Tema: cores, fontes, grade de pixel e textos do dominio ativo, mais o elemento
// que esta valendo agora.
// Le ~/.config/dominios/atual/hud-tema.json (ou o caminho em $DOMINIOS_TEMA) e
// recarrega sozinho quando o arquivo muda ou o dominio troca. Se o arquivo faltar,
// valem os valores do grimorio embutidos aqui. $DOMINIOS_ESTADO troca a pasta de
// estado (padrao ~/.local/state/dominios), como no resto do projeto.
Singleton {
    id: tema

    readonly property string casa: Quickshell.env("HOME")
    readonly property string caminho: Quickshell.env("DOMINIOS_TEMA") || casa + "/.config/dominios/atual/hud-tema.json"
    readonly property string pastaEstado: Quickshell.env("DOMINIOS_ESTADO") || casa + "/.local/state/dominios"

    readonly property var padrao: ({
        dominio: "grimorio", nome: "Grimório",
        cor: {
            fundo: "#17141D", superficie: "#1F1A28", superficie2: "#2C2440", contorno: "#3A3348",
            texto: "#EDE7F6", texto_suave: "#B0A7C4",
            primaria: "#A99BD9", sobre_primaria: "#17141D",
            secundaria: "#C8BDEC", sobre_secundaria: "#1F1A28",
            terciaria: "#D3AE73", sobre_terciaria: "#332714",
            erro: "#E8866E", sobre_erro: "#3A211B", aviso: "#FFD43B", ok: "#74C5B0"
        },
        elementos: {
            fogo: "#E8866E", agua: "#7FBBE0", terra: "#D3AE73",
            vento: "#74C5B0", eletricidade: "#FFD43B", "mana-pura": "#B4A5DD"
        },
        fonte: { ui: "Alegreya Sans", destaque: "Cinzel", mono: "FantasqueSansM Nerd Font", icones: "Symbols Nerd Font" },
        forma: { raio: 14, borda: 1, vaos: 16 },
        texto: {
            rotulo: "DESPERTAR DA MANA", lema: "A mana está em todos, e o poder que ela dá é justo.",
            expansao: "O grimório se abre.", bloqueio: "O grimório está selado.",
            notificacao: "Do grimório:", missoes_titulo: "OFÍCIOS DO DIA",
            ficha_titulo: "FICHA DO CONJURADOR", ficha_usuario: "CONJURADOR",
            ficha_cpu: "FOCO", ficha_memoria: "MANA", ficha_bateria: "FÔLEGO"
        }
    })

    // o JSON lido por cima do padrao: chave que faltar no arquivo cai no padrao
    property var dados: padrao
    property bool doArquivo: false          // true quando `dados` veio do arquivo
    signal mudou()

    readonly property string dominio: dados.dominio
    readonly property string nome: dados.nome

    // ---- grade de pixel: 1 pixel de arte = `px` pixels de tela. Toda peca de pixel
    // art e ampliada por este fator; tamanhos e posicoes de pecas sao multiplos dele.
    readonly property int px: 3
    function grade(v) {                     // arredonda um valor de tela para a grade
        return Math.round(v / px) * px;
    }

    // pasta das pecas geradas por arte/gerar.py; Tema.peca("gema-fogo") da o caminho
    readonly property url arte: Qt.resolvedUrl("../arte/")
    function peca(nome) {
        if (!nome)
            return "";
        if (nome.startsWith("~/"))
            return "file://" + casa + nome.slice(1);
        if (nome.indexOf("/") >= 0)
            return nome.startsWith("/") ? "file://" + nome : nome;
        return arte + nome + ".png";
    }

    // ---- acervo de sprites CC0 (hud/sprites/indice.json), lido uma vez.
    // Tema.sprite("mago") -> { url, x, y, l, a, quadros } ou null se o nome nao existe.
    property var sprites: ({})
    readonly property url pastaSprites: Qt.resolvedUrl("../sprites/")
    function sprite(nome) {
        if (!nome)
            return null;
        const s = sprites[nome] || (nome === "elemento-mana-pura" ? sprites["elemento-mana"] : undefined);
        if (!s)
            return null;
        return { url: pastaSprites + encodeURI(s.arquivo), x: s.x || 0, y: s.y || 0, l: s.l, a: s.a, quadros: s.quadros || 1 };
    }
    FileView {
        id: indice
        path: String(tema.pastaSprites).replace("file://", "") + "indice.json"
        blockLoading: true
        printErrors: false
    }
    Component.onCompleted: {            // leitura bloqueante: o acervo ja existe antes do primeiro sprite
        try {
            tema.sprites = JSON.parse(indice.text());
        } catch (e) {
            console.warn("Tema: sem acervo de sprites (" + indice.path + "): " + e);
        }
    }

    // ---- cores de base (neutros do dominio)
    readonly property color fundo: dados.cor.fundo
    readonly property color superficie: dados.cor.superficie
    readonly property color superficie2: dados.cor.superficie2
    readonly property color contorno: dados.cor.contorno
    readonly property color texto: dados.cor.texto
    readonly property color textoSuave: dados.cor.texto_suave
    readonly property color primaria: dados.cor.primaria
    readonly property color sobrePrimaria: dados.cor.sobre_primaria
    readonly property color secundaria: dados.cor.secundaria
    readonly property color sobreSecundaria: dados.cor.sobre_secundaria
    readonly property color terciaria: dados.cor.terciaria
    readonly property color sobreTerciaria: dados.cor.sobre_terciaria
    readonly property color erro: dados.cor.erro
    readonly property color sobreErro: dados.cor.sobre_erro
    readonly property color aviso: dados.cor.aviso
    readonly property color ok: dados.cor.ok
    readonly property color ouro: dados.cor.aviso          // recompensa
    readonly property color perigo: dados.cor.erro
    readonly property color tintaPapel: "#3A2C20"          // texto sobre pergaminho
    readonly property color tintaPapelSuave: "#7C6748"

    // ---- elementos
    // mapa nome -> "#RRGGBB" (fogo, agua, terra, vento, eletricidade, mana-pura)
    readonly property var elementos: dados.elementos
    readonly property var nomesElementos: ["fogo", "agua", "terra", "vento", "eletricidade", "mana-pura"]
    readonly property var rotulosElementos: ({
        fogo: "Fogo", agua: "Água", terra: "Terra", vento: "Vento", eletricidade: "Eletricidade", "mana-pura": "Mana pura"
    })

    // elemento ativo: vem do Nucleo; antes da primeira mensagem vale o elemento.json
    // $HUD_ELEMENTO fixa um elemento (teste: ver o widget nas seis cores)
    readonly property string elemento: {
        const n = Quickshell.env("HUD_ELEMENTO") || (Nucleo.elemento && Nucleo.elemento.elemento);
        return n && elementos && elementos[n] ? n : "mana-pura";
    }
    // motivo so vale para o elemento que ele explica (com $HUD_ELEMENTO, por exemplo, nao)
    readonly property string motivoElemento: (Nucleo.elemento && Nucleo.elemento.elemento === elemento
                                              && Nucleo.elemento.motivo) || ""

    // cor de destaque: a do elemento ativo, com transicao. Todo acento usa esta.
    property color destaque: corDe(elemento)
    Behavior on destaque {
        ColorAnimation { duration: 1200; easing.type: Easing.InOutQuad }
    }

    // cor de um elemento pelo nome; fora do grimorio (sem elementos) cai na primaria
    function corDe(nome) {
        const c = elementos ? elementos[nome] : undefined;
        return c ? Qt.color(c) : primaria;
    }

    // ---- fontes lisas (texto corrido e numeros)
    readonly property string fonteUi: dados.fonte.ui
    readonly property string fonteDestaque: dados.fonte.destaque
    readonly property string fonteMono: dados.fonte.mono
    readonly property string fonteIcones: dados.fonte.icones

    // ---- fontes de pixel. `em` e o corpo em pixels de arte: o tamanho na tela e
    // em * px (so assim cada pixel da fonte cai inteiro na grade). `alta` e a altura
    // da maiuscula em pixels de arte.
    readonly property var pixel: ({
        rotulo: { familia: "Silkscreen", em: 8, alta: 5, negrito: false, aperto: 1 },
        titulo: { familia: "Silkscreen", em: 8, alta: 5, negrito: true },
        miudo: { familia: "Micro 5", em: 11, alta: 5, negrito: false },
        medio: { familia: "Jersey 10", em: 56 / 3, alta: 10, negrito: false },
        grande: { familia: "Jersey 15", em: 27, alta: 15, negrito: false },
        enorme: { familia: "Jersey 25", em: 41, alta: 25, negrito: false },
        gotico: { familia: "Jacquard 12", em: 21, alta: 15, negrito: false },
        goticoGrande: { familia: "Jacquard 24", em: 43, alta: 31, negrito: false }
    })

    // ---- forma (pixels de tela)
    readonly property int raio: dados.forma.raio
    readonly property int borda: dados.forma.borda
    readonly property int vao: dados.forma.vaos
    readonly property int respiro: 18                       // folga interna padrao das janelas

    // ---- textos do dominio (lema, rotulo, ficha_titulo...)
    readonly property var textos: dados.texto

    // cor com outra opacidade: Tema.alfa(Tema.destaque, 0.4)
    function alfa(cor, a) {
        return Qt.rgba(cor.r, cor.g, cor.b, a);
    }

    // mistura duas cores, t de 0 (so a) a 1 (so b)
    function mistura(a, b, t) {
        if (typeof a === "string")
            a = Qt.color(a);
        if (typeof b === "string")
            b = Qt.color(b);
        return Qt.rgba(a.r + (b.r - a.r) * t, a.g + (b.g - a.g) * t, a.b + (b.b - a.b) * t, a.a + (b.a - a.a) * t);
    }

    function _mescla(base, extra) {
        if (extra === null || typeof extra !== "object" || Array.isArray(extra))
            return extra === undefined || extra === null ? base : extra;
        if (base === null || typeof base !== "object")
            return extra;
        const r = {};
        for (const k in base) r[k] = base[k];
        for (const k in extra) r[k] = _mescla(base[k], extra[k]);
        return r;
    }

    function _aplica(txt) {
        let lido;
        try {
            lido = JSON.parse(txt);
        } catch (e) {
            console.warn("Tema: " + caminho + " nao e JSON valido (" + e + "); mantendo o tema anterior");
            return;
        }
        const novo = _mescla(padrao, lido);
        // os elementos sao so do grimorio: outro dominio nao herda os do padrao
        if (lido.elementos !== undefined)
            novo.elementos = lido.elementos;
        dados = novo;
        doArquivo = true;
        mudou();
    }

    FileView {
        id: arquivo
        path: tema.caminho
        watchChanges: true
        printErrors: false
        onLoaded: tema._aplica(text())
        onFileChanged: reload()
        onLoadFailed: console.warn("Tema: sem " + tema.caminho + ", usando o padrao embutido")
    }

    // `atual` e um link trocado por rename e o FileView nao percebe a troca (medido):
    // ele segue olhando o arquivo antigo. O `dominio` reescreve este outro arquivo a
    // cada troca, entao ele serve de aviso para reler o tema.
    FileView {
        path: tema.pastaEstado + "/atual"
        watchChanges: true
        printErrors: false
        onFileChanged: { reload(); recarga.restart(); }
    }

    Timer {
        id: recarga
        interval: 250
        onTriggered: arquivo.reload()
    }
}
