import QtQuick
import qs.componentes

// Céus: clima de Porto Alegre e a lua na fase real. Dados: Nucleo.elemento.clima.
Janela {
    id: ceus

    // arte de pixel em texto: cada letra da `paleta` vira uma celula da grade
    component Pixeis: Canvas {
        property var linhas: []
        property var paleta: ({})
        width: (linhas.length > 0 ? linhas[0].length : 0) * Tema.px
        height: linhas.length * Tema.px
        renderTarget: Canvas.Image
        antialiasing: false
        onLinhasChanged: requestPaint()
        onPaletaChanged: requestPaint()
        onPaint: {
            const g = getContext("2d");
            g.clearRect(0, 0, width, height);
            for (let y = 0; y < linhas.length; y++)
                for (let x = 0; x < linhas[y].length; x++) {
                    const c = paleta[linhas[y][x]];
                    if (c === undefined)
                        continue;
                    g.fillStyle = c.toString();
                    g.fillRect(x * Tema.px, y * Tema.px, Tema.px, Tema.px);
                }
        }
    }

    readonly property var arte: ({
        nascer: ["....A....", "...AAA...", "..AAAAA..", ".........", "...YYY...", "..YYYYY..", "YYYYYYYYY", "LLLLLLLLL"],
        poente: ["..AAAAA..", "...AAA...", "....A....", ".........", "...OOO...", "..OOOOO..", "OOOOOOOOO", "LLLLLLLLL"],
        gota: ["....G....", "...GGG...", "..GGGGG..", ".GGGGGGG.", ".GGHGGGG.", ".GHGGGGG.", "..GGGGG..", "...GGG..."],
        vento: ["...VVVV..", "..V....V.", ".......V.", ".VVVVVV..", ".........", "VVVVVVVV.", ".......V.", "..VVVVV.."],
        chuva: ["..CCCC...", ".CCCCCC..", "CCCCCCCCC", ".CCCCCCC.", ".........", ".G..G..G.", "..G..G...", ".G..G..G."],
        sensacao: ["...TTT...", "...TWT...", "...TWT...", "...TRT...", "...TRT...", "..TRRRT..", "..TRRRT..", "...TTT..."]
    })
    readonly property var paleta: ({
        A: Tema.textoSuave, Y: Tema.ouro, O: Tema.mistura(Tema.ouro, Tema.corDe('fogo'), 0.6), L: Tema.contorno,
        G: Tema.corDe("agua"), H: Tema.mistura(Tema.corDe("agua"), Tema.texto, 0.6), V: Tema.corDe("vento"),
        C: Tema.textoSuave, T: Tema.contorno, W: Tema.superficie, R: Tema.mistura(Tema.perigo, Tema.corDe("fogo"), 0.5)
    })

    // lua pixel por codigo (inline: o qs nao enxerga outro arquivo da pasta widgets)
    // CeusLua: a lua desenhada por codigo na grade de pixel, na fase real.
    // `fase` 0..1 (0 nova, .25 crescente, .5 cheia, .75 minguante). Porto Alegre fica no
    // hemisferio sul: a lua crescente se ilumina pela esquerda. Redesenha so quando a fase muda.
    component CeusLua: Item {
        id: luaRaiz

        property real fase: 0.5
        property bool sul: true
        readonly property int n: 21                 // celulas de arte por lado
        readonly property int celula: Tema.px

        width: n * celula
        height: n * celula

        readonly property color claro: Tema.mistura(Tema.texto, Tema.ouro, 0.22)
        readonly property color meio: Tema.mistura(claro, Tema.superficie2, 0.3)
        readonly property color sombraClara: Tema.mistura(claro, Tema.superficie2, 0.58)
        readonly property color escuro: Tema.mistura(Tema.superficie2, Tema.contorno, 0.2)
        readonly property color escuroBorda: Tema.mistura(Tema.superficie2, Tema.contorno, 0.85)

        // crateras: [dx, dy, raio] em celulas a partir do centro
        readonly property var crateras: [[-4, -4, 2], [3, -5, 1], [4, 2, 2], [-3, 4, 2], [0, 0, 1], [-7, 1, 1], [1, 7, 1]]

        function celulaDe(x, y) {                   // cor da celula ou null (fora do disco)
            const c = (n - 1) / 2, r = n / 2 - 0.35;
            const dx = x - c, dy = y - c;
            const d2 = dx * dx + dy * dy;
            if (d2 > r * r)
                return null;
            const w = Math.sqrt(Math.max(0, r * r - dy * dy));
            const k = Math.cos(2 * Math.PI * fase);
            const waxing = fase < 0.5;
            // posicao horizontal vista da Terra: no sul a crescente acende a esquerda
            let xv = sul ? -dx : dx;
            const lit = waxing ? xv > k * w : xv < -k * w;
            let cr = false;
            for (let i = 0; i < crateras.length; i++) {
                const q = crateras[i];
                if ((dx - q[0]) * (dx - q[0]) + (dy - q[1]) * (dy - q[1]) <= (q[2] - 0.4) * (q[2] - 0.4))
                    cr = true;
            }
            const borda = d2 > (r - 1.1) * (r - 1.1);
            if (!lit)
                return borda ? escuroBorda : (cr ? Tema.mistura(escuro, escuroBorda, 0.5) : escuro);
            if (cr)
                return sombraClara;
            return borda ? meio : claro;
        }

        // halo liso atras (so aparece com lua clara)
        Image {
            source: Tema.peca("brilho-mana-pura")
            anchors.centerIn: parent
            width: parent.width * 2
            height: width
            opacity: 0.08 + 0.5 * (1 - Math.cos(2 * Math.PI * luaRaiz.fase)) / 2
        }

        Canvas {
            id: tela
            anchors.fill: parent
            renderTarget: Canvas.Image
            antialiasing: false
            onPaint: {
                const g = getContext("2d");
                g.clearRect(0, 0, width, height);
                g.imageSmoothingEnabled = false;
                for (let y = 0; y < luaRaiz.n; y++)
                    for (let x = 0; x < luaRaiz.n; x++) {
                        const c = luaRaiz.celulaDe(x, y);
                        if (c === null)
                            continue;
                        g.fillStyle = c.toString();
                        g.fillRect(x * luaRaiz.celula, y * luaRaiz.celula, luaRaiz.celula, luaRaiz.celula);
                    }
            }
        }
        onFaseChanged: tela.requestPaint()
        onClaroChanged: tela.requestPaint()
    }

    titulo: "Céus"
    respiro: 0

    // exemplo para a foto, ate o nucleo responder
    readonly property var clima: Nucleo.elemento ? Nucleo.elemento.clima : null
    readonly property bool temClima: clima !== null && clima !== undefined && clima.temperatura_c !== undefined

    function nomeLua(n) {
        const t = String(n || "").replace(/^Lua /, "");
        return t.charAt(0).toUpperCase() + t.slice(1);
    }
    function num(v, casas) { return Number(v).toFixed(casas).replace(".", ","); }
    function hora(iso) { return iso ? String(iso).slice(11, 16) : "--:--"; }

    // codigo WMO -> peca em pixel
    function iconeDoTempo(c, dia) {
        if (c === undefined || c === null) return "nuvem";
        if (c <= 1) return dia ? "sol" : "lua";
        if (c === 2) return "parcial";
        if (c === 3) return "nuvem";
        if (c === 45 || c === 48) return "neblina";
        if (c >= 71 && c <= 77 || c === 85 || c === 86) return "neve";
        if (c >= 95) return "tempestade";
        return "chuva";
    }
    readonly property string tempo: temClima ? iconeDoTempo(clima.codigo, clima.e_dia) : "nuvem"

    // ---- sem dados
    Item {
        visible: !ceus.temClima
        anchors.fill: parent
        Icone { id: nuvemVazia; nome: "nuvem"; anchors.left: parent.left; anchors.leftMargin: 18; anchors.verticalCenter: parent.verticalCenter }
        Texto {
            anchors.left: nuvemVazia.right
            anchors.leftMargin: 18
            anchors.verticalCenter: parent.verticalCenter
            tamanho: 20
            text: "Os céus estão encobertos."
        }
    }

    // ---- coluna A: icone, temperatura, descricao, sol
    Item {
        id: colA
        visible: ceus.temClima
        x: 3
        width: 168
        height: parent.height

        Item {
            id: simbolo
            width: 42
            height: 42
            y: 3
            Icone { visible: ceus.tempo !== "parcial" && ceus.tempo !== "neblina"; nome: ceus.tempo }
            Item {                          // parcial: sol (ou lua) atras da nuvem
                visible: ceus.tempo === "parcial"
                Icone { nome: ceus.clima && ceus.clima.e_dia ? "sol" : "lua"; x: 0; y: -3 }
                Icone { nome: "nuvem"; x: 9; y: 6 }
            }
            Icone { visible: ceus.tempo === "neblina"; nome: "neblina"; tamanho: 11; cor: Tema.textoSuave }
        }
        TextoPixel {
            tipo: "grande"
            sombra: true
            color: Tema.destaque
            x: simbolo.width + 12
            y: -12
            text: ceus.temClima ? Math.round(ceus.clima.temperatura_c) + "°" : ""
        }
        Texto {
            x: 0
            y: 48
            width: colA.width
            tamanho: 19
            wrapMode: Text.NoWrap
            elide: Text.ElideRight
            text: ceus.temClima ? (ceus.clima.descricao || "") : ""
        }
        Row {                               // nascer e por do sol
            y: 78
            spacing: 18
            Row {
                spacing: 6
                Pixeis { linhas: ceus.arte.nascer; paleta: ceus.paleta }
                Numero { tamanho: 15; y: 3; text: ceus.temClima ? ceus.hora(ceus.clima.nascer) : "" }
            }
            Row {
                spacing: 6
                Pixeis { linhas: ceus.arte.poente; paleta: ceus.paleta }
                Numero { tamanho: 15; y: 3; text: ceus.temClima ? ceus.hora(ceus.clima.por) : "" }
            }
        }
    }

    // ---- coluna B: sensacao, umidade, vento, chuva
    Column {
        visible: ceus.temClima
        x: 189
        y: 0
        width: 120
        spacing: 0
        Repeater {
            model: ceus.temClima ? [
                { a: "sensacao", v: ceus.num(ceus.clima.sensacao_c, 1) + " °C", r: "Sensação" },
                { a: "gota", v: ceus.num(ceus.clima.umidade, 0) + "%", r: "Umidade" },
                { a: "vento", v: ceus.num(ceus.clima.vento_kmh, 1) + " km/h", r: "Vento" },
                { a: "chuva", v: ceus.num(ceus.clima.chuva_mm, 1) + " mm", r: "Chuva" }
            ] : []
            Item {
                required property var modelData
                width: parent.width
                height: 27
                Pixeis { y: 0; linhas: ceus.arte[parent.modelData.a]; paleta: ceus.paleta }
                Numero { x: 39; y: 3; tamanho: 16; text: parent.modelData.v }
            }
        }
    }

    // ---- coluna C: a lua
    Item {
        visible: ceus.temClima && ceus.clima.lua_fase !== undefined
        x: ceus.corpo.width - width - 3
        width: 108
        height: parent.height
        CeusLua {
            id: lua
            fase: ceus.temClima && ceus.clima.lua_fase !== undefined ? ceus.clima.lua_fase : 0.5
            anchors.horizontalCenter: parent.horizontalCenter
            y: 3
        }
        Texto {
            width: parent.width
            horizontalAlignment: Text.AlignHCenter
            y: lua.y + lua.height + 6
            tamanho: 15
            suave: true
            wrapMode: Text.NoWrap
            text: ceus.nomeLua(ceus.temClima ? ceus.clima.lua_nome : "")
        }
    }
}
