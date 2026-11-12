import QtQuick

// Icone: icone pequeno de interface (~33 px). Procura o `nome` nesta ordem:
//   1. simbolo da casa, na grade: "fogo", "agua", "terra", "vento", "eletricidade", "mana-pura"
//   2. sprite do acervo (hud/sprites/indice.json), desenhado 1:1 (34 px): "moeda",
//      "coracao", "espada", "pocao", "grimorio", "sol", "lua", "elemento-fogo"...
//      (nuvem, chuva e tempestade saem da versao em pixel feita por arte/gerar.py)
//   3. icone pequeno desenhado em pixel (`mapas`, 7 x 7), quando `tamanho` < 9: os
//      de botao (tocar, pausar, proxima, anterior, certo, fechar, mais, menos)
//   4. glifo de Nerd Font em pseudo pixel (desenhado pequeno, sem suavizar, e
//      ampliado na grade): nomes em `glifos`, ou passe `glifo` direto. Abaixo de 9
//      pixels de arte o glifo nao se le: o desenho sobe para 9.
// So os caminhos 3 e 4 aceitam `cor`. Para um sprite do acervo grande, use Figura.
Item {
    id: icone

    property string nome: ""
    property string glifo: ""               // glifo direto, ex.: ""
    property int tamanho: 9                 // lado do glifo em pixels de ARTE (9 = 27 px)
    property color cor: _janela ? _janela.tinta : Tema.texto

    readonly property var _janela: Hud.janelaDe(icone)
    readonly property var glifos: ({
        estrela: 0xf005, usuario: 0xf007, certo: 0xf00c, fechar: 0xf00d, livro: 0xf02d, musica: 0xf001,
        tocar: 0xf04b, pausar: 0xf04c, parar: 0xf04d, proxima: 0xf051, anterior: 0xf048, chama: 0xf06d,
        folha: 0xf06c, raio: 0xf0e7, gota: 0xf043, frasco: 0xf0c3, trofeu: 0xf091, cadeado: 0xf023,
        bussola: 0xf14e, terminal: 0xf120, codigo: 0xf121, github: 0xf09b, git: 0xf1d3, bateria: 0xf240,
        wifi: 0xf1eb, chip: 0xf2db, termometro: 0xf2c9, varinha: 0xf0d0, olho: 0xf06e, calendario: 0xf073,
        sino: 0xf0f3, engrenagem: 0xf013, aviso: 0xf071, info: 0xf05a, "seta-cima": 0xf062,
        "seta-baixo": 0xf063, "seta-esquerda": 0xf060, "seta-direita": 0xf061, mais: 0xf067, menos: 0xf068,
        tomada: 0xf1e6, baixar: 0xf019, subir: 0xf093, disco: 0xf0a0, pasta: 0xf07b, busca: 0xf002,
        casa: 0xf015, fantasma: 0xf02a0, coroa: 0xf01a5, memoria: 0xf035b, robo: 0xf06a9, pena: 0xf06d3,
        dado: 0xf1152, neblina: 0xf0591, nublado: 0xf0590, parcial: 0xf0595
    })

    // pecas da casa de 34 px que passam na frente do acervo (o clima do acervo e liso)
    readonly property var daCasa: ({ nuvem: "clima-nuvem", chuva: "clima-chuva", tempestade: "clima-tempestade" })

    readonly property bool _simbolo: glifo === "" && Tema.nomesElementos.indexOf(nome) >= 0
    readonly property bool _casa: glifo === "" && daCasa[nome] !== undefined
    readonly property bool _acervo: glifo === "" && !_simbolo && !_casa && Tema.sprite(nome) !== null
    readonly property bool _figura: _simbolo || _casa || _acervo

    // icones de botao desenhados na grade (7 x 7): legiveis onde o glifo pequeno nao e
    readonly property var mapas: ({
        tocar: [".s.....", ".ss....", ".sss...", ".ssss..", ".sss...", ".ss....", ".s....."],
        pausar: [".ss.ss.", ".ss.ss.", ".ss.ss.", ".ss.ss.", ".ss.ss.", ".ss.ss.", ".ss.ss."],
        anterior: [".s...s.", ".s..ss.", ".s.sss.", ".sssss.", ".s.sss.", ".s..ss.", ".s...s."],
        proxima: [".s...s.", ".ss..s.", ".sss.s.", ".sssss.", ".sss.s.", ".ss..s.", ".s...s."],
        certo: ["......s", ".....ss", "s...ss.", "ss.ss..", ".sss...", "..s....", "......."],
        fechar: ["ss...ss", ".ss.ss.", "..sss..", "...s...", "..sss..", ".ss.ss.", "ss...ss"],
        mais: ["...s...", "...s...", "...s...", "sssssss", "...s...", "...s...", "...s..."],
        menos: [".......", ".......", ".......", "sssssss", ".......", ".......", "......."]
    })
    readonly property bool _pixel: !_figura && glifo === "" && tamanho < 9 && mapas[nome] !== undefined
    readonly property int _lado: _pixel ? 7 : Math.max(9, tamanho)
    readonly property string _glifo: _pixel ? "" : glifo !== "" ? glifo : (!_figura && glifos[nome] ? String.fromCodePoint(glifos[nome]) : "")

    implicitWidth: _figura ? sp.implicitWidth : _lado * Tema.px
    implicitHeight: _figura ? sp.implicitHeight : _lado * Tema.px

    Figura {
        id: sp
        visible: icone._figura
        fonte: icone._simbolo ? "simbolo-" + icone.nome : icone._casa ? icone.daCasa[icone.nome] : icone._acervo ? icone.nome : ""
        ponto: icone._simbolo ? 0 : 1
        quadros: 1
    }

    Pixels {
        visible: icone._pixel
        mapa: visible ? icone.mapas[icone.nome] : []
        cores: ({ s: icone.cor })
    }

    // glifo desenhado 1x numa textura pequena e ampliado por vizinho mais proximo
    Item {
        visible: icone._glifo !== ""
        width: icone._lado
        height: icone._lado
        scale: Tema.px
        transformOrigin: Item.TopLeft
        layer.enabled: visible
        layer.smooth: false
        Text {
            anchors.centerIn: parent
            text: icone._glifo
            color: icone.cor
            font.family: Tema.fonteIcones
            font.pixelSize: icone._lado
            renderType: Text.NativeRendering
            antialiasing: false
        }
    }
}
