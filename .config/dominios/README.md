# Domínios

Quatro temas completos pro desktop, trocados de uma vez só: papel de parede, barra,
cores, terminal, prompt, animações de janela, sons, tela de bloqueio e apps. E um quinto,
o Neutro, que é o modo apresentação: desktop comum pra mostrar pra cliente (`Mod+N`).
Feito em 10/11/2026. Tudo o que define aparência está em **um arquivo**:
[`dominios.toml`](dominios.toml).

| Domínio | De onde vem | Cara |
|---|---|---|
| `sistema` | Solo Leveling | Azul elétrico no preto, barra de HUD no topo, janela de missões viva na área de trabalho |
| `grimorio` | Despertar da Mana | Cores do `identidade/tokens.toml` do livro (o tema escuro que estava pronto e sem uso), Cinzel, teu sigilo |
| `setor2814` | Tropa dos Lanternas | Esmeralda, barra em pílula embaixo, cores do terminal = espectro emocional |
| `maldicao` | JJK, Chainsaw Man, phonk | Preto, sangue e osso, canto vivo, barra vertical na esquerda |
| `neutro` | Nada | Modo apresentação: grafite com azul, barra comum no topo, papel de dunas. Fora do ciclo |

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

Os atalhos que já existiam continuam nas mesmas teclas. A única tecla que mudou de
destino é `Mod+Return` (abria o Alacritty, agora abre o kitty).

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

## O que tem dentro

| Pasta ou arquivo | Função |
|---|---|
| `dominios.toml` | Fonte única: cores, fontes, forma e textos dos 4 domínios |
| `modelos/` | Modelos de kitty, alacritty, niri, Noctalia, starship, fastfetch, btop, cava, GTK, VS Code, Discord, Spotify |
| `gerar/` | `construir.py` (modelos), `papeis.py` (papéis de parede, logos), `sons.py` (sons sintetizados), `login.py` (tela de login) |
| `papeis/`, `sons/` | Arte e sons gerados |
| `_build/<domínio>/` | Saída. `atual` é um link pro domínio ativo |
| `bin/` | `dominio`, `missao`, `agentes`, `som-diagnostico`, `terminal` |
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

## Apps

| App | Estado | O que falta tu fazer |
|---|---|---|
| VS Code | Extensão `dominios.dominios-tema` instalada, tema acompanha o domínio | Nada. Teu tema anterior era `SynthWave '84` (o `settings.json` original está em `~/.rice-backup/2026-11-10/vscode-settings.json.antes`) |
| Chrome | Página de nova aba em `chrome-nova-aba/` | Carregar a extensão uma vez (abaixo) |
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
Depois de criar ou mudar um domínio (o Neutro, por exemplo), roda de novo e responde `s`
só na parte 1: é ela que leva a tela de login nova pro sistema.

| Parte | O que faz | Testado? |
|---|---|---|
| 0. Atualização | `pacman -Syu` (teu banco de pacotes é de 30/09) mais `cava papirus-icon-theme playerctl grim` | Não dá pra desfazer a atualização em si |
| 1. Login (SDDM) | Tema `dominios` em `/usr/share/sddm/themes`, segue o domínio ativo no próximo logout | Tela testada nos 4 domínios com o greeter real em modo de teste; login de verdade não |
| 2. Boot (Plymouth) | Splash com um dos 4 emblemas sorteado a cada boot. Reconstrói o initramfs | Só em simulador. O primeiro boot é o primeiro teste real |
| 3. Extras | `extras.d/10-audio-alc256.sh`: correção do áudio no kernel | Não. Vale depois do reboot |

Se o boot travar no splash: no menu do systemd-boot aperta `e`, apaga a palavra `splash`,
dá boot e roda o script com `--desfazer`.

Tela de bloqueio: travar e destravar por `loginctl unlock-session` foi testado; destravar
digitando a senha não (eu não tenho tua senha). Se a senha não entrar: `Ctrl+Alt+F3`, faz
login no terminal e roda `loginctl unlock-session 2`.

## No repositório de dotfiles

Só a fonte vai pro git (uns 100 arquivos, 720 kB). O `.gitignore` desta pasta deixa de fora:

- o que é gerado (`_build/`, `papeis/`, `sons/`, arte e fontes da tela de login, emblemas do boot);
- `missoes.toml`, que é a tua rotina e o repositório é público. Se quiser publicar, apaga a
  linha dele no `.gitignore`.

Numa máquina nova, depois de clonar: `dominio arte`, `python3 gerar/login.py sddm plymouth`,
`dominio instalar` e, pra login e boot, `sudo root/instalar-root.sh`.

## Desfazer tudo

```sh
dominio desinstalar                      # tira includes e links; no próximo login sobe o Noctalia 5 de fábrica
tar -xzf ~/.rice-backup/2026-11-10/config-antes.tar.gz -C ~   # configs exatamente como estavam
```

O shell antigo (Quickshell) não volta com o `desinstalar`: a atualização do sistema tirou
ele do pacote. A tua config dele continua em `~/.config/noctalia/settings.json`.

O que foi instalado em `~/.local` sem root: kitty (`~/.local/kitty.app`), starship, fontes
(`~/.local/share/fonts/dominios`), Vesktop e Spicetify. As correções de áudio ficam, de propósito.
