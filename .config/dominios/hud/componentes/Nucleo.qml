pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Io

// Nucleo: a unica fonte de dados do HUD. Sobe ~/.config/dominios/bin/nucleo como
// processo filho (um so para o HUD inteiro), le uma linha JSON por mensagem
// ({"canal": ..., "dados": ...}) e guarda o ultimo valor de cada canal numa
// propriedade. Contrato em hud/dados/CONTRATO.md.
//
// Widget nenhum roda script para dado que ja existe aqui: use Nucleo.<canal>.
// Todo canal pode estar null enquanto a primeira mensagem nao chega.
Singleton {
    id: nucleo

    readonly property string casa: Quickshell.env("HOME")
    // $HUD_NUCLEO troca o comando por uma linha de shell (teste); "nao" desliga o processo.
    // A bancada (dev/prova) usa `nucleo --uma-vez`, que emite tudo uma vez e NAO toca som.
    readonly property string comando: Quickshell.env("HUD_NUCLEO") || casa + "/.config/dominios/bin/nucleo"
    readonly property var _args: Quickshell.env("HUD_NUCLEO") ? ["sh", "-c", comando] : [comando]
    readonly property string pastaEstado: Quickshell.env("DOMINIOS_ESTADO") || casa + "/.local/state/dominios"
    readonly property bool desligado: comando === "nao"

    // ---- canais
    property var elemento: null         // {elemento, motivo, desde, travado, anterior, candidatos, clima, maquina}
    property var jogador: null          // ficha: {nome, titulo, classe, nivel, rank, xp, xp_proximo, atributos, eventos...}
    property var maquina: null          // {cpu_pct, nucleos, mem_pct, temp_c, bateria_pct, na_tomada, processos...} a cada 2 s
    property var familiares: []         // [{id, projeto, estado, desde, descricao}]
    property var oficios: null          // {titulo, itens [{id, texto, feito, categoria}], feitos, total, sequencia_dias, termina_em_s}
    property var cronica: null          // {semanas, total_ano, hoje, sequencia, atualizado}
    property var pagina: null           // {texto, autor, obra}
    property var pressao: ({ nivel: "ok" })
    signal dialogo(var fala)            // {id, titulo, texto, retrato, tipo, som}
    signal mensagem(string canal, var dados)    // toda mensagem, inclusive de canal que este arquivo nao conhece

    readonly property bool vivo: proc.running
    property int quedas: 0

    // a casca liga isto enquanto a mesa esta a vista; so ai o nucleo mede a maquina
    property bool amostrar: false
    onAmostrarChanged: _manda("maquina " + (amostrar ? 1 : 0))

    // ---- comandos para o nucleo
    function som(nome) { _manda("som " + nome); }
    function oficio(id) { _manda("oficio " + id); }
    function travarElemento(nome) { _manda("elemento travar " + nome); }
    function soltarElemento() { _manda("elemento soltar"); }

    function _manda(linha) {
        if (proc.running)
            proc.write(linha + "\n");
    }

    readonly property var _canais: ["elemento", "jogador", "maquina", "familiares", "oficios", "cronica", "pagina", "pressao"]

    function _recebe(linha) {
        if (linha.length < 2)
            return;
        let m;
        try {
            m = JSON.parse(linha);
        } catch (e) {
            console.warn("Nucleo: linha que nao e JSON: " + linha.slice(0, 100));
            return;
        }
        if (!m || typeof m.canal !== "string")
            return;
        if (m.canal === "dialogo") {
            if (m.dados)
                dialogo(m.dados);
        } else if (_canais.indexOf(m.canal) >= 0) {
            if (m.dados !== null && m.dados !== undefined || m.canal === "cronica")
                nucleo[m.canal] = m.dados;
        }
        mensagem(m.canal, m.dados);
    }

    Process {
        id: proc
        command: nucleo._args
        stdinEnabled: true
        running: !nucleo.desligado
        stdout: SplitParser { onRead: linha => nucleo._recebe(linha) }
        stderr: SplitParser { onRead: linha => console.warn("nucleo: " + linha) }
        onStarted: {
            subida.restart();
            if (nucleo.amostrar)
                nucleo._manda("maquina 1");
        }
        // cobre saida normal, queda e falha ao subir (binario ausente nao emite `exited`)
        onRunningChanged: {
            if (running || nucleo.desligado)
                return;
            // espera crescente: 1 s, 2 s, 4 s... ate 60 s; zera se ele ficou de pe 30 s
            nucleo.quedas = subida.running ? nucleo.quedas + 1 : 1;
            subida.stop();
            volta.interval = Math.min(60000, 1000 * Math.pow(2, Math.min(nucleo.quedas - 1, 6)));
            if (nucleo.quedas === 1 || nucleo.quedas === 5)
                console.warn("Nucleo: " + nucleo.comando + " nao esta de pe; nova tentativa em " + volta.interval / 1000 + " s");
            volta.restart();
        }
    }

    Timer { id: subida; interval: 30000 }       // rodando = o processo subiu ha menos de 30 s
    Timer { id: volta; onTriggered: proc.running = true }

    // valores iniciais, para o HUD nao nascer vazio (e para funcionar sem o nucleo)
    FileView {
        path: nucleo.pastaEstado + "/elemento.json"
        printErrors: false
        onLoaded: { if (nucleo.elemento === null) try { nucleo.elemento = JSON.parse(text()); } catch (e) {} }
    }
    FileView {
        path: nucleo.pastaEstado + "/jogador.json"
        printErrors: false
        onLoaded: { if (nucleo.jogador === null) try { nucleo.jogador = JSON.parse(text()); } catch (e) {} }
    }
}
