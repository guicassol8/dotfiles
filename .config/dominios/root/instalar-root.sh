#!/usr/bin/env bash
# Domínios: a parte que precisa de root (atualização, login SDDM, boot Plymouth, extras).
#
#   sudo ~/.config/dominios/root/instalar-root.sh              instala, perguntando antes de cada parte
#   sudo ~/.config/dominios/root/instalar-root.sh --desfazer   desfaz o que este script fez
#
# Pode rodar de novo quantas vezes quiser. Ele nunca mexe nas entradas do bootloader
# nem na linha de comando do kernel, e não reinicia o SDDM.
#
# Onde as coisas ficam:
#   /usr/share/sddm/themes/dominios       tema de login (cópia de root/sddm/dominios)
#   /etc/sddm.conf.d/10-dominios.conf     escolhe o tema de login
#   /var/lib/dominios/sddm.conf           domínio ativo; é teu, o comando `dominio` reescreve
#   /usr/share/plymouth/themes/dominios   tema de boot (cópia de root/plymouth/dominios)
#   /var/lib/dominios-root/               de root: o que havia antes, para o --desfazer
set -Eeuo pipefail

readonly TEMA=dominios
readonly SDDM_DESTINO=/usr/share/sddm/themes/$TEMA
readonly SDDM_CONF=/etc/sddm.conf.d/10-dominios.conf
readonly DADOS=/var/lib/dominios
readonly ESTADO=/var/lib/dominios-root
readonly PLY_DESTINO=/usr/share/plymouth/themes/$TEMA
readonly MARCA="# Gerado por dominios/root/instalar-root.sh. Para desfazer: instalar-root.sh --desfazer"
readonly PACOTES=(cava papirus-icon-theme playerctl grim)
readonly CHAVEIROS=(archlinux-keyring cachyos-keyring)
readonly ESPACO_MINIMO_MB=150

USUARIO=""
GRUPO=""
CASA=""
AQUI=""
RAIZ=""
PEDIR_REBOOT=0
TEMPORARIOS=()

# ------------------------------------------------------------------ conversa
if [[ -t 1 ]]; then
    N=$'\033[1m'; A=$'\033[33m'; V=$'\033[31m'; Z=$'\033[0m'
else
    N=""; A=""; V=""; Z=""
fi

titulo() { printf '\n%s== %s ==%s\n' "$N" "$1" "$Z"; }
diz()    { printf '%s\n' "$1"; }
aviso()  { printf '%sAviso:%s %s\n' "$A" "$Z" "$1" >&2; }
erro()   { printf '%sErro:%s %s\n' "$V" "$Z" "$1" >&2; }

pergunta() {
    local resposta=""
    printf '%s%s [s/N]%s ' "$N" "$1" "$Z"
    read -r resposta || true
    [[ "$resposta" =~ ^[sS]([iI][mM])?$ ]]
}

uso() {
    cat <<'EOF'
Domínios: a parte que precisa de root.

  sudo ~/.config/dominios/root/instalar-root.sh              instala (pergunta antes de cada parte)
  sudo ~/.config/dominios/root/instalar-root.sh --desfazer   desfaz o que este script fez
  ~/.config/dominios/root/instalar-root.sh --ajuda           mostra esta ajuda

Partes: 0 atualização do sistema (opcional), 1 login (SDDM), 2 boot (Plymouth), 3 extras.
EOF
}

limpa() {
    local t
    for t in "${TEMPORARIOS[@]}"; do
        if [[ -n "$t" && -e "$t" ]]; then
            rm -rf -- "$t"
        fi
    done
    return 0
}
trap limpa EXIT
trap 'erro "Algo falhou na linha $LINENO e eu parei aqui. Dá para rodar de novo sem medo, ou usar --desfazer."' ERR

# ------------------------------------------------------------------- comuns
# Copia um tema da tua pasta para o sistema: só os itens pedidos, nada de link,
# tudo como root:root 644/755. Monta ao lado do destino e imprime o caminho da pasta
# pronta (quem chama registra em TEMPORARIOS e depois usa troca_pasta).
prepara_copia() {
    local origem=$1 destino=$2
    shift 2
    local pai tmp item
    pai=$(dirname -- "$destino")
    if [[ ! -d "$pai" ]]; then
        erro "A pasta $pai não existe."
        return 1
    fi
    for item in "$@"; do
        if [[ ! -e "$origem/$item" || -L "$origem/$item" ]]; then
            erro "Falta $origem/$item (ou é um link)."
            return 1
        fi
    done
    tmp=$(mktemp -d -- "$pai/.$TEMA.XXXXXX") || return 1
    for item in "$@"; do
        if ! cp -rP --no-preserve=mode,ownership -- "$origem/$item" "$tmp/"; then
            erro "Não consegui copiar $origem/$item."
            rm -rf -- "$tmp"
            return 1
        fi
    done
    # confere a cópia, não a origem: nada de link ou arquivo especial vindo da home
    if [[ -n "$(find "$tmp" ! -type f ! -type d -print -quit)" ]]; then
        erro "Tem link simbólico ou arquivo especial em $origem. Não instalo isso como root."
        rm -rf -- "$tmp"
        return 1
    fi
    if ! { chown -R root:root -- "$tmp" \
            && find "$tmp" -type d -exec chmod 755 {} + \
            && find "$tmp" -type f -exec chmod 644 {} +; }; then
        erro "Não consegui ajustar as permissões da cópia."
        rm -rf -- "$tmp"
        return 1
    fi
    printf '%s\n' "$tmp"
}

# Põe a pasta nova no lugar da antiga.
troca_pasta() {
    local nova=$1 destino=$2
    case "$destino" in
        /usr/share/sddm/themes/"$TEMA" | /usr/share/plymouth/themes/"$TEMA") ;;
        *) erro "Destino inesperado: $destino"; return 1 ;;
    esac
    rm -rf -- "$destino.velho"
    if [[ -e "$destino" || -L "$destino" ]]; then
        mv -- "$destino" "$destino.velho"
    fi
    mv -- "$nova" "$destino"
    rm -rf -- "$destino.velho"
}

remove_pasta_do_tema() {
    local destino=$1
    case "$destino" in
        /usr/share/sddm/themes/"$TEMA" | /usr/share/plymouth/themes/"$TEMA") ;;
        *) erro "Destino inesperado: $destino"; return 1 ;;
    esac
    rm -rf -- "$destino" "$destino.velho"
}

# Regenera o tema a partir do dominios.toml atual, como o teu usuário (sem root).
regenera() {
    local alvo=$1
    if [[ -f "$RAIZ/gerar/login.py" ]] && command -v python3 >/dev/null 2>&1; then
        if runuser -u "$USUARIO" -- env HOME="$CASA" python3 "$RAIZ/gerar/login.py" "$alvo"; then
            return 0
        fi
        aviso "Não consegui regenerar o tema ($alvo). Sigo com os arquivos que já estavam prontos."
    else
        aviso "Sem gerar/login.py ou sem python3. Sigo com os arquivos que já estavam prontos."
    fi
    return 0
}

prepara_estado() {
    install -d -o root -g root -m 755 "$ESTADO"
}

# ------------------------------------------------------- 0. atualização
secao_atualizacao() {
    titulo "0. Sistema: atualização completa e pacotes que faltam (opcional)"
    local f mais_novo=0 m dias faltavam=() p
    for f in /var/lib/pacman/sync/*.db; do
        if [[ -f "$f" ]]; then
            m=$(stat -c %Y -- "$f")
            if (( m > mais_novo )); then
                mais_novo=$m
            fi
        fi
    done
    if (( mais_novo > 0 )); then
        dias=$(( ($(date +%s) - mais_novo) / 86400 ))
        diz "A base de pacotes desta máquina é de $(date -d "@$mais_novo" '+%d/%m/%Y') (há $dias dias): o sistema não é atualizado desde então."
    else
        diz "Não achei a base de pacotes sincronizada: o sistema parece nunca ter sido atualizado."
    fi
    diz "Se topar, esta parte roda:"
    diz "  1. pacman -Sy --needed ${CHAVEIROS[*]}"
    diz "     (chaveiros primeiro, senão pacote novo é recusado por assinatura desconhecida)"
    diz "  2. pacman -Syu --needed ${PACOTES[*]}"
    diz "     (atualização completa e o que os Domínios usam e ainda falta)"
    diz "O pacman mostra a lista e pede a tua confirmação antes de baixar qualquer coisa."
    diz "Depois de uma atualização desse tamanho (kernel, mesa, systemd), reinicia a máquina."
    if ! pergunta "Atualizar o sistema agora?"; then
        diz "Pulei a atualização."
        return 0
    fi
    if ! command -v pacman >/dev/null 2>&1; then
        aviso "Não achei o pacman. Pulei a atualização."
        return 0
    fi
    for p in "${PACOTES[@]}"; do
        pacman -Qq -- "$p" >/dev/null 2>&1 || faltavam+=("$p")
    done
    if ! pacman -Sy --needed "${CHAVEIROS[@]}"; then
        aviso "A atualização dos chaveiros falhou ou foi cancelada. Não segui com o resto da atualização."
        return 0
    fi
    if ! pacman -Syu --needed "${PACOTES[@]}"; then
        aviso "A atualização falhou ou foi cancelada. A lista de pacotes já foi renovada, então antes de"
        aviso "instalar qualquer outra coisa roda: sudo pacman -Syu --needed ${PACOTES[*]}"
        return 0
    fi
    # guarda só o que este script trouxe, para o --desfazer poder oferecer a remoção
    prepara_estado
    for p in "${faltavam[@]}"; do
        if pacman -Qq -- "$p" >/dev/null 2>&1 && ! grep -qxF -- "$p" "$ESTADO/pacotes-instalados" 2>/dev/null; then
            printf '%s\n' "$p" >> "$ESTADO/pacotes-instalados"
        fi
    done
    PEDIR_REBOOT=1
    diz "Sistema atualizado. Reinicia quando terminar aqui."
}

desfaz_atualizacao() {
    titulo "0. Sistema"
    local lista=() p
    diz "Atualização de sistema não tem volta por aqui (e não precisa)."
    if [[ -s "$ESTADO/pacotes-instalados" ]]; then
        while IFS= read -r p; do
            [[ "$p" =~ ^[a-z0-9@._+-]+$ ]] || continue
            if pacman -Qq -- "$p" >/dev/null 2>&1; then
                lista+=("$p")
            fi
        done < "$ESTADO/pacotes-instalados"
    fi
    if (( ${#lista[@]} == 0 )); then
        diz "Este script não instalou nenhum pacote que ainda esteja aí."
        rm -f -- "$ESTADO/pacotes-instalados"
        return 0
    fi
    diz "Pacotes que este script instalou: ${lista[*]}"
    diz "O resto do desktop dos Domínios usa esses pacotes (visualizador de áudio, ícones, controle de mídia, captura de tela)."
    if pergunta "Remover esses pacotes (pacman -Rns)?"; then
        if pacman -Rns "${lista[@]}"; then
            rm -f -- "$ESTADO/pacotes-instalados"
        else
            aviso "O pacman não removeu os pacotes. Deixei como está."
        fi
    else
        diz "Deixei os pacotes instalados."
    fi
}

# ------------------------------------------------------------- 1. SDDM
# Imprime "arquivo:valor" da última definição de [Theme] Current, na ordem em que o
# SDDM lê: /usr/lib/sddm/sddm.conf.d, /etc/sddm.conf.d e por fim /etc/sddm.conf.
sddm_tema_efetivo() {
    local arquivos=() f
    for f in /usr/lib/sddm/sddm.conf.d/*.conf /etc/sddm.conf.d/*.conf /etc/sddm.conf; do
        if [[ -f "$f" ]]; then
            arquivos+=("$f")
        fi
    done
    if (( ${#arquivos[@]} == 0 )); then
        return 0
    fi
    awk '
        /^[[:space:]]*\[/ {
            secao = $0
            gsub(/^[[:space:]]*\[|\][[:space:]]*$/, "", secao)
            next
        }
        secao == "Theme" && /^[[:space:]]*Current[[:space:]]*=/ {
            valor = $0
            sub(/^[^=]*=[[:space:]]*/, "", valor)
            sub(/[[:space:]]+$/, "", valor)
            achou = FILENAME ":" valor
        }
        END { if (achou != "") print achou }
    ' "${arquivos[@]}"
}

# Domínio ativo agora (link ~/.config/dominios/atual), ou "sistema" se não der para saber.
dominio_ativo() {
    local alvo nome
    alvo=$(readlink -- "$RAIZ/atual" 2>/dev/null || true)
    nome=${alvo##*/}
    if [[ "$nome" =~ ^[a-z0-9_-]+$ && -f "$AQUI/sddm/$TEMA/arte/$nome-fundo.jpg" ]]; then
        printf '%s\n' "$nome"
    else
        printf 'sistema\n'
    fi
}

# Grava o sddm.conf como o teu usuário, com arquivo temporário e mv: root nunca
# escreve dentro de uma pasta que é tua.
grava_dominio() {
    # além do domínio vai a ficha do jogador (jogador_nome, jogador_linha, jogador_xp),
    # que o Grimório mostra como "arquivo de jogo salvo"; o gancho 50-login a mantém em dia
    # shellcheck disable=SC2016
    runuser -u "$USUARIO" -- env HOME="$CASA" sh -c '
        tmp="$1/.sddm.conf.$$"
        { printf "[General]\ndominio=%s\n" "$2"
          python3 "$3/gerar/login.py" jogador 2>/dev/null | LC_ALL=C grep -E "^jogador_(nome|linha|xp)=[^[:cntrl:]]*$" || true
        } > "$tmp" && chmod 644 "$tmp" && mv -f "$tmp" "$1/sddm.conf"
    ' sh "$DADOS" "$1" "$RAIZ"
}

secao_sddm() {
    titulo "1. Login (SDDM)"
    local origem="$AQUI/sddm/$TEMA" nova dominio efetivo
    diz "O que esta parte faz:"
    diz "  - regenera o tema com as cores atuais do dominios.toml (como $USUARIO, sem root);"
    diz "  - copia o tema para $SDDM_DESTINO;"
    diz "  - cria $DADOS (teu, 0755) com sddm.conf dizendo qual é o domínio ativo e a ficha do"
    diz "    jogador (nome, nível, classe, título), que o Grimório mostra como arquivo de jogo salvo;"
    diz "  - liga $SDDM_DESTINO/theme.conf.user a esse arquivo,"
    diz "    assim a tela de login acompanha o comando dominio;"
    diz "  - escreve $SDDM_CONF escolhendo o tema."
    diz "Não reinicio o SDDM (isso derrubaria a tua sessão): o tema aparece no próximo logout ou boot."
    if ! pergunta "Instalar o tema de login?"; then
        diz "Pulei o login."
        return 0
    fi
    if ! command -v sddm >/dev/null 2>&1; then
        aviso "O SDDM não está instalado. Pulei o login."
        return 0
    fi
    if [[ ! -x /usr/bin/sddm-greeter-qt6 ]]; then
        aviso "Não achei /usr/bin/sddm-greeter-qt6 e o tema é Qt 6. Pulei o login."
        return 0
    fi

    regenera sddm
    if ! nova=$(prepara_copia "$origem" "$SDDM_DESTINO" Main.qml metadata.desktop theme.conf dominios.js componentes arte fontes); then
        aviso "Não instalei o tema de login."
        return 0
    fi
    TEMPORARIOS+=("$nova")
    ln -s -- "$DADOS/sddm.conf" "$nova/theme.conf.user"

    # o que valia antes, anotado uma vez só
    prepara_estado
    if [[ ! -e "$ESTADO/sddm-anterior" ]]; then
        sddm_tema_efetivo > "$ESTADO/sddm-anterior"
    fi

    install -d -o "$USUARIO" -g "$GRUPO" -m 755 "$DADOS"
    dominio=$(dominio_ativo)
    grava_dominio "$dominio"
    troca_pasta "$nova" "$SDDM_DESTINO"

    install -d -o root -g root -m 755 /etc/sddm.conf.d
    if [[ -e "$SDDM_CONF" ]] && ! grep -qF -- "$MARCA" "$SDDM_CONF"; then
        cp -- "$SDDM_CONF" "$ESTADO/10-dominios.conf.original"
        aviso "Já existia um $SDDM_CONF que não era meu. Guardei uma cópia em $ESTADO."
    fi
    printf '%s\n[Theme]\nCurrent=%s\n' "$MARCA" "$TEMA" > "$SDDM_CONF.novo"
    chmod 644 "$SDDM_CONF.novo"
    mv -f -- "$SDDM_CONF.novo" "$SDDM_CONF"

    efetivo=$(sddm_tema_efetivo)
    if [[ "${efetivo##*:}" == "$TEMA" ]]; then
        diz "Tema de login instalado. Domínio na tela de login agora: $dominio."
    else
        aviso "Instalei, mas ${efetivo%:*} define outro tema (Current=${efetivo##*:}) e ganha do meu arquivo."
        aviso "Apaga ou comenta essa linha lá para o tema dos Domínios valer."
    fi
    diz "Para ver sem sair da sessão: sddm-greeter-qt6 --test-mode --theme $SDDM_DESTINO"
}

desfaz_sddm() {
    titulo "1. Login (SDDM)"
    local anterior
    if [[ ! -e "$SDDM_CONF" && ! -e "$SDDM_DESTINO" && ! -e "$DADOS" ]]; then
        diz "Nada do login para desfazer."
        rm -f -- "$ESTADO/sddm-anterior"
        return 0
    fi
    diz "Vou apagar $SDDM_CONF, $SDDM_DESTINO e $DADOS/sddm.conf."
    diz "O SDDM volta para o tema que valia antes; não reinicio o SDDM."
    if ! pergunta "Desfazer o tema de login?"; then
        diz "Deixei o login como está."
        return 0
    fi
    if [[ -e "$SDDM_CONF" ]]; then
        if grep -qF -- "$MARCA" "$SDDM_CONF"; then
            rm -f -- "$SDDM_CONF"
            if [[ -f "$ESTADO/10-dominios.conf.original" ]]; then
                mv -f -- "$ESTADO/10-dominios.conf.original" "$SDDM_CONF"
            fi
        else
            aviso "$SDDM_CONF não foi escrito por mim. Não apaguei."
        fi
    fi
    remove_pasta_do_tema "$SDDM_DESTINO"
    if [[ -d "$DADOS" && ! -L "$DADOS" ]]; then
        rm -f -- "$DADOS/sddm.conf"
        rmdir --ignore-fail-on-non-empty -- "$DADOS" 2>/dev/null || true
    fi
    anterior=$(sddm_tema_efetivo)
    if [[ -n "${anterior##*:}" ]]; then
        diz "Login desfeito. Tema do SDDM agora: ${anterior##*:} (definido em ${anterior%:*})."
    else
        diz "Login desfeito. O SDDM volta para o tema padrão dele."
    fi
    rm -f -- "$ESTADO/sddm-anterior"
}

# ---------------------------------------------------------- 2. Plymouth
regenera_initramfs() {
    if command -v update-initramfs >/dev/null 2>&1; then
        update-initramfs          # atalho do CachyOS: aqui ele chama mkinitcpio -P
    elif command -v mkinitcpio >/dev/null 2>&1; then
        mkinitcpio -P
    else
        erro "Não achei update-initramfs nem mkinitcpio."
        return 1
    fi
}

# Caminho das imagens que os presets do mkinitcpio geram.
imagens_initramfs() {
    local preset
    for preset in /etc/mkinitcpio.d/*.preset; do
        [[ -f "$preset" ]] || continue
        (
            set +eu
            # shellcheck disable=SC1090
            . "$preset"
            for p in "${PRESETS[@]}"; do
                v="${p}_image"
                if [[ -n "${!v}" ]]; then
                    printf '%s\n' "${!v}"
                fi
            done
        ) 2>/dev/null || true
    done
}

# Confere se cada initramfs leva o tema e o que ele precisa para desenhar texto.
# (Sem fonte e sem o plugin de rótulo, o plugin "script" desta versão do Plymouth cai.)
confere_initramfs() {
    local img lista item ruim=0 viu=0
    local precisa=(
        "usr/share/plymouth/themes/$TEMA/$TEMA.plymouth"
        "usr/share/plymouth/themes/$TEMA/$TEMA.script"
        "usr/lib/plymouth/script.so"
        "usr/lib/plymouth/label-freetype.so"
        "usr/share/fonts/Plymouth.ttf"
    )
    if ! command -v lsinitcpio >/dev/null 2>&1; then
        aviso "Sem lsinitcpio: não deu para conferir o conteúdo do initramfs."
        return 0
    fi
    while IFS= read -r img; do
        [[ -f "$img" ]] || continue
        viu=1
        lista=$(lsinitcpio "$img" 2>/dev/null || true)
        for item in "${precisa[@]}"; do
            if ! grep -qF -- "$item" <<< "$lista"; then
                aviso "$img: falta $item"
                ruim=1
            fi
        done
    done < <(imagens_initramfs)
    if (( viu == 0 )); then
        aviso "Não achei as imagens dos presets para conferir (UKI ou caminho diferente)."
    fi
    return "$ruim"
}

plymouth_tema_atual() {
    plymouth-set-default-theme 2>/dev/null || true
}

# Troca o tema padrão (nome ou --reset). O plymouth-set-default-theme usa `sed -ie` e
# deixa um /etc/plymouth/plymouthd.confe para trás: apago, se ele não existia antes.
plymouth_define() {
    local sobra=/etc/plymouth/plymouthd.confe tinha=0 rc=0
    if [[ -e "$sobra" ]]; then
        tinha=1
    fi
    plymouth-set-default-theme "$1" || rc=$?
    if (( tinha == 0 )); then
        rm -f -- "$sobra"
    fi
    return "$rc"
}

# Volta o tema padrão do Plymouth para um nome dado, ou para o padrão da distribuição.
plymouth_volta_para() {
    local nome=$1
    if [[ "$nome" =~ ^[A-Za-z0-9._-]+$ && "$nome" != "$TEMA" && -f "/usr/share/plymouth/themes/$nome/$nome.plymouth" ]]; then
        plymouth_define "$nome"
    else
        plymouth_define --reset
    fi
}

secao_plymouth() {
    titulo "2. Boot (Plymouth)"
    local origem="$AQUI/plymouth/$TEMA" nova f livre atual anterior
    local itens=("$TEMA.plymouth" "$TEMA.script")
    diz "O que esta parte faz:"
    diz "  - regenera o tema com as cores atuais do dominios.toml (como $USUARIO, sem root);"
    diz "  - copia o tema para $PLY_DESTINO;"
    diz "  - anota o tema de boot atual e passa a usar o dos Domínios (plymouth-set-default-theme);"
    diz "  - RECONSTRÓI O INITRAMFS dos kernels instalados (mkinitcpio -P), porque o Plymouth"
    diz "    vai dentro dele. Leva um minuto ou dois. Depois confere se o tema entrou inteiro;"
    diz "    se algo faltar, volta sozinho para o tema anterior e reconstrói de novo."
    diz "A cada boot aparece o emblema de um dos domínios, sorteado (o do Grimório é o livro em pixel art)."
    diz "Não mexo nas entradas do bootloader nem na linha de comando do kernel."
    diz "Se um dia o boot parar na animação: no menu do systemd-boot aperta 'e', apaga a"
    diz "palavra 'splash' da linha e dá Enter. Depois roda este script com --desfazer."
    if ! pergunta "Instalar o tema de boot e reconstruir o initramfs?"; then
        diz "Pulei o boot."
        return 0
    fi
    if ! command -v plymouth-set-default-theme >/dev/null 2>&1; then
        aviso "O Plymouth não está instalado. Pulei o boot."
        return 0
    fi
    if [[ ! -f /usr/lib/plymouth/script.so || ! -f /usr/lib/plymouth/label-freetype.so ]]; then
        aviso "Faltam plugins do Plymouth (script.so ou label-freetype.so). Pulei o boot."
        return 0
    fi
    if grep -qw 'plymouth.prefer-fbcon' /proc/cmdline 2>/dev/null; then
        aviso "A linha do kernel tem plymouth.prefer-fbcon, e com ela o plugin script do Plymouth cai. Pulei o boot."
        return 0
    fi
    if [[ -x /usr/lib/plymouth/plymouth-font-file ]] && [[ -z "$(/usr/lib/plymouth/plymouth-font-file Sans 2>/dev/null || true)" ]]; then
        aviso "O Plymouth não achou uma fonte para levar no initramfs. Pulei o boot."
        return 0
    fi
    if [[ -d /boot ]]; then
        livre=$(df --output=avail -B1M /boot 2>/dev/null | awk 'NR == 2 { print $1 + 0 }' || true)
        if [[ -n "$livre" ]] && (( livre < ESPACO_MINIMO_MB )); then
            aviso "/boot só tem ${livre} MB livres (quero pelo menos ${ESPACO_MINIMO_MB}). Não reconstruo o initramfs assim. Pulei o boot."
            return 0
        fi
    fi

    regenera plymouth
    for f in "$origem"/*.png; do
        if [[ -f "$f" ]]; then
            itens+=("$(basename -- "$f")")
        fi
    done
    if ! nova=$(prepara_copia "$origem" "$PLY_DESTINO" "${itens[@]}"); then
        aviso "Não instalei o tema de boot."
        return 0
    fi
    TEMPORARIOS+=("$nova")
    troca_pasta "$nova" "$PLY_DESTINO"

    prepara_estado
    atual=$(plymouth_tema_atual)
    if [[ "$atual" != "$TEMA" && ! -e "$ESTADO/plymouth-anterior" ]]; then
        printf '%s\n' "$atual" > "$ESTADO/plymouth-anterior"
    fi
    anterior=$(cat "$ESTADO/plymouth-anterior" 2>/dev/null || true)

    if ! plymouth_define "$TEMA"; then
        aviso "O plymouth-set-default-theme recusou o tema. Não mexi no initramfs e o boot fica como estava."
        remove_pasta_do_tema "$PLY_DESTINO"
        rm -f -- "$ESTADO/plymouth-anterior"
        return 0
    fi
    diz "Tema de boot escolhido. Reconstruindo o initramfs..."
    if regenera_initramfs && confere_initramfs; then
        diz "Tema de boot instalado. Ele aparece no próximo boot."
        return 0
    fi
    aviso "O initramfs não ficou como devia. Voltando para o tema anterior (${anterior:-padrão da distribuição})."
    if ! plymouth_volta_para "$anterior"; then
        erro "Não consegui voltar o tema de boot. Roda: sudo plymouth-set-default-theme ${anterior:---reset} && sudo mkinitcpio -P"
        return 0
    fi
    if regenera_initramfs; then
        aviso "Voltei para o tema anterior e reconstruí o initramfs. O boot fica como estava antes."
    else
        erro "A reconstrução do initramfs falhou de novo. Antes de reiniciar, roda: sudo mkinitcpio -P e lê o erro."
    fi
    remove_pasta_do_tema "$PLY_DESTINO"
    rm -f -- "$ESTADO/plymouth-anterior"
}

desfaz_plymouth() {
    titulo "2. Boot (Plymouth)"
    local atual anterior
    if ! command -v plymouth-set-default-theme >/dev/null 2>&1; then
        diz "O Plymouth não está instalado. Nada do boot para desfazer."
        return 0
    fi
    atual=$(plymouth_tema_atual)
    anterior=$(cat "$ESTADO/plymouth-anterior" 2>/dev/null || true)
    if [[ "$atual" != "$TEMA" && ! -e "$PLY_DESTINO" ]]; then
        diz "Nada do boot para desfazer (tema atual: ${atual:-nenhum})."
        rm -f -- "$ESTADO/plymouth-anterior"
        return 0
    fi
    diz "Vou voltar o tema de boot para ${anterior:-o padrão da distribuição}, apagar $PLY_DESTINO"
    diz "e RECONSTRUIR O INITRAMFS (mkinitcpio -P) para o boot parar de usar o tema dos Domínios."
    if ! pergunta "Desfazer o tema de boot?"; then
        diz "Deixei o boot como está."
        return 0
    fi
    if [[ "$atual" == "$TEMA" ]]; then
        if ! plymouth_volta_para "$anterior"; then
            erro "Não consegui voltar o tema de boot. Deixei tudo como estava; roda: sudo plymouth-set-default-theme ${anterior:---reset}"
            return 0
        fi
        diz "Tema de boot agora: $(plymouth_tema_atual). Reconstruindo o initramfs..."
        if ! regenera_initramfs; then
            erro "A reconstrução do initramfs falhou. Deixei $PLY_DESTINO no lugar; roda sudo mkinitcpio -P e lê o erro."
            return 0
        fi
    else
        diz "O tema de boot atual já é outro ($atual). Só apago a pasta."
    fi
    remove_pasta_do_tema "$PLY_DESTINO"
    rm -f -- "$ESTADO/plymouth-anterior"
    diz "Boot desfeito."
}

# ------------------------------------------------------------ 3. extras
# Cada executável em root/extras.d/*.sh é oferecido um por um. A primeira linha de
# comentário (fora o #!) é a descrição. No --desfazer eles recebem --desfazer.
secao_extras() {
    local modo=${1:-} lista=() f desc i
    titulo "3. Extras"
    for f in "$AQUI"/extras.d/*.sh; do
        if [[ -f "$f" && -x "$f" ]]; then
            lista+=("$f")
        fi
    done
    if (( ${#lista[@]} == 0 )); then
        diz "Nenhum extra em $AQUI/extras.d."
        return 0
    fi
    if [[ -n "$modo" ]]; then
        # desfaz na ordem inversa
        local invertida=()
        for (( i = ${#lista[@]} - 1; i >= 0; i-- )); do
            invertida+=("${lista[i]}")
        done
        lista=("${invertida[@]}")
    fi
    diz "Cada extra roda como root. Vale abrir o arquivo antes de dizer sim."
    for f in "${lista[@]}"; do
        if [[ -n "$(find "$f" \( -perm /022 -o \( ! -user root ! -user "$USUARIO" \) \) -print -quit)" ]]; then
            aviso "$(basename -- "$f") não é teu ou pode ser alterado por outros usuários. Não rodo."
            continue
        fi
        desc=$(awk '/^#!/ { next } /^#/ { sub(/^#+[[:space:]]*/, ""); if (length($0) > 0) { print; exit } }' "$f")
        printf '\n  %s%s%s: %s\n' "$N" "$(basename -- "$f")" "$Z" "${desc:-sem descrição}"
        if [[ -n "$modo" ]]; then
            pergunta "  Desfazer este extra?" || continue
        else
            pergunta "  Rodar este extra?" || continue
        fi
        if [[ -n "$modo" ]]; then
            DOMINIOS_USUARIO="$USUARIO" DOMINIOS_CASA="$CASA" DOMINIOS_RAIZ="$RAIZ" "$f" "$modo" \
                || aviso "$(basename -- "$f") terminou com erro."
        else
            DOMINIOS_USUARIO="$USUARIO" DOMINIOS_CASA="$CASA" DOMINIOS_RAIZ="$RAIZ" "$f" \
                || aviso "$(basename -- "$f") terminou com erro."
        fi
    done
}

# ------------------------------------------------------------ principal
MODO=instalar
case "${1:-}" in
    "") ;;
    --desfazer) MODO=desfazer ;;
    -h | --ajuda | --help) uso; exit 0 ;;
    *) erro "Opção desconhecida: $1"; uso; exit 2 ;;
esac
if (( $# > 1 )); then
    erro "Só aceito uma opção por vez."
    uso
    exit 2
fi

if (( EUID != 0 )); then
    erro "Isto precisa de root. Roda assim: sudo $0${1:+ $1}"
    exit 1
fi
USUARIO=${SUDO_USER:-}
if [[ -z "$USUARIO" || "$USUARIO" == root ]] || ! id -u -- "$USUARIO" >/dev/null 2>&1; then
    erro "Roda com sudo a partir do teu usuário (não direto como root): preciso do SUDO_USER para saber de quem é a pasta dos Domínios."
    exit 1
fi
GRUPO=$(id -gn -- "$USUARIO")
CASA=$(getent passwd "$USUARIO" | cut -d: -f6)
AQUI=$(cd -- "$(dirname -- "$(readlink -f -- "${BASH_SOURCE[0]}")")" && pwd -P)
RAIZ=$(dirname -- "$AQUI")
if [[ -z "$CASA" || ! -f "$RAIZ/dominios.toml" ]]; then
    erro "Não achei o dominios.toml em $RAIZ. Este script tem de ficar em ~/.config/dominios/root/."
    exit 1
fi

if [[ "$MODO" == instalar ]]; then
    diz "${N}Domínios: instalação da parte de root${Z} (usuário: $USUARIO, pasta: $RAIZ)"
    diz "Pergunto antes de cada parte. Enter sozinho é não."
    secao_atualizacao
    secao_sddm
    secao_plymouth
    secao_extras
    titulo "Pronto"
    diz "Para desfazer tudo: sudo $AQUI/instalar-root.sh --desfazer"
    if (( PEDIR_REBOOT )); then
        diz "O sistema foi atualizado: reinicia a máquina quando puder."
    fi
else
    diz "${N}Domínios: desfazendo a parte de root${Z} (usuário: $USUARIO, pasta: $RAIZ)"
    diz "Pergunto antes de cada parte. Enter sozinho é não."
    secao_extras --desfazer
    desfaz_plymouth
    desfaz_sddm
    desfaz_atualizacao
    rmdir --ignore-fail-on-non-empty -- "$ESTADO" 2>/dev/null || true
    titulo "Pronto"
    diz "Para instalar de novo: sudo $AQUI/instalar-root.sh"
fi
