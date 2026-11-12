# Dominios: cores, prompt e saudacao do terminal.
# Carregado pela ultima linha de ~/.config/fish/config.fish.
status is-interactive; or return

set -g __dominio_raiz ~/.config/dominios
test -r $__dominio_raiz/atual/fish.fish; and source $__dominio_raiz/atual/fish.fish
set -g __dominio_visto (readlink $__dominio_raiz/atual 2>/dev/null)

# Grimorio: o arquivo vivo do terminal (kitty e starship) precisa existir antes do primeiro prompt
if test (basename (string replace -r '/$' '' -- "$__dominio_visto")) = grimorio
    set -l __h $__dominio_raiz/ganchos/elemento.d/60-terminal
    test -r ~/.local/state/dominios/starship-elemento.toml; or SEM_SINAL=1 $__h 2>/dev/null
    test -r ~/.local/state/dominios/starship-elemento.toml; and test -r $__dominio_raiz/atual/fish.fish; and source $__dominio_raiz/atual/fish.fish
end

if type -q starship
    # (o fish.fish do grimorio troca por ~/.local/state/dominios/starship-elemento.toml)
    set -q STARSHIP_CONFIG; and string match -q "*starship-elemento.toml" -- $STARSHIP_CONFIG; or set -gx STARSHIP_CONFIG $__dominio_raiz/atual/starship.toml
    starship init fish | source
    functions -q __dominio_pos_init; and __dominio_pos_init
end

# Gancho do dominio: fish.fish pode definir __dominio_nao_achado (comando inexistente)
function fish_command_not_found
    if functions -q __dominio_nao_achado
        __dominio_nao_achado $argv
    else
        __fish_default_command_not_found_handler $argv
    end
end

# Saudacao: ficha do dominio. No kitty o logo e imagem; nos outros, braille.
# Dominio com [modo] saudacao = false (o Neutro) abre o terminal limpo.
function fish_greeting
    test "$__dominio_saudacao" = false; and return
    # dominio com saudacao propria (Sistema: ficha + frase)
    if functions -q __dominio_saudacao_propria
        __dominio_saudacao_propria
        return
    end
    set -l cfg ~/.config/dominios/atual/fastfetch.jsonc
    if not test -r $cfg
        fastfetch
    else if test "$TERM" = xterm-kitty; and test -r ~/.config/dominios/atual/logo.png
        fastfetch -c $cfg --logo-type kitty-direct --logo ~/.config/dominios/atual/logo.png --logo-width 28 --logo-height 14
    else
        fastfetch -c $cfg
    end
end

# Shells ja abertos pegam as cores novas no proximo prompt apos trocar de dominio
function __dominio_recarrega --on-event fish_prompt
    set -l d (readlink ~/.config/dominios/atual 2>/dev/null)
    if test "$d" != "$__dominio_visto"
        set -g __dominio_visto $d
        # tira o que o dominio anterior definiu (funcoes de selo, ganchos)
        functions -e __sistema_selo __grimorio_selo __dominio_nao_achado __dominio_saudacao_propria __dominio_pos_init
        set -e SISTEMA_SELO GRIMORIO_SELO EZA_COLORS EZA_ICON_SPACING BAT_THEME BAT_STYLE
        set -gx STARSHIP_CONFIG $__dominio_raiz/atual/starship.toml
        test -r ~/.config/dominios/atual/fish.fish; and source ~/.config/dominios/atual/fish.fish
    end
end

# O kitty usa TERM=xterm-kitty; `kitten ssh` leva o terminfo para o servidor
if test "$TERM" = xterm-kitty; and type -q kitten
    alias ssh "kitten ssh"
end
