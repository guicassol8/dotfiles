pragma ComponentBehavior: Bound
import QtQuick

// Tela de login em pixel art (HD-2D) do Grimório: título gótico, relógio, e embaixo o
// "arquivo de jogo salvo" (retrato, nome, nível, classe, título e xp) com o campo de senha.
// Tudo na grade de 3 px de tela por pixel de arte. Os campos ficam aqui e o Main.qml
// os alcança por campoUsuario, campoSenha e seletor.
Item {
    id: tela

    required property var t
    required property var r

    readonly property alias campoUsuario: usuario
    readonly property alias campoSenha: senha
    readonly property alias seletor: sessao
    readonly property var pecas: r.tema.arte.pecas
    readonly property int g: t.px(3)
    readonly property bool pedeUsuario: r.semUsuario || r.jogadorNome.length === 0

    function peca(nome) {
        return r.arquivo(pecas[nome])
    }

    function mistura(a, b, f) {
        return Qt.rgba(a.r * (1 - f) + b.r * f, a.g * (1 - f) + b.g * f, a.b * (1 - f) + b.b * f, 1)
    }

    anchors.fill: parent
    visible: r.principal

    // título, no alto
    Item {
        id: cabeca

        x: Math.round((tela.width - width) / 2)
        y: tela.g * 6
        width: tituloTexto.width
        height: tituloTexto.height

        TextoPixel {
            id: tituloTexto

            g: tela.g
            corpo: 43
            text: tela.r.tema.titulo
            color: tela.t.cor.texto
            font.family: tela.t.pxGotico
            corSombra: Qt.alpha(tela.t.cor.primaria, 0.55)
            contorno: true
        }
    }

    TextoPixel {
        x: Math.round((tela.width - width) / 2)
        y: cabeca.y + cabeca.height + tela.g * 1
        g: tela.g
        corpo: 21
        text: tela.r.tema.frase
        color: tela.t.cor.secundaria
        font.family: tela.t.pxGoticoPequeno
        contorno: true
    }

    // relógio e data no canto
    Column {
        x: tela.width - width - tela.g * 20
        y: tela.g * 8
        spacing: tela.g * 1

        TextoPixel {
            anchors.right: parent.right
            g: tela.g
            corpo: 41
            text: Qt.formatTime(tela.r.agora, tela.t.txt.formato_hora)
            color: tela.t.cor.texto
            font.family: tela.t.pxRelogio
            contorno: true
        }

        TextoPixel {
            anchors.right: parent.right
            g: tela.g
            corpo: 8
            text: tela.r.agora.toLocaleDateString(Qt.locale(tela.t.txt.localidade), tela.t.txt.formato_data).toUpperCase()
            color: tela.t.cor.primaria
            font.family: tela.t.pxRotulo
            aperto: -1
            contorno: true
        }
    }

    // ------------------------------------------------------------ painel
    Item {
        id: painel

        readonly property int largura: tela.g * 330
        readonly property int altura: tela.g * 58

        width: largura
        height: altura
        x: Math.round((tela.width - width) / 2) + tela.r.tremor
        y: tela.g * 280

        BorderImage {
            source: tela.peca("sombra")
            smooth: false
            x: -tela.g * 6
            y: -tela.g * 3
            width: painel.width + tela.g * 12
            height: painel.height + tela.g * 12
            border { left: 30; right: 30; top: 30; bottom: 30 }
            opacity: 0.75
        }

        Rectangle {
            anchors.fill: parent
            anchors.margins: 2 * tela.g
            gradient: Gradient {
                GradientStop { position: 0; color: Qt.alpha(tela.mistura(tela.t.cor.superficie2, tela.t.cor.fundo, 0.45), 0.9) }
                GradientStop { position: 1; color: Qt.alpha(tela.mistura(tela.t.cor.fundo, tela.t.cor.fundo, 0.06), 0.94) }
            }
        }

        Fatias {
            anchors.fill: parent
            g: tela.g
            fonte: tela.peca("moldura")
            borda: 12
        }

        Repeater {
            model: 4

            Image {
                required property int index

                source: tela.peca("gema")
                smooth: false
                width: 5 * tela.g
                height: width
                x: index % 2 === 0 ? 2 * tela.g : painel.width - 7 * tela.g
                y: index < 2 ? 2 * tela.g : painel.height - 7 * tela.g
            }
        }

        // placa de título na linha de cima da moldura
        Item {
            x: 10 * tela.g
            y: -2 * tela.g
            width: placaTexto.width + 10 * tela.g
            height: 11 * tela.g

            Fatias {
                anchors.fill: parent
                g: tela.g
                fonte: tela.peca("placa")
                borda: 4
                bordaEsquerda: 5
                bordaDireita: 5
            }

            TextoPixel {
                id: placaTexto

                x: 5 * tela.g
                y: Math.round((parent.height - height) / 2) - tela.g
                g: tela.g
                corpo: 8
                aperto: -1
                text: String(tela.t.estilo.arquivo).toUpperCase()
                color: tela.t.cor.texto
                font.family: tela.t.pxRotulo
            }
        }

        // retrato
        Item {
            id: retrato

            x: 20 * tela.g
            y: 11 * tela.g
            width: 36 * tela.g
            height: width

            Rectangle {
                anchors.fill: parent
                anchors.margins: tela.g
                gradient: Gradient {
                    GradientStop { position: 0; color: tela.mistura(tela.t.cor.superficie2, tela.t.cor.primaria, 0.26) }
                    GradientStop { position: 1; color: tela.mistura(tela.t.cor.fundo, "#000000", 0.3) }
                }
            }

            Image {
                anchors.centerIn: parent
                source: tela.peca("conjurador")
                smooth: false
                width: 32 * tela.g
                height: width
            }

            Fatias {
                anchors.fill: parent
                g: tela.g
                fonte: tela.peca("retrato")
                borda: 3
            }
        }

        // ficha: nome, nível, classe e título, barra de xp
        Item {
            id: ficha

            x: retrato.x + retrato.width + 9 * tela.g
            y: retrato.y
            width: 140 * tela.g
            height: retrato.height
            visible: !tela.pedeUsuario

            TextoPixel {
                id: nome

                g: tela.g
                corpo: 56 / 3
                text: tela.r.jogadorNome
                color: tela.t.cor.texto
                font.family: tela.t.pxNome
            }

            TextoPixel {
                y: nome.height + tela.g * 1
                g: tela.g
                corpo: 11
                text: tela.r.jogadorLinha
                color: tela.t.cor.texto_suave
                font.family: tela.t.pxMiudo
                sombra: false
            }

            Item {
                y: ficha.height - 6 * tela.g
                width: ficha.width
                height: 6 * tela.g

                Entalhe { anchors.fill: parent; g: tela.g; cor: Qt.darker(tela.t.cor.fundo, 1.7) }

                Rectangle {
                    x: tela.g
                    y: tela.g
                    width: parent.width - 2 * tela.g
                    height: 4 * tela.g
                    color: Qt.darker(tela.t.cor.superficie, 1.2)
                }

                Rectangle {
                    x: tela.g
                    y: tela.g
                    width: Math.round((parent.width - 2 * tela.g) * Math.max(0, Math.min(1, tela.r.jogadorXp)) / tela.g) * tela.g
                    height: 4 * tela.g
                    color: tela.t.cor.primaria

                    Rectangle {
                        width: parent.width
                        height: tela.g
                        color: tela.t.cor.secundaria
                    }
                }
            }
        }

        // sem usuário guardado: pede o nome
        Item {
            x: ficha.x
            y: retrato.y
            width: ficha.width
            height: retrato.height
            visible: tela.pedeUsuario

            TextoPixel {
                id: rotuloUsuario

                y: tela.g * 4
                g: tela.g
                corpo: 8
                aperto: -1
                text: tela.r.tema.usuario.toUpperCase()
                color: tela.t.cor.texto_suave
                font.family: tela.t.pxRotulo
            }

            Campo {
                id: usuario
                objectName: "campoUsuario"

                t: tela.t
                y: rotuloUsuario.y + rotuloUsuario.height + 2 * tela.g
                width: parent.width
                height: 18 * tela.g
                travado: tela.r.ocupado
                KeyNavigation.tab: senha
                onAceito: {
                    if (texto.trim().length === 0 || senha.texto.length > 0)
                        tela.r.entrar()
                    else
                        senha.forceActiveFocus()
                }
            }
        }

        // senha
        Item {
            x: ficha.x + ficha.width + 9 * tela.g
            y: retrato.y
            width: painel.width - x - 20 * tela.g
            height: retrato.height

            TextoPixel {
                id: rotuloSenha

                y: tela.g * 4
                g: tela.g
                corpo: 8
                aperto: -1
                text: tela.r.tema.senha.toUpperCase()
                color: tela.t.cor.texto_suave
                font.family: tela.t.pxRotulo
            }

            Campo {
                id: senha
                objectName: "campoSenha"

                t: tela.t
                y: rotuloSenha.y + rotuloSenha.height + 2 * tela.g
                width: parent.width
                height: 18 * tela.g
                senha: true
                erro: tela.r.falhou
                travado: tela.r.ocupado
                KeyNavigation.tab: sessao
                onAceito: tela.r.entrar()
                onTextoChanged: {
                    if (texto.length > 0 && !tela.r.ocupado && tela.r.mensagem.length > 0) {
                        tela.r.falhou = false
                        tela.r.mensagem = ""
                    }
                }
            }
        }
    }

    // aviso: mensagem do login, Caps Lock ou a ajuda de teclado
    TextoPixel {
        objectName: "aviso"
        x: Math.round((tela.width - width) / 2)
        y: painel.y + painel.height + tela.g * 5
        g: tela.g
        corpo: 11
        text: tela.r.textoAviso()
        font.family: tela.t.pxMiudo
        sombra: false
        contorno: true
        color: tela.r.mensagem.length > 0 ? (tela.r.falhou ? tela.t.cor.erro : tela.t.cor.texto)
             : tela.r.caps ? tela.t.cor.aviso : tela.t.cor.texto_suave
    }

    // rodapé: sessão à esquerda, energia à direita
    Seletor {
        id: sessao
        objectName: "seletor"

        t: tela.t
        x: tela.t.px(52)
        y: tela.height - height - tela.t.px(36)
        rotulo: tela.r.tema.sessao
        nomes: tela.r.nomesSessoes
        KeyNavigation.tab: botaoSuspender
    }

    Row {
        x: tela.width - width - tela.t.px(52)
        y: tela.height - height - tela.t.px(36)
        spacing: tela.t.px(6)

        Botao {
            id: botaoSuspender
            objectName: "botaoSuspender"

            t: tela.t
            rotulo: tela.r.caixa(tela.t.txt.suspender, tela.t.estilo.rotulos_caixa)
            enabled: sddm.canSuspend
            KeyNavigation.tab: botaoReiniciar
            onAcionado: sddm.suspend()
        }

        Botao {
            id: botaoReiniciar
            objectName: "botaoReiniciar"

            t: tela.t
            rotulo: tela.r.caixa(tela.t.txt.reiniciar, tela.t.estilo.rotulos_caixa)
            enabled: sddm.canReboot
            KeyNavigation.tab: botaoDesligar
            onAcionado: sddm.reboot()
        }

        Botao {
            id: botaoDesligar
            objectName: "botaoDesligar"

            t: tela.t
            rotulo: tela.r.caixa(tela.t.txt.desligar, tela.t.estilo.rotulos_caixa)
            enabled: sddm.canPowerOff
            KeyNavigation.tab: tela.pedeUsuario ? usuario : senha
            onAcionado: sddm.powerOff()
        }
    }
}
