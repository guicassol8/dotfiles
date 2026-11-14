# Heróis dos seis elementos

Seis aventureiros do mesmo grupo, em pixel art na grade nativa do gerador (cada pixel de arte amostrado 1:1, sem reamostrar o corpo).

- `heroi-<elemento>-128.png`: corpo inteiro, tela 128x128, pé da frente na linha 125, fundo transparente, alfa 0/255, contorno `#17141D`.
- `heroi-<elemento>-64.png`: o mesmo corpo reduzido 2x, com olhos retocados.
- `heroi-<elemento>-busto-96/48/32.png`: cabeça e ombros, rosto centrado, de um close do mesmo desenho (edição do bruto do corpo).
- Curandeira, busto: recorte largo (rosto em ~1/3 do quadro, borda da cúpula e água atrás do ombro), 96 por vizinho puro da grade nativa; o vidro que mostrava o fundo verde virou transparência.
- Bastião, `heroi-terra-busto-32.png`: desenhado a mão por script (`terra32.py`) a partir do 96, porque a redução virava mancha: elmo com crista, viseira em T escura com olhos claros, três tons de pedra.
- Pendente: a Faísca Viva nova (cabelo longo branco-azulado de estática com pontas amarelas, pulseiras de cobre, sem a pose de braços abertos). Os prompts estão em `prompts.py` (`ELETRICIDADE_NOVA`); não foi comprada porque todos os provedores de imagem do Rialto respondiam `upstream_403` em 13/11. Até lá ficam os arquivos atuais dela.

| elemento | título | corpo (Rialto) | busto (Rialto) |
|---|---|---|---|
| fogo | O Espadachim da Brasa | Nano Banana 2 (n02) | Nano Banana 2 Edit (b01) |
| agua | A Curandeira da Cúpula | Nano Banana 2 (n01) | Nano Banana 2 Edit (b01) |
| eletricidade | A Faísca Viva | Nano Banana 2 (n01) | Nano Banana 2 Edit (b02) |
| terra | O Bastião de Pedra | Nano Banana 2 (n01) + Nano Banana 2 Edit (e01) | Nano Banana 2 Edit (b01) |
| vento | O Bardo Andarilho | Nano Banana 2 (n02) | Nano Banana 2 Edit (b01) |
| mana-pura | A Arquimaga da Biblioteca | Nano Banana 2 (n03) | Nano Banana 2 Edit (b01) |

## Prompt do corpo

Linha do personagem + bloco de estilo (igual nos seis). `{fundo}`: verde chapado `#00FF00` em todos, magenta `#FF00FF` no vento. `{altura}`: 85, ou 90 no vento e na mana pura.

Bloco de estilo:

> Full-body character sprite for a classic fantasy RPG, 16-bit pixel art in the HD-2D style of Octopath Traveler. Crisp hard-edged square pixels as if drawn on a 128x128 pixel canvas, clean 1-pixel near-black outline around the whole figure, limited palette, flat cel shading with 2 or 3 tones per color, no anti-aliasing, no blur, no soft glow, no gradients. One character standing in a confident idle pose, three-quarter view facing the viewer, centered, feet near the bottom edge, the figure from head to feet fills about {altura} percent of the image height. JRPG proportions about 4 heads tall with a slightly large head and a clearly readable face with visible eyes. Clothes in deep violet, dark plum and charcoal tones with small warm gold trim, but the character is dominated by the element color. Strong elemental aura: the element bursts out of the body and swirls all around the figure in many crisp pixel shapes, clearly visible even at small size, everything kept inside the frame. Plain flat solid {fundo} background, no ground, no cast shadow, no scenery, no text, no letters, no frame, no border.

**fogo**: A young male swordsman in a dark plum kimono with ember-orange sash and sleeve trims, holding one unsheathed katana in his right hand with the blade pointing down and wreathed in fire, his spiky hair is made of living flames from the roots up (bright orange and yellow fire hair), glowing embers rising all around him and flame tongues licking up from his shoulders and sleeves. Dominant color: warm coral-orange fire.

**agua**: A gentle young female healer in long violet and white robes, carrying on her back a big round glass dome full of glowing light-blue magical water, water streams spilling from the dome and floating droplets and ribbons of water orbiting around her, a small healing staff in one hand. Dominant color: soft sky blue water.

**eletricidade**: A lively young woman in light short adventurer clothes (cropped top, shorts, wraps), wild spiky electrified hair standing up, bright yellow zigzag lightning bolts bursting out of her whole body and crackling around her arms and legs, small sparks. Dominant color: bright electric yellow.

**terra**: A big broad man in heavy armor made of carved sandstone and rock plates, a helmet that almost hides his face with only the eyes visible, a huge round stone tower shield in one hand and a heavy stone warhammer in the other, chunks of rock and pebbles floating around him. Dominant color: warm sandy ochre and earth brown.

**vento**: A cheerful young male bard in a travelling cloak, a wide-brimmed hat with a long feather, playing a wooden flute, musical notes, green leaves and pale cream petals swirling around him in curling teal wind streaks blowing from the flute. The wind streaks wrap tightly around his body in a narrow spiral and never reach farther to the sides than the width of his hat brim. Dominant color: mint teal green wind.

**mana-pura**: A tall elegant archmage woman with long silver-white hair, in long flowing deep violet robes with lavender trim and a high collar, her eyes glowing bright lilac, one hand raised toward an open spellbook that floats in the air in front of her chest with glowing pages, several small glowing geometric arcane sigils (circles, triangles, diamonds and four-pointed stars, no letters) orbiting around her in a ring, wisps of lilac mana flowing out of the book. Dominant color: soft lilac violet.

O Bastião final é uma edição do n01 (a aura de areia lia como fogo):

> {link} Edit this pixel art sprite: remove the large sandy flame-shaped aura behind the stone knight. Instead, surround him with more floating chunks of rock and small pebbles orbiting close around his body (within a short distance of him), plus a few small dust puffs at his feet, all drawn as crisp pixel shapes with a dark 1-pixel outline. Keep the knight himself exactly the same: same sandstone armor, helmet, round stone shield, stone warhammer, pose, colors, pixel size and outline. The whole artwork must be compact, no wider than it is tall. Keep the plain flat solid pure chroma-key green (#00FF00) background, no ground, no shadow, no text.

## Prompt do busto (Nano Banana 2 Edit, link do bruto final do corpo)

> {link} Using this exact character, draw a close-up bust portrait for an RPG dialogue box: head and shoulders only, face centered, facing the viewer in a slight three-quarter view, the same face, hair, colors and clothing details, with the element effects ({efeito}) around the head and shoulders. Same 16-bit pixel art style with crisp square pixels, near-black 1-pixel outline, flat cel shading, no anti-aliasing, no blur. The head and shoulders fill the frame. Plain flat solid {fundo} background, no text, no frame, no border.

- fogo: his hair made of living flames, embers rising
- agua: the glass dome on her back filled with light-blue water, no green inside it, floating water droplets
- eletricidade: wild spiky electrified yellow hair, a few thin yellow zigzag lightning bolts behind her shoulders, never covering the face, most of the background left empty
- terra: his stone helmet almost hiding the face with the eyes visible, floating rocks and pebbles
- vento: teal wind streaks, musical notes, leaves and petals swirling, the flute at his lips
- mana-pura: her eyes glowing lilac, small geometric glowing sigils orbiting, lilac mana wisps

## Refazer

Brutos, scripts e planilha de gastos em `~/.cache/dominios-dev/arte/seis/`: `prompts.py` (textos acima), `todos.sh` (corpos: `herois.py` acha a grade e amostra 1:1, `montar.py` faz paleta curta, contorno, linha de base e o 64), `retoque_corpo.py` (olhos do 64), `bustos.sh` (roda `olhos.py`, `busto.py` com retoque de olho e viseira, e `terra32.py`).
