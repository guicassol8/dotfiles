# Créditos

O que não foi escrito ou desenhado aqui, de onde veio e sob qual licença. Conferido em
12/11/2026 contra `hud/sprites/indice.json`, `hud/papel/cenas/ORIGEM.md` e os
`CREDITOS.md` e `LICENCA.txt` dos pacotes baixados.

Resumo: o que o grimório usa de terceiros é CC0 (nenhum crédito obrigatório, citado por
cortesia) e fontes sob a SIL Open Font License. Nenhuma arte CC-BY ou OGA-BY entrou no que
roda. O resto é arte e som gerados por IA.

## Fontes (SIL OFL 1.1)

Fontes livres, todas do Google Fonts, instaladas em `~/.local/share/fonts/dominios` e
`~/.local/share/fonts/despertar-da-mana`. A licença pede que o texto dela acompanhe a
fonte quando redistribuída: as cópias estão em `chrome-nova-aba/fontes/OFL-*.txt` e em
`~/.local/share/fonts/dominios/licencas/`.

| Fonte | Onde aparece no grimório |
|---|---|
| Silkscreen (Regular e Bold) | Rótulos e títulos em pixel do HUD, nova aba |
| Jersey 10, 15 e 25 | Números e destaques em pixel, relógio |
| Jacquard 12 e 24 | Palavra de destaque em gótico pixelado |
| Micro 5 | Nota miúda em pixel |
| Alegreya Sans | Texto corrido do grimório; também na nova aba e no login |
| Cinzel e Cinzel Decorative | Destaque do grimório (`destaque` no `dominios.toml`) |
| FantasqueSansM Nerd Font | Fonte mono do terminal, no grimório (fonte do sistema, não vem junto) |
| JetBrains Mono | Mono de reserva e números do HUD |

Fontes dos outros domínios, também livres: Orbitron, Rajdhani, Chakra Petch, Share Tech
Mono, Anton, Barlow Condensed, Rubik Glitch, Martian Mono, DotGothic16, Spectral e os
símbolos do Nerd Fonts. Eu não reabri a licença de cada uma uma por uma: todas são
publicadas como livres, mas confirma antes de redistribuir uma delas fora deste projeto.

## Sprites e ícones livres (OpenGameArt.org, CC0)

Em uso: lidos por `hud/sprites/indice.json` (42 arquivos de 8 pacotes). Licença conferida
na página de cada recurso em 11/11/2026. O repositório guarda só os arquivos que o HUD usa,
mais o `LICENCA.txt` de cada pacote; os pacotes inteiros ficam só na máquina.

| Pacote | Autor | Licença | Usado para |
|---|---|---|---|
| [496 pixel art icons for medieval/fantasy RPG](https://opengameart.org/content/496-pixel-art-icons-for-medievalfantasy-rpg) | gnola14 (enviado por MedicineStorm) | CC0 | 25 nomes do acervo: os seis elementos, coração, mana, estrela de XP, moeda, escudo, espada, grimório, pergaminho, poção, cristal, chave, mapa, relógio, tocha, sol, lua, neve, vento |
| [Dungeon Crawl 32x32 tiles](https://opengameart.org/content/dungeon-crawl-32x32-tiles) | Dungeon Crawl Stone Soup (bart, MedicineStorm, vlzvl) | CC0 | 9 monstros e familiares: caveira, dragão, corvo, slime, morcego, esqueleto, golem, fantasma, chefe |
| [Mini fantasy sprites](https://opengameart.org/content/mini-fantasy-sprites) | Chappi | CC0 | O mago, o espírito de chama e o orc (com fundo transparente refeito aqui, `_alpha.png`) |
| [32x32 pixel art creatures vol. 3](https://opengameart.org/content/32x32-pixel-art-creatures-volume-3) | paulb | CC0 | Familiares: gato, slime, espírito verde |
| [Weather icons](https://opengameart.org/content/weather-icons) | farcodev | CC0 | Nuvem, chuva, tempestade (registrados no acervo) |
| [RPG UI icons](https://opengameart.org/content/rpg-ui-icons) | NaranjaIncognita | CC0 | Ampulheta |
| [Animated candle](https://opengameart.org/content/animated-candle) | tchevin | CC0 | Vela |
| [Flags](https://opengameart.org/content/flags-0) | autor não identificado na página | CC0 | Bandeira |

## Cenários livres baixados e não usados

`hud/papel/fontes-livres/CREDITOS.md` lista 20 pacotes de cenário do OpenGameArt que foram
garimpados como candidatos (autores como Luis Zuno/ansimuz, CraftPix.net, surt, Warspawn,
Sparklin Labs, jaymeehuynh e outros, com licenças CC0, CC-BY 3.0/4.0 e OGA-BY 3.0). **Nenhum
entrou no grimório:** as cenas finais são geradas (abaixo). Os pacotes ficam só na máquina,
fora do repositório. Se um dia algum for usado: CC-BY e OGA-BY pedem crédito, então
ele tem de entrar aqui antes.

## Arte gerada por IA

Comprada por chamadas pagas no marketplace Rialto, na noite de 11/11/2026. Nenhuma arte
de licença livre entrou nas cenas, então não há crédito obrigatório. Os prompts e os
parâmetros do pixelizador estão em `hud/papel/cenas/ORIGEM.md`. Os prompts das cenas, que estão lá, não têm dado pessoal;
os dos sons não foram guardados no projeto, só o registro de gastos.

| O quê | Onde fica | Provedor (modelo) |
|---|---|---|
| Cenas da noite: fogo, água, terra, vento, mana pura | `hud/papel/cenas/<elemento>.png` | FLUX.2 Flash |
| Cena da noite: eletricidade | `hud/papel/cenas/eletricidade.png` | Nano Banana 2 |
| Aurora, dia e entardecer de cada cena | `hud/papel/cenas/<elemento>-<hora>.png` | Nano Banana 2 Edit, a partir da cena da noite |
| Cena de título | `hud/papel/cenas/titulo.png` | Nano Banana 2 e Nano Banana 2 Edit |
| Conjurador (96, 48 e 32 px) | `hud/sprites/conjurador-*.png` | Ideogram (Transparent Sprites) |
| Oito familiares e seis emblemas | `hud/sprites/familiar-*.png`, `emblema-*.png` | Nano Banana 2 |
| Efeitos sonoros (16 sons) | `sons/grimorio/estudio/` | ElevenLabs (SFX) |
| Trilhas curtas (login, nível, dia completo, título) | `sons/grimorio/estudio/` | Stable Audio 2.5 |

As imagens passam pelo `hud/papel/pixelar.py` (paleta reduzida, grade de pixel) e os sons
por `gerar/estudio.py` (corte, loudness, fade), então o que está no disco é o resultado
tratado, não o arquivo do provedor. Os provedores não aceitam semente: o mesmo prompt gera
outra imagem. Sobre direitos: a licença de uso do que sai de cada provedor é a dos termos
dele no Rialto; não li esses termos, então confere antes de publicar ou vender algo que
inclua essa arte. O repositório de dotfiles é público e as cenas e sprites gerados vão
nele.

## Feito aqui, sem terceiros

Chiptune sintetizado por código (`gerar/sons_grimorio.py`, `gerar/sons.py`), cursor
`Grimorio` (`gerar/cursor.py`), peças de moldura, gemas, setas e selos do HUD
(`hud/arte/gerar.py`), cenas de reserva (`hud/papel/reservas.py`), emblemas em pixel do
login (`gerar/emblema_pixel.py`) e o pixelizador.
