import QtQuick
import Quickshell
import Quickshell.Services.Mpris
import qs.componentes

// Bardo: a musica que esta tocando. Capa do album em pixel (reduzida e ampliada por
// vizinho mais proximo), titulo, artista, barras de audio do `cava` sobre a barra de
// progresso, e tres botoes de placa na borda de cima (anterior, tocar/pausar, proxima).
// Dados: Mpris (o jogador que esta tocando, senao o pausado) e `cava` em saida crua,
// que so roda com musica tocando e a mesa a vista.
//
// `pulso` (0..1) e o grave suavizado: o cenario pulsa com ele (a casca liga).
// `amostra` troca os dados de verdade por um exemplo (teste fora da tela):
//   HUD_AMOSTRA_BARDO='{"titulo": "...", "artista": "...", "capa": "/caminho.png",
//     "posicao": 83, "duracao": 225, "tocando": true, "niveis": [3, 5, 8, ...]}'
//   HUD_AMOSTRA_BARDO='{"vazio": true}'          sem musica
// Sem `niveis` e com `tocando`, o cava de verdade roda (para testar o caminho todo).
Janela {
    id: bardo

    titulo: "Bardo"

    // ================================================================ dados
    property var amostra: {
        const t = Quickshell.env("HUD_AMOSTRA_BARDO");
        if (!t)
            return null;
        try {
            return JSON.parse(t);
        } catch (e) {
            console.warn("Bardo: HUD_AMOSTRA_BARDO nao e JSON (" + e + ")");
            return null;
        }
    }

    // jogador ativo: o que esta tocando; senao o pausado com faixa; senao o primeiro
    readonly property var jogador: {
        if (amostra)
            return null;
        const l = Mpris.players ? Mpris.players.values : [];
        let pausado = null;
        for (let i = 0; i < l.length; i++) {
            if (l[i].isPlaying)
                return l[i];
            if (!pausado && l[i].playbackState === MprisPlaybackState.Paused && l[i].trackTitle)
                pausado = l[i];
        }
        return pausado || (l.length > 0 ? l[0] : null);
    }

    readonly property bool temFaixa: amostra ? !amostra.vazio : (jogador !== null && (jogador.trackTitle || "") !== "")
    readonly property string faixa: amostra ? (amostra.titulo || "") : jogador ? (jogador.trackTitle || "") : ""
    readonly property string artista: amostra ? (amostra.artista || "") : jogador ? (jogador.trackArtist || jogador.identity || "") : ""
    readonly property string capa: {
        const c = amostra ? (amostra.capa || "") : jogador ? (jogador.trackArtUrl || "") : "";
        return c.startsWith("/") ? "file://" + c : c;
    }
    readonly property bool tocando: amostra ? !!amostra.tocando : jogador !== null && jogador.isPlaying
    readonly property real posicao: amostra ? (amostra.posicao || 0) : jogador && jogador.positionSupported ? jogador.position : 0
    readonly property real duracao: amostra ? (amostra.duracao || 0) : jogador && jogador.lengthSupported ? jogador.length : 0
    readonly property real progresso: duracao > 0 ? Math.max(0, Math.min(1, posicao / duracao)) : 0

    // controles (nunca acionados em teste)
    function anterior() { if (jogador && jogador.canGoPrevious) jogador.previous(); }
    function alternar() { if (jogador && jogador.canTogglePlaying) jogador.togglePlaying(); }
    function proxima() { if (jogador && jogador.canGoNext) jogador.next(); }

    // o Mpris nao avisa quando a posicao anda: pede a leitura uma vez por segundo
    Timer {
        interval: 1000
        repeat: true
        running: bardo.jogador !== null && bardo.tocando && Hud.visivel
        onTriggered: bardo.jogador.positionChanged()
    }

    function relogio(s) {
        s = Math.max(0, Math.floor(s));
        const h = Math.floor(s / 3600), m = Math.floor(s / 60) % 60, ss = s % 60;
        return (h > 0 ? h + ":" + (m < 10 ? "0" : "") : "") + m + ":" + (ss < 10 ? "0" : "") + ss;
    }

    // ---- visualizador: cava em saida crua, ASCII, `barras` valores de 0 a `degraus`
    readonly property int barras: 16
    readonly property int degraus: 8
    readonly property int quadrosPorSegundo: 15
    property var niveis: []
    property real pulso: 0                  // grave suavizado, 0..1

    // o visualizador e animacao: para escondido, na bateria e com a memoria apertada
    readonly property bool ouvindo: tocando && Hud.animar && !(amostra && amostra.niveis)
    // o cenario pulsa com o grave (caminho compartilhado: Hud.pulso)
    Binding { target: Hud; property: "pulso"; value: bardo.pulso }
    Component.onDestruction: Hud.pulso = 0

    Coletor {
        id: cava
        ativo: bardo.ouvindo
        continuo: true
        json: false
        religar: 5000
        // a configuracao vai num arquivo do runtime (o cava so le de arquivo)
        comando: "f=\"${XDG_RUNTIME_DIR:-/tmp}/dominios-bardo-cava.conf\"; printf '%s\\n' "
            + "'[general]' 'framerate = " + bardo.quadrosPorSegundo + "' 'bars = " + bardo.barras + "' 'autosens = 1' "
            + "'lower_cutoff_freq = 40' 'higher_cutoff_freq = 12000' "
            + "'[input]' 'method = pipewire' 'source = auto' "
            + "'[output]' 'method = raw' 'raw_target = /dev/stdout' 'data_format = ascii' "
            + "'ascii_max_range = " + bardo.degraus + "' 'bar_delimiter = 59' 'frame_delimiter = 10' "
            + "'channels = mono' 'mono_option = average' "
            + "'[smoothing]' 'noise_reduction = 70' > \"$f\" && exec nice -n 10 cava -p \"$f\""
        onAtualizado: linha => bardo._quadro(linha)
    }
    onOuvindoChanged: if (!ouvindo) { niveis = []; pulso = 0; }

    function _quadro(linha) {
        const v = linha.split(";");
        const l = [];
        for (let i = 0; i < barras; i++)
            l.push(Math.max(0, Math.min(degraus, parseInt(v[i]) || 0)));
        niveis = l;
        const grave = (l[0] + l[1] + l[2]) / (3 * degraus);
        pulso += (grave - pulso) * (grave > pulso ? 0.6 : 0.2);
    }

    // niveis mostrados: os do cava, os da amostra, ou deitados
    readonly property var _vistos: amostra && amostra.niveis ? amostra.niveis : niveis

    // ================================================================ desenho

    // botoes de placa na linha de cima da moldura, a direita (onde iria a etiqueta)
    Row {
        visible: bardo.temFaixa
        spacing: Tema.px
        x: bardo.corpo.width + 2 * Tema.px - width
        y: -bardo.corpo.y
        BotaoPixel {
            mapa: bardo.iconeAnterior
            ativo: bardo.amostra !== null || (bardo.jogador !== null && bardo.jogador.canGoPrevious)
            onClicado: bardo.anterior()
        }
        BotaoPixel {
            mapa: bardo.tocando ? bardo.iconePausar : bardo.iconeTocar
            ativo: bardo.amostra !== null || (bardo.jogador !== null && bardo.jogador.canTogglePlaying)
            onClicado: bardo.alternar()
        }
        BotaoPixel {
            mapa: bardo.iconeProxima
            ativo: bardo.amostra !== null || (bardo.jogador !== null && bardo.jogador.canGoNext)
            onClicado: bardo.proxima()
        }
    }

    // ---- capa, numa moldurinha
    Item {
        id: quadroCapa
        width: 24 * Tema.px
        height: 24 * Tema.px

        Rectangle {
            x: Tema.px
            y: Tema.px
            width: parent.width - 2 * Tema.px
            height: parent.height - 2 * Tema.px
            gradient: Gradient {
                GradientStop { position: 0; color: Tema.mistura(Tema.superficie2, Tema.destaque, 0.22) }
                GradientStop { position: 1; color: Tema.mistura(Tema.fundo, "#000000", 0.3) }
            }
        }
        Image {                             // 20 x 20 pixels de arte, ampliados sem suavizar
            id: arte
            visible: bardo.temFaixa && status === Image.Ready
            x: 2 * Tema.px
            y: 2 * Tema.px
            width: 20 * Tema.px
            height: 20 * Tema.px
            source: bardo.temFaixa ? bardo.capa : ""
            sourceSize: Qt.size(20, 20)
            fillMode: Image.PreserveAspectCrop
            smooth: false
            mipmap: false
            asynchronous: true
        }
        Rectangle {                         // luz de cima, lisa (o "HD" do HD-2D)
            visible: arte.visible
            x: 2 * Tema.px
            y: 2 * Tema.px
            width: 20 * Tema.px
            height: 6 * Tema.px
            gradient: Gradient {
                GradientStop { position: 0; color: Qt.rgba(1, 1, 1, 0.16) }
                GradientStop { position: 1; color: Qt.rgba(1, 1, 1, 0) }
            }
        }
        Pixels {                            // sem capa: nota; sem musica: o alaude
            visible: !arte.visible
            x: 3 * Tema.px
            y: 3 * Tema.px
            mapa: bardo.temFaixa ? bardo.nota : bardo.alaude
            cores: bardo.temFaixa ? bardo.coresNota : bardo.coresAlaude
        }
        Fatias { anchors.fill: parent; fonte: "retrato-moldura"; borda: 3 }
    }

    // ---- lado direito
    Item {
        id: lado
        x: quadroCapa.width + 5 * Tema.px
        width: parent.width - x
        height: parent.height

        // com musica: titulo e artista
        Texto {
            visible: bardo.temFaixa
            y: -4
            width: parent.width
            tamanho: 19
            text: bardo.faixa
            elide: Text.ElideRight
            maximumLineCount: 1
            wrapMode: Text.NoWrap
        }
        Texto {
            visible: bardo.temFaixa
            y: 19
            width: parent.width
            tamanho: 15
            suave: true
            text: bardo.artista
            elide: Text.ElideRight
            maximumLineCount: 1
            wrapMode: Text.NoWrap
        }

        // sem musica: o bardo descansa
        TextoPixel {
            visible: !bardo.temFaixa
            tipo: "rotulo"
            sombra: true
            color: Tema.destaque
            text: "O bardo descansa"
            font.capitalization: Font.AllUppercase
            y: -3
        }
        Texto {
            visible: !bardo.temFaixa
            y: 27
            tamanho: 15
            suave: true
            text: "Toque algo e ele volta a cantar."
        }

        // ---- barras de audio em pe sobre a barra de progresso, com os tempos nas pontas
        Numero {
            id: tempoJa
            visible: bardo.temFaixa && bardo.duracao > 0
            tamanho: 13
            suave: true
            text: bardo.relogio(bardo.posicao)
            anchors.bottom: parent.bottom
            anchors.bottomMargin: -4
        }
        Numero {
            id: tempoTotal
            visible: tempoJa.visible
            tamanho: 13
            suave: true
            text: bardo.relogio(bardo.duracao)
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            anchors.bottomMargin: -4
        }

        Item {
            id: palco
            readonly property int passo: 4 * Tema.px            // barra de 3 pixels de arte + 1 de vao
            width: bardo.barras * passo - Tema.px
            height: (bardo.degraus + 2) * Tema.px
            x: Tema.grade((parent.width - width) / 2)
            y: parent.height - height

            Repeater {
                model: bardo.barras
                Item {
                    id: coluna
                    required property int index
                    readonly property int nivel: {
                        const v = bardo._vistos;
                        return v && v.length > index ? Math.max(0, Math.min(bardo.degraus, v[index])) : 0;
                    }
                    readonly property bool tocada: bardo.temFaixa && (index + 0.5) / bardo.barras <= bardo.progresso
                    readonly property color cor: tocada ? Tema.destaque : Tema.mistura(Tema.destaque, Tema.fundo, 0.55)
                    x: index * palco.passo
                    width: 3 * Tema.px
                    height: palco.height - 2 * Tema.px

                    Rectangle {                     // corpo da barra (deitada: 1 pixel de arte)
                        y: parent.height - height
                        width: parent.width
                        height: Math.max(1, coluna.nivel) * Tema.px
                        color: Tema.mistura(coluna.cor, Tema.fundo, 0.28)
                    }
                    Rectangle {                     // topo aceso
                        y: parent.height - Math.max(1, coluna.nivel) * Tema.px
                        width: parent.width
                        height: Tema.px
                        color: coluna.tocada ? Tema.mistura(Tema.destaque, "#ffffff", 0.4) : coluna.cor
                    }
                }
            }

            // barra de progresso: o chao das barras
            Rectangle {
                y: parent.height - Tema.px
                width: parent.width
                height: Tema.px
                color: Tema.alfa(Tema.contorno, 0.9)
            }
            Rectangle {
                visible: bardo.temFaixa
                y: parent.height - Tema.px
                width: Tema.grade(parent.width * bardo.progresso)
                height: Tema.px
                color: Tema.destaque
            }
            Rectangle {                             // cabeca de leitura
                visible: bardo.temFaixa && bardo.duracao > 0
                x: Math.min(parent.width - width, Tema.grade(parent.width * bardo.progresso))
                y: parent.height - 2 * Tema.px
                width: Tema.px
                height: 2 * Tema.px
                color: Tema.mistura(Tema.destaque, "#ffffff", 0.6)
            }
        }
    }

    // ================================================================ pixel art propria

    // alaude 18 x 18 (o: contorno, l/w/d: madeira clara/media/escura, n: braco,
    // p: cravelhal, h: boca, s: cordas)
    readonly property var alaude: [
        "..............oo..",
        ".............oppo.",
        ".............ooppo",
        "............onoopo",
        "...........onsnoo.",
        "..........onsno...",
        "....oooooonsno....",
        "...olllwwnsno.....",
        "..olllwwnsno......",
        ".olllwhhsnwo......",
        ".ollwwhswwdo......",
        "ollwwwshwddo......",
        "olwwwswwdddo......",
        "owwdswwdddo.......",
        ".owwdwddddo.......",
        ".owwwdddoo........",
        "..ooddoo..........",
        "....oo............"
    ]
    readonly property var coresAlaude: ({
        o: Tema.mistura(Tema.fundo, "#000000", 0.45),
        l: Tema.mistura(Tema.corDe("terra"), "#ffffff", 0.35),
        w: Tema.corDe("terra"),
        d: Tema.mistura(Tema.corDe("terra"), Tema.fundo, 0.42),
        n: Tema.mistura(Tema.corDe("terra"), Tema.fundo, 0.55),
        p: Tema.mistura(Tema.corDe("terra"), Tema.fundo, 0.68),
        h: Tema.fundo,
        s: Tema.texto
    })
    // duas colcheias 18 x 18, na cor do elemento
    readonly property var nota: [
        "..................",
        "..................",
        ".......ooooooooo..",
        "......oslllllllso.",
        "......ossssssssso.",
        "......osoooooooso.",
        "......oso.....oso.",
        "......oso.....oso.",
        "......oso.....oso.",
        "......oso.....oso.",
        "......oso.....oso.",
        "....oooso...oooso.",
        "...olssso..olssso.",
        "...osssso..osssso.",
        "....osso....osso..",
        ".....oo......oo...",
        "..................",
        ".................."
    ]
    readonly property var coresNota: ({
        o: Tema.mistura(Tema.fundo, "#000000", 0.45),
        s: Tema.destaque,
        l: Tema.mistura(Tema.destaque, "#ffffff", 0.5)
    })

    // icones dos botoes, 5 x 7 (o glifo da Nerd Font no tamanho da placa nao se le)
    readonly property var iconeAnterior: ["s...s", "s..ss", "s.sss", "sssss", "s.sss", "s..ss", "s...s"]
    readonly property var iconeProxima: ["s...s", "ss..s", "sss.s", "sssss", "sss.s", "ss..s", "s...s"]
    readonly property var iconeTocar: [".s...", ".ss..", ".sss.", ".ssss", ".sss.", ".ss..", ".s..."]
    readonly property var iconePausar: ["ss.ss", "ss.ss", "ss.ss", "ss.ss", "ss.ss", "ss.ss", "ss.ss"]

    // placa clicavel do tamanho da placa de titulo, com icone de pixel
    component BotaoPixel: Item {
        id: bp
        property var mapa: []
        property bool ativo: true
        signal clicado()
        readonly property bool _dentro: toque.containsMouse && ativo
        width: 15 * Tema.px
        height: 11 * Tema.px
        opacity: ativo ? 1 : 0.45
        Item {
            width: parent.width
            height: parent.height
            y: toque.pressed && bp.ativo ? Tema.px : 0
            Fatias { anchors.fill: parent; fonte: "placa-normal"; bordaEsquerda: 5; bordaDireita: 5 }
            Rectangle {
                visible: bp._dentro
                x: 2 * Tema.px
                y: 2 * Tema.px
                width: parent.width - 4 * Tema.px
                height: parent.height - 4 * Tema.px
                color: Tema.alfa(Tema.destaque, 0.22)
            }
            Pixels {
                x: 6 * Tema.px
                y: 3 * Tema.px
                mapa: bp.mapa
                cores: ({ s: Qt.rgba(0, 0, 0, 0.6) })
            }
            Pixels {
                x: 5 * Tema.px
                y: 2 * Tema.px
                mapa: bp.mapa
                cores: ({ s: bp._dentro ? Tema.mistura(Tema.destaque, "#ffffff", 0.5) : Tema.texto })
            }
        }
        MouseArea {
            id: toque
            anchors.fill: parent
            hoverEnabled: true
            cursorShape: bp.ativo ? Qt.PointingHandCursor : Qt.ArrowCursor
            onClicked: if (bp.ativo) bp.clicado()
        }
    }

    // desenha um mapa de letras na grade, uma faixa horizontal por trecho de mesma cor
    component Pixels: Item {
        id: px
        property var mapa: []
        property var cores: ({})
        implicitWidth: (mapa.length > 0 ? mapa[0].length : 0) * Tema.px
        implicitHeight: mapa.length * Tema.px
        width: implicitWidth
        height: implicitHeight
        readonly property var _trechos: {
            const r = [];
            for (let y = 0; y < mapa.length; y++) {
                const linha = mapa[y];
                let x = 0;
                while (x < linha.length) {
                    const c = linha[x];
                    let f = x;
                    while (f < linha.length && linha[f] === c)
                        f++;
                    if (c !== "." && cores[c] !== undefined)
                        r.push({ x: x, y: y, l: f - x, c: cores[c] });
                    x = f;
                }
            }
            return r;
        }
        Repeater {
            model: px._trechos
            Rectangle {
                required property var modelData
                x: modelData.x * Tema.px
                y: modelData.y * Tema.px
                width: modelData.l * Tema.px
                height: Tema.px
                color: modelData.c
            }
        }
    }
}
