// Domínios: tela de login (SDDM, Qt 6).
//
// Um esqueleto só para os domínios todos. Cor, fonte, forma, texto e composição vêm
// de dominios.js, gerado por ~/.config/dominios/gerar/login.py a partir de
// dominios.toml. Aqui não há cor nem nome de fonte literal.
//
// O domínio mostrado é `config.dominio` (theme.conf, com theme.conf.user por cima).
// O valor só serve de chave numa tabela fixa: nome desconhecido cai no padrão.
import QtQuick
import QtQml
import QtQml.Models
import "componentes"
import "dominios.js" as Dados

FocusScope {
    id: raiz

    // ------------------------------------------------------------ domínio
    readonly property string pedido: config.dominio === undefined ? "" : String(config.dominio)
    readonly property string chave: Dados.dominios.hasOwnProperty(pedido) ? pedido : Dados.padrao
    readonly property var tema: Dados.dominios[chave]
    readonly property bool principal: typeof primaryScreen === "undefined" ? true : primaryScreen

    // ------------------------------------------------------------- estado
    property date agora: new Date()
    property string mensagem: ""
    property bool falhou: false
    property bool ocupado: false
    property real tremor: 0
    readonly property bool caps: keyboard.capsLock === true
    readonly property var nomesSessoes: {
        var lista = []
        for (var i = 0; i < sessoes.count; ++i) {
            var s = sessoes.objectAt(i)
            lista.push(s ? s.name : "")
        }
        return lista
    }

    function arquivo(relativo) {
        return relativo ? Qt.resolvedUrl(relativo) : ""
    }

    function caixa(texto, modo) {
        return modo === "alta" ? texto.toUpperCase() : texto
    }

    function usuarioInicial() {
        var ultimo = userModel.lastUser
        if (ultimo && ultimo.length > 0)
            return ultimo
        if (usuarios.count === 1 && usuarios.objectAt(0))
            return usuarios.objectAt(0).name
        return ""
    }

    function precisaSenha(nome) {
        for (var i = 0; i < usuarios.count; ++i) {
            var u = usuarios.objectAt(i)
            if (u && u.name === nome)
                return u.needsPassword
        }
        return true
    }

    function focoPadrao() {
        if (campoUsuario.texto.length === 0)
            campoUsuario.forceActiveFocus()
        else
            campoSenha.forceActiveFocus()
    }

    function textoAviso() {
        var partes = []
        if (mensagem.length > 0)
            partes.push(mensagem)
        if (caps)
            partes.push(tokens.txt.caps)
        return partes.length > 0 ? partes.join(tokens.txt.separador) : tokens.txt.ajuda
    }

    function entrar() {
        if (ocupado)
            return
        var nome = campoUsuario.texto.trim()
        if (nome.length === 0) {
            falhou = true
            mensagem = tokens.txt.sem_usuario
            campoUsuario.forceActiveFocus()
            return
        }
        if (campoSenha.texto.length === 0 && precisaSenha(nome)) {
            falhou = false
            mensagem = tokens.txt.sem_senha
            campoSenha.forceActiveFocus()
            return
        }
        falhou = false
        mensagem = tokens.txt.entrando
        ocupado = true
        guarda.restart()
        sddm.login(nome, campoSenha.texto, seletor.indice)
    }

    function limpar() {
        if (ocupado)
            return
        campoSenha.texto = ""
        falhou = false
        mensagem = ""
        focoPadrao()
    }

    width: 1920
    height: 1080
    focus: true

    Keys.onEscapePressed: raiz.limpar()

    Component.onCompleted: {
        campoUsuario.texto = usuarioInicial()
        seletor.indice = Math.max(0, Math.min(sessionModel.lastIndex, sessoes.count - 1))
        focoPadrao()
    }

    // -------------------------------------------------------------- dados
    QtObject {
        id: tokens

        readonly property var cor: raiz.tema.cor
        readonly property var estilo: raiz.tema.estilo
        readonly property var txt: Dados.textos
        readonly property real escala: Math.max(0.5, Math.min(raiz.width / 1920, raiz.height / 1080))
        readonly property int raio: Math.round(raiz.tema.forma.raio * escala)
        readonly property int borda: Math.max(1, Math.round(raiz.tema.forma.borda * escala))
        readonly property bool centro: estilo.alinhamento === "centro"
        readonly property string ui: fonteUi.status === FontLoader.Ready ? fonteUi.name : raiz.tema.fonte.ui
        readonly property string destaque: fonteDestaque.status === FontLoader.Ready ? fonteDestaque.name
                                                                                      : raiz.tema.fonte.destaque
        readonly property int pesoUi: raiz.tema.fonte.peso_ui
        readonly property int pesoForte: fonteForte.status === FontLoader.Ready ? raiz.tema.fonte.peso_forte : pesoUi
        readonly property int pesoDestaque: raiz.tema.fonte.peso_destaque
        readonly property var eixosDestaque: raiz.tema.fonte.eixos.destaque
        readonly property bool rotulosEmDestaque: estilo.rotulos_fonte === "destaque"
        readonly property string fonteRotulos: rotulosEmDestaque ? destaque : ui
        readonly property int pesoRotulos: rotulosEmDestaque ? pesoDestaque : pesoForte
        readonly property var eixosRotulos: rotulosEmDestaque ? eixosDestaque : ({})

        function px(valor) {
            return Math.round(valor * escala)
        }
    }

    FontLoader {
        id: fonteUi

        source: raiz.arquivo(raiz.tema.fonte.arquivos.ui)
    }

    FontLoader {
        id: fonteForte

        source: raiz.arquivo(raiz.tema.fonte.arquivos.forte)
    }

    FontLoader {
        id: fonteDestaque

        source: raiz.arquivo(raiz.tema.fonte.arquivos.destaque)
    }

    Instantiator {
        id: usuarios

        model: userModel

        delegate: QtObject {
            required property string name
            required property bool needsPassword
        }
    }

    Instantiator {
        id: sessoes

        model: sessionModel

        delegate: QtObject {
            required property string name
        }
    }

    Timer {
        interval: 1000
        running: true
        repeat: true
        onTriggered: raiz.agora = new Date()
    }

    // Se o SDDM não responder ao pedido de login, a tela destrava sozinha.
    Timer {
        id: guarda

        interval: 20000
        onTriggered: {
            raiz.ocupado = false
            raiz.mensagem = ""
        }
    }

    Connections {
        target: sddm

        function onLoginFailed() {
            guarda.stop()
            raiz.ocupado = false
            raiz.falhou = true
            raiz.mensagem = tokens.txt.senha_errada
            campoSenha.texto = ""
            campoSenha.forceActiveFocus()
            animaTremor.restart()
        }

        function onLoginSucceeded() {
            guarda.stop()
            raiz.falhou = false
            raiz.mensagem = tokens.txt.bem_vindo
        }

        function onInformationMessage(message) {
            raiz.mensagem = message
        }
    }

    SequentialAnimation {
        id: animaTremor

        NumberAnimation { target: raiz; property: "tremor"; to: -tokens.px(12); duration: 50 }
        NumberAnimation { target: raiz; property: "tremor"; to: tokens.px(12); duration: 80 }
        NumberAnimation { target: raiz; property: "tremor"; to: -tokens.px(7); duration: 70 }
        NumberAnimation { target: raiz; property: "tremor"; to: tokens.px(7); duration: 70 }
        NumberAnimation { target: raiz; property: "tremor"; to: 0; duration: 50 }
    }

    // -------------------------------------------------------------- fundo
    Rectangle {
        anchors.fill: parent
        color: tokens.cor.fundo
    }

    Image {
        anchors.fill: parent
        source: raiz.arquivo(raiz.tema.arte.fundo)
        fillMode: Image.PreserveAspectCrop
        smooth: true
    }

    Rectangle {
        anchors.fill: parent
        color: tokens.cor.fundo
        opacity: tokens.estilo.veu
    }

    // grão fino: disfarça as faixas do degradê escuro
    Image {
        anchors.fill: parent
        visible: tokens.estilo.grao > 0
        source: visible ? raiz.arquivo(Dados.grao) : ""
        fillMode: Image.Tile
        smooth: false
        opacity: tokens.estilo.grao
    }

    MouseArea {
        anchors.fill: parent
        onClicked: raiz.focoPadrao()
    }

    // ----------------------------------------------------------- conteúdo
    Item {
        id: tela

        anchors.fill: parent
        visible: raiz.principal

        // relógio e data
        Column {
            id: relogio

            readonly property bool aoCentro: tokens.estilo.relogio === "centro"

            x: aoCentro ? Math.round(painel.baseX + (painel.width - width) / 2) : painel.baseX
            y: tokens.px(aoCentro ? 54 : 70)
            spacing: tokens.px(2)

            Text {
                x: relogio.aoCentro ? Math.round((relogio.width - width) / 2) : 0
                text: Qt.formatTime(raiz.agora, tokens.txt.formato_hora)
                color: tokens.cor.texto
                font.family: tokens.destaque
                font.weight: tokens.pesoDestaque
                font.variableAxes: tokens.eixosDestaque
                font.pixelSize: tokens.px(tokens.estilo.relogio_tamanho)
            }

            Text {
                x: relogio.aoCentro ? Math.round((relogio.width - width) / 2) : 0
                text: raiz.caixa(raiz.agora.toLocaleDateString(Qt.locale(tokens.txt.localidade), tokens.txt.formato_data),
                                 tokens.estilo.data_caixa)
                color: tokens.cor.texto_suave
                font.family: tokens.ui
                font.weight: tokens.pesoUi
                font.pixelSize: tokens.px(tokens.estilo.texto_tamanho)
                font.letterSpacing: tokens.px(tokens.estilo.texto_tamanho) * tokens.estilo.data_espaco
            }
        }

        // painel de login
        Item {
            id: painel

            readonly property int margem: tokens.px(34)
            readonly property int baseX: Math.round(raiz.width * tokens.estilo.painel_x - width / 2)

            width: tokens.px(tokens.estilo.painel_largura)
            height: conteudo.height + 2 * margem
            x: baseX + raiz.tremor
            y: Math.max(relogio.y + relogio.height + tokens.px(26),
                        Math.round((raiz.height - height) / 2) + tokens.px(tokens.estilo.painel_dy))

            Moldura {
                anchors.fill: parent
                t: tokens
            }

            // bloco lateral com o selo
            Rectangle {
                id: bloco

                visible: tokens.estilo.emblema === "lado"
                width: visible ? tokens.px(tokens.estilo.emblema_tamanho) : 0
                anchors.left: parent.left
                anchors.top: parent.top
                anchors.bottom: parent.bottom
                color: tokens.cor.primaria

                Image {
                    anchors.centerIn: parent
                    width: Math.round(parent.width * 0.86)
                    height: width
                    source: bloco.visible ? raiz.arquivo(raiz.tema.arte.emblema) : ""
                    mipmap: true
                }
            }

            Column {
                id: conteudo

                x: bloco.width + painel.margem
                y: painel.margem
                width: painel.width - bloco.width - 2 * painel.margem

                Image {
                    id: emblemaTopo

                    visible: tokens.estilo.emblema === "topo"
                    width: tokens.px(tokens.estilo.emblema_tamanho)
                    height: width
                    x: Math.round((conteudo.width - width) / 2)
                    source: visible ? raiz.arquivo(raiz.tema.arte.emblema) : ""
                    mipmap: true
                }

                Item {
                    visible: emblemaTopo.visible
                    width: 1
                    height: tokens.px(16)
                }

                Row {
                    id: cabecalho

                    x: tokens.centro ? Math.round((conteudo.width - width) / 2) : 0
                    spacing: tokens.px(14)

                    Image {
                        id: emblemaCabecalho

                        visible: tokens.estilo.emblema === "cabecalho"
                        width: tokens.px(tokens.estilo.emblema_tamanho)
                        height: width
                        anchors.verticalCenter: parent.verticalCenter
                        source: visible ? raiz.arquivo(raiz.tema.arte.emblema) : ""
                        mipmap: true
                    }

                    Text {
                        id: titulo

                        anchors.verticalCenter: parent.verticalCenter
                        width: Math.min(implicitWidth, conteudo.width
                                        - (emblemaCabecalho.visible ? emblemaCabecalho.width + cabecalho.spacing : 0))
                        text: raiz.tema.titulo
                        color: tokens.cor.primaria
                        fontSizeMode: Text.HorizontalFit
                        minimumPixelSize: tokens.px(12)
                        font.family: tokens.destaque
                        font.weight: raiz.tema.fonte.peso_titulo
                        font.variableAxes: tokens.eixosDestaque
                        font.pixelSize: tokens.px(tokens.estilo.titulo_tamanho)
                        font.letterSpacing: tokens.px(tokens.estilo.titulo_tamanho) * tokens.estilo.titulo_espaco
                    }
                }

                Item {
                    width: 1
                    height: tokens.px(12)
                }

                // divisor: à esquerda, traço forte e filete; ao centro, filete, ponto, filete
                Item {
                    width: conteudo.width
                    height: tokens.px(9)

                    Rectangle {
                        visible: !tokens.centro
                        anchors.verticalCenter: parent.verticalCenter
                        width: parent.width
                        height: Math.max(1, tokens.px(1))
                        color: tokens.cor.contorno
                    }

                    Rectangle {
                        visible: !tokens.centro
                        anchors.verticalCenter: parent.verticalCenter
                        width: tokens.px(56)
                        height: tokens.borda + 1
                        color: tokens.cor.primaria
                    }

                    Rectangle {
                        visible: tokens.centro
                        anchors.verticalCenter: parent.verticalCenter
                        x: Math.round(parent.width * 0.2)
                        width: Math.round(parent.width * 0.26)
                        height: Math.max(1, tokens.px(1))
                        color: tokens.cor.contorno
                    }

                    Rectangle {
                        visible: tokens.centro
                        anchors.verticalCenter: parent.verticalCenter
                        x: Math.round(parent.width * 0.54)
                        width: Math.round(parent.width * 0.26)
                        height: Math.max(1, tokens.px(1))
                        color: tokens.cor.contorno
                    }

                    Rectangle {
                        visible: tokens.centro
                        anchors.centerIn: parent
                        width: tokens.px(7)
                        height: width
                        radius: Math.min(tokens.raio, width / 2)
                        color: tokens.cor.primaria
                    }
                }

                Item {
                    width: 1
                    height: tokens.px(12)
                }

                Text {
                    width: conteudo.width
                    visible: text.length > 0
                    text: raiz.tema.frase
                    wrapMode: Text.WordWrap
                    horizontalAlignment: tokens.centro ? Text.AlignHCenter : Text.AlignLeft
                    lineHeight: 1.15
                    color: tokens.cor.texto
                    font.family: tokens.ui
                    font.weight: tokens.pesoUi
                    font.pixelSize: tokens.px(tokens.estilo.frase_tamanho)
                    font.letterSpacing: tokens.px(tokens.estilo.frase_tamanho) * tokens.estilo.frase_espaco
                }

                Item {
                    width: 1
                    height: tokens.px(24)
                }

                Text {
                    width: conteudo.width
                    text: raiz.tema.usuario
                    horizontalAlignment: tokens.centro ? Text.AlignHCenter : Text.AlignLeft
                    color: tokens.cor.texto_suave
                    font.family: tokens.fonteRotulos
                    font.weight: tokens.pesoRotulos
                    font.variableAxes: tokens.eixosRotulos
                    font.pixelSize: tokens.px(tokens.estilo.rotulos_tamanho)
                    font.letterSpacing: tokens.px(tokens.estilo.rotulos_tamanho) * tokens.estilo.rotulos_espaco
                }

                Item {
                    width: 1
                    height: tokens.px(6)
                }

                Campo {
                    id: campoUsuario
                    objectName: "campoUsuario"

                    t: tokens
                    width: conteudo.width
                    travado: raiz.ocupado
                    KeyNavigation.tab: campoSenha
                    onAceito: {
                        if (texto.trim().length === 0 || campoSenha.texto.length > 0)
                            raiz.entrar()
                        else
                            campoSenha.forceActiveFocus()
                    }
                }

                Item {
                    width: 1
                    height: tokens.px(14)
                }

                Text {
                    width: conteudo.width
                    text: raiz.tema.senha
                    horizontalAlignment: tokens.centro ? Text.AlignHCenter : Text.AlignLeft
                    color: tokens.cor.texto_suave
                    font.family: tokens.fonteRotulos
                    font.weight: tokens.pesoRotulos
                    font.variableAxes: tokens.eixosRotulos
                    font.pixelSize: tokens.px(tokens.estilo.rotulos_tamanho)
                    font.letterSpacing: tokens.px(tokens.estilo.rotulos_tamanho) * tokens.estilo.rotulos_espaco
                }

                Item {
                    width: 1
                    height: tokens.px(6)
                }

                Campo {
                    id: campoSenha
                    objectName: "campoSenha"

                    t: tokens
                    width: conteudo.width
                    senha: true
                    erro: raiz.falhou
                    travado: raiz.ocupado
                    KeyNavigation.tab: seletor
                    onAceito: raiz.entrar()
                    onTextoChanged: {
                        if (texto.length > 0 && !raiz.ocupado && raiz.mensagem.length > 0) {
                            raiz.falhou = false
                            raiz.mensagem = ""
                        }
                    }
                }

                Item {
                    width: 1
                    height: tokens.px(10)
                }

                // aviso: mensagem do login, Caps Lock ou, sem nada a dizer, a ajuda de teclado
                Text {
                    objectName: "aviso"
                    width: conteudo.width
                    height: tokens.px(26)
                    text: raiz.textoAviso()
                    elide: Text.ElideRight
                    verticalAlignment: Text.AlignVCenter
                    horizontalAlignment: tokens.centro ? Text.AlignHCenter : Text.AlignLeft
                    color: raiz.mensagem.length > 0 ? (raiz.falhou ? tokens.cor.erro : tokens.cor.texto)
                         : raiz.caps ? tokens.cor.aviso
                         : tokens.cor.texto_suave
                    font.family: tokens.ui
                    font.weight: raiz.mensagem.length > 0 || raiz.caps ? tokens.pesoForte : tokens.pesoUi
                    font.pixelSize: tokens.px(tokens.estilo.texto_tamanho - 4)
                }
            }
        }

        // rodapé: sessão à esquerda, lema ao centro, energia à direita
        Seletor {
            id: seletor
            objectName: "seletor"

            t: tokens
            x: tokens.px(52)
            y: raiz.height - height - tokens.px(36)
            rotulo: raiz.tema.sessao
            nomes: raiz.nomesSessoes
            KeyNavigation.tab: botaoSuspender
        }

        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            y: raiz.height - height - tokens.px(46)
            width: Math.min(implicitWidth, raiz.width - 2 * Math.max(seletor.width, energia.width) - tokens.px(200))
            visible: text.length > 0
            text: raiz.tema.rodape
            elide: Text.ElideRight
            color: tokens.cor.texto_suave
            opacity: 0.8
            font.family: tokens.ui
            font.weight: tokens.pesoUi
            font.pixelSize: tokens.px(tokens.estilo.texto_tamanho - 3)
        }

        Row {
            id: energia

            x: raiz.width - width - tokens.px(52)
            y: raiz.height - height - tokens.px(36)
            spacing: tokens.px(6)

            Botao {
                id: botaoSuspender
                objectName: "botaoSuspender"

                t: tokens
                rotulo: raiz.caixa(tokens.txt.suspender, tokens.estilo.rotulos_caixa)
                enabled: sddm.canSuspend
                KeyNavigation.tab: botaoReiniciar
                onAcionado: sddm.suspend()
            }

            Botao {
                id: botaoReiniciar
                objectName: "botaoReiniciar"

                t: tokens
                rotulo: raiz.caixa(tokens.txt.reiniciar, tokens.estilo.rotulos_caixa)
                enabled: sddm.canReboot
                KeyNavigation.tab: botaoDesligar
                onAcionado: sddm.reboot()
            }

            Botao {
                id: botaoDesligar
                objectName: "botaoDesligar"

                t: tokens
                rotulo: raiz.caixa(tokens.txt.desligar, tokens.estilo.rotulos_caixa)
                enabled: sddm.canPowerOff
                KeyNavigation.tab: campoUsuario
                onAcionado: sddm.powerOff()
            }
        }
    }
}
