import QtQuick
import qs.componentes

// Página do Dia: a frase estoica do grimório, em pergaminho, com capitular gótica de
// pixel e corpo em serifa. O corpo é quebrado por código (as duas primeiras linhas
// contornam a capitular) e o tamanho da letra é o maior que cabe sem cortar.
// Dados: Nucleo.pagina {texto, autor, obra}.
Janela {
    id: pagina

    titulo: "Página do Dia"
    variante: "pergaminho"
    respiro: 12

    readonly property var exemplo: ({ texto: "A mana está em todos os lugares.", autor: "Grimório", obra: null })
    readonly property var p: Nucleo.pagina || exemplo
    readonly property string texto: String(p.texto || "").trim()
    readonly property string inicial: texto.charAt(0)
    readonly property string resto: texto.slice(1)

    readonly property string serifa: "Alegreya"
    readonly property int larguraCap: 42            // capitular + respiro, na grade
    readonly property int linhasCap: 2
    readonly property var tamanhos: [22, 21, 20, 19, 18, 17, 16, 15, 14]
    readonly property int alturaCorpo: corpo.height - 48

    // quebra gulosa: as `linhasCap` primeiras linhas perdem a largura da capitular
    function quebra(tamanho) {
        const palavras = resto.split(/\s+/);
        const linhas = [];
        let atual = "";
        for (let i = 0; i < palavras.length; i++) {
            const larg = corpo.width - (linhas.length < linhasCap ? larguraCap : 0);
            const tenta = atual === "" ? palavras[i] : atual + " " + palavras[i];
            if (atual !== "" && medidas.at(tamanho).advanceWidth(tenta) > larg) {
                linhas.push(atual);
                atual = palavras[i];
            } else {
                atual = tenta;
            }
        }
        if (atual !== "")
            linhas.push(atual);
        return linhas;
    }

    // escolhe o maior tamanho em que tudo cabe
    readonly property var layout: {
        if (medidas.pronto && texto !== "") {
            let melhor = null;
            for (let i = 0; i < tamanhos.length; i++) {
                const t = tamanhos[i];
                const linhas = quebra(t);
                const alto = Math.round(t * 1.2);
                melhor = { tamanho: t, linhas: linhas, alto: alto };
                if (linhas.length * alto <= alturaCorpo)
                    break;
            }
            return melhor;
        }
        return { tamanho: 18, linhas: [], alto: 22 };
    }

    // medidor: um FontMetrics por tamanho candidato
    Item {
        id: medidas
        property bool pronto: false
        property var fm: ({})
        function at(t) { return fm[t]; }
        Component.onCompleted: {
            const m = {};
            for (let i = 0; i < pagina.tamanhos.length; i++)
                m[pagina.tamanhos[i]] = modelo.createObject(medidas, { pixel: pagina.tamanhos[i] });
            fm = m;
            pronto = true;
        }
        Component {
            id: modelo
            FontMetrics {
                property int pixel: 18
                font.family: pagina.serifa
                font.pixelSize: pixel
                font.weight: Font.Medium
            }
        }
    }

    // corpo da frase
    Item {
        id: livro
        width: parent.width
        height: pagina.alturaCorpo
        // frase curta: desce um pouco, para nao ficar colada no titulo
        y: Tema.grade(Math.max(0, Math.min(18, (pagina.alturaCorpo - Math.max(pagina.linhasCap, pagina.layout.linhas.length) * pagina.layout.alto) / 2)))

        TextoPixel {
            tipo: "gotico"
            color: Tema.mistura(pagina.acento, Tema.tintaPapel, 0.45)
            text: pagina.inicial
            x: 0
            y: -9
            width: pagina.larguraCap
        }
        Repeater {
            model: pagina.layout.linhas
            Text {
                required property int index
                required property string modelData
                x: index < pagina.linhasCap ? pagina.larguraCap : 0
                y: index * pagina.layout.alto
                text: modelData
                color: pagina.tinta
                font.family: pagina.serifa
                font.pixelSize: pagina.layout.tamanho
                font.weight: Font.Medium
                renderType: Text.NativeRendering
                textFormat: Text.PlainText
                wrapMode: Text.NoWrap
            }
        }
    }

    // ornamento e assinatura
    Divisor {
        id: filete
        anchors.bottom: assinatura.top
        anchors.bottomMargin: 3
        width: parent.width
        height: 15
    }
    Text {
        id: assinatura
        anchors.bottom: parent.bottom
        anchors.right: parent.right
        width: parent.width
        horizontalAlignment: Text.AlignRight
        elide: Text.ElideLeft
        wrapMode: Text.NoWrap
        textFormat: Text.StyledText
        font.family: pagina.serifa
        font.pixelSize: 17
        font.weight: Font.Medium
        color: pagina.tintaSuave
        text: "<b><font color=\"" + pagina.tinta + "\">" + pagina.p.autor + "</font></b>"
            + (pagina.p.obra ? "<i>, " + pagina.p.obra + "</i>" : "")
    }
}
