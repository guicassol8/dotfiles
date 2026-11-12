import QtQuick
import qs.componentes

// Cronica: os dias de trabalho (GitHub fundido com os commits locais, o maior dos dois) nas ultimas 26 semanas como cristais de
// pixel (9 px com 3 de vao, 5 niveis calibrados pelos quantis dos proprios dados),
// com o total do ano, os feitos de hoje e a sequencia. Dados: Nucleo.cronica.
Janela {
    id: cron

    titulo: "Crônica"

    readonly property var c: Nucleo.cronica
    readonly property var semanas: c && c.semanas ? c.semanas : []

    // limiares dos niveis 2, 3 e 4: quantis 1/3, 2/3 e 0,9 dos dias com feito
    readonly property var cortes: {
        const v = [];
        for (const s of semanas)
            for (const d of s)
                if (d > 0)
                    v.push(d);
        v.sort((a, b) => a - b);
        if (v.length === 0)
            return [1, 2, 3];
        const q = f => v[Math.min(v.length - 1, Math.floor(f * v.length))];
        return [q(0.34), q(0.67), q(0.9)];
    }
    function nivel(d) {
        if (!(d > 0))
            return 0;
        return d >= cortes[2] ? 4 : d >= cortes[1] ? 3 : d >= cortes[0] ? 2 : 1;
    }
    // sobe de um tom quase apagado ate o destaque cheio
    function corNivel(n) {
        return n === 0 ? Tema.alfa(Tema.destaque, 0.10)
            : Tema.mistura(Tema.mistura(Tema.fundo, Tema.destaque, [0, 0.52, 0.68, 0.84, 1.0][n]), "#ffffff", n === 4 ? 0.12 : 0);
    }
    readonly property int diaHoje: new Date().getDay()      // 0 = domingo, linha da grade
    function milhar(n) {
        return String(Math.round(n || 0)).replace(/\B(?=(\d{3})+(?!\d))/g, ".");
    }

    // grade: 26 colunas x 7 linhas
    Item {
        id: grade
        visible: cron.c !== null && cron.semanas.length > 0
        width: 26 * 12 - 3
        height: 7 * 12 - 3
        Repeater {
            model: cron.semanas.length * 7
            Item {
                id: dia
                required property int index
                readonly property int col: Math.floor(index / 7) + (26 - cron.semanas.length)
                readonly property int lin: index % 7
                readonly property bool ultima: col === 25
                readonly property bool futuro: ultima && lin > cron.diaHoje
                readonly property int cont: cron.semanas[col - (26 - cron.semanas.length)][lin] || 0
                readonly property int n: cron.nivel(cont)
                readonly property bool hoje: ultima && lin === cron.diaHoje
                x: col * 12
                y: lin * 12
                width: 9
                height: 9
                visible: !futuro
                Rectangle {
                    anchors.fill: parent
                    color: cron.corNivel(dia.n)
                }
                Rectangle {                     // faceta clara, canto de cima
                    visible: dia.n > 0
                    width: 3
                    height: 3
                    color: Tema.mistura(cron.corNivel(dia.n), "#ffffff", 0.45)
                }
                Rectangle {                     // sombra do canto de baixo
                    visible: dia.n > 0
                    x: 6; y: 6
                    width: 3
                    height: 3
                    color: Tema.mistura(cron.corNivel(dia.n), "#120c22", 0.45)
                }
                Rectangle {                     // marca de hoje: aro de ouro no vao
                    visible: dia.hoje
                    x: -3; y: -3
                    width: 15
                    height: 15
                    color: "transparent"
                    border.width: 3
                    border.color: Tema.ouro
                }
            }
        }
    }

    // numeros grandes, embaixo da grade
    Row {
        visible: grade.visible
        y: grade.height + 6
        width: parent.width
        spacing: 0
        Repeater {
            model: [
                { r: "Ano", v: cron.milhar(cron.c ? cron.c.total_ano : 0), cor: "" },
                { r: "Hoje", v: String(cron.c ? cron.c.hoje : 0), cor: "ouro" },
                { r: "Dias", v: String(cron.c ? cron.c.sequencia : 0), cor: "" }
            ]
            Item {
                id: est
                required property var modelData
                required property int index
                width: index === 0 ? 165 : index === 1 ? 102 : 117
                height: 27
                Rotulo { text: est.modelData.r; y: 0 }
                TextoPixel {
                    tipo: "medio"
                    sombra: true
                    x: est.width - width - (est.index === 2 ? 0 : 12)
                    y: -7
                    color: est.modelData.cor === "ouro" ? Tema.ouro : Tema.texto
                    text: est.modelData.v
                }
            }
        }
    }

    // sem dados
    Row {
        visible: !grade.visible
        anchors.centerIn: parent
        spacing: 9
        Icone { nome: "github"; anchors.verticalCenter: parent.verticalCenter; cor: Tema.textoSuave }
        Texto { suave: true; tamanho: 16; anchors.verticalCenter: parent.verticalCenter; text: "A crônica está fora de alcance" }
    }
}
