# Domínios

Quatro temas completos pro desktop, trocados de uma vez só: papel de parede, barra,
cores, terminal, prompt, animações de janela, sons, tela de bloqueio e apps. E um quinto,
o Neutro, que é o modo apresentação: desktop comum pra mostrar pra cliente (`Mod+N`).
Feito em 10/11/2026; o Grimório virou o modo HD-2D na noite de 11 pra 12/11.
Tudo o que define aparência está em **um arquivo**: [`dominios.toml`](dominios.toml).

| Domínio | De onde vem | Cara |
|---|---|---|
| `sistema` | Solo Leveling | Azul elétrico no preto, barra de HUD no topo, janela de missões viva na área de trabalho |
| `grimorio` | Despertar da Mana | RPG clássico de magia em pixel art (HD-2D), seis elementos que mudam sozinhos, HUD próprio na mesa. Ver a próxima seção |
| `setor2814` | Tropa dos Lanternas | Esmeralda, barra em pílula no topo, cores do terminal = espectro emocional |
| `maldicao` | JJK, Chainsaw Man, phonk | Preto, sangue e osso, canto vivo, barra vertical na esquerda |
| `neutro` | Nada | Modo apresentação: grafite com azul, barra comum no topo, papel de dunas. Fora do ciclo |

## Grimório HD-2D

O desktop vira o grimório do conjurador: pixel art nítida com luz moderna por cima (a
referência é Octopath Traveler), em cima do RPG autoral Despertar da Mana.

- **Seis elementos**: fogo, água, terra, vento, eletricidade e mana pura. O ativo muda
  sozinho com o mundo real (clima de Porto Alegre, CPU, bateria, hora) e dita a cor de
  destaque de tudo: moldura das janelas, barra, bloqueio, terminal, Claude Code, nova aba.
- **Seis lugares de fundo**, um por elemento (forja, santuário submerso, ruínas na floresta,
  picos no céu, torre da tempestade, biblioteca arcana), cada um em quatro horas do dia
  (aurora, dia, entardecer, noite). O papel de parede é a cena de título.
- **A mesa**: um HUD próprio (Quickshell) com o cenário vivo e 11 widgets: Ficha do
  Conjurador, Ofícios do Dia, Bardo, Relógio, Familiares, Núcleo, Crônica, Céus,
  Elemento, Página do Dia e Mapa. Roda como serviço de usuário (`dominios-hud.service`)
  com teto de memória, e só existe no domínio `grimorio`.
- **`Mod+G`** abre o grimório por cima das janelas; **Esc** fecha.
- Nível e XP vêm dos teus commits, ofícios e agentes. Som de chiptune e de estúdio.
  Terminal, Claude Code e nova aba do Chrome seguem o elemento.
- Quem manda em tudo isso é o `bin/nucleo`, um processo só de dados (cerca de 17 MB).

Direção de arte, vocabulário e regras do HUD: [`hud/dev/REGRAS.md`](hud/dev/REGRAS.md) e
[`hud/LEIA.md`](hud/LEIA.md). Créditos da arte e das fontes: [`CREDITOS.md`](CREDITOS.md).

Estado em 12/11 de manhã, pra tu saber o que foi visto de verdade:

| O quê | Estado |
|---|---|
| Serviço do HUD ligar, desligar, reerguer depois de `kill -9` | Testado |
| Seis cenas (noite e dia), aurora, entardecer, fusão das horas, troca de elemento, diálogo, abertura do login, modo crítico | Visto em tela |
| Grimório por cima de uma janela de teste | Visto, com o HUD de verdade |
| `Mod+G` apertado na tecla e `Esc` de verdade | Não: só testados por IPC e pelo log do Wayland |
| Mesa real no workspace 2 depois das 00:52 | Não fotografada (o foco voltou pro workspace 1) |
| Som | Mudo até o despertar (ver "Revelação da manhã" e "Som") |
| Login e boot novos | Prontos, não instalados (ver "Precisa de sudo") |

## Uso

| O quê | Como |
|---|---|
| Escolher domínio | `Mod+X` ou `dominio menu` |
| Próximo domínio | `Mod+Shift+X` ou `dominio proximo` |
| Ir direto | `dominio maldicao` |
| Modo apresentação (liga e desliga) | `Mod+N` ou `dominio apresentar` |
| Missões diárias | `Mod+M`, clique no contador da barra, ou `missao` |
| HUD de agentes | `Mod+A`, clique no robô da barra, ou `agentes` |
| Terminal (kitty) | `Mod+Return`. O Alacritty ficou em `Mod+Shift+Return` |
| Ligar ou desligar sons | `dominio som on` / `dominio som off` |
| Saúde do áudio | `som-diagnostico` |
| Abrir o grimório por cima das janelas (só no domínio `grimorio`) | `Mod+G` ou `hud alternar`. `Esc` fecha |
| Esconder os widgets e ver só o cenário (liga e desliga, fica guardado) | `Mod+Shift+G` ou `hud paisagem` (`ligar`, `desligar`) |
| Protetor de tela: o cenário sozinho depois de 3 min parado, na tomada; qualquer tecla volta | Sozinho. Testar na hora: `hud contemplar`. Minutos e liga/desliga: `[grimorio.contemplacao]` no `dominios.toml`, depois `dominio construir grimorio` |
| Notificação com o dono longe (Claude pedindo resposta, WhatsApp...): a tela acorda sozinha | Sozinho, pelo plugin do Noctalia (`bin/acordar-tela`). Fica quieto no modo apresentação. Registro em `~/.local/state/dominios/acordar-tela.log` |
| Ver o elemento ativo e o porquê | `elemento` |
| Travar, soltar, passar o elemento | `elemento travar fogo`, `elemento soltar`, `elemento proximo` |
| Ver a tua ficha (nível, XP, atributos) | `jogador` |
| Estado do HUD (memória e CPU) | `hud estado` |
| Reiniciar o HUD depois de mexer no código | `hud reiniciar` |
| Falar na caixa de diálogo do HUD | `hud dizer "Título" "texto"` |
| Tocar a abertura do login agora | `hud abertura` |
| Pacote de som do grimório | `som-pacote estado`, `som-pacote chiptune`, `som-pacote estudio` |
| Brinquedos de terminal | `brinquedos` (menu), `brinquedos chuva`, `brinquedos fogueira`, `brinquedos circulo` |
| Armar a revelação da manhã | `despertar --estado` e, pra armar, o comando de "Revelação da manhã" |

Os atalhos que já existiam continuam nas mesmas teclas. A única tecla que mudou de
destino é `Mod+Return` (abria o Alacritty, agora abre o kitty). `Mod+G` é novo e vale em
qualquer domínio, mas só faz algo no `grimorio` (nos outros o HUD está desligado e o
comando avisa isso e sai).

## Elementos

O `elemento` (`bin/elemento`, código em `hud/dados/elemento.py`) escolhe o elemento
ativo e grava `~/.local/state/dominios/elemento.json`. Cada sinal do mundo real vota com
um peso, e o elemento com mais peso ganha:

| Elemento | O que puxa |
|---|---|
| fogo | bateria baixa, CPU quente, calor, pôr do sol |
| água | chuva, garoa, umidade alta com nuvem |
| terra | tarde, tempo calmo e seco, máquina ociosa, fim de semana |
| vento | vento forte, brisa de dia claro, manhã |
| eletricidade | trovoada (agora ou na previsão), CPU sustentada alta, 3 ou mais agentes Claude |
| mana pura | madrugada, noite, e o padrão quando nada se destaca |

Regras: o elemento fica no mínimo 20 min; depois só cede se o líder passar por 8 pontos;
sinal urgente (bateria abaixo de 10%, trovoada agora, CPU fervendo) troca na hora. O clima
vem do Open-Meteo (Porto Alegre, uma consulta a cada 15 min no máximo; sem rede segue só
com hora e máquina).

- Travar na mão: `elemento travar fogo` (nomes: `fogo`, `agua`, `terra`, `vento`,
  `eletricidade`, `mana-pura`). Voltar ao automático: `elemento soltar`.
- `elemento simular --dia` mostra como seriam 24 h, sem gravar nada.
- Pesos e limites: tabela no topo de `hud/dados/elemento.py` (`elemento --help`).
- Cores dos seis: `[grimorio.elementos]` no `dominios.toml`. Depois, `dominio construir`.
- A cada troca rodam os ganchos de `ganchos/elemento.d/` (nova aba, terminal, moldura do
  niri, paleta do Noctalia, Claude Code). Executável novo ali entra sozinho; recebe o
  elemento novo e o anterior (ver `ganchos/elemento.d/LEIA`). Quem troca de domínio roda
  os de `ganchos/expandir.d/`.
- O tema do niri do grimório (cursor em pixel `Grimorio`, moldura na cor do elemento,
  janela que se materializa de um mosaico) vive em `modelos/_por_dominio/grimorio/niri.kdl`
  e `niri-animacoes.kdl`; o cursor é gerado por `gerar/cursor.py`.

## A mesa e os widgets

Cada widget é um arquivo `hud/widgets/<Nome>.qml`, e o lugar dele na tela é uma linha de
`hud/mesa.json` (`widget`, `x`, `y`, `largura`, `altura`; opcionais `ativo: false` e
`props`). A mesa relê o arquivo sozinha.

| Widget | O que mostra |
|---|---|
| Ficha do Conjurador | Nível, XP e atributos do `jogador`; bateria é o fôlego e memória é a mana |
| Ofícios do Dia | As tuas missões do `missoes.toml`; clicar marca como feito |
| Bardo | O que está tocando e um visualizador (`cava`) |
| Relógio | Hora e data, sobre o cenário |
| Familiares | Os agentes Claude ativos: conjurando, aguardando ou ociosos |
| Núcleo | CPU, memória, temperatura e rede; processos pesados como monstros com barra de vida; bestiário |
| Crônica | Teus commits do GitHub nas últimas 26 semanas |
| Céus | Clima de Porto Alegre e fase da lua |
| Elemento | A roda dos seis, o ativo aceso, e o motivo |
| Página do Dia | Uma frase por dia (`hud/dados/frases.toml`) |
| Mapa | Os workspaces do niri como salas |

- Mexer no visual ou criar widget: [`hud/LEIA.md`](hud/LEIA.md) tem os componentes, as
  vagas da mesa, o jeito de testar sem encostar no HUD de verdade e as armadilhas do
  Quickshell. Os dados vêm todos do `bin/nucleo` (contrato em `hud/dados/CONTRATO.md`).
- Cores, grade (1 pixel de arte = 3 pixels de tela) e o resto da linguagem: `hud/componentes/`.
- Depois de mexer num `.qml` com o HUD ligado ele recarrega sozinho, mas deixa uns MB
  a mais: `hud reiniciar`.
- Cenários e prints de teste: nunca rode `qs -p hud` nem `hud ligar` só pra testar. Use
  `hud/dev/prova` (ver o `LEIA.md`).

## Nível e ofícios

O `jogador` (`bin/jogador`, código em `hud/dados/jogador.py`) guarda a tua ficha em
`~/.local/state/dominios/jogador.json`. O XP vem de:

| Fonte | XP |
|---|---|
| Commit teu (autor = teu `git config --global user.email`) | 20, uma vez por hash |
| Ofício do dia concluído | 20 |
| Dia com todos os ofícios | 60 mais 5 por dia de sequência (até 10) |
| Dia perdido | menos 40 (não rebaixa o nível) |
| Agente invocado / de volta (sessão que durou 2 min ou mais) | 10 / 15 |

Na primeira execução ele contou todo o histórico de commits e as sessões do Claude Code.
Nível: `xp_proximo(n) = round(50 * n^1.4)`. Rank de E a S pelo nível.

- `jogador` mostra a ficha; `jogador conceder 50 "motivo"` dá XP na mão;
  `jogador gastar <atributo> [n]` gasta pontos livres (3 por nível ganho); `jogador eventos`.
- Ofícios: edita `missoes.toml` (é a tua rotina, não vai pro repositório).
- O nível alimenta a Ficha do Conjurador, a linha de status do Claude Code e o terminal.

## Som

Dois pacotes em `sons/grimorio/`: **chiptune** (sintetizado por código, `gerar/sons_grimorio.py`)
e **estúdio** (20 sons comprados e tratados por `gerar/estudio.py`: elementos, nível,
login, título, notificações, ofício, familiares). O estúdio vale por cima do chiptune; o
que não tem versão de estúdio continua chiptune.

- `som-pacote estado` mostra o ativo (agora: estúdio) e quais sons vêm de onde.
  `som-pacote chiptune` e `som-pacote estudio` trocam.
- `bin/som-eventos` toca os sons dos eventos do niri (janela, workspace, visão geral); o
  `nucleo` o embute e também toca os eventos do jogo (troca de elemento, XP, nível, ofício,
  familiar, tomada, bateria baixa).
- Liga e desliga geral: `dominio som on` / `off` (já existia).
- **O núcleo arranca mudo se existir `$XDG_RUNTIME_DIR/dominios-silencio`.** Esse arquivo
  foi posto durante a noite e está lá agora: é por isso que o grimório está calado. A
  revelação da manhã (`despertar`) apaga ele. Pra liberar na mão: `rm "$XDG_RUNTIME_DIR/dominios-silencio"`
  e, se continuar mudo, `hud reiniciar`.
- Durante a noite os sons só foram gerados e medidos, ninguém tocou. Ouvir é o teste que falta.

## Terminal

No grimório o kitty, o prompt (starship) e a ficha da abertura (fastfetch) seguem o
elemento ativo. A ficha tem a linha **CAPÍTULO** com o nome do elemento e o motivo, e as
barras de vida, mana e XP (`bin/ficha-linha`). Os arquivos vivos ficam em
`~/.local/state/dominios/` (`kitty-elemento.conf`, `starship-elemento.toml`) e são
refeitos pelo gancho `elemento.d/60-terminal`.

- Onde mexer: `modelos/_por_dominio/grimorio/` (`kitty-extra.conf`, `starship*.toml`,
  `fastfetch.jsonc`, `fish.fish`) e `gerar/terminal_elemento.py`. Depois, `dominio construir`.
- `brinquedos` abre um menu (fzf, gum ou lista numerada) com o que estiver instalado, mais
  três animações próprias em pixel: `chuva` (chuva de runas), `fogueira` e `circulo`
  (círculo mágico com os seis elementos). Saem com `q`, `Esc` ou `Ctrl+C`.

## Claude Code

O Claude Code usa o tema `Domínios` e uma linha de status que seguem o domínio e o elemento
(`bin/claude-tema` e `bin/claude-status`). A linha mostra elemento, nível e ofícios do
lado esquerdo e modelo e contexto do direito.

- O tema gerado é `~/.claude/themes/dominios.json`, refeito pelos ganchos
  `elemento.d/70-claude` e `expandir.d/70-claude`.
- Ligar: `claude-tema --instalar` (já feito; faz backup antes). Desligar: ver "Como desligar
  ou desfazer".
- Backup do que havia: `~/.rice-backup/2026-11-12/claude-settings.json.antes` (o tema era
  `dark` e não havia linha de status).

## Nova aba do Chrome

A nova aba mostra a cena do elemento ativo, a hora, os ofícios e a página do dia. O
`bin/nova-aba-estado` escreve `chrome-nova-aba/estado.json` e `cena.png`, chamado pelos
ganchos `50-nova-aba` (troca de elemento e de domínio). Esses dois arquivos são gerados e
não vão pro repositório. A extensão continua a mesma: carregar uma vez (ver "Apps").

## Login e boot

A tela de login (SDDM) e o splash de boot (Plymouth) têm o grimório em pixel, mas **só
valem depois de instalar com sudo** (ver "Precisa de sudo"). O que está instalado agora
ainda é o de 10/11 (a arte do grimório em `/usr/share/sddm/themes/dominios` difere da
de `root/sddm/dominios`). Os arquivos de arte são gerados: `python3 gerar/login.py sddm plymouth`.
Visto só em foto de teste do greeter; login de verdade e boot de verdade não foram testados.

## Revelação da manhã

`bin/despertar` é um vigia pra tu abrir o notebook de manhã e ver o grimório com a abertura
inteira, em vez de achar tudo já ligado. Ele olha só os contadores de interrupção do
teclado e do touchpad (nunca o que tu digita). Quando, depois das 05:30, chega um toque
depois de pelo menos 90 min de silêncio, ele: restaura o brilho, espera destravar, leva
o foco pra um workspace vazio, apaga o `dominios-silencio` (libera o som), toca a abertura
e desliga a cafeína. Toque de madrugada só acende a tela; passou das 14:00 sem revelar,
ele só restaura brilho e som e sai. Nunca revela no Neutro nem com o HUD desligado.

```sh
despertar --estado                                    # o que ele está pensando (não mexe em nada)
systemd-run --user --unit dominios-despertar --collect \
    ~/.config/dominios/bin/despertar --brilho 65535   # armar
systemctl --user stop dominios-despertar              # desarmar
```

Em 12/11, ao conferir, a unidade `dominios-despertar` **não estava armada** (inativa).
`despertar --simular` e as variáveis `DESPERTAR_SIM_*` (no topo do script) testam a
decisão sem tela nem som; a revelação de verdade, com a tela, não foi vista.

## Modo apresentação (domínio Neutro)

`Mod+N` troca pro Neutro e guarda o domínio em que tu estava. `Mod+N` de novo volta pra ele.

O que muda enquanto está ligado:

- Barra comum: áreas de trabalho, janela, data e hora, bandeja, rede, Bluetooth, volume,
  bateria. Sem botão de domínio, missões, agentes, mídia nem sino de notificações. Um ícone
  aparece só quando microfone, câmera ou tela estão sendo capturados.
- Não Perturbe ligado (as notificações vão pro histórico sem aparecer) e tela sempre
  acordada. Na saída os dois voltam como estavam.
- Sem som de interface, sem animação própria de janela, sem brilho colorido em volta.
- Terminal opaco, fonte 13, prompt comum e sem a ficha na abertura.
- Tela de bloqueio só com hora, data e senha. Nova aba do Chrome só com hora e busca.
- VS Code no tema de fábrica `Default Dark Modern` (chave `vscode_tema` no `dominios.toml`).
- `Mod+Shift+X` fica travado, pra um toque sem querer não trocar o desktop no meio da reunião.

Limites:

- O splash de boot continua sorteando um dos 4 emblemas (ele vive no initramfs e não tem
  como seguir o domínio sem root). Se for ligar o note na frente do cliente, liga antes.
- A tela de login só fica neutra depois de reinstalar o tema com sudo (ver "Precisa de sudo").
  Até lá, com o Neutro ativo, ela mostra a do Sistema.
- `Mod+M` e `Mod+A` continuam abrindo missões e agentes se tu apertar.
- Discord e Spotify acompanham com as cores neutras, mas não foram vistos em janela.
- `Mod+P` (modo projetor, que é teu e ajusta a resolução do monitor externo) é separado:
  um não liga o outro.

## Como mudar alguma coisa

1. Cor, fonte, raio, texto: edita `dominios.toml`.
2. Estrutura de um arquivo gerado (barra, prompt, shader): edita o modelo em `modelos/`
   (o que é específico de um domínio fica em `modelos/_por_dominio/<domínio>/`).
3. Roda `dominio construir`. Arte e sons: `dominio arte`.

Nunca edita `_build/`: é saída gerada. A sintaxe dos modelos (`{{cor.primaria|alfa:0.5}}`)
está no topo de `gerar/construir.py`.

Missões: edita `missoes.toml` (vieram do teu Protocolo de Rotina).

Grimório: elementos, mesa, som, terminal e o resto têm "onde mexer" nas seções acima.
As cores do HUD continuam saindo do `dominios.toml`: o modelo `modelos/hud-tema.json`
vira `_build/grimorio/hud-tema.json` no `dominio construir`.

## O que tem dentro

| Pasta ou arquivo | Função |
|---|---|
| `dominios.toml` | Fonte única: cores, fontes, forma e textos dos domínios (e dos seis elementos do grimório) |
| `modelos/` | Modelos de kitty, alacritty, niri, Noctalia, starship, fastfetch, btop, cava, GTK, VS Code, Discord, Spotify |
| `gerar/` | `construir.py` (modelos), `papeis.py` (papéis de parede, logos), `sons.py`, `sons_grimorio.py` e `estudio.py` (sons), `login.py` (tela de login e boot), `cursor.py` (cursor em pixel), `sessao_elemento.py` e `terminal_elemento.py` (arquivos por elemento) |
| `papeis/`, `sons/` | Arte e sons gerados (as cenas do HUD ficam em `hud/papel/cenas/`) |
| `_build/<domínio>/` | Saída. `atual` é um link pro domínio ativo |
| `bin/` | `dominio`, `missao`, `agentes`, `som-diagnostico`, `terminal`, e do grimório: `nucleo`, `jogador`, `elemento`, `som-pacote`, `som-eventos`, `brinquedos`, `claude-tema`, `claude-status`, `ficha-linha`, `barra-selo`, `nova-aba-estado`, `despertar` |
| `hud/` | O HUD do grimório (Quickshell): `hud` (comando), `shell.qml`, `mesa.json`, `widgets/`, `componentes/`, `casca/`, `dados/` (núcleo, elemento, jogador), `papel/` (cenário vivo e cenas), `sprites/`, `arte/`, `dev/` (provas), `LEIA.md` |
| `ganchos/elemento.d/` | Rodados a cada troca de elemento, com o elemento novo e o anterior |
| `CREDITOS.md` | Fontes, pacotes de arte livre e arte gerada |
| `shell/` | Noctalia 5: config base, plugin Luau, iniciador com modo seguro |
| `niri-atalhos.kdl`, `niri-shell.kdl` | Atalhos novos e os atalhos do shell, incluídos no fim da config do niri |
| `ganchos/expandir.d/` | Executáveis rodados a cada troca, com o nome do domínio |
| `root/` | O que precisa de sudo (login, boot, áudio no kernel). Ver abaixo |

## Shell: Noctalia 5

O shell passou do noctalia-shell 4.7 (Quickshell) pro Noctalia 5 nativo, que já estava
instalado. Medido na mesma idade de processo (75 a 90 s): **138 MB contra 325 MB** de PSS.

A atualização do sistema de 10/11/2026 levou o Noctalia de 5.2.0 pra 5.4.1 (152 MB de PSS
com 30 s) e **tirou o shell antigo do sistema**: o pacote `noctalia-shell` virou 5.4.1 e
não traz mais nenhum arquivo do Quickshell. `qs -c noctalia-shell` não sobe mais nada.
O pacote antigo segue em `/var/cache/pacman/pkg/noctalia-shell-4.7.7-3-any.pkg.tar.zst`.

- Config base: `shell/base.toml` (vira `~/.config/noctalia/10-dominios.toml`).
- Por domínio: `modelos/noctalia.toml` e `modelos/_por_dominio/*/noctalia-barra.toml`.
- Plugin: `shell/plugin/dominios/` (widget de comando na barra, painéis de missões e
  agentes, janela de missões na área de trabalho, som de notificação).
- O que tu mudar pela janela de Configurações do Noctalia vai pra
  `~/.local/state/noctalia/settings.toml` e passa a valer em todos os domínios, por cima
  destes arquivos. Pra voltar ao declarado, apaga aquele arquivo.
- Posição de widget ajustada pelo editor gráfico não sobrevive à troca de domínio (o
  Noctalia copia os widgets pro arquivo de estado e a troca limpa essa cópia). Pra mudar
  de vez, edita o modelo.
- Se o Noctalia cair duas vezes seguidas ao subir, `shell/iniciar` sobe ele em modo
  seguro: config de fábrica, sem os Domínios e sem o plugin (testado em 10/11). Pra
  forçar: `touch ~/.config/dominios/shell/modo-seguro` e relogar. Pra achar o erro:
  `noctalia config validate`.
- Grimório (12/11): barra, bloqueio, notificações e niri têm modelo próprio em
  `modelos/_por_dominio/grimorio/` (`noctalia.toml`, `niri.kdl`). A cor de destaque segue o
  elemento ativo: `gerar/sessao_elemento.py` gera `_build/grimorio/sessao/<elemento>/` e os
  ganchos `elemento.d/65-niri` (moldura e animação de janela, via
  `~/.local/state/dominios/niri-elemento.kdl`) e `66-noctalia` (aponta a paleta
  `dominio-grimorio` para a do elemento, sem regravar o `settings.toml`) aplicam a cada troca.
  O papel `papeis/grimorio.png` é a cena de título (`grimorio-titulo.png`); a arte antiga
  ficou em `grimorio-antigo.png`. Cursor em pixel (`Grimorio`, 32) só nele, por
  `expandir.d/45-cursor`.
- Nomes de cor: o Noctalia 5.4 aposentou `surface_variant` e `outline`. Os modelos e o
  plugin já usam `surface_container` e `outline_variant` (o plugin declara `plugin_api = 43`).

## Áudio

Causa do som que resetava (medida): o codec ALC256 deste Acer alterna o controle
`Headset Mic Jack` umas 5 vezes por segundo enquanto toca. Cada alternância fazia o
WirePlumber reprocessar as rotas, crescer até o teto de 256 MB e ser morto (184 reinícios
em 7 dias). O Bluetooth caía junto.

- Contorno ativo, sem root: `~/.config/alsa-card-profile/mixer/paths/analog-input-headset-mic.conf`.
- Fone Bluetooth: `~/.config/wireplumber/wireplumber.conf.d/60-bluetooth-fone.conf` deixa o
  fone no perfil de música quando um app abre o microfone (o microfone usado passa a ser o
  do notebook). Pra usar o microfone do fone, troca o perfil na mão. Apagar o arquivo
  volta ao padrão.
- Correção na origem (kernel), precisa de sudo e reboot: `root/extras.d/10-audio-alc256.sh`.
- Conferir: `som-diagnostico`.

## Memória e desempenho

Medido em 12/11/2026 com o serviço de verdade, 11 widgets, cenário e núcleo de verdade
(detalhe em `hud/LEIA.md`). O notebook tem 8 GB, então isso foi tratado como prioridade.

| Situação | Memória (PSS) | CPU (% de um núcleo) |
|---|---|---|
| Mesa à vista, parada | HUD cerca de 128 MB, núcleo cerca de 17 MB | cerca de 3% (cenário a 10 fps) |
| Com música no Bardo | idem | cerca de 3,7% (o `cava` soma 1%) |
| Escondida atrás das janelas | cerca de 122 MB e 17,5 MB | cerca de 0,2% (cenário, sprites e amostragem param) |
| Na bateria | idem | cerca de 0,05% (o cenário congela num quadro; a animação só roda com o carregador ligado) |
| Memória do sistema apertada | idem | congela; em nível crítico o HUD se recolhe |

- Teto do serviço: `MemoryHigh=260M` (o kernel aperta) e `MemoryMax=330M` (o kernel mata e
  o serviço reergue). GPU: cerca de 5% do sistema com a mesa à vista contra 4% sem o HUD.
- O serviço sobe com ambiente enxuto (sem tema GTK, jemalloc afinado, Vulkan, só as fontes
  usadas); isso tirou o HUD de 273 MB pra cerca de 114 MB num teste. Tabela completa no `LEIA.md`.
- Ver agora: `hud estado`.

## Apps

| App | Estado | O que falta tu fazer |
|---|---|---|
| VS Code | Extensão `dominios.dominios-tema` instalada, tema acompanha o domínio | Nada. Teu tema anterior era `SynthWave '84` (o `settings.json` original está em `~/.rice-backup/2026-11-10/vscode-settings.json.antes`) |
| Chrome | Página de nova aba em `chrome-nova-aba/` (no grimório mostra a cena do elemento) | Carregar a extensão uma vez (abaixo) |
| Discord | Vesktop 1.6.9 em `~/.local/opt/vesktop`, tema pré-ligado | Abrir o Vesktop e fazer login. O Discord oficial continua instalado e intocado |
| Spotify | Spicetify 2.46.4 aplicado no Spotify 1.2.92 | Abrir. Ver avisos abaixo |

Chrome, uma vez só:

1. Abre `chrome://extensions` e liga o "Modo do desenvolvedor" (canto de cima, à direita).
2. "Carregar sem compactação" e escolhe `~/.config/dominios/chrome-nova-aba` (a pasta
   `.config` é oculta: `Ctrl+L` na janela de arquivos e cola o caminho).
3. Abre uma aba nova e, quando o Chrome perguntar, clica em "Manter".

Spotify:

- Se o Spotify se atualizar e as cores sumirem: fecha e roda `spicetify backup apply`
  (repete a cada atualização do Spotify).
- Se abrir quebrado ou com tela preta: `spicetify restore` volta ao original.

Discord: se o tema não vier ligado, Configurações > Vencord > Temas e liga "Domínio".

Não testado em janela de verdade: Vesktop e Spotify com o tema (ninguém fez login nem
abriu os dois durante a madrugada), e a extensão dentro do teu Chrome.

## Precisa de sudo

```sh
sudo ~/.config/dominios/root/instalar-root.sh
```

Pergunta `[s/N]` antes de cada parte e desfaz com `--desfazer`. Rodado em 10/11 às 09:23.
**Rodar de novo agora**, porque a tela de login e o boot do grimório são novos. Respostas:

| Parte | O que faz | Responde | Testado? |
|---|---|---|---|
| 0. Atualização | `pacman -Syu` (teu banco de pacotes era de 30/09) mais `cava papirus-icon-theme playerctl grim` | **N**. Já foi feita em 10/11; não precisa repetir | Não dá pra desfazer a atualização em si |
| 1. Login (SDDM) | Tema `dominios` em `/usr/share/sddm/themes`, segue o domínio ativo no próximo logout. É ela que leva a tela de login nova (grimório em pixel) pro sistema | **s** | Tela vista em foto com o greeter real em modo de teste; login de verdade não |
| 2. Boot (Plymouth) | Splash com um dos emblemas sorteado a cada boot. Reconstrói o initramfs | **s** | Só em simulador. O primeiro boot é o primeiro teste real |
| 3. Extras | `extras.d/10-audio-alc256.sh`: correção do áudio no kernel (precisa de reboot) | **a teu critério** | Não. Vale depois do reboot; abre o arquivo antes (ver "Áudio") |

Antes de rodar, se mexeu na arte de login: `python3 gerar/login.py sddm plymouth`.

Se o boot travar no splash: no menu do systemd-boot aperta `e`, apaga a palavra `splash`,
dá boot e roda o script com `--desfazer`.

Tela de bloqueio: travar e destravar por `loginctl unlock-session` foi testado; destravar
digitando a senha não (eu não tenho tua senha). Se a senha não entrar: `Ctrl+Alt+F3`, faz
login no terminal e roda `loginctl unlock-session 2`.

## No repositório de dotfiles

O repositório é **público**: só a fonte vai pro git. O `.gitignore` desta pasta deixa de fora:

| O quê | Por quê |
|---|---|
| `_build/`, `atual`, `papeis/`, `sons/` | Saída gerada (`dominio construir`, `dominio arte`) |
| Arte e fontes da tela de login e do boot em `root/` | Gerado por `gerar/login.py` |
| `chrome-nova-aba/estado.json` e `cena.png` (além de `dominio.json` e `papel.png`) | Estado do momento, refeito a cada troca de elemento; o `estado.json` tem teus ofícios e tua ficha |
| `hud/sprites/fontes-livres/` e `hud/papel/fontes-livres/`, menos o que o HUD usa | Pacotes brutos baixados do OpenGameArt (50 MB, milhares de arquivos). Entram só os 42 PNGs que o `hud/sprites/indice.json` aponta (CC0), o `LICENCA.txt` de cada pacote e o `CREDITOS.md`. Os pacotes de cenário (`papel/fontes-livres`) não são usados por nada |
| `hud/papel/*.qsb` e `hud/papel/dev/*.qsb` | Shader compilado; refaz com `hud/papel/compilar` |
| `__pycache__/`, `*.pyc` | Cache do Python |
| `hud/dev/REGRAS.md` | Tem teu nome, idade, cidade e gostos (as regras dos agentes); fica só na máquina |
| `missoes.toml` | É a tua rotina. Se quiser publicar, apaga a linha dele no `.gitignore` |

Numa máquina nova, depois de clonar: `dominio arte`, `python3 gerar/login.py sddm plymouth`,
`dominio instalar`, `hud/papel/compilar` (o HUD precisa do shader compilado; o compilador é o `qsb` do Qt 6, em
`/usr/lib/qt6/bin/qsb`), e, pra login e boot, `sudo root/instalar-root.sh`. O cenário do
grimório vem pronto em `hud/papel/cenas/`. Os sons de estúdio (`sons/`) não vão pro git:
numa máquina nova só existe o chiptune, que o `dominio arte` gera. Cuidado com o
repositório de dotfiles: ele tem um token que não está commitado, então nunca `git add -u`
na raiz e confere o `git status` antes de dar push.

## Como desligar ou desfazer

Cada peça nova tem volta própria, sem mexer nas outras:

| Peça | Como desligar ou desfazer |
|---|---|
| HUD (mesa e `Mod+G`) | Agora: `hud desligar`. Ele volta no próximo login se o domínio for o `grimorio`. Pra sair de vez, troca de domínio (`dominio sistema`): o gancho `expandir.d/60-hud` desliga o HUD em todo domínio que não seja o grimório. Pra tirar do login: apaga a linha `hud sessao` do `niri-shell.kdl` e a do `Mod+G` do `niri-atalhos.kdl` |
| Som do grimório | Tudo: `dominio som off`. Voltar ao chiptune: `som-pacote chiptune`. Núcleo mudo: ver "Som" |
| Tema do Claude Code | `claude-tema --desfazer`: devolve `theme` e `statusLine` do backup (`~/.rice-backup/2026-11-12/claude-settings.json.antes`; lá o tema era `dark` e não havia linha de status) e apaga `~/.claude/themes/dominios.json`. Não testei rodar o `--desfazer` |
| Cursor em pixel | Troca de domínio: o gancho `expandir.d/45-cursor` volta `capitaine-cursors` 24. Pra apagar o tema: `rm -r ~/.local/share/icons/Grimorio` e tira o bloco `cursor` do `modelos/_por_dominio/grimorio/niri.kdl` |
| Revelação da manhã | `systemctl --user stop dominios-despertar` |
| Nova aba do Chrome | Remove a extensão em `chrome://extensions`, ou troca de domínio |
| Tela de login e boot | `sudo root/instalar-root.sh --desfazer` |
| Elemento travado | `elemento soltar` |
| Grimório antigo (papel de parede) | A arte antiga ficou em `papeis/grimorio-antigo.png` (e `-desfocado`). Pra usar de volta: `cp papeis/grimorio-antigo.png papeis/grimorio.png`, o mesmo com `-desfocado`, e `dominio expandir grimorio`. **Não testei.** O `dominio arte` rebota a cena de título por cima; pra valer de vez, apaga a entrada `"grimorio"` do dicionário `CAPA` em `gerar/papeis.py` (também não testado). O grimório antigo não tinha HUD, então o `hud desligar` já basta |

Desfazer tudo (os domínios inteiros):

```sh
dominio desinstalar                      # tira includes e links; no próximo login sobe o Noctalia 5 de fábrica
tar -xzf ~/.rice-backup/2026-11-10/config-antes.tar.gz -C ~   # configs exatamente como estavam
```

O shell antigo (Quickshell) não volta com o `desinstalar`: a atualização do sistema tirou
ele do pacote. A tua config dele continua em `~/.config/noctalia/settings.json`.

O que foi instalado em `~/.local` sem root: kitty (`~/.local/kitty.app`), starship, fontes
(`~/.local/share/fonts/dominios`), Vesktop e Spicetify. As correções de áudio ficam, de propósito.
