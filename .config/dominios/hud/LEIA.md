# HUD do grimório: como fazer um widget

O desktop é o grimório do conjurador, em HD-2D: pixel art nítida na grade, com vidro escuro e luz lisa por cima. Um widget é um arquivo `hud/widgets/Nome.qml` com uma `Janela` na raiz. Ele entra na mesa pela linha dele em `hud/mesa.json`; a casca (`shell.qml`) não se edita.

## Linguagem visual

Faça:
- **Grade de 3 px** (`Tema.px`). Posição, tamanho e espaçamento de tudo que é pixel são múltiplos de 3. Espaços usuais: 3, 6, 9, 12, 18.
- **Texto em pixel só pelos componentes** (`Rotulo`, `Titulo`, `TextoPixel`): eles cravam a fonte na grade. Texto corrido em `Texto`, valores em `Numero` (fontes lisas).
- **Cor de acento = `Tema.destaque`** (a do elemento ativo, muda sozinha com transição). Ouro (`Tema.ouro`) só para recompensa, `Tema.perigo` só para perigo. Base nos neutros: `Tema.texto`, `textoSuave`, `fundo`, `superficie`, `superficie2`, `contorno`. Cor de um elemento: `Tema.corDe("agua")`.
- **Dados pelo `Nucleo`** (`Nucleo.jogador`, `maquina`, `oficios`, `familiares`, `cronica`, `pagina`, `elemento`). Todo canal pode ser `null` no começo: trate. Tenha um exemplo embutido para a foto de teste.
- Título de janela curto (até uns 16 caracteres), etiqueta até 8. Texto em PT-BR, direto, sem travessão.

Não faça:
- `font.pixelSize` em fonte de pixel, escala fracionária, rotação, cantos arredondados, degradê decorativo, cor literal (`"#..."`).
- `MultiEffect`, `ShaderEffect`, `layer.effect`, `QtQuick.Controls`, `QtQuick.Shapes`: custam RAM (o teto do HUD inteiro é 200 MB) e somem na foto fora da tela. Brilho e sombra já vêm prontos em `Janela` e `Gema`.
- Animação contínua a 60 fps. Anime por evento, ou por `Timer` lento (até 8 fps) com `running: ... && Hud.animar`.
- Rodar script para dado que o `Nucleo` já tem. `Coletor` é só para o que está fora dele (ex.: `cava`).
- Outra `Janela` dentro de janela, outro `Dialogo` (a casca já tem um: use `Hud.dizer`).

## Componentes (`import qs.componentes`)

| Componente | O que é | Propriedades que importam |
|---|---|---|
| `Janela` | moldura de pixel, vidro, placa de título, gemas nos cantos | `titulo`, `etiqueta`, `variante` ("normal", "pergaminho", "ouro", "perigo"), `respiro` (18), `gemas`; os filhos vão para dentro; `tinta`, `tintaSuave`, `acento` |
| `Rotulo` | legenda em pixel, maiúsculas, tom suave (15 px de altura) | `text` |
| `Titulo` | título de seção em pixel com sombra | `text` |
| `TextoPixel` | qualquer fonte de pixel | `tipo`: "rotulo", "titulo", "miudo", "medio" (30 px), "grande" (45), "enorme" (75), "gotico" (45, nunca em CAIXA ALTA), "goticoGrande" (93); `sombra`, `contorno` (borda dura de 1 pixel de arte nos quatro lados: texto solto sobre a cena viva, como o relógio), `escala`, `color` |
| `Texto` | texto corrido liso | `text`, `tamanho` (18), `suave` |
| `Numero` | valor em mono liso | `text`, `tamanho` (17), `suave` |
| `Campo` | linha de ficha: rótulo e valor (24 px) | `rotulo`, `valor`, `numero`, `corValor` |
| `Barra` | barra segmentada de RPG (45 px com cabeçalho, 21 sem) | `valor` 0..1, `tipo` ("vida", "mana", "folego", "xp") ou `cor`, `rotulo`, `texto` |
| `Medidor` | orbe com líquido (99 x 99) | `valor` 0..1, `cor`, `texto`, `rotulo` |
| `Grafico` | histórico em colunas de pixel | `valores` [n], `maximo`, `tipo` ("colunas", "linha"), `colado`, `cor` |
| `Selo` | escudo de rank | `rank` "E".."S" |
| `Figura` | imagem de pixel art (o "Sprite") | `fonte`, `fps`, `quadros`, `escala`, `ponto` |
| `Icone` | ícone pequeno (~33 px) | `nome`, `cor` e `tamanho` (só glifo), `glifo` |
| `Gema` | pedra do elemento | `elemento` (ativo por padrão, ou "apagada"), `grande`, `brilho` 0..1 |
| `Retrato` | sprite em moldurinha (114 x 114) | `fonte` ("mago"), `fps`, `luz` |
| `Divisor` | filete com florão; com `rotulo` vira cabeçalho de seção | `rotulo` |
| `Botao` | placa clicável (33 px de altura) | `texto`, `icone`, `marcado`, `ativo`, sinal `clicado()` |
| `Fatias` | 9 fatias na grade, para peça própria | `fonte`, `borda` (em pixels de arte) |
| `Pixels` | mapa de letras desenhado na grade (ícone de pixel feito à mão) | `mapa` ["s.s", ...], `cores` ({ s: cor }) |
| `Coletor` | roda comando e entrega JSON em `dados` | `comando`, `intervalo` (ms), `continuo`, `ativo`, `json`; `dados`, `erro`, `atualizado()` |
| `Arquivo` | lê e observa um arquivo JSON | `caminho`, `dados`, `existe`, `atualizado()` |

Singletons: `Tema` (cores, `px`, `elemento`, `destaque`, `corDe()`, `alfa(cor, a)`, `mistura(a, b, t)`, `grade(v)`, `textos`, `ajustes` (de `[grimorio.hud]`)), `Nucleo` (canais; `som(nome)`, `oficio(id)`, `travarElemento(nome)`, `soltarElemento()`), `Hud` (`aberto`, `mesaLivre`, `visivel`, `animar`, `paisagem`, `contemplando`, `recolhido`, `apertado`, `naBateria`, `pulso`, `agora`, `hora`, `abertura`, `dizer({titulo, texto, retrato, tipo})`).

`Hud.animar` é a chave de toda animação ociosa: falso com a mesa escondida, em paisagem, na contemplação, na bateria, com a memória apertada ou recolhida (o cenário usa `Hud.animarCena`, que segue andando em paisagem e na contemplação). Relógio: use `Hud.agora` (um `SystemClock` só para o HUD inteiro), não crie outro.

### Os seis heróis

Arte em `hud/sprites/` (`heroi-<elemento>-128.png` e `-64.png` de corpo inteiro; `-busto-96/48/32.png`), todos no `indice.json`. Os títulos vêm de `[grimorio.herois]` do `dominios.toml`, pelo `hud-tema.json`: `Tema.heroi("fogo")` devolve o título e `Tema.temHeroi("fogo")` diz se há título e arte (sem eles cada lugar cai no medalhão do elemento ou no encapuzado). O encapuzado (`conjurador-*`) segue sendo o dono.
- **Dialogo**: a fala `retrato: "elemento-<nome>"` vira `heroi-<nome>-busto-96` com `ponto: 1` (1:1, como o medalhão) dentro do `Retrato` (miolo de 102 px); o título da fala é o do herói (`dados/dialogo.py` lê `dados/herois.py`, que relê o `dominios.toml`).
- **Elemento**: o corpo de 64 px (`ponto: 1`) no lugar do medalhão, no meio da roda.
- **Abertura do login** (`casca/Mesa.qml`): corpo de 64 px ao lado do "Capítulo".
- **Nova aba**: `dados/nova_aba.py` copia o corpo de 128 px para `chrome-nova-aba/heroi.png` quando o elemento muda e põe `heroi` (título) no `estado.json`.
- Testar a fala fora da tela: um `.qml` dentro de `hud/` com um `Dialogo { }` que chama `enfileirar({ id, titulo, texto, retrato: "elemento-fogo", tipo: "elemento" })` num `Timer` de 400 ms (o tema carrega assíncrono), e `hud/dev/prova dev/Teste.qml --tamanho 900x126 --sem-tela --elemento fogo`.

### Figura e Icone: de onde vem a imagem

- **Acervo** (`hud/sprites/indice.json`, 46 nomes CC0): `mago` e `familiar-espirito` (4 quadros, use `fps: 3`), `familiar-gato`, `-slime`, `-dragao`, `-corvo`, `monstro-slime`, `-morcego`, `-esqueleto`, `-golem`, `-fantasma`, `-chefe`, `-orc`, `elemento-fogo` ... `elemento-mana-pura`, `coracao`, `mana`, `folego`, `estrela-xp`, `moeda`, `escudo`, `espada`, `grimorio`, `pergaminho`, `pocao`, `cristal`, `chave`, `mapa`, `relogio`, `tocha`, `sol`, `lua`, `neve`, `vento`, `ampulheta`, `caveira`, `bandeira`, `vela`. São grandes (32 a 34 px de arte).
- **Escala**: `Figura { fonte: "monstro-slime" }` sai na grade, ~100 px (ilustração, retrato, monstro). `Icone { nome: "moeda" }` desenha 1:1, 34 px (ícone de linha). Em `Figura`, o mesmo com `ponto: 1`. Não use `ponto: 2`: pixel de 2 px ao lado de pixel de 3 px aparece.
- **Peças da casa** (`hud/arte/`, feitas por `arte/gerar.py`): `simbolo-<elemento>` (11 x 11, na grade), `gema-`/`gemao-<elemento>`, `clima-nuvem`, `clima-chuva`, `clima-tempestade`, `florao`, `seta-baixo`, `seta-direita`, `selo-<rank>`. Peça nova: acrescente no `gerar.py` (1 pixel do PNG = 1 pixel de arte) e confira o PNG.
- `Icone { nome: "fogo" }` (os seis elementos) usa o símbolo da casa. Nome que não é sprite cai num glifo de Nerd Font em pseudo pixel: `certo`, `fechar`, `musica`, `tocar`, `pausar`, `proxima`, `anterior`, `chip`, `memoria`, `termometro`, `bateria`, `wifi`, `github`, `git`, `terminal`, `robo`, `coroa`, `trofeu`, `calendario`, `sino`, `aviso`, `baixar`, `subir`, `nublado`, `neblina`, `parcial` (lista completa em `Icone.qml`). Faltam no acervo: nota musical, fases da lua, estrelas soltas.

## Widget mínimo completo

```qml
import QtQuick
import qs.componentes

Janela {
    id: pagina
    titulo: "Página do Dia"
    variante: "pergaminho"

    readonly property var p: Nucleo.pagina || { texto: "A mana está em todos.", autor: "Grimório", obra: null }

    Column {
        anchors.fill: parent
        spacing: 9
        Texto { width: parent.width; tamanho: 20; text: pagina.p.texto }
        Texto { suave: true; text: pagina.p.autor + (pagina.p.obra ? ", " + pagina.p.obra : "") }
    }
}
```

Os filhos da `Janela` ficam numa área útil de `largura - 72` por `altura - 90` (com título; `altura - 72` sem). A casca define o tamanho: não fixe `width` nem `height` na raiz.

## Vagas da mesa (1920 x 1080, barra do Noctalia nos 30 px de cima)

| Arquivo | Título | x, y | Tamanho | Área útil | Conteúdo |
|---|---|---|---|---|---|
| `Relogio` | (sem moldura) | 600, 54 | 720 x 216 | | pronto |
| `Ficha` | Ficha do Conjurador | 24, 54 | 456 x 546 | 384 x 456 | pronto |
| `Oficios` | Ofícios do Dia | 24, 618 | 456 x 258 | 384 x 168 | `Nucleo.oficios`; clique chama `Nucleo.oficio(id)` |
| `Bardo` | Bardo | 24, 894 | 456 x 162 | 384 x 72 | mídia e visualizador (`cava` por `Coletor` contínuo) |
| `Familiares` | Familiares | 1440, 54 | 456 x 258 | 384 x 168 | `Nucleo.familiares` |
| `Maquina` | Núcleo | 1440, 330 | 456 x 330 | 384 x 240 | `Nucleo.maquina`; processos pesados como monstros com barra de vida |
| `Cronica` | Crônica | 1440, 678 | 456 x 198 | 384 x 108 | `Nucleo.cronica`: 26 semanas, cristal de 9 px mais 3 de vão |
| `Ceus` | Céus | 1440, 894 | 456 x 162 | 384 x 72 | `Nucleo.elemento.clima` e lua |
| `Elemento` | Elemento | 498, 846 | 228 x 210 | 156 x 120 | roda dos seis, o ativo aceso, `Tema.motivoElemento` |
| `Pagina` | Página do Dia | 744, 846 | 432 x 210 | 360 x 120 | `Nucleo.pagina`, variante pergaminho |
| `Mapa` | Mapa | 1194, 846 | 228 x 210 | 156 x 120 | workspaces do niri como salas (`import Quickshell.Niri`) |

O miolo (x 498 a 1422, y 288 a 828) fica livre para o cenário. A caixa de diálogo aparece ali embaixo (510, 702, 900 x 126) só quando há fala. Vaga cujo arquivo não existe fica vazia, sem erro. Para mexer em vaga, edite `mesa.json` (campos `widget`, `x`, `y`, `largura`, `altura`; opcionais `ativo: false` e `props: {}`); a mesa relê sozinha.

## Como testar

```sh
hud/dev/prova Oficios                       # foto em ~/.cache/dominios-dev/prova/Oficios.png, no tamanho da vaga
hud/dev/prova Oficios /tmp/x.png --elemento fogo --espera 4
hud/dev/prova dev/Mostruario.qml --tamanho 1320x690    # todos os componentes juntos (bom para copiar uso)
hud/dev/prova casca/Mesa.qml --tamanho 1920x1080       # a mesa inteira
```

- Um comando só: sobe o widget sozinho, fotografa com 30 px de margem e sai. Avisos e erros de QML saem no terminal: zero aviso é a meta. Olhe a foto com Read (recorte ou reduza antes se for grande).
- Com o teste visual pausado (o dono no computador), a prova desenha **fora da tela** sozinha: nada aparece no monitor. É desenho por software: pixel art, texto, sombra e vidro saem iguais; shader não aparece. `--na-tela` e `--sem-tela` forçam o modo.
- Os dados são os reais (`nucleo --uma-vez`, sem som). Dados fingidos: `HUD_NUCLEO='cat teste.jsonl; cat >/dev/null' hud/dev/prova ...`, uma linha `{"canal": ..., "dados": ...}` por mensagem.
- **Nunca rode `qs -p hud` nem `hud/hud ligar` para testar**: sobe o núcleo de verdade, que toca som. O HUD de verdade é o serviço `dominios-hud` (ver "Serviço").
- Várias provas podem rodar juntas (e junto com o HUD de verdade): a prova usa `--allow-duplicate` e apaga a foto velha antes, então foto que não saiu é erro, nunca sucesso.
- Na tela, com o HUD inteiro: `HUD_DEV=1` (camada Overlay, fundo opaco, cena opaca, sem teclado: nunca aparece nada do dono), `HUD_DEV_ABERTO=1` (com o grimório aberto), `HUD_ELEMENTO=vento`, `HUD_HORA=12` (variante da hora), `HUD_ABERTURA=1` (a abertura do login). Exemplo: `HUD_DEV=1 HUD_HORA=12 HUD_ELEMENTO=vento HUD_NUCLEO='~/.config/dominios/bin/nucleo --uma-vez; cat >/dev/null' hud/dev/tela hud /tmp/x.png 6`.
- Fora da tela o cenário aparece parado (a cena sem shader, `GraphicsInfo.Software`): serve para julgar a composição.

## Armadilhas deste Quickshell (noctalia-qs 0.0.12)

- **Um segundo `.qml` dentro de `widgets/` não vira tipo**: os widgets entram por `Loader` com URL, sem `import qs.widgets`, então o vizinho não é achado (e a casca o trataria como widget sem vaga). Peça auxiliar de um widget vai como componente embutido no próprio arquivo (`component Pixels: Item { ... }`); se servir a mais de um, vai para `componentes/`.
- `TextoPixel` com `contorno` e sem `sombra` some fora da tela (o contorno cobre o texto): use os dois juntos, como o relógio.
- Glifo de Nerd Font abaixo de 9 pixels de arte não se lê: o `Icone` sobe para 9 sozinho, e os ícones de botão (`tocar`, `pausar`, `proxima`, `anterior`, `certo`, `fechar`, `mais`, `menos`) com `tamanho` menor que 9 saem desenhados em pixel (7 x 7).

- `Sprite` já é um tipo do QtQuick e ganha do nosso: por isso o componente se chama `Figura`.
- O `qs` só enxerga QML dentro da pasta do shell. Módulo é pasta: `import qs.componentes`. Um arquivo carregado por `Loader`/`LazyLoader` só acha `qs.*` se o arquivo de entrada também importar o módulo.
- `PanelWindow` não carrega fora do Wayland (a prova fora da tela usa `FloatingWindow`): widget não cria janela.
- Fora da tela, item com `layer.effect` ou `ShaderEffect` some sem aviso.
- `FileView` percebe gravação no lugar e troca por rename, mas não a troca de um link simbólico. Use `Arquivo`.
- `Process` que não consegue subir não emite `exited`: observe `running` (o `Coletor` e o `Nucleo` já tratam).
- Mudar um `.qml` carregado recarrega o HUD inteiro: é esperado.
- Em JS, `Tema.mistura` aceita cor ou texto `"#rrggbb"`; `Qt.rgba` com `undefined` dá preto sem avisar.

## Cenário (`papel/Papel.qml`)

A `Mesa` carrega o cenário atrás dos widgets e amarra: `elemento` (de `Nucleo.elemento`, ou `"titulo"` na abertura), `chuva` (código WMO de garoa, chuva ou temporal, ou `chuva_mm > 0`), `pulso` (`Hud.pulso`, que o Bardo escreve com o grave do `cava`), `hora` (`Hud.hora`), `nascer` e `por` (do clima), `rodando` (`Hud.animar`). Um `ShaderEffect` só, 10 fps por `Timer` (`HUD_FPS` troca, para medir).

- **Hora do dia**: `cenas/<elemento>-aurora.png`, `-dia.png`, `-entardecer.png` (a sem sufixo é a noite), cada uma com `-luz.png`. Fases pelo sol do clima: aurora de 45 min antes a 1h15 depois do nascer, dia até 1 h antes do pôr, entardecer até 36 min depois, noite no resto (sem clima: nascer 5h30, pôr 19h). A virada funde em 8 s; a troca de elemento varre em 2,4 s. Variante que faltar cai na noite com a correção de cor da hora. A pasta é relida a cada fase e a cada 15 min: arquivo novo entra sozinho.
- **Legibilidade**: o shader acalma só onde há widget (laterais, x < 470 e > 1450, com rampa até 653/1267; faixa de baixo, y > 790) e põe teto de luminância ali (a `vento-dia` é muito mais clara que as outras); o miolo fica com a cena inteira. Um poço de sombra pequeno atrás do relógio, e o texto do relógio leva `contorno`. A cena da noite já vem pintada de noite: a correção de cor da noite (`_chaves`) é quase neutra, para não escurecer em dobro.
- **Parado** (`rodando: false`): congela no último quadro; troca pedida parada acontece de uma vez.
- **Abertura do login**: `hud sessao` deixa a marca `$XDG_RUNTIME_DIR/dominios-hud-abertura`; a casca a consome (vale uma vez, por 2 min). A cena `titulo` com "Despertar da Mana" e o capítulo do elemento, uns 3 s, com o som `login`; depois a cena varre para o lugar e os widgets desdobram em cascata. `hud ligar` comum e reinício por falha não têm abertura.
- **Mod+G**: o grimório sobe por cima das janelas (camada Overlay, foco de teclado exclusivo: Esc fecha de primeira; clique no vazio fecha, clique no corpo de um widget não). O cenário entra junto com o véu, a 92% (as janelas ficam só como sombra), os widgets desdobram de novo em cascata e o nome "Grimório" aparece e some no meio. Fecha sozinho se a mesa ficar livre ou se a última janela fechar.
- **Paisagem** (`hud paisagem`, Mod+Shift+G): widgets, diálogo, calma do shader (uniforme `mesa`) e o véu esmaecem em 500 ms; a máscara de entrada fica vazia; estado em `~/.local/state/dominios/hud.json`. **Contemplação** (`hud contemplar`, ou o ocioso do Noctalia chamando `hud ocioso`/`voltou`, de `[grimorio.contemplacao]`): a superfície sobe para Overlay com o cenário opaco, hora e lugar no canto, sem teclado nem clique; um `IdleMonitor` também desfaz na primeira entrada. Teste fora da tela: `HUD_PAISAGEM=1` ou `HUD_CONTEMPLAR=1` antes do `hud/dev/prova casca/Mesa.qml`.
- **Letreiro de sala** (`casca/Letreiro.qml`): ao trocar de workspace, "Sala 2" (gótico, número em pixel na cor do elemento) e um baú por janela aparecem no meio da tela por ~750 ms: a faixa abre do centro numa varredura de pixels, segura e fecha. Mora numa segunda `PanelWindow` da casca, na camada Top, máscara vazia fixa e sem teclado, criada por `LazyLoader` só no letreiro e solta 20 s depois. Trocas em rajada só atualizam a placa aberta. Não aparece em paisagem, contemplação, visão geral do niri, grimório aberto nem com a memória apertada; na bateria aparece (evento curto, como as animações do niri). Ver na hora: `hud letreiro`. Desligar: `letreiro_sala = false` em `[grimorio.hud]`, depois `dominio construir grimorio`. Foto: `HUD_AMOSTRA_LETREIRO='{"sala": 2, "janelas": 3, "aberto": 1}' hud/dev/prova casca/Letreiro.qml --tamanho 612x180`.
- **Testar a fusão das horas**: `PAPEL_ELEMENTO=terra PAPEL_HORA=12 PAPEL_HORA_PARA=18.3 PAPEL_HORA_EM=2 hud/dev/tela hud/papel/dev /tmp/f.png 2.5 4 2.2`.

## Economia

| Situação | O que acontece |
|---|---|
| mesa escondida (janelas na frente) | cenário, sprites, visualizador e amostragem da máquina param; CPU ~0 |
| mesa a vista, parada | cenário a 10 fps e máquina a cada 2 s: ~3% de um núcleo (qs 2,6 + núcleo 0,4) |
| com música | + `cava` a 15 fps: ~3,6% (qs 2,3, cava 1,0, núcleo 0,4) |
| paisagem ou contemplação | só o cenário a 10 fps; widgets e amostragem da máquina param |
| na bateria | tudo congela num quadro (`Hud.naBateria`) |
| troca de workspace | o letreiro: uma superfície de 612 x 180 por ~750 ms; parado, nenhuma (destruída 20 s depois) |
| `Nucleo.pressao.nivel` "apertado" | idem (`Hud.apertado`) |
| "crítico" | cenário e widgets descarregados, só um aviso pequeno (`Hud.recolhido`) |

## Serviço (`hud/hud`)

O HUD roda como `dominios-hud.service` do systemd do usuário (a unidade é reescrita a cada `hud ligar`): `Restart=always` com espera crescente (2 s até 60 s), `MemoryHigh=260M`, `MemoryMax=330M` (qs + núcleo + cava; passou disso, o kernel mata e o serviço reergue). Comandos: `hud ligar`, `desligar`, `reiniciar`, `estado` (PSS, memória do serviço, CPU medida em 1 s), `alternar` (Mod+G), `sessao` (no login, pelo `niri-shell.kdl`: liga só no grimório), `log`. O gancho `ganchos/expandir.d/60-hud` liga no grimório e desliga nos outros domínios a cada troca.

## Memória (medida em 11/11/2026, PSS do `qs` com os 11 widgets e o cenário a vista)

| Ambiente do processo | PSS | Anônima |
|---|---|---|
| padrão da sessão | 272,6 MB | 185,9 MB |
| só `QT_QPA_PLATFORMTHEME=` (sem GTK) | 236,3 | 157,7 |
| só `QSG_RENDER_LOOP=basic` | 270,0 (CPU 10,7% → 5,8%) | 182,2 |
| só `MALLOC_CONF` (o qs usa jemalloc) | 165,2 | 77,2 |
| só `MALLOC_ARENA_MAX=2` | 264,0 (sem efeito: não é glibc) | 175,9 |
| só `QSG_RHI_BACKEND=vulkan` | 257,3 | 177,7 |
| tema + loop + jemalloc | 151,8 | 73,3 |
| + `QT_QUICK_CONTROLS_STYLE=Basic` | 156,2 (sem efeito: não há Controls) | 77,0 |
| tema + loop + jemalloc + vulkan | 135,2 | 63,5 |
| + `FONTCONFIG_FILE` só com as fontes usadas (`fontes/fonts.conf`) | **114,3** | 49,2 |

O serviço usa a última linha. Imagens já vão com `cache: false` no cenário (640 x 360) e as peças de pixel são pequenas; `Loader` por widget fora de vista não compensa (a mesa inteira aparece ou some de uma vez).

### Medida de 12/11/2026 (serviço de verdade, 11 widgets, cenário, núcleo de verdade)

| Situação | PSS qs | PSS núcleo | CPU (% de um núcleo) | GPU (ocupação total do sistema) |
|---|---|---|---|---|
| mesa a vista, parada, 12 fps (antes) | 132 MB | 17 MB | qs 3,4 + núcleo 0,4 | 6,4% |
| mesa a vista, parada, 10 fps | ~125 MB | 17 MB | qs 2,6 + núcleo 0,4 | 5,1% (4,0% sem HUD) |
| com música (`HUD_AMOSTRA_BARDO` tocando, cava sem som) | ~97 (dev) | | qs 2,3 + cava 1,0 + núcleo 0,4 | 5,0% |
| escondida atrás de janela | 122 MB | 17,5 MB | qs 0,03 + núcleo 0,2 | sem diferença |
| na bateria (congelado) | | | qs 0,05 | 0 |

Cada recarga de .qml com o serviço ligado deixa uns MB a mais: depois de mexer no código, `hud reiniciar`.
