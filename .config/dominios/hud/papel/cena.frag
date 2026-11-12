#version 440
// Papel vivo do grimorio (HD-2D): cena em pixel art 640x360 ampliada por vizinho mais
// proximo, com luz moderna por cima. Um passo so, em resolucao de tela.
// "a" = coordenada em pixels de arte (0..640, 0..360), y para baixo.

layout(location = 0) in vec2 qt_TexCoord0;
layout(location = 0) out vec4 fragColor;

layout(std140, binding = 0) uniform buf {
    mat4 qt_Matrix;
    float qt_Opacity;
    float tempo;
    float pulso;
    float energia;
    float transicao;     // 0 = so a cena velha, 1 = so a nova
    float chuva;
    float fator;         // px de tela por px de arte (3 em 1080p)
    float tipoVelho;     // 0 fogo, 1 agua, 2 terra, 3 vento, 4 eletricidade, 5 mana pura
    float tipoNovo;
    float fusao;         // 0 troca de capitulo (varredura em pixels), 1 fase do dia (fusao lisa)
    float gradVelho;     // quanto da correcao de cor da hora cada cena recebe (a variante ja vem pintada)
    float gradNovo;
    vec2 tamanho;        // px de tela do item
    vec2 deslocamento;   // onde a grade comeca (cobre e centraliza)
    vec4 corVelho;
    vec4 corNovo;
    vec4 matiz;          // rgb: tom da hora; a: exposicao
    vec4 ajuste;         // x: saturacao, y: forca das luzes, z: escurecer, w: nitido
    float mesa;          // 1: calma atras dos widgets e poco do relogio; 0: so o cenario (paisagem)
};
layout(binding = 1) uniform sampler2D cenaVelha;
layout(binding = 2) uniform sampler2D luzVelha;
layout(binding = 3) uniform sampler2D cenaNova;
layout(binding = 4) uniform sampler2D luzNova;

const vec2 GRADE = vec2(640.0, 360.0);
const float TAU = 6.2831853;

float hash12(vec2 p) {
    vec3 p3 = fract(vec3(p.xyx) * 0.1031);
    p3 += dot(p3, p3.yzx + 33.33);
    return fract((p3.x + p3.y) * p3.z);
}
vec2 hash22(vec2 p) {
    vec3 p3 = fract(vec3(p.xyx) * vec3(0.1031, 0.1030, 0.0973));
    p3 += dot(p3, p3.yzx + 33.33);
    return fract((p3.xx + p3.yz) * p3.zy);
}

// ---------- cena ----------
vec3 gradua(vec3 c) {
    c *= matiz.rgb * matiz.a;
    float l = dot(c, vec3(0.2126, 0.7152, 0.0722));
    return max(mix(vec3(l), c, ajuste.x), 0.0);
}

// cena de um slot com desfoque de miniatura, luz da hora, ciclo de paleta e brilho
vec3 cena(sampler2D img, sampler2D luz, vec2 a, vec2 ai, float desf, float tipo, float grad, float t, out float mascara) {
    vec2 uvPx = (ai + 0.5) / GRADE;
    vec2 uvC = a / GRADE;
    vec3 c = textureLod(img, ajuste.w > 0.5 ? uvPx : uvC, 0.0).rgb;
    if (desf > 0.02) {
        float lod = desf * 2.4;
        vec2 o = exp2(lod) * 0.55 / GRADE;
        vec3 b = textureLod(img, uvC + vec2(o.x, o.y * 0.4), lod).rgb
               + textureLod(img, uvC - vec2(o.x, o.y * 0.4), lod).rgb
               + textureLod(img, uvC + vec2(-o.x * 0.4, o.y), lod).rgb
               + textureLod(img, uvC + vec2(o.x * 0.4, -o.y), lod).rgb;
        c = mix(c, b * 0.25, smoothstep(0.0, 0.45, desf));
    }
    float m = textureLod(luz, uvPx, 0.0).a;
    vec3 brilho = textureLod(luz, uvC, 0.0).rgb;
    mascara = m;

    // as fontes de luz escapam do escuro da noite
    c = mix(mix(c, gradua(c), grad), c * (0.85 + 0.35 * ajuste.y), m * 0.85);

    // ciclo de paleta nas fontes de luz: faixas em degrau que andam
    vec3 onda = tipo < 0.5 ? vec3(0.13, 0.55, 3.2)       // fogo: sobe
              : (tipo < 1.5 ? vec3(0.30, 0.90, -1.3)     // agua: ondula
              : vec3(0.21, 0.37, -1.0));
    float o1 = sin(ai.x * onda.x + ai.y * onda.y + t * onda.z + sin(ai.y * 0.21 + t * 0.7) * 1.5);
    c += c * m * 0.20 * step(0.55, o1);

    // brilho tremulando (fogo treme mais)
    float amp = tipo < 0.5 ? 0.24 : 0.08;
    float w = tipo < 0.5 ? 5.0 : 1.3;
    float pisca = 1.0 + amp * (0.6 * sin(t * w + a.x * 0.031) * sin(t * w * 1.37 + a.y * 0.047 + 1.3)
                             + 0.4 * sin(t * w * 2.3 + a.x * 0.011));
    c += brilho * (0.45 + 0.55 * ajuste.y) * pisca * (1.0 + 0.6 * pulso + 1.5 * energia);
    return c;
}

// ---------- particulas ----------
// uma camada numa grade de celulas que desliza a vel (px de arte/s); uma particula por celula
void celula(vec2 a, vec2 cel, vec2 vel, float dens, float semente, float t,
            out vec2 c, out vec2 r, out float ativo) {
    vec2 g = (a - vel * t) / cel;
    vec2 id = floor(g);
    r = hash22(id + semente * 5.77);
    ativo = step(hash12(id + semente * 17.31), dens);
    c = (id + 0.3 + 0.4 * r) * cel + vel * t;
}
float pixel(vec2 pc, vec2 c) {           // 1 se pc e o pixel de arte da particula
    return step(max(abs(pc.x - c.x), abs(pc.y - c.y)), 0.5);
}
float halo(vec2 a, vec2 c, float raio) {
    vec2 d = a - c;
    return exp(-dot(d, d) / (raio * raio));
}

// rgb = luz somada, a = cobertura (particula opaca, como folha)
vec4 particulas(vec2 a, vec2 ai, float tipo, float t, float m, float desf) {
    vec2 pc = ai + 0.5;
    vec3 cor = vec3(0.0);
    float cob = 0.0;
    vec2 c, r;
    float on;
    float nit = 1.0 - desf * 0.7;        // na faixa desfocada a particula vira so brilho
    float bok = 1.0 + desf * 1.5;

    if (tipo < 0.5) {
        // fogo: brasas subindo
        for (int i = 0; i < 2; i++) {
            float fi = float(i);
            celula(a, vec2(18.0 + fi * 12.0), vec2(0.0, -(17.0 - fi * 7.0)), 0.32, fi + 1.0, t, c, r, on);
            if (on < 0.5) continue;
            c.x += sin(t * (1.1 + r.y) + r.x * TAU) * 2.5;
            c = floor(c) + 0.5;
            float vida = smoothstep(10.0, 170.0, c.y) * (0.55 + 0.45 * sin(t * (3.0 + r.x * 3.0) + r.y * TAU));
            vec3 ce = mix(vec3(1.0, 0.42, 0.14), vec3(1.0, 0.86, 0.42), r.y);
            cor += ce * (pixel(pc, c) * 1.2 * nit + halo(a, c, 3.0 * bok) * 0.30) * vida * (1.0 - fi * 0.4);
        }
    } else if (tipo < 1.5) {
        // agua: bolhas subindo devagar e reflexos que acendem e somem
        celula(a, vec2(20.0), vec2(0.0, -7.0), 0.28, 3.0, t, c, r, on);
        if (on > 0.5) {
            c.x += sin(t * 1.4 + r.x * TAU) * 1.6;
            c = floor(c) + 0.5;
            float b = 0.5 + 0.3 * sin(t * 0.8 + r.y * TAU);
            cor += vec3(0.70, 0.88, 1.0) * (pixel(pc, c) * 0.8 * nit + halo(a, c, 2.5 * bok) * 0.12) * b;
        }
        celula(a, vec2(12.0), vec2(4.0, 0.0), 0.22, 4.0, t, c, r, on);
        if (on > 0.5) {
            c = floor(c) + 0.5;
            float g = pow(max(0.0, sin(t * (0.9 + r.x) + r.y * TAU)), 10.0) * (0.25 + m);
            cor += vec3(0.85, 0.95, 1.0) * (pixel(pc, c) * nit + halo(a, c, 3.0) * 0.25) * g;
        }
    } else if (tipo < 2.5) {
        // terra: vagalumes vagando e folhas caindo
        celula(a, vec2(32.0), vec2(0.0, -1.5), 0.35, 5.0, t, c, r, on);
        if (on > 0.5) {
            c += vec2(sin(t * 0.7 + r.x * TAU), cos(t * 0.53 + r.y * TAU)) * 5.0;
            c = floor(c) + 0.5;
            float b = pow(0.5 + 0.5 * sin(t * 1.1 + r.x * TAU), 2.0);
            cor += vec3(0.86, 0.96, 0.45) * (pixel(pc, c) * 1.1 * nit + halo(a, c, 4.5 * bok) * 0.28) * b;
        }
        celula(a, vec2(36.0), vec2(9.0, 13.0), 0.22, 6.0, t, c, r, on);
        if (on > 0.5) {
            c.x += sin(t * 1.3 + r.y * TAU) * 4.0;
            c = floor(c) + 0.5;
            vec2 d = pc - c;
            float deitada = step(0.0, sin(t * 2.0 + r.x * TAU));
            vec2 ext = mix(vec2(1.0, 2.0), vec2(2.0, 1.0), deitada);   // 1x2 ou 2x1, gira caindo
            float hit = step(-0.5, d.x) * step(d.x, ext.x - 0.5) * step(-0.5, d.y) * step(d.y, ext.y - 0.5);
            vec3 cf = mix(vec3(0.62, 0.42, 0.22), vec3(0.50, 0.62, 0.30), r.y) * gradua(vec3(1.0));
            cor += cf * hit * 0.9;
            cob = max(cob, hit * 0.9);
        }
    } else if (tipo < 3.5) {
        // vento: riscos de vento e petalas
        celula(a, vec2(72.0, 9.0), vec2(110.0, 0.0), 0.20, 7.0, t, c, r, on);
        if (on > 0.5) {
            c = floor(c) + 0.5;
            float compr = 8.0 + 14.0 * r.x;
            float dx = c.x - pc.x;
            float hit = step(abs(pc.y - c.y), 0.5) * step(0.0, dx) * step(dx, compr);
            cor += vec3(0.78, 0.96, 0.90) * hit * (1.0 - dx / compr) * 0.32 * nit;
        }
        celula(a, vec2(26.0), vec2(26.0, 8.0), 0.25, 8.0, t, c, r, on);
        if (on > 0.5) {
            c.y += sin(t * 1.7 + r.x * TAU) * 3.0;
            c = floor(c) + 0.5;
            float hit = pixel(pc, c);
            vec3 cp = mix(vec3(1.0, 0.74, 0.82), vec3(1.0, 0.92, 0.95), r.y) * gradua(vec3(1.0));
            cor += cp * hit * 0.85 + vec3(1.0, 0.8, 0.9) * halo(a, c, 2.0 * bok) * 0.05;
            cob = max(cob, hit * 0.85);
        }
    } else if (tipo < 4.5) {
        // eletricidade: fagulhas que estalam (a chuva e o relampago vem de fora)
        celula(a, vec2(40.0), vec2(0.0, 0.0), 0.22, 9.0, t, c, r, on);
        if (on > 0.5) {
            c = floor(c) + 0.5;
            float g = pow(max(0.0, sin(t * (1.3 + r.x) + r.y * TAU)), 24.0);
            cor += vec3(1.0, 0.90, 0.45) * (pixel(pc, c) * 1.3 * nit + halo(a, c, 4.0) * 0.35) * g;
        }
    } else {
        // mana pura: motas subindo e runas flutuando
        celula(a, vec2(16.0), vec2(0.0, -5.0), 0.30, 10.0, t, c, r, on);
        if (on > 0.5) {
            c.x += sin(t * 0.9 + r.x * TAU) * 2.0;
            c = floor(c) + 0.5;
            float b = 0.45 + 0.55 * pow(0.5 + 0.5 * sin(t * 1.2 + r.y * TAU), 2.0);
            cor += vec3(0.76, 0.70, 1.0) * (pixel(pc, c) * 0.9 * nit + halo(a, c, 3.0 * bok) * 0.22) * b;
        }
        celula(a, vec2(58.0), vec2(0.0, -6.0), 0.25, 11.0, t, c, r, on);
        if (on > 0.5) {
            c = floor(c) + 0.5;
            vec2 d = pc - c;                     // glifo 5x5 espelhado, 15 bits do hash
            float dentro = step(max(abs(d.x), abs(d.y)), 2.0);
            float idx = (d.y + 2.0) * 3.0 + abs(d.x);
            float bits = floor(r.x * 32768.0);
            float bit = mod(floor(bits / exp2(idx)), 2.0);
            float vida = pow(max(0.0, sin(t * 0.35 + r.y * TAU)), 2.0);
            vec3 cr = vec3(0.80, 0.72, 1.0);
            cor += cr * (dentro * bit * 0.75 * nit + halo(a, c, 6.0 * bok) * 0.10) * vida;
        }
    }
    return vec4(cor * (1.0 + 0.5 * pulso + energia), cob);
}

// chuva em pixel: riscos inclinados em degrau, 1 px para a esquerda a cada 4 de queda
vec3 gotas(vec2 ai, float dens, float t) {
    float u = ai.x + floor(ai.y / 4.0);
    if (mod(u, 3.0) > 0.5) return vec3(0.0);
    float colu = floor(u / 3.0);
    if (hash12(vec2(colu, 7.0)) > dens) return vec3(0.0);
    float vel = 210.0 + 90.0 * hash12(vec2(colu, 3.0));
    float per = 60.0 + 60.0 * hash12(vec2(colu, 5.0));
    float f = mod(ai.y - t * vel - hash12(vec2(colu, 9.0)) * per, per);
    float compr = 6.0;
    return vec3(0.68, 0.76, 0.95) * step(f, compr) * (f + 1.0) / compr * 0.40;
}

void main() {
    vec2 uv = qt_TexCoord0;
    vec2 a = (uv * tamanho - deslocamento) / fator;
    a = clamp(a, vec2(0.0), GRADE - 0.001);
    vec2 ai = floor(a);
    float t = tempo;

    // desfoque de miniatura: alto e baixo da tela fora de foco
    float desf = clamp(smoothstep(0.30, 0.0, uv.y) + smoothstep(0.72, 1.0, uv.y), 0.0, 1.0);

    float mN, mV;
    vec3 col = cena(cenaNova, luzNova, a, ai, desf, tipoNovo, gradNovo, t, mN);
    vec4 part = particulas(a, ai, tipoNovo, t, mN, desf);
    float eTipo = step(3.5, tipoNovo) * step(tipoNovo, 4.5);

    // troca de capitulo: varredura que dissolve em pixels, com uma linha de luz na frente
    if (transicao < 0.999) {
        vec3 velha = cena(cenaVelha, luzVelha, a, ai, desf, tipoVelho, gradVelho, t, mV);
        vec4 partV = particulas(a, ai, tipoVelho, t, mV, desf);
        float lim = 0.78 * (ai.x / GRADE.x) + 0.22 * hash12(floor(ai / 2.0));
        float s = transicao * 1.3 - 0.15;
        float nova = mix(step(lim, s), smoothstep(0.0, 1.0, transicao), fusao);
        col = mix(velha, col, nova);
        part = mix(partV, part, nova);
        eTipo = mix(step(3.5, tipoVelho) * step(tipoVelho, 4.5), eTipo, nova);
        float linha = exp(-abs(lim - s) * 70.0) * sin(3.14159 * clamp(transicao, 0.0, 1.0)) * (1.0 - fusao);
        col += mix(corNovo.rgb, vec3(1.0), 0.35) * linha * 0.9;
    }
    vec3 corEl = mix(corVelho.rgb, corNovo.rgb, step(0.5, transicao));

    col = col * (1.0 - part.a) + part.rgb;

    // chuva (eletricidade sempre chove)
    float ch = max(chuva, eTipo * 0.55);
    if (ch > 0.01) {
        col *= 1.0 - 0.22 * ch;
        col += gotas(ai, ch * 0.55, t) * (1.0 - desf * 0.5);
    }
    // relampago raro na torre da tempestade
    if (eTipo > 0.01) {
        float ciclo = 19.0;
        float k = floor(t / ciclo);
        float dt = t - (k * ciclo + hash12(vec2(k, 2.0)) * 12.0);
        float clarao = step(0.4, hash12(vec2(k, 9.0))) * step(0.0, dt)
                     * (exp(-dt * 6.0) + 0.7 * step(0.22, dt) * exp(-(dt - 0.22) * 5.0));
        col += (vec3(0.16, 0.17, 0.22) + col * 0.7) * clarao * (1.0 - uv.y * 0.5) * eTipo;
    }

    // surto: onda de luz em pixel saindo do centro + clarao na cor do elemento
    if (energia > 0.001) {
        float rs = (1.0 - energia) * 420.0;
        float anel = step(abs(length(ai + 0.5 - GRADE * 0.5) - rs), 1.0);
        col += corEl * (anel * 0.7 + 0.16 * (1.0 - length(uv - 0.5))) * energia;
    }

    // calma para os widgets: laterais (x < 470 e > 1450, rampa ate 653/1267) e faixa de
    // baixo (y > 790); o miolo fica com a cena inteira. Vinheta; escurecer geral
    float lado = smoothstep(0.16, 0.255, abs(uv.x - 0.5));
    float baixo = smoothstep(0.73, 0.785, uv.y);
    float calma = max(lado, baixo) * mesa;
    float l = dot(col, vec3(0.2126, 0.7152, 0.0722));
    col = mix(col, mix(vec3(l), col, 0.7) * 0.55, calma);
    // cena clara (vento de dia): onde ha widget a luminancia tem teto, o vidro e o texto
    // continuam legiveis; nas cenas escuras isto quase nao age
    float l2 = dot(col, vec3(0.2126, 0.7152, 0.0722));
    float teto = 0.13;
    col *= mix(1.0, teto / max(teto, l2), calma * 0.9);
    // poco de sombra atras do relogio (x 600..1320, y 54..270): a hora se le sobre qualquer cena
    vec2 dr = (uv - vec2(0.5, 0.14)) / vec2(0.17, 0.115);
    float rel = exp(-dot(dr, dr) * 1.2) * mesa;
    float lr = dot(col, vec3(0.2126, 0.7152, 0.0722));
    col = mix(col, mix(vec3(lr), col, 0.5) * 0.3, rel * 0.85);
    float vin = smoothstep(0.42, 1.05, length((uv - 0.5) * vec2(1.15, 1.5)));
    col *= (1.0 - 0.45 * vin) * (1.0 - ajuste.z);

    // pontilhado minimo so para os degrades de luz nao formarem bandas
    vec2 fc = floor(gl_FragCoord.xy);
    col += (hash12(fc) + hash12(fc + 71.3) - 1.0) / 255.0;
    fragColor = vec4(col, 1.0) * qt_Opacity;
}
