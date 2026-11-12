# Origem das cenas

Tudo aqui é arte gerada por IA, comprada no Rialto com ordem do orquestrador (11/11/2026). Nenhuma arte de
licença livre entrou, então não há crédito obrigatório. Os originais ficam em
`~/.cache/dominios-dev/arte/bruto/<elemento>/` e os scripts que refazem tudo ficam em `~/.cache/dominios-dev/arte/`:

- `final.sh`: as seis cenas da noite e o título;
- `horas.sh`: aurora, dia e entardecer (rode depois do `final.sh`, porque usa a máscara de luz da noite);
- `papeis.py`: prévias paradas e desfocadas em `~/.config/dominios/papeis/`;
- `sprites_todos.sh`: personagens em `hud/sprites/`.

Os provedores não aceitam semente. O mesmo prompt gera outra imagem; para refazer igual, use os originais guardados.

## Bloco de estilo (igual em todas as cenas, no fim do prompt)

> 16-bit pixel art game background, HD-2D style like Octopath Traveler, wide cinematic establishing shot, night,
> dark moody atmosphere, deep violet-black shadows, the main glowing landmark and all the light concentrated in the
> center of the frame, left and right thirds and the bottom foreground dark, calm and empty, crisp clean pixels,
> limited palette, no characters, no people, no text, no UI, no border, no frame

As cenas da FLUX.2 Flash começam com `Wide 16:9 landscape image, 1920x1080.`. Esse provedor devolve 1024x768 e o
`pixelar.py` corta para 16:9. A da Nano Banana 2 começa com `Aspect ratio 16:9, wide landscape. Symmetrical centered
composition.` e acrescenta `Detailed 16-bit pixel art game background on a 640x360 pixel canvas` ao bloco. Ela sai em
1376x768, já em 16:9.

## Noite (cena base)

Parâmetros comuns: `--cores 48 --reducao moda --limpar 2`.

| cena | original | provedor | lugar no prompt | pixelizador |
|---|---|---|---|---|
| fogo | rialto-r01 | FLUX.2 Flash | A dwarven forge inside a volcanic cave, a river of glowing magma flowing toward the center, great anvils and a huge forge furnace glowing orange-red in the center, dark basalt rock walls. | `--elemento fogo --puxar 0.5 --croma 1.1 --vinheta 0.35` |
| agua | rialto-r10 | FLUX.2 Flash | A sunken temple sanctuary on the deep sea floor, ancient ruined pillars and arches, the shrine sits in the vertical middle of the image, shafts of pale blue light falling from far above onto the central shrine, corals and seaweed in dark silhouette at the sides, deep blue water, small bubbles. | `--elemento agua --puxar 0.4 --croma 1.5 --vinheta 0.35` |
| terra | rialto-r03 | FLUX.2 Flash | Ancient stone ruins in an old forest, moss-covered broken arch and pillars, huge ancient trees, fireflies, warm golden amber light glowing through the central arch, dark green-brown forest. | `--elemento terra --puxar 0.5 --croma 1.2 --vinheta 0.35` |
| vento | rialto-r13 | FLUX.2 Flash | Floating sky islands at night high above a sea of clouds, an aurora of glowing teal-green wind ribbons swirling across the dark indigo sky, the clouds below tinted teal by the aurora, dark mountain peak silhouettes framing the left and right edges, in the center a floating island with a small wind shrine emitting bright teal-green light and a rope bridge to a smaller island. | `--elemento vento --puxar 0.4 --croma 1.3 --vinheta 0.55 --gama 1.1 --vertical 0.4` |
| eletricidade | rialto-n11 | Nano Banana 2 | The tower exactly at the horizontal center. A tall wizard tower with warm glowing windows on a rocky sea cliff in a thunderstorm at night, a huge bright golden-yellow forked lightning bolt striking the tower top from the clouds directly above it, branching electric yellow arcs, heavy rain, dark heavy storm clouds lit yellow near the bolt, dark rocky shore at the left and right edges. | `--elemento eletricidade --puxar 0.5 --croma 1.2 --vinheta 0.35` |
| mana-pura | rialto-r08 | FLUX.2 Flash | An arcane library hall at night, towering dark bookshelves up to the vaulted ceiling on both sides, in the center a large glowing violet crystal floating above a stone pedestal with smaller crystal shards orbiting it, soft violet-lavender light, a tall arched moonlit window behind, no letters, no symbols. | `--elemento mana-pura --puxar 0.5 --croma 1.2 --vinheta 0.35` |

Na segunda rodada gerei as seis de novo na Nano Banana 2, em 16:9 nativo. Ela tem a grade de pixel mais verdadeira,
mas o ponto focal sai menor e mais apagado. Só a torre da tempestade ganhou da versão anterior: raio amarelo
centrado e laterais calmas.

## Hora do dia: `<cena>-aurora`, `-dia`, `-entardecer` (a noite é a cena base)

Feitas com **Nano Banana 2 Edit** a partir do mesmo original da noite: o link https do original vai no `goal`. Todo
prompt segue o modelo abaixo; a primeira frase muda conforme o lugar e a hora.

> Edit this pixel art scene: change only the time of day to <hora>. <como a luz muda no lugar>. Keep the exact same
> composition, framing, aspect ratio, <objetos do lugar> in exactly the same positions and shapes, the same crisp
> 16-bit pixel art style with the same pixel size, and keep the left and right edges and the bottom fairly dark.

Como a luz muda em cada lugar:

- **vento:** céu do anil ao rosa-pêssego, depois azul claro, depois violeta a laranja.
- **terra:** luz rosa-dourada com névoa, depois sol verde entre as copas, depois laranja-avermelhado rasante.
- **eletricidade:** tempestade com fresta rosa, depois cinza-azulada de dia, depois faixa laranja sob as nuvens. O raio amarelo fica nas três.
- **agua:** os fachos de luz da superfície mudam de cor: rosa-ouro, depois turquesa com cáusticas, depois âmbar.
- **mana-pura:** muda o céu na janela e a luz que entra por ela.
- **fogo:** o brilho roxo no teto da caverna vira uma abertura para o céu, com um facho de luz.

O alinhamento foi conferido com `alinhar.py` (correlação de fase): deslocamento 0 px em todas, e as cenas fundem sem
pulo. Os mesmos parâmetros da noite valem para as horas, com três ajustes:

- `-luz.png` usa a máscara da noite (`--mascara`): as fontes de luz são as mesmas e estão no mesmo lugar.
- Aurora: gama x1,2 e vinheta +0,10. Dia: gama x1,4 e vinheta +0,15 (vento-dia usa gama x1,6). Assim as laterais continuam escuras para as janelas.
- Fogo e mana-pura são interiores e não levam esse escurecimento.

Também testei a FLUX Kontext (US$ 0,048). Ela manteve o desenho, mas transformou o mar de nuvens em névoa lisa, então foi descartada.

## Título: `titulo.png`

Nano Banana 2, depois Nano Banana 2 Edit:

> Aspect ratio 16:9, wide landscape. Title screen art for a classic magic RPG. Symmetrical centered composition: a
> large closed ancient grimoire with a deep purple cover, gold filigree corners and a glowing lavender crystal set in
> the middle of the cover, floating slightly above a round stone altar in the center of the image, radiating violet
> mana light and a soft magic circle of light on the altar, and six elemental orbs orbiting it in a ring: an orange-red
> fire orb, a light blue water orb, an amber earth orb, a teal-green wind orb, a bright yellow lightning orb and a
> lavender mana orb, each with a small glow trail. Background a dark starry void with faint violet nebula, the upper
> third empty and dark for a title. Detailed 16-bit pixel art on a 640x360 pixel canvas, HD-2D style like Octopath
> Traveler, crisp clean pixels, limited palette, left and right thirds and the bottom dark and calm, no characters, no
> people, no text, no letters, no runes, no UI, no border, no frame

A edição tirou um painel retangular que o modelo desenhou no fundo e trocou a estrela do círculo por anéis.
Pixelizador: `--puxar 0.4 --croma 1.1 --vinheta 0.3 --cores 64 --metodo octree --reducao moda --limpar 2`, sem
`--elemento`: com ele, os seis orbes viravam lilás. O terço de cima fica livre para o título.

## Opções novas do pixelar.py (as antigas continuam iguais)

- `--reducao moda`: mapeia a paleta em 1920x1080, e cada bloco 3x3 fica com a cor mais frequente.
- `--limpar N`: N passadas tirando pixel órfão.
- `--croma F`: realça a croma das cores vivas depois do puxão.
- `--vinheta F`: escurece os terços laterais e a faixa de baixo antes da paleta.
- `--gama G`.
- `--vertical V`: onde cortar quando a imagem é mais alta que 16:9.
- `--metodo octree`: paleta que guarda cores pequenas e vivas.

## Prévias paradas

`~/.config/dominios/papeis/grimorio-<cena>.png` mostra a cena 3x por vizinho mais próximo, com o brilho da `-luz.png`
somado (x0,6), como o shader faz. O `-desfocado.png` aplica desfoque gaussiano de 22 px e multiplica por 0,72, a
mesma receita de `gerar/papeis.py`.

## Personagens (`hud/sprites/`, registrados no `indice.json` com licença "gerado")

| sprites | provedor | como foram feitos |
|---|---|---|
| conjurador (96, 48 e 32) | Ideogram Transparent Sprites | fundo transparente |
| 8 familiares (48 e 32) | Nano Banana 2 | uma folha 4x2 sobre verde chapado |
| 6 emblemas (64) | Nano Banana 2 | uma folha 3x2 sobre magenta chapado |

Os recortes saem por moda ponderada, que dá peso extra a cores claras e vivas para olhos e gemas não sumirem. Os
originais ficam em `~/.cache/dominios-dev/arte/sprites/`.
