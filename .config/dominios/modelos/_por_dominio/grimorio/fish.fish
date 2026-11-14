# Dominio {{nome}}. Gerado por `dominio construir`. Lido por fish/init.fish.
set -g fish_color_normal {{cor.texto|sem#}}
set -g fish_color_command {{cor.primaria|sem#}}
set -g fish_color_keyword {{cor.secundaria|sem#}}
set -g fish_color_quote {{ansi.verde|sem#}}
set -g fish_color_redirection {{cor.terciaria|sem#}}
set -g fish_color_end {{cor.secundaria|sem#}}
set -g fish_color_error {{cor.erro|sem#}}
set -g fish_color_param {{cor.texto|sem#}}
set -g fish_color_option {{ansi.ciano|sem#}}
set -g fish_color_comment {{cor.texto_suave|sem#}}
set -g fish_color_operator {{cor.terciaria|sem#}}
set -g fish_color_escape {{ansi.magenta|sem#}}
set -g fish_color_autosuggestion {{ansi.preto_claro|sem#}}
set -g fish_color_selection --background={{cor.superficie2|sem#}}
set -g fish_color_search_match --background={{cor.superficie2|sem#}}
set -g fish_color_valid_path --underline
set -g fish_color_cwd {{cor.primaria|sem#}}
set -g fish_color_user {{cor.secundaria|sem#}}
set -g fish_color_host {{cor.texto_suave|sem#}}
set -g fish_color_cancel {{cor.erro|sem#}}
set -g fish_pager_color_progress {{cor.texto_suave|sem#}}
set -g fish_pager_color_prefix {{cor.primaria|sem#}}
set -g fish_pager_color_completion {{cor.texto|sem#}}
set -g fish_pager_color_description {{cor.texto_suave|sem#}}
set -g fish_pager_color_selected_background --background={{cor.superficie2|sem#}}
set -gx DOMINIO {{dominio}}
set -g __dominio_saudacao {{modo.saudacao|minusculo}}

# ---------------------------------------------------------------- so do Grimorio
set -g fish_color_autosuggestion {{cor.contorno|claro:0.3|sem#}}
set -g fish_color_match --background={{cor.superficie2|sem#}}
set -g fish_color_history_current --bold
set -g fish_color_command brmagenta --bold
set -g fish_color_cwd brmagenta
set -g fish_pager_color_prefix brmagenta
set -g fish_color_quote {{elementos.vento|sem#}}
set -g fish_color_param {{cor.texto|sem#}}
set -g fish_color_option {{elementos.agua|sem#}}
set -g fish_color_operator {{elementos.eletricidade|sem#}}
set -g fish_color_redirection {{elementos.terra|sem#}}
set -g fish_color_escape {{elementos.mana-pura|sem#}}
set -g fish_color_error {{elementos.fogo|sem#}}
set -g fish_pager_color_selected_prefix {{cor.secundaria|sem#}}
set -g fish_pager_color_selected_completion {{cor.texto|sem#}}
set -g fish_pager_color_selected_description {{cor.texto_suave|sem#}}

# Prompt segue o elemento ativo: o gancho ganchos/elemento.d/60-terminal reescreve este arquivo
set -l __sel ~/.local/state/dominios/starship-elemento.toml
test -r $__sel; and set -gx STARSHIP_CONFIG $__sel

# fzf: pagina do grimorio (borda arredondada, titulo, cabecalho em mana clara)
set -gx FZF_DEFAULT_OPTS "--color=bg+:{{cor.superficie2}},bg:-1,spinner:{{elementos.vento}},hl:{{elementos.terra}},fg:{{cor.texto}},header:{{cor.secundaria}},info:{{cor.texto_suave}},pointer:{{cor.primaria}},marker:{{elementos.vento}},fg+:{{cor.texto}},prompt:{{cor.primaria}},hl+:{{elementos.eletricidade}},border:{{cor.contorno}},label:{{cor.primaria}},query:{{cor.texto}},separator:{{cor.contorno}},scrollbar:{{cor.contorno}},gutter:-1 --border=rounded --border-label=' ✦ GRIMÓRIO ✦ ' --border-label-pos=3 --info=inline-right --prompt='{{>prompt-simbolo}} ' --pointer='▌' --marker='◆' --padding=0,1"

# eza: arquivos nos elementos (pastas em mana, executaveis vento, links agua, chaves terra)
set -gx EZA_COLORS "di=1;{{cor.primaria|ansi}}:ex=1;{{elementos.vento|ansi}}:ln={{elementos.agua|ansi}}:or={{elementos.fogo|ansi}}:so={{elementos.mana-pura|ansi}}:pi={{elementos.terra|ansi}}:bd={{elementos.terra|ansi}}:cd={{elementos.terra|ansi}}:ur={{elementos.eletricidade|ansi}}:uw={{elementos.fogo|ansi}}:ux={{elementos.vento|ansi}}:ue={{elementos.vento|ansi}}:gr={{elementos.eletricidade|ansi}}:gw={{elementos.fogo|ansi}}:gx={{elementos.vento|ansi}}:tr={{elementos.eletricidade|ansi}}:tw={{elementos.fogo|ansi}}:tx={{elementos.vento|ansi}}:sn={{elementos.agua|ansi}}:sb={{cor.secundaria|ansi}}:uu={{cor.secundaria|ansi}}:gu={{cor.secundaria|ansi}}:un={{cor.contorno|ansi}}:gn={{cor.contorno|ansi}}:da={{cor.texto_suave|ansi}}:xx={{cor.contorno|ansi}}:lp={{cor.contorno|ansi}}:in={{cor.texto_suave|ansi}}:hd=1;4;{{cor.texto_suave|ansi}}:ga={{elementos.vento|ansi}}:gm={{elementos.eletricidade|ansi}}:gd={{elementos.fogo|ansi}}:gv={{elementos.mana-pura|ansi}}:gt={{elementos.agua|ansi}}:*.md={{cor.texto|ansi}}:*.py={{elementos.eletricidade|ansi}}:*.rs={{elementos.fogo|ansi}}:*.js={{elementos.eletricidade|ansi}}:*.ts={{elementos.agua|ansi}}:*.json={{elementos.terra|ansi}}:*.toml={{elementos.terra|ansi}}"
set -gx EZA_ICON_SPACING 1

# bat usa as 16 cores do terminal (que sao as do dominio); man e less coloridos
set -gx BAT_THEME ansi
set -gx BAT_STYLE numbers,changes,header
set -gx MANPAGER "sh -c 'col -bx | bat -l man -p'"
set -gx MANROFFOPT -c
set -gx LESS_TERMCAP_md (printf '\e[1;{{cor.primaria|ansi}}m')
set -gx LESS_TERMCAP_me (printf '\e[0m')
set -gx LESS_TERMCAP_us (printf '\e[4;{{elementos.terra|ansi}}m')
set -gx LESS_TERMCAP_ue (printf '\e[0m')
set -gx LESS_TERMCAP_so (printf '\e[1;{{elementos.eletricidade|ansi}}m')
set -gx LESS_TERMCAP_se (printf '\e[0m')
set -gx LESS_TERMCAP_mb (printf '\e[1;{{elementos.fogo|ansi}}m')

# Selo de nivel/rank para o prompt, lido de jogador.json sem processo externo
function __grimorio_selo --on-event fish_prompt
    set -l arq ~/.local/state/dominios/jogador.json
    if not test -r $arq
        set -e GRIMORIO_SELO
        return
    end
    read -z -l json < $arq
    set -l nv (string match -rg '"nivel"\s*:\s*(\d+)' -- $json)
    set -l rk (string match -rg '"rank"\s*:\s*"([^"]*)"' -- $json)
    if test -z "$nv"
        set -e GRIMORIO_SELO
    else
        set -gx GRIMORIO_SELO "NV.$nv"(test -n "$rk"; and echo " ▪ $rk")
    end
end

# Comando inexistente: magia desconhecida
function __dominio_nao_achado
    set -l c1 (set_color {{elementos.fogo|sem#}})
    set -l c2 (set_color {{cor.primaria|sem#}})
    set -l c3 (set_color {{cor.texto_suave|sem#}})
    set -l rs (set_color normal)
    printf '\n  %s✧ Magia desconhecida%s  %s%s%s\n' $c1 $rs $c2 (string escape -- $argv[1]) $rs
    printf '  %sO grimório não registra este feitiço.%s\n\n' $c3 $rs
end

# Saudacao: ficha + uma frase do grimorio
function __dominio_saudacao_propria
    set -l cfg ~/.config/dominios/atual/fastfetch.jsonc
    set -l json ~/.local/state/dominios/elemento.json
    set -l el
    if test -r $json
        read -z -l ej < $json
        set el (string match -rg '"elemento"\s*:\s*"([^"]*)"' -- $ej)
        test -r ~/.config/dominios/atual/terminal/$el/fastfetch.jsonc; and set cfg ~/.config/dominios/atual/terminal/$el/fastfetch.jsonc
    end
    # heroi do elemento ativo, de corpo inteiro (x3 tem a altura da ficha; x2 se a janela for estreita);
    # o kitty o mostra no tamanho nativo, entao o aumento e inteiro e nitido. Sem a arte: o encapuzado.
    set -l heroi
    if test -n "$el"
        set -l esc 3
        test "$COLUMNS" -lt 125 2>/dev/null; and set esc 2
        set heroi ~/.config/dominios/papeis/grimorio-heroi-$el-x$esc.png
        test -r $heroi; or set heroi
    end
    set -l img ~/.config/dominios/papeis/grimorio-retrato.png
    test -r $img; or set img ~/.config/dominios/papeis/grimorio-emblema-pixel.png
    test -r $img; or set img ~/.config/dominios/atual/logo.png
    if test "$TERM" = xterm-kitty; and test -n "$heroi"
        fastfetch -c $cfg --logo-type kitty-direct --logo $heroi
    else if test "$TERM" = xterm-kitty; and test -r $img
        fastfetch -c $cfg --logo-type kitty-direct --logo $img --logo-width 30 --logo-height 15
    else
        fastfetch -c $cfg
    end
    set -l frases \
        "O grimório se abre." \
        "A mana está em todos." \
        "Cada feitiço começa com uma palavra." \
        "O poder que a mana dá é justo." \
        "Os familiares aguardam o chamado." \
        "Sem mana, só resta a teimosia. Ela também vale." \
        "A fogueira está acesa. Descanse se precisar." \
        "Seis elementos, um conjurador." \
        "Uma nova página em branco." \
        "Nenhuma masmorra se limpa sozinha." \
        "Boss de rank superior detectado no backlog." \
        "Deadline é só uma masmorra com cronômetro." \
        "Quem estuda a magia a fundo vira mestre." \
        "Ponto de atributo disponível."
    set -l h (date +%H)
    set -l turno manhã
    test $h -ge 12; and set turno tarde
    test $h -ge 18; and set turno noite
    test $h -lt 5; and set turno madrugada
    set -l frase $frases[(random 1 (count $frases))]
    printf '  %s✦%s %s%s%s  %s· %s%s\n\n' (set_color {{cor.primaria|sem#}} --bold) (set_color normal) (set_color {{cor.texto|sem#}}) $frase (set_color normal) (set_color {{cor.texto_suave|sem#}}) $turno (set_color normal)
end

function __dominio_pos_init
    functions -q enable_transience; and enable_transience
end
