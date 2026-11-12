import QtQuick
import qs.componentes

// Maquina (Nucleo): em cima os sinais vitais (oito cristais de carga, calor, mana,
// eter, disco e a rede em historico); embaixo o bestiario, os processos mais
// pesados como monstros. Dados: Nucleo.maquina (chega a cada 2 s, so com a mesa a vista).
Janela {
    id: maq

    titulo: "Núcleo"

    // exemplo ate o nucleo responder
    readonly property var exemplo: ({
        cpu_pct: 0, nucleos: [0, 0, 0, 0, 0, 0, 0, 0], carga1: 0, mem_pct: 0, mem_usada_mb: 0,
        mem_total_mb: 0, mem_disponivel_mb: 0, swap_pct: 0, temp_c: 0, rede_baixa_kbps: 0,
        rede_sobe_kbps: 0, disco_pct: 0, processos: []
    })
    readonly property var m: Nucleo.maquina || exemplo
    readonly property var nucleos: m.nucleos && m.nucleos.length > 0 ? m.nucleos : exemplo.nucleos
    readonly property var procs: m.processos || []

    // historico da rede (40 amostras), so cresce quando chega dado novo
    property var histBaixa: []
    property var histSobe: []
    Connections {
        target: Nucleo
        function onMaquinaChanged() {
            const mm = Nucleo.maquina;
            if (!mm)
                return;
            maq.histBaixa = maq._empurra(maq.histBaixa, mm.rede_baixa_kbps || 0);
            maq.histSobe = maq._empurra(maq.histSobe, mm.rede_sobe_kbps || 0);
        }
    }
    function _empurra(lista, v) {
        const n = lista.concat([v]);
        return n.length > 40 ? n.slice(n.length - 40) : n;
    }

    function fmtMem(mb) {
        const v = mb || 0;
        return v >= 1024 ? (v / 1024).toFixed(1).replace(".", ",") + " GB" : Math.round(v) + " MB";
    }
    function fmtRede(kb) {
        const v = kb || 0;
        return v >= 1024 ? (v / 1024).toFixed(1).replace(".", ",") + " MB/s" : Math.round(v) + " KB/s";
    }
    function pct(v) { return Math.round(v || 0) + "%"; }

    // cor do calor: vento (fresco), ouro (morno), fogo (quente)
    function corCalor(t) {
        const f = Math.max(0, Math.min(1, (t - 45) / 40));
        return f < 0.5 ? Tema.mistura(Tema.corDe("vento"), Tema.ouro, f * 2) : Tema.mistura(Tema.ouro, Tema.corDe("fogo"), (f - 0.5) * 2);
    }

    // monstro estavel por nome do processo
    readonly property var bichos: ["monstro-slime", "monstro-morcego", "monstro-esqueleto", "monstro-golem", "monstro-fantasma", "monstro-chefe"]
    function bichoDe(nome) {
        let h = 5381;
        const s = String(nome || "");
        for (let i = 0; i < s.length; i++)
            h = ((h * 33) + s.charCodeAt(i)) >>> 0;
        return bichos[h % bichos.length];
    }
    function nomeCurto(nome) {
        return String(nome || "").split(/[\/+:]/)[0];
    }

    Column {
        anchors.fill: parent
        spacing: 0

        // ---- sinais vitais (120 px)
        Item {
            width: parent.width
            height: 120

            // nucleos: oito cristais em colunas
            Item {
                id: esq
                width: 117
                height: parent.height
                Rotulo { text: "Núcleos"; y: -3 }
                Row {
                    y: 21
                    spacing: 3
                    Repeater {
                        model: 8
                        Item {
                            id: col
                            required property int index
                            readonly property real carga: Math.max(0, Math.min(100, maq.nucleos[index] || 0))
                            readonly property int acesos: carga > 0 ? Math.max(1, Math.round(carga / 100 * 7)) : 0
                            width: 12
                            height: 81
                            Repeater {
                                model: 7
                                Rectangle {
                                    required property int index
                                    readonly property bool aceso: (6 - index) < col.acesos
                                    readonly property bool topo: (6 - index) === col.acesos - 1
                                    width: 12
                                    height: 9
                                    y: index * 12
                                    color: !aceso ? Tema.alfa(Tema.destaque, 0.14)
                                        : (6 - index) >= 5 ? Tema.mistura(Tema.destaque, Tema.corDe("fogo"), 0.55)
                                        : Tema.mistura(Tema.destaque, "#120c22", 0.12)
                                    Rectangle {          // faceta do cristal
                                        visible: parent.aceso
                                        width: 3
                                        height: 3
                                        color: Tema.mistura(parent.color, "#ffffff", parent.topo ? 0.7 : 0.4)
                                    }
                                }
                            }
                        }
                    }
                }
                Numero {
                    y: 104
                    tamanho: 14
                    suave: true
                    text: maq.pct(maq.m.cpu_pct) + "  carga " + (maq.m.carga1 || 0).toFixed(2).replace(".", ",")
                }
            }

            // sinais da direita
            Column {
                x: 135
                width: parent.width - x
                spacing: 3

                Repeater {
                    model: [
                        { r: "Calor", t: "temp" }, { r: "Mana", t: "mem" }, { r: "Éter", t: "swap" }, { r: "Disco", t: "disco" }
                    ]
                    Item {
                        id: lin
                        required property var modelData
                        width: parent.width
                        height: 21
                        readonly property real v: modelData.t === "temp" ? Math.max(0, Math.min(1, (maq.m.temp_c || 0) / 100))
                            : modelData.t === "mem" ? (maq.m.mem_pct || 0) / 100
                            : modelData.t === "swap" ? (maq.m.swap_pct || 0) / 100 : (maq.m.disco_pct || 0) / 100
                        readonly property string txt: modelData.t === "temp" ? Math.round(maq.m.temp_c || 0) + " °C"
                            : modelData.t === "mem" ? (maq.m.mem_usada_mb / 1024).toFixed(1).replace(".", ",") + "/" + (maq.m.mem_total_mb / 1024).toFixed(1).replace(".", ",") + " GB"
                            : modelData.t === "swap" ? maq.pct(maq.m.swap_pct) : maq.pct(maq.m.disco_pct)
                        Rotulo { text: lin.modelData.r; y: 0; anchors.verticalCenter: parent.verticalCenter }
                        Barra {
                            x: 69
                            width: 99
                            valor: lin.v
                            cor: lin.modelData.t === "temp" ? maq.corCalor(maq.m.temp_c || 0)
                                : lin.modelData.t === "mem" ? Tema.corDe("agua")
                                : lin.modelData.t === "swap" ? Tema.corDe("mana-pura") : Tema.corDe("terra")
                        }
                        Numero {
                            anchors.right: parent.right
                            anchors.verticalCenter: parent.verticalCenter
                            tamanho: 14
                            suave: true
                            text: lin.txt
                        }
                    }
                }

                // rede: baixa e sobe
                Row {
                    spacing: 9
                    Repeater {
                        model: [{ b: true }, { b: false }]
                        Item {
                            id: rede
                            required property var modelData
                            width: (parent.parent.width - 9) / 2
                            height: 24
                            Grafico {
                                anchors.fill: parent
                                colado: true
                                valores: rede.modelData.b ? maq.histBaixa : maq.histSobe
                                cor: rede.modelData.b ? Tema.corDe("agua") : Tema.destaque
                                tipo: "linha"
                            }
                            Numero {
                                x: 3
                                y: -2
                                tamanho: 13
                                text: (rede.modelData.b ? "↓ " : "↑ ") + maq.fmtRede(rede.modelData.b ? maq.m.rede_baixa_kbps : maq.m.rede_sobe_kbps)
                            }
                        }
                    }
                }
            }
        }

        Divisor { width: parent.width; rotulo: "Bestiário" }

        // ---- bestiario (96 px)
        Item {
            id: besta
            width: parent.width
            height: 96

            readonly property var chefe: maq.procs.length > 0 ? maq.procs[0] : null

            // o chefe
            Item {
                width: 201
                height: parent.height
                visible: besta.chefe !== null
                Rectangle {
                    x: 0; y: 0; width: 96; height: 96
                    color: Tema.alfa(Tema.perigo, 0.10)
                    border.width: 3
                    border.color: Tema.alfa(Tema.perigo, 0.55)
                }
                Figura { x: 0; y: 0; fonte: maq.bichoDe(besta.chefe ? besta.chefe.nome : ""); fps: 0 }
                Rotulo { x: 108; y: -3; text: "Chefe"; color: Tema.perigo }
                Texto {
                    x: 108; y: 20; width: parent.width - 108
                    tamanho: 19
                    elide: Text.ElideRight
                    wrapMode: Text.NoWrap
                    text: besta.chefe ? maq.nomeCurto(besta.chefe.nome) : ""
                }
                Numero {
                    x: 108; y: 44
                    tamanho: 22
                    color: Tema.ouro
                    text: besta.chefe ? maq.pct(besta.chefe.cpu_pct) : ""
                }
                Barra {
                    x: 108; y: 72
                    width: 93
                    tipo: "vida"
                    valor: besta.chefe ? besta.chefe.cpu_pct / 100 : 0
                }
                Numero {
                    anchors.right: parent.right
                    y: 49
                    tamanho: 14
                    suave: true
                    text: besta.chefe ? maq.fmtMem(besta.chefe.mem_mb) : ""
                }
            }

            // os demais
            Column {
                x: 213
                width: parent.width - x
                spacing: 0
                Repeater {
                    model: Math.min(4, Math.max(0, maq.procs.length - 1))
                    Item {
                        id: bicho
                        required property int index
                        readonly property var p: maq.procs[index + 1]
                        width: parent.width
                        height: 24
                        Item {
                            width: 30; height: 24; clip: true
                            Figura { x: -1; y: -4; fonte: maq.bichoDe(bicho.p.nome); ponto: 1 }
                        }
                        Texto {
                            x: 33; y: -3; width: 60
                            tamanho: 15
                            elide: Text.ElideRight
                            wrapMode: Text.NoWrap
                            text: maq.nomeCurto(bicho.p.nome)
                        }
                        Rectangle {                      // vida, 100% = um nucleo
                            x: 33; y: 19; width: parent.width - 33; height: 3
                            color: Tema.alfa(Tema.corDe("fogo"), 0.22)
                            Rectangle {
                                width: Tema.grade(Math.min(1, bicho.p.cpu_pct / 100) * parent.width)
                                height: 3
                                color: Tema.corDe("fogo")
                            }
                        }
                        Numero {
                            anchors.right: parent.right
                            y: 0
                            tamanho: 13
                            text: maq.pct(bicho.p.cpu_pct) + "  " + maq.fmtMem(bicho.p.mem_mb)
                        }
                    }
                }
            }
        }
    }
}
