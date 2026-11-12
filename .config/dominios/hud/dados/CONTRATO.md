# Nucleo de dados do HUD: contrato

Um unico processo Python (`hud/dados/nucleo.py`, so biblioteca padrao) alimenta o HUD inteiro. Motivo: RAM. Tres ou quatro daemons separados custavam ~45 MB; um so tem de ficar abaixo de 25 MB de RSS e perto de 0% de CPU.

O HUD (QML) sobe o nucleo como processo filho e le o stdout. Nenhum widget roda script proprio para dado que ja existe aqui.

## Saida (stdout)

Uma linha JSON por mensagem, com flush: `{"canal": "<nome>", "dados": <objeto>}`. Ao iniciar, o nucleo emite o estado atual de todos os canais (para o HUD nao nascer vazio). Depois, so quando muda ou no intervalo indicado.

| Canal | Quando | Dados |
|---|---|---|
| `elemento` | na troca e a cada minuto | conteudo de `~/.local/state/dominios/elemento.json` (elemento, motivo, desde, travado, anterior, candidatos, clima, maquina) |
| `jogador` | quando muda | conteudo de `~/.local/state/dominios/jogador.json` (nome, classe e titulo respeitam `jogador-prefs.json`, escrito por `jogador nome|classe|titulo`) |
| `maquina` | a cada 2 s, so com a amostragem ligada | `cpu_pct`, `nucleos` [pct], `carga1`, `mem_pct`, `mem_usada_mb`, `mem_total_mb`, `mem_disponivel_mb`, `swap_pct`, `temp_c`, `bateria_pct`, `na_tomada`, `bateria_min` (ou null), `rede_baixa_kbps`, `rede_sobe_kbps`, `disco_pct`, `processos` [{nome, cpu_pct, mem_mb}] (os 5 que mais usam CPU, atualizados a cada 6 s) |
| `familiares` | quando muda, conferido a cada 5 s | lista de agentes Claude ativos: [{id, projeto, estado ("conjurando"\|"aguardando"\|"ocioso"), desde (ISO), descricao}] |
| `oficios` | quando muda | missoes do dia: `titulo`, `itens` [{id, texto, feito, categoria}], `feitos`, `total`, `sequencia_dias`, `termina_em_s` |
| `cronica` | ao iniciar (cache), a cada 2 min (commits locais) e a cada 30 min (GitHub) | dias de trabalho fundidos: cada dia vale o MAIOR entre as contribuicoes do GitHub e os commits locais (`dias_commit` de `jogador-estado.json`, todos os ramos e repositorios). `semanas` [[n x7]] (26, domingo a sabado), `total_ano` (soma dos dias fundidos do ano corrente), `hoje`, `sequencia` (dias seguidos com algo, hoje em aberto nao quebra), `fontes` {github, local} (booleanos), `atualizado`. Sem rede ou sem `gh` sai so com os locais; null so sem nenhuma fonte |
| `pagina` | ao iniciar e na virada do dia | frase do dia: `texto`, `autor`, `obra` (ou null) |
| `dialogo` | por evento | fala para a caixa de dialogo: `id`, `titulo`, `texto`, `retrato` ("conjurador"\|"familiar"\|"grimorio"\|"elemento-<nome>"), `tipo` ("info"\|"recompensa"\|"perigo"\|"elemento"), `som` (nome ou null) |
| `pressao` | quando muda | `nivel` ("ok"\|"apertado"\|"critico") pela memoria disponivel; em "critico" o HUD se recolhe |

## Entrada (stdin)

Uma linha por comando: `maquina 1` / `maquina 0` (liga e desliga a amostragem de 2 s; o HUD desliga quando nao esta visivel), `som <nome>` (toca um som), `oficio <id>` (alterna uma missao), `elemento travar <nome>` / `elemento soltar`, `sair`.

## Sons

O nucleo embute o daemon de eventos (`bin/som-eventos`): toca nos eventos do niri (janela, workspace, visao geral) e nos proprios eventos (troca de elemento, XP, nivel, titulo, oficio concluido, familiar invocado e concluido, tomada, bateria baixa). Respeita `dominio som on|off`. Arranca MUDO se existir `$XDG_RUNTIME_DIR/dominios-silencio` (o orquestrador usa isso durante a noite).

## Regras

- Nada derruba o processo: cada fonte roda protegida e, se falhar, o canal emite o ultimo valor bom.
- Sem varrer disco em laco. Git, GitHub e clima ficam em cache.
- `elemento.py` e `jogador.py` continuam funcionando sozinhos pelo CLI; o nucleo importa as funcoes `seguir(emitir, intervalo, parar)` deles.
