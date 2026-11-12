import QtQuick
import qs.componentes

// Familiares: os agentes Claude que o conjurador invocou. Uma linha por familiar:
// a criatura (escolhida pelo id, sempre a mesma), o projeto, o estado, o que esta
// fazendo e ha quanto tempo foi invocado. Quem aguarda ordens vem primeiro e leva
// um "!" de ouro; quem conjura respira um brilho e da pulinhos; quem esta ocioso
// dorme. Um familiar so ganha a janela inteira, com a criatura grande. Cabem
// quatro linhas; passando disso, a ultima vira "+N". Dados: Nucleo.familiares.
Janela {
    id: fam

    titulo: "Familiares"
    etiqueta: lista.length > 0 ? String(lista.length) : ""

    // aguardando primeiro (e a vez do dono), depois conjurando, depois ociosos
    readonly property var ordem: ({ aguardando: 0, conjurando: 1, ocioso: 2 })
    readonly property var lista: {
        const l = Array.isArray(Nucleo.familiares) ? Nucleo.familiares.slice() : [];
        l.sort((a, b) => (ordem[a.estado] ?? 3) - (ordem[b.estado] ?? 3)
            || String(a.desde).localeCompare(String(b.desde)) || String(a.id).localeCompare(String(b.id)));
        return l;
    }
    readonly property int cabem: 4
    readonly property bool sobra: lista.length > cabem
    readonly property int mostrados: sobra ? cabem - 1 : lista.length
    readonly property int alturaLinha: 14 * Tema.px

    // ---- palavras e cores de estado
    readonly property var palavras: ({ conjurando: "Conjurando", aguardando: "Aguardando", ocioso: "Dormindo" })
    function corEstado(e) {
        return e === "aguardando" ? Tema.ouro : e === "conjurando" ? Tema.destaque : fam.tintaSuave;
    }

    // ---- a criatura de cada familiar, estavel pelo id
    readonly property var criaturas: ["familiar-coruja-32", "familiar-gato-32", "familiar-raposa-32", "familiar-slime-32",
        "familiar-fada-32", "familiar-dragao-32", "familiar-corvo-32", "familiar-chama-32"]
    function criatura(id) {
        const s = String(id);
        let h = 2166136261;                 // FNV-1a com uma mistura no fim: ids vizinhos se espalham
        for (let i = 0; i < s.length; i++)
            h = Math.imul(h ^ s.charCodeAt(i), 16777619) >>> 0;
        h = (h ^ (h >>> 13)) >>> 0;
        h = Math.imul(h, 0x5bd1e995) >>> 0;
        h = (h ^ (h >>> 15)) >>> 0;
        return criaturas[h % criaturas.length];
    }
    function nomeProjeto(p) {
        return !p || p === "~" ? "casa" : String(p);
    }

    // ---- tempo: ha quanto foi invocado (relogio de 30 s, so com a mesa a vista)
    property double agora: Date.now()
    Timer {
        interval: 30000
        repeat: true
        triggeredOnStart: true
        running: Hud.visivel && fam.lista.length > 0
        onTriggered: fam.agora = Date.now()
    }
    function ha(desde) {
        const t = Date.parse(desde);
        if (isNaN(t))
            return "";
        const min = Math.max(0, Math.floor((agora - t) / 60000));
        if (min < 1)
            return "agora";
        if (min < 60)
            return "há " + min + " min";
        const h = Math.floor(min / 60);
        if (h < 24)
            return "há " + h + " h" + (min % 60 > 0 ? " " + (min % 60) + " min" : "");
        return "há " + Math.floor(h / 24) + (h < 48 ? " dia" : " dias");
    }

    // ---- vida: um relogio lento para todos. 3 quadros/s se alguem conjura, 1/s se so ha quem durma
    readonly property bool conjura: lista.some((f, i) => i < mostrados && f.estado === "conjurando")
    readonly property bool dorme: lista.length === 0 || lista.some((f, i) => i < mostrados && f.estado === "ocioso")
    property int tique: 0
    Timer {
        interval: fam.conjura ? 333 : 1000
        repeat: true
        running: (fam.conjura || fam.dorme) && Hud.animar && fam.visible
        onTriggered: fam.tique = (fam.tique + 1) % 600
    }
    readonly property int passo: tique % 6                                    // pulso de 2 s
    readonly property bool sono: Math.floor(tique / (conjura ? 3 : 1)) % 2 === 1  // zZ troca a cada 1 s
    readonly property var pulso: [0.24, 0.36, 0.48, 0.58, 0.48, 0.36]
    readonly property var pulo: [0, 0, -1, -1, 0, 0]                          // em pixels de arte

    // ---- peca: pixels de arte soltos (lista de [x, y]); `lado` em px de tela
    component Pixels: Item {
        id: px
        property var pontos: []
        property color cor
        property int lado: Tema.px
        Repeater {
            model: px.pontos
            Rectangle {
                required property var modelData
                x: modelData[0] * px.lado
                y: modelData[1] * px.lado
                width: px.lado
                height: px.lado
                color: px.cor
            }
        }
    }

    // ---- peca: "!" de ouro, a vez do dono
    component Alerta: Item {
        id: al
        property int escala: 1
        readonly property var pontos: [[0, 0], [1, 0], [0, 1], [1, 1], [0, 2], [1, 2], [0, 4], [1, 4]]
        width: 3 * Tema.px * escala
        height: 6 * Tema.px * escala
        Pixels { x: al.escala * Tema.px; y: al.escala * Tema.px; lado: al.escala * Tema.px; pontos: al.pontos; cor: Tema.alfa("#000000", 0.6) }
        Pixels { lado: al.escala * Tema.px; pontos: al.pontos; cor: Tema.ouro }
        Pixels { lado: al.escala * Tema.px; pontos: [[0, 0]]; cor: Tema.mistura(Tema.ouro, "#ffffff", 0.6) }
    }

    // ---- peca: "zZ" de quem dorme, os dois sobem e descem um pixel, alternados
    component Sono: Item {
        id: sn
        property bool troca: false
        property int escala: 1
        readonly property int lado: Tema.px * escala
        readonly property var zMiudo: [[0, 0], [1, 0], [2, 0], [3, 0], [2, 1], [1, 2], [0, 3], [1, 3], [2, 3], [3, 3]]
        readonly property var zGrande: [[0, 0], [1, 0], [2, 0], [3, 0], [4, 0], [3, 1], [2, 2], [1, 3], [0, 4], [1, 4], [2, 4], [3, 4], [4, 4]]
        width: 11 * lado
        height: 11 * lado
        Repeater {
            model: [[sn.zMiudo, 0, 6, 1], [sn.zGrande, 5, 1, 0]]
            Item {
                required property var modelData
                x: modelData[1] * sn.lado
                y: (modelData[2] - (sn.troca ? 1 - modelData[3] : modelData[3])) * sn.lado
                Pixels { x: sn.lado; y: sn.lado; lado: sn.lado; pontos: modelData[0]; cor: Tema.alfa("#000000", 0.55) }
                Pixels { lado: sn.lado; pontos: modelData[0]; cor: Tema.textoSuave }
            }
        }
    }

    // ---- peca: a criatura com brilho, alerta ou sono conforme o estado
    component Bicho: Item {
        id: bc
        property var familiar: ({})
        property int escala: 0                  // 0 = icone (1 px por pixel de arte); 1 = na grade
        readonly property string estado: familiar.estado || "ocioso"
        readonly property bool vivo: estado === "conjurando"

        Image {                                 // brilho que respira enquanto conjura
            visible: bc.vivo
            source: bc.vivo ? Tema.peca("brilho-" + Tema.elemento) : ""
            anchors.centerIn: parent
            width: bc.escala > 0 ? 174 : 66
            height: width
            opacity: fam.pulso[fam.passo]
        }
        Figura {
            fonte: fam.criatura(bc.familiar.id)
            ponto: bc.escala > 0 ? 0 : 1
            escala: Math.max(1, bc.escala)
            fps: bc.vivo ? 3 : 0
            x: Tema.grade((parent.width - width) / 2)
            y: Tema.grade((parent.height - height) / 2) + (bc.vivo && quadros === 1 ? fam.pulo[fam.passo] * Tema.px : 0)
            opacity: bc.estado === "ocioso" ? 0.62 : 1
        }
        Alerta {                                // ao lado da criatura, sem cobrir o desenho
            visible: bc.estado === "aguardando"
            escala: Math.max(1, bc.escala * 2)
            x: bc.escala > 0 ? bc.width - Tema.px : bc.width - width
            y: bc.escala > 0 ? 2 * Tema.px : 0
        }
        Sono {
            visible: bc.estado === "ocioso"
            troca: fam.sono
            escala: Math.max(1, bc.escala * 2)
            x: bc.width - width + (bc.escala > 0 ? 2 * Tema.px : 0)
            y: bc.escala > 0 ? -7 * Tema.px : -2 * Tema.px
        }
    }

    // ================= um so familiar: a janela e dele
    Item {
        id: heroi
        visible: fam.lista.length === 1
        anchors.fill: parent
        readonly property var f: fam.lista[0] || ({})
        readonly property string estado: f.estado || "ocioso"
        readonly property color cor: fam.corEstado(estado)

        Bicho {
            id: grande
            familiar: heroi.f
            escala: 1
            width: 36 * Tema.px
            height: 36 * Tema.px
            y: Tema.grade((parent.height - height) / 2)
        }
        Column {
            x: grande.width + 6 * Tema.px
            width: parent.width - x
            anchors.verticalCenter: parent.verticalCenter
            spacing: Tema.px

            Row {
                spacing: 2 * Tema.px
                Rectangle {
                    width: 2 * Tema.px
                    height: 2 * Tema.px
                    anchors.verticalCenter: parent.verticalCenter
                    color: heroi.cor
                }
                TextoPixel {
                    tipo: "titulo"
                    sombra: true
                    color: heroi.cor
                    font.capitalization: Font.AllUppercase
                    text: fam.palavras[heroi.estado] || heroi.estado
                }
            }
            TextoPixel {
                tipo: "medio"
                sombra: true
                width: parent.width
                elide: Text.ElideRight
                text: fam.nomeProjeto(heroi.f.projeto)
            }
            Texto {
                width: parent.width
                tamanho: 16
                suave: true
                text: heroi.f.descricao || ""
                maximumLineCount: 2
                elide: Text.ElideRight
            }
            Item { width: 1; height: Tema.px }
            Texto {
                tamanho: 14
                suave: true
                opacity: 0.85
                text: "Invocado " + fam.ha(heroi.f.desde)
                visible: fam.ha(heroi.f.desde) !== ""
            }
        }
    }

    // ================= varios: uma linha cada
    Column {
        visible: fam.lista.length > 1
        width: parent.width
        // poucas linhas: o bloco fica no meio da janela, nao colado no titulo
        y: Tema.grade(Math.max(0, (parent.height - height) / 2))
        spacing: 0

        Repeater {
            model: fam.lista.length > 1 ? fam.mostrados : 0
            Item {
                id: linha
                required property int index
                readonly property var f: fam.lista[index] || ({})
                readonly property string estado: f.estado || "ocioso"
                readonly property bool vivo: estado === "conjurando"
                readonly property bool espera: estado === "aguardando"
                readonly property bool dormindo: estado === "ocioso"
                readonly property color cor: fam.corEstado(estado)

                width: parent.width
                height: fam.alturaLinha

                Rectangle {                     // faixa do estado
                    width: parent.width
                    height: parent.height - Tema.px
                    color: Tema.alfa(linha.cor, linha.espera ? 0.12 : linha.vivo ? 0.07 : 0.03)
                }
                Rectangle {
                    width: Tema.px
                    height: parent.height - Tema.px
                    color: linha.cor
                    opacity: linha.dormindo ? 0.35 : 1
                }
                Bicho {
                    familiar: linha.f
                    x: 3 * Tema.px
                    width: 12 * Tema.px
                    height: parent.height - Tema.px
                }

                // linha de cima: projeto e ha quanto tempo
                Texto {
                    id: projeto
                    x: 17 * Tema.px
                    width: parent.width - x - tempo.width - 4 * Tema.px
                    tamanho: 17
                    font.weight: Font.Bold
                    opacity: linha.dormindo ? 0.75 : 1
                    text: fam.nomeProjeto(linha.f.projeto)
                    elide: Text.ElideRight
                    maximumLineCount: 1
                    wrapMode: Text.NoWrap
                }
                Texto {
                    id: tempo
                    anchors.right: parent.right
                    anchors.rightMargin: 2 * Tema.px
                    anchors.baseline: projeto.baseline
                    tamanho: 14
                    suave: true
                    text: fam.ha(linha.f.desde)
                    wrapMode: Text.NoWrap
                }

                // linha de baixo: o estado, na cor dele, e o que esta fazendo
                Texto {
                    id: palavra
                    x: 17 * Tema.px
                    y: 7 * Tema.px
                    tamanho: 15
                    font.weight: Font.Bold
                    color: linha.cor
                    text: fam.palavras[linha.estado] || linha.estado
                    wrapMode: Text.NoWrap
                }
                Texto {
                    anchors.left: palavra.right
                    anchors.leftMargin: 2 * Tema.px
                    anchors.right: parent.right
                    anchors.rightMargin: 2 * Tema.px
                    y: 7 * Tema.px
                    tamanho: 15
                    suave: true
                    text: linha.f.descricao || ""
                    elide: Text.ElideRight
                    maximumLineCount: 1
                    wrapMode: Text.NoWrap
                }
            }
        }

        // os que nao couberam
        Item {
            id: resto
            visible: fam.sobra
            width: parent.width
            height: fam.alturaLinha
            readonly property var lista: fam.lista.slice(fam.mostrados)
            function conta(e) {
                return lista.filter(f => f.estado === e).length;
            }

            Rectangle {
                width: parent.width
                height: parent.height - Tema.px
                color: Tema.alfa(fam.tintaSuave, 0.04)
            }
            Row {
                x: 3 * Tema.px
                anchors.verticalCenter: parent.verticalCenter
                spacing: -2 * Tema.px
                Repeater {
                    model: Math.min(3, resto.lista.length)
                    Figura {
                        required property int index
                        fonte: fam.criatura(resto.lista[index] ? resto.lista[index].id : "")
                        ponto: 1
                        opacity: 0.7
                    }
                }
            }
            TextoPixel {
                id: mais
                x: 32 * Tema.px
                anchors.verticalCenter: parent.verticalCenter
                tipo: "medio"
                sombra: true
                text: "+" + resto.lista.length
            }
            Texto {
                anchors.left: mais.right
                anchors.leftMargin: 3 * Tema.px
                anchors.right: parent.right
                anchors.verticalCenter: parent.verticalCenter
                tamanho: 15
                suave: true
                elide: Text.ElideRight
                maximumLineCount: 1
                wrapMode: Text.NoWrap
                text: {
                    const p = [];
                    const a = resto.conta("aguardando"), c = resto.conta("conjurando"), o = resto.conta("ocioso");
                    if (a)
                        p.push(a + " aguardando");
                    if (c)
                        p.push(c + " conjurando");
                    if (o)
                        p.push(o + " dormindo");
                    return p.join(", ");
                }
            }
        }
    }

    // ================= ninguem invocado
    Row {
        visible: fam.lista.length === 0
        anchors.centerIn: parent
        spacing: 6 * Tema.px
        Item {
            width: dorminhoco.width
            height: dorminhoco.height
            anchors.verticalCenter: parent.verticalCenter
            Figura {
                id: dorminhoco
                fonte: "familiar-coruja-32"
                opacity: 0.5
            }
            Sono {
                troca: fam.sono
                escala: 1
                x: parent.width - 9 * Tema.px
                y: -Tema.px
            }
        }
        Column {
            anchors.verticalCenter: parent.verticalCenter
            spacing: Tema.px
            Texto { text: "Nenhum familiar invocado"; tamanho: 19 }
            Texto { text: "O círculo de invocação descansa."; tamanho: 15; suave: true }
        }
    }
}
