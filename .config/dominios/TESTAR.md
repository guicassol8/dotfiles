# Roteiro de teste do Grimório HD-2D

Feito em 12/11/2026, para rodar depois do primeiro reinício. Vai na ordem; cada item diz o que fazer e o que tem de acontecer. Deixa o **carregador ligado** (na bateria o cenário congela, de propósito). O que nunca foi visto por ninguém está marcado com (1ª vez).

## 1. Ligar

| # | Faz | Tem de acontecer |
|---|---|---|
| 1 | Reinicia | (1ª vez) Splash em pixel: o grimório, "Despertar da Mana" e a barra enchendo. Se travar no splash: no menu do systemd-boot aperta `e`, apaga a palavra `splash`, dá boot e roda `sudo ~/.config/dominios/root/instalar-root.sh --desfazer` |
| 2 | Tela de login | (1ª vez com senha) Grimório com os orbes, caixa ARQUIVO SALVO com teu nível. Erra a senha uma vez de propósito pra ver o estado de erro, depois entra |
| 3 | Entrou | Abertura de uns 3 s (título e tema musical) e a mesa se desdobra |

## 2. A mesa (workspace vazio)

| # | Faz | Tem de acontecer |
|---|---|---|
| 4 | Olha | 11 widgets, relógio no centro em cima, cenário com partículas se movendo |
| 5 | Clica num ofício | Marca, risca, toca som, a barra de progresso anda. Clica de novo pra desmarcar |
| 6 | Clica num elemento da roda | Trava nele (cadeado) e tudo troca de cor em 1 a 2 s. Clica no mesmo de novo: solta |
| 7 | Clica numa sala do Mapa | Vai pra aquele workspace |
| 8 | Toca uma música (Spotify) | Bardo mostra capa em pixel, título, barras dançando; os botões pausam e pulam; o brilho do cenário pulsa com o grave |

## 3. Por cima das janelas

| # | Faz | Tem de acontecer |
|---|---|---|
| 9 | Com janelas abertas, `Mod+G` | (1ª vez pela tecla) O grimório abre por cima, com as janelas como sombra. `Esc` ou `Mod+G` fecha |
| 10 | Clica no selo `NV 35` da barra | Mesmo efeito |
| 11 | Abre e fecha um terminal | Janela se materializa de um mosaico e se desfaz em blocos; moldura na cor do elemento |
| 12 | Passa o mouse por link, texto e borda de janela | Cursor em pixel: seta com gema, luva, barra em I, setas de redimensionar |

## 4. Elemento trocando tudo junto

| # | Faz | Tem de acontecer |
|---|---|---|
| 13 | No terminal: `elemento proximo` (repete umas vezes) | Mudam juntos: cenário, molduras, barra, cores do terminal aberto, e uma fala na caixa de diálogo com o som do elemento |
| 14 | `elemento` | Mostra o elemento, o motivo e os votos dos candidatos |
| 15 | `elemento soltar` | Volta ao automático |

## 5. Terminal, Claude Code e Chrome

| # | Faz | Tem de acontecer |
|---|---|---|
| 16 | Abre um kitty | Ficha com o conjurador, nível, corações, mana e a linha CAPÍTULO |
| 17 | Digita um comando que não existe | "Magia desconhecida"; um comando que falha mostra "A conjuração falhou" no prompt |
| 18 | `brinquedos` | Menu com chuva, fogueira e círculo |
| 19 | Abre o `claude` | Borda e destaque na cor do elemento, linha de status com elemento e nível |
| 20 | Nova aba no Chrome | Cena do elemento, relógio, busca, nível e ofícios |

## 6. Som (ninguém ouviu antes de ti)

| # | Faz | Tem de acontecer |
|---|---|---|
| 21 | Abre e fecha janela, troca de workspace | Bipes curtos e baixos |
| 22 | `notify-send "Teste" "do grimório"` | Sino de cristal |
| 23 | `som-pacote chiptune` e repete | Tudo vira sintetizado. `som-pacote estudio` volta |
| 24 | Se cansar | `dominio som off` cala tudo; `dominio som on` volta |

## 7. Modo sério e economia

| # | Faz | Tem de acontecer |
|---|---|---|
| 25 | `Mod+N` | Some tudo: mesa, cursor, molduras, cores do terminal e do Claude Code. `Mod+N` de novo volta tudo |
| 26 | Tira o carregador | Cenário congela num quadro (até 1 min pra perceber se a mesa não estiver à vista). Recoloca: volta a animar |
| 27 | `~/.config/dominios/hud/hud estado` | Memória perto de 130 MB no HUD; CPU perto de 3% com a mesa à vista e perto de 0% escondida |
| 28 | Bloqueia a tela com teu atalho | Grimório selado, hora em pixel, senha destrava |

## 8. Nível

| # | Faz | Tem de acontecer |
|---|---|---|
| 29 | `jogador` | Ficha no terminal |
| 30 | Faz um commit em qualquer repositório | Em até 1 min: +20 XP, fala na caixa de diálogo |

## Se algo der errado

- Desligar a mesa: `~/.config/dominios/hud/hud desligar` (liga de volta com `ligar`).
- Tudo que foi mudado e como desfazer cada peça: seção "Como desligar ou desfazer" do `README.md`.
- Me conta o número do item que falhou e o que apareceu; o estado do projeto está salvo na memória.
