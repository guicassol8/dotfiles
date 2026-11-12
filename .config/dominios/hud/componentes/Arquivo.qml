import QtQuick
import Quickshell
import Quickshell.Io

// Arquivo: le um arquivo (JSON por padrao) e rele sozinho quando ele muda.
//
//   Arquivo { id: ficha; caminho: "~/.local/state/dominios/jogador.json" }
//   ... ficha.dados.nivel      (null enquanto nao leu ou se o arquivo nao existe)
//
// Aguenta gravacao no lugar e troca atomica por rename (medido). NAO percebe a
// troca de um link simbolico no caminho: nesse caso chame recarregar().
Scope {
    id: arq

    property string caminho: ""         // aceita ~/ no comeco
    property bool json: true            // false: `dados` recebe o texto cru
    property bool observar: true

    // ---- saida
    property var dados: null            // ultimo conteudo bom (pode nascer com um valor de exemplo)
    property string texto: ""
    property bool existe: false
    property string erro: ""
    signal atualizado(var dados)

    function recarregar() {
        visao.reload();
    }

    readonly property string _real: caminho.startsWith("~/") ? Quickshell.env("HOME") + caminho.slice(1) : caminho

    function _recebe(t) {
        existe = true;
        texto = t;
        if (!json) {
            dados = t;
        } else {
            try {
                dados = JSON.parse(t);
            } catch (e) {
                // arquivo pela metade: fica com o conteudo anterior e espera a proxima mudanca
                erro = "JSON invalido: " + e;
                return;
            }
        }
        erro = "";
        atualizado(dados);
    }

    FileView {
        id: visao
        path: arq._real
        watchChanges: arq.observar
        printErrors: false
        onLoaded: arq._recebe(text())
        onFileChanged: reload()
        onLoadFailed: err => { arq.existe = false; arq.erro = "nao deu para ler " + arq._real; }
    }
}
