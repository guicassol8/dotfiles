# Dominios: cores, prompt e saudacao do terminal.
# Carregado pela ultima linha de ~/.config/fish/config.fish.
status is-interactive; or return

set -g __dominio_raiz ~/.config/dominios
test -r $__dominio_raiz/atual/fish.fish; and source $__dominio_raiz/atual/fish.fish
set -g __dominio_visto (readlink $__dominio_raiz/atual 2>/dev/null)

if type -q starship
    set -gx STARSHIP_CONFIG $__dominio_raiz/atual/starship.toml
    starship init fish | source
end

# Saudacao: ficha do dominio. No kitty o logo e imagem; nos outros, braille.
# Dominio com [modo] saudacao = false (o Neutro) abre o terminal limpo.
function fish_greeting
    test "$__dominio_saudacao" = false; and return
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
        test -r ~/.config/dominios/atual/fish.fish; and source ~/.config/dominios/atual/fish.fish
    end
end

# O kitty usa TERM=xterm-kitty; `kitten ssh` leva o terminfo para o servidor
if test "$TERM" = xterm-kitty; and type -q kitten
    alias ssh "kitten ssh"
end
