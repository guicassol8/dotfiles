import QtQuick
import Quickshell.Io

// Papel de parede vivo do grimorio (HD-2D). Cena em pixel art 640x360 de cenas/<elemento>.png
// com a mascara cenas/<elemento>-luz.png (feitas pelo pixelar.py), ampliada por vizinho mais
// proximo, com luz da hora, brilho, particulas do elemento, chuva e troca animada de capitulo.
// Um ShaderEffect so, sem camada nem alvo intermediario; o tempo anda por Timer no fps pedido.
//
// Hora do dia: se existir cenas/<elemento>-<fase>.png (fase: aurora, dia, entardecer; a
// cena sem sufixo e a noite) ela entra no lugar, pintada para aquela hora, com fusao
// suave na troca de fase. Sem a variante, vale a cena da noite com correcao de cor da
// hora (tabela _chaves). A luz da variante e <elemento>-<fase>-luz.png, ou a da noite.
// A pasta e relida a cada troca de fase e a cada 15 min a vista: arquivo novo entra sozinho.
//
// rodando: false congela num quadro (bateria, memoria apertada, mesa escondida). Troca
// pedida com a cena parada acontece de uma vez, sem animacao.
// Sem GPU (desenho por software, foto fora da tela) mostra a cena parada, sem shader.
Item {
    id: raiz
    anchors.fill: parent

    property string elemento: "mana-pura"   // fogo, agua, terra, vento, eletricidade, mana-pura
    property real hora: _relogio            // 0..24; padrao: o relogio
    property real nascer: 5.5               // hora do nascer e do por do sol (o clima manda)
    property real por: 19.0
    property real chuva: 0                  // 0..1
    property real pulso: 0                  // 0..1, grave da musica
    property real energia: 0                // 0..1, surto momentaneo (surto() anima de 1 a 0)
    property bool rodando: true
    property int fps: 10                    // 10 quadros/s: medido, 12 custava ~0,5% de um nucleo a mais
    property bool nitido: true              // false: amplia com filtro linear
    property real escurecer: 0.10           // escurecimento geral para o texto por cima
    property real mesa: 1                   // 1: calma atras dos widgets e poco do relogio; 0: so o cenario
    property real duracaoTroca: 2.4         // segundos da troca de capitulo
    property real duracaoFusao: 8           // segundos da fusao entre fases do dia
    property real tempo: 0                  // segundos de cena; da a volta a cada 2 h

    // arquivos de cenas/ (sem .png); `temTitulo`: existe cenas/titulo.png
    property var arquivos: []
    readonly property bool temTitulo: arquivos.indexOf("titulo") >= 0
    readonly property url titulo: Qt.resolvedUrl("cenas/titulo.png")

    property var cores: ({
        "fogo": "#E8866E", "agua": "#7FBBE0", "terra": "#D3AE73",
        "vento": "#74C5B0", "eletricidade": "#FFD43B", "mana-pura": "#B4A5DD"
    })
    readonly property var _tipos: ({ "fogo": 0, "agua": 1, "terra": 2, "vento": 3, "eletricidade": 4, "mana-pura": 5 })
    readonly property var _reservas: ({
        "fogo": "reserva-a", "terra": "reserva-a", "eletricidade": "reserva-a",
        "agua": "reserva-b", "vento": "reserva-b", "mana-pura": "reserva-b"
    })

    // ---- fase do dia, pelo sol de verdade quando o clima informa
    readonly property string fase: {
        const h = ((hora % 24) + 24) % 24;
        if (h >= nascer - 0.75 && h < nascer + 1.25) return "aurora";
        if (h >= nascer + 1.25 && h < por - 1.0) return "dia";
        if (h >= por - 1.0 && h < por + 0.6) return "entardecer";
        return "noite";
    }
    // a cena que vale agora: a variante da fase, se o arquivo existe; senao a da noite
    readonly property string cena: fase !== "noite" && arquivos.indexOf(elemento + "-" + fase) >= 0 ? elemento + "-" + fase : elemento
    readonly property string luzCena: cena !== elemento && arquivos.indexOf(cena + "-luz") >= 0 ? cena + "-luz" : elemento + "-luz"
    // quanto da correcao de cor da hora a cena recebe: a variante ja vem pintada
    function _gradDe(nome) { return nome === "titulo" || (nome.indexOf("-") >= 0 && _tipos[nome] === undefined && !nome.startsWith("reserva")) ? 0 : 1; }

    // estado interno, amostrado no ritmo do Timer (nada redesenha a 60 fps)
    property real _relogio: _agoraHora()
    property real _pulso: 0
    property real _energia: 0
    property real _transicao: 1
    property real _fusao: 0                 // 0 troca de capitulo (varredura), 1 fase do dia (fusao)
    property real _tipoVelho: 5
    property real _tipoNovo: 5
    property real _gradVelho: 1
    property real _gradNovo: 1
    property color _corVelho: "#B4A5DD"
    property color _corNovo: "#B4A5DD"
    property bool _surtando: false
    property bool _esperando: false         // troca aguardando a cena nova carregar
    property string _elAtual: ""

    function surto() { energia = 1; _surtando = true; }

    function _agoraHora() { const d = new Date(); return d.getHours() + d.getMinutes() / 60; }
    function _url(nome) { return Qt.resolvedUrl("cenas/" + nome + ".png"); }
    function _nomeDe(url) { const s = String(url); return s.substring(s.lastIndexOf("/") + 1).replace(/\.png$/, ""); }

    function _trocar() {
        if (_nomeDe(imgNova.source) === cena && _nomeDe(luzNova.source) === luzCena && _elAtual === elemento)
            return;
        const mesmoElemento = _elAtual === elemento;
        const temVelha = imgNova.status === Image.Ready && String(imgNova.source) !== "";
        if (temVelha) {
            imgVelha.source = imgNova.source;
            luzVelha.source = luzNova.source;
            _tipoVelho = _tipoNovo;
            _corVelho = _corNovo;
            _gradVelho = _gradNovo;
            _fusao = mesmoElemento ? 1 : 0;
            _transicao = 0;
            _esperando = true;
        }
        _elAtual = elemento;
        _tipoNovo = _tipos[elemento] !== undefined ? _tipos[elemento] : 5;
        _corNovo = cores[elemento] || "#B4A5DD";
        _gradNovo = _gradDe(cena);
        imgNova.source = _url(cena);
        luzNova.source = _url(luzCena);
    }

    // cena com problema cai na reserva do elemento
    function _reserva(img, ehLuz) {
        if (img.status !== Image.Error) return;
        const r = _reservas[elemento] || "reserva-b";
        if (_nomeDe(img.source).replace(/-luz$/, "") === r) return;
        console.warn("papel: sem cena " + _nomeDe(img.source) + ", usando " + r);
        if (!ehLuz) _gradNovo = 1;
        img.source = _url(ehLuz ? r + "-luz" : r);
    }

    function _pronta() {
        if (_esperando && imgNova.status === Image.Ready && luzNova.status === Image.Ready) {
            _esperando = false;
            if (!rodando || !visible)
                _concluir();                // parado: troca de uma vez
        }
    }
    function _concluir() {
        if (_esperando)
            return;                         // ainda carregando: _pronta conclui
        _transicao = 1;
        imgVelha.source = "";
        luzVelha.source = "";
    }
    onRodandoChanged: if (!rodando && _transicao < 1) _concluir()

    // tom da hora: [hora, r, g, b, exposicao, saturacao, forca das luzes]
    readonly property var _chaves: [
        [0.0, 0.88, 0.91, 1.00, 0.96, 0.92, 1.00],
        [4.5, 0.88, 0.91, 1.00, 0.96, 0.92, 1.00],
        [6.0, 0.98, 0.72, 0.80, 0.86, 0.95, 0.70],   // aurora
        [7.5, 1.00, 0.92, 0.86, 0.96, 1.00, 0.40],
        [9.0, 1.00, 1.00, 1.00, 1.00, 1.00, 0.25],   // dia
        [16.5, 1.00, 0.98, 0.94, 1.00, 1.00, 0.25],
        [18.0, 1.10, 0.80, 0.62, 0.95, 1.10, 0.50],  // entardecer
        [19.3, 0.80, 0.60, 0.82, 0.86, 0.90, 0.80],
        [20.5, 0.88, 0.91, 1.00, 0.96, 0.92, 1.00],  // noite (a cena base ja e pintada de noite)
        [24.0, 0.88, 0.91, 1.00, 0.96, 0.92, 1.00]
    ]
    readonly property var _tom: {
        const h = ((hora % 24) + 24) % 24;
        const k = _chaves;
        let i = 0;
        while (i < k.length - 2 && h >= k[i + 1][0]) i++;
        let f = (h - k[i][0]) / Math.max(1e-3, k[i + 1][0] - k[i][0]);
        f = f * f * (3 - 2 * f);
        const v = [];
        for (let j = 1; j < 7; j++) v.push(k[i][j] + (k[i + 1][j] - k[i][j]) * f);
        return v;
    }

    Timer {
        id: relogio
        property double ultimo: Date.now()
        interval: Math.round(1000 / Math.max(1, raiz.fps))
        repeat: true
        running: raiz.rodando && raiz.visible && !raiz._software
        onRunningChanged: ultimo = Date.now()
        onTriggered: {
            const agora = Date.now();
            const dt = Math.min(0.25, Math.max(0, (agora - ultimo) / 1000));
            ultimo = agora;
            raiz.tempo = (raiz.tempo + dt) % 7200;
            const k = raiz.pulso > raiz._pulso ? 0.7 : 0.25;   // grave sobe rapido, desce devagar
            raiz._pulso += (raiz.pulso - raiz._pulso) * k;
            if (raiz._surtando) {
                raiz.energia = Math.max(0, raiz.energia - dt / 2.4);
                raiz._surtando = raiz.energia > 0;
            }
            raiz._energia = raiz.energia;
            if (!raiz._esperando && raiz._transicao < 1) {
                const dur = raiz._fusao > 0.5 ? raiz.duracaoFusao : raiz.duracaoTroca;
                raiz._transicao = Math.min(1, raiz._transicao + dt / dur);
                if (raiz._transicao >= 1) raiz._concluir();
            }
        }
    }
    Timer {   // relogio de parede: so importa se ninguem amarrou a hora
        interval: 60000; repeat: true; running: raiz.rodando
        onTriggered: raiz._relogio = raiz._agoraHora()
    }

    // ---- quais cenas existem (o diretor de arte entrega variantes durante o dia)
    Process {
        id: lista
        command: ["sh", "-c", "cd \"$1\" && ls -1 *.png 2>/dev/null", "sh", String(Qt.resolvedUrl("cenas")).replace("file://", "")]
        stdout: StdioCollector {
            onStreamFinished: {
                const l = text.split("\n").filter(s => s.endsWith(".png")).map(s => s.slice(0, -4));
                if (l.join() !== raiz.arquivos.join())
                    raiz.arquivos = l;
            }
        }
    }
    function relerCenas() { if (!lista.running) lista.running = true; }
    Timer { interval: 15 * 60000; repeat: true; running: raiz.visible; onTriggered: raiz.relerCenas() }
    onFaseChanged: relerCenas()
    onCenaChanged: if (_elAtual !== "") _trocar()
    onLuzCenaChanged: if (_elAtual !== "") _trocar()
    onElementoChanged: if (_elAtual !== "") _trocar()
    Component.onCompleted: { relerCenas(); _trocar(); }

    // texturas pequenas (640x360), sem cache de pixmap
    Image {
        id: imgNova
        visible: false; asynchronous: true; cache: false
        smooth: true; mipmap: true            // mipmap alimenta o desfoque de miniatura
        onStatusChanged: { raiz._reserva(imgNova, false); raiz._pronta(); }
    }
    Image {
        id: luzNova
        visible: false; asynchronous: true; cache: false; smooth: true
        onStatusChanged: { raiz._reserva(luzNova, true); raiz._pronta(); }
    }
    Image { id: imgVelha; visible: false; cache: false; smooth: true; mipmap: true }
    Image { id: luzVelha; visible: false; cache: false; smooth: true }

    Rectangle { anchors.fill: parent; color: "#17141D" }

    // sem GPU (foto fora da tela): a cena parada, ampliada sem suavizar, com a calma dos lados
    readonly property bool _software: GraphicsInfo.api === GraphicsInfo.Software
    Image {
        visible: raiz._software
        anchors.fill: parent
        source: visible ? imgNova.source : ""
        fillMode: Image.PreserveAspectCrop
        smooth: false
        cache: false
        Rectangle { anchors.fill: parent; color: "#000000"; opacity: 0.35 * raiz.mesa }
    }

    ShaderEffect {
        id: efeito
        anchors.fill: parent
        readonly property bool _novaPronta: imgNova.status === Image.Ready && luzNova.status === Image.Ready
        readonly property bool _usaVelha: raiz._transicao < 1 && imgVelha.status === Image.Ready && luzVelha.status === Image.Ready
        visible: !raiz._software && (_novaPronta || _usaVelha)

        // enquanto a nova carrega, os dois lados mostram a velha
        property variant cenaNova: _novaPronta ? imgNova : imgVelha
        property variant luzNova: _novaPronta ? luzNova : luzVelha
        property variant cenaVelha: _usaVelha ? imgVelha : imgNova
        property variant luzVelha: _usaVelha ? luzVelha : luzNova

        property real tempo: raiz.tempo
        property real pulso: raiz._pulso
        property real energia: raiz._energia
        property real transicao: _usaVelha ? raiz._transicao : 1
        property real fusao: raiz._fusao
        property real chuva: raiz.chuva
        property real fator: Math.max(1, Math.ceil(Math.max(width / 640, height / 360) - 0.001))
        property real tipoVelho: raiz._tipoVelho
        property real tipoNovo: _novaPronta ? raiz._tipoNovo : raiz._tipoVelho
        property real gradVelho: raiz._gradVelho
        property real gradNovo: _novaPronta ? raiz._gradNovo : raiz._gradVelho
        property size tamanho: Qt.size(width, height)
        property point deslocamento: Qt.point((width - 640 * fator) / 2, (height - 360 * fator) / 2)
        property color corVelho: raiz._corVelho
        property color corNovo: raiz._corNovo
        property vector4d matiz: Qt.vector4d(raiz._tom[0], raiz._tom[1], raiz._tom[2], raiz._tom[3])
        property vector4d ajuste: Qt.vector4d(raiz._tom[4], raiz._tom[5], raiz.escurecer, raiz.nitido ? 1 : 0)
        property real mesa: raiz.mesa

        fragmentShader: Qt.resolvedUrl("cena.frag.qsb")
    }
}
