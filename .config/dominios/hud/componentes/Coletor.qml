import QtQuick
import Quickshell
import Quickshell.Io

// Coletor: roda um comando e entrega a saida ja lida como JSON em `dados`.
//
//   uma vez        Coletor { comando: ["missao", "widget", "--json"] }
//   a cada N ms    Coletor { comando: "sensors -j"; intervalo: 5000 }
//   continuo       Coletor { comando: ["jogador", "seguir"]; continuo: true }
//                  (o processo fica vivo e cada LINHA da saida e uma atualizacao)
//
// `ativo: false` pausa: para o relogio e, no modo continuo, mata o processo.
// Nunca roda duas vezes ao mesmo tempo: se o comando demorar mais que o
// intervalo, a rodada seguinte e pulada.
Scope {
    id: coletor

    property var comando: []            // lista de argumentos, ou um texto (roda em sh -c)
    property int intervalo: 0           // ms entre rodadas; 0 = so uma vez
    property bool continuo: false
    property bool ativo: true
    property bool json: true            // false: `dados` recebe o texto cru, sem interpretar
    property int religar: 3000          // continuo: ms ate subir de novo se o processo morrer; 0 = nao religa

    // ---- saida
    property var dados: null            // ultimo resultado bom (pode nascer com um valor de exemplo)
    property string texto: ""           // ultima saida crua
    property string erro: ""            // vazio quando a ultima rodada deu certo
    property bool pronto: false         // ja chegou ao menos um resultado
    property int rodadas: 0
    signal atualizado(var dados)
    signal falhou(string erro)

    // roda agora, fora do relogio (ignorado no modo continuo e se ja estiver rodando)
    function atualizar() {
        if (!continuo && !proc.running && _args.length > 0)
            proc.running = true;
    }

    readonly property var _args: typeof comando === "string"
        ? (comando.trim() === "" ? [] : ["sh", "-c", comando])
        : (comando || [])

    function _recebe(bruto) {
        const t = bruto.trim();
        if (t === "")
            return;
        texto = t;
        if (!json) {
            dados = t;
        } else {
            try {
                dados = JSON.parse(t);
            } catch (e) {
                _falha("JSON invalido: " + e + " em: " + t.slice(0, 80));
                return;
            }
        }
        erro = "";
        pronto = true;
        rodadas += 1;
        atualizado(dados);
    }

    function _falha(msg) {
        erro = msg;
        falhou(msg);
    }

    function _liga() {
        if (!ativo || _args.length === 0)
            return;
        espera.stop();
        if (continuo) {
            proc.running = true;
        } else if (intervalo > 0 || !pronto) {
            atualizar();
        }
    }

    onAtivoChanged: {
        if (ativo) {
            _liga();
        } else {
            espera.stop();
            if (continuo)
                proc.running = false;
        }
    }
    on_ArgsChanged: {
        if (proc.running && continuo) {
            proc.running = false;       // o onExited religa com o comando novo
        } else {
            Qt.callLater(_liga);
        }
    }
    Component.onCompleted: _liga()

    Process {
        id: proc
        command: coletor._args
        stdout: coletor.continuo ? linhas : inteiro
        stderr: StdioCollector { id: erros }
        onExited: (codigo, estado) => {
            if (codigo !== 0 && coletor.ativo)
                coletor._falha("saiu com codigo " + codigo + (erros.text ? ": " + erros.text.trim().slice(0, 200) : ""));
            if (coletor.continuo && coletor.ativo && coletor.religar > 0)
                espera.restart();
        }
    }

    StdioCollector {
        id: inteiro
        onStreamFinished: coletor._recebe(text)
    }

    SplitParser {
        id: linhas
        onRead: linha => coletor._recebe(linha)
    }

    Timer {
        interval: Math.max(50, coletor.intervalo)
        repeat: true
        running: coletor.ativo && !coletor.continuo && coletor.intervalo > 0
        onTriggered: coletor.atualizar()
    }

    Timer {
        id: espera
        interval: Math.max(200, coletor.religar)
        onTriggered: coletor._liga()
    }
}
