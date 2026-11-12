import QtQuick
import qs.componentes

// Mostruario: todos os componentes da base lado a lado, para conferir de uma vez.
//   hud/dev/prova dev/Mostruario.qml --tamanho 1320x750
Item {
    implicitWidth: 1320
    implicitHeight: 750

    Janela {
        x: 0; y: 0; width: 432; height: 402
        titulo: "Ficha"
        etiqueta: "Nv 35"
        Column {
            anchors.fill: parent
            spacing: 9
            Row {
                spacing: 12
                Retrato { fonte: "mago"; fps: 3 }
                Column {
                    spacing: 0
                    TextoPixel { tipo: "gotico"; text: "Guilherme"; color: Tema.destaque; sombra: true; height: 54; y: -9 }
                    Texto { text: "Arcanista de Rank B"; suave: true }
                    Row { spacing: 9; Selo { rank: "B" } Selo { rank: "S" } Selo { rank: "E" } Selo { rank: "A" } }
                }
            }
            Barra { width: parent.width; tipo: "vida"; valor: 0.72; rotulo: "Vida"; texto: "72/100" }
            Barra { width: parent.width; tipo: "mana"; valor: 0.41; rotulo: "Mana"; texto: "3,1 GB" }
            Barra { width: parent.width; tipo: "xp"; valor: 0.9; rotulo: "Experiência"; texto: "2970/7255" }
        }
    }
    Janela {
        x: 450; y: 0; width: 420; height: 402
        titulo: "Componentes"
        Column {
            anchors.fill: parent
            spacing: 6
            Campo { width: parent.width; rotulo: "Classe"; valor: "Invocador" }
            Campo { width: parent.width; rotulo: "Sequência"; valor: "12 dias"; numero: true }
            Divisor { width: parent.width }
            Texto { width: parent.width; text: "Texto corrido em fonte lisa: ação, lição, pé, í, õ. Legível por horas." }
            Divisor { width: parent.width; rotulo: "Atributos" }
            Row {
                spacing: 9
                Icone { nome: "fogo" } Icone { nome: "agua" } Icone { nome: "terra" } Icone { nome: "vento" }
                Icone { nome: "eletricidade" } Icone { nome: "mana-pura" }
                Icone { nome: "moeda" } Icone { nome: "espada" } Icone { nome: "pocao" }
            }
            Row {
                spacing: 9
                Icone { nome: "trofeu"; cor: Tema.ouro } Icone { nome: "musica" } Icone { nome: "tocar" } Icone { nome: "chip" }
                Icone { nome: "github" } Icone { nome: "bateria" } Icone { nome: "wifi" } Icone { nome: "coroa"; tamanho: 11 }
                Icone { nome: "robo"; tamanho: 11 } Icone { nome: "nublado"; tamanho: 11 }
            }
            Row { spacing: 9; Botao { texto: "Concluir" } Botao { texto: "Tocar"; icone: "tocar"; marcado: true } Botao { icone: "proxima" } }
        }
    }
    Janela {
        x: 888; y: 0; width: 432; height: 402
        titulo: "Núcleo"
        variante: "perigo"
        etiqueta: "87 °C"
        Row {
            anchors.fill: parent
            spacing: 15
            Medidor { valor: 0.62; texto: "62"; rotulo: "Mana"; cor: Tema.corDe("agua") }
            Medidor { valor: 0.18; texto: "18"; rotulo: "Fôlego"; cor: Tema.corDe("vento") }
            Column {
                spacing: 9
                Grafico { width: 150; height: 60; valores: [3, 8, 12, 30, 22, 18, 40, 55, 80, 62, 45, 30, 28, 35, 60, 90, 70, 50, 20, 10, 5, 12, 33, 48, 52]; maximo: 100 }
                Grafico { width: 150; height: 45; tipo: "linha"; colado: true; cor: Tema.corDe("fogo")
                    valores: [3, 8, 12, 30, 22, 18, 40, 55, 80, 62, 45, 30, 28, 35, 60, 90, 70, 50, 20, 10, 5, 12, 33, 48, 52, 3, 8, 12, 30, 22, 18, 40, 55, 80, 62, 45, 30, 28, 35, 60, 90, 70, 50, 20, 10, 5, 12, 33, 48, 52] }
                Row { spacing: 6; Gema { grande: true; brilho: 0.6 } Gema { elemento: "fogo"; grande: true } Gema { elemento: "apagada"; grande: true } }
            }
        }
    }
    Janela {
        x: 0; y: 426; width: 432; height: 198
        titulo: "Recompensa"
        variante: "ouro"
        etiqueta: "+60 XP"
        Column {
            anchors.fill: parent
            spacing: 6
            TextoPixel { tipo: "medio"; text: "Nível 36"; color: Tema.ouro; sombra: true }
            Texto { width: parent.width; text: "Todos os ofícios do dia cumpridos. A sequência chegou a 12 dias." }
        }
    }
    Janela {
        x: 450; y: 426; width: 420; height: 198
        titulo: "Página do Dia"
        variante: "pergaminho"
        Column {
            anchors.fill: parent
            spacing: 6
            Texto { width: parent.width; tamanho: 20; text: "Não é porque as coisas são difíceis que não ousamos; é porque não ousamos que elas são difíceis." }
            Texto { suave: true; text: "Sêneca, Cartas a Lucílio" }
        }
    }
    Column {
        x: 888; y: 426; spacing: 0
        TextoPixel { tipo: "enorme"; text: "21:47"; sombra: true }
        TextoPixel { tipo: "gotico"; text: "Quarta-feira"; color: Tema.destaque }
        Row { spacing: 12; Rotulo { text: "11 de novembro" } TextoPixel { tipo: "miudo"; text: "Lua crescente" } }
    }
    Figura { x: 1215; y: 426; fonte: "monstro-slime" }
    Figura { x: 1215; y: 530; fonte: "familiar-espirito" }
    Dialogo {
        id: fala
        x: 0; y: 624; width: 900; height: 126
        Component.onCompleted: enfileirar({ titulo: "Grimório", texto: "O vento virou. A torre da tempestade acende as runas e o elemento agora é eletricidade.", retrato: "grimorio", tipo: "elemento" })
    }
}
