#!/bin/bash
# Audio: desliga na origem a deteccao falsa do microfone de headset (ALC256, pino 0x19)
#
# Causa (medida em 2026-11-10): neste Acer A515-45 o codec ALC256 alterna o controle
# "Headset Mic Jack" umas 5 vezes por segundo enquanto toca som. O driver trata o pino
# 0x19 como tomada com deteccao de presenca (pincfg 0x03a1103c), mas o pino flutua.
# Cada alternancia fazia o WirePlumber reprocessar as rotas ate estourar a memoria e
# ser morto, e o audio (e o Bluetooth) resetava.
#
# O contorno no PipeWire ja esta ativo em ~/.config/alsa-card-profile/. Este script
# resolve no kernel: declara o pino como "sem deteccao de presenca" (0x03a1113c), o
# que para os eventos de vez. O microfone de headset P2 continua existindo, so nao
# e detectado sozinho. Vale a partir do proximo boot.
#
# Uso: sudo ./10-audio-alc256.sh            aplica
#      sudo ./10-audio-alc256.sh --desfazer  remove
set -euo pipefail
FW=/usr/lib/firmware/acer-a515-45-alc256.fw
CONF=/etc/modprobe.d/acer-a515-45-alc256.conf

[ "$(id -u)" -eq 0 ] || { echo "Rode com sudo."; exit 1; }

if [ "${1:-}" = "--desfazer" ]; then
    rm -f "$FW" "$CONF"
    echo "Removido. Reinicie para o codec voltar ao padrao do driver."
    exit 0
fi

codec=$(grep -l "Realtek ALC256" /proc/asound/card*/codec#* 2>/dev/null | head -1 || true)
if [ -z "$codec" ] || ! grep -q "0x1025152b" "$codec"; then
    echo "Nao achei o codec ALC256 com Subsystem Id 0x1025152b. Nada foi alterado."
    exit 1
fi

cat > "$FW" <<'PATCH'
[codec]
0x10ec0256 0x1025152b 0

[pincfg]
0x19 0x03a1113c
PATCH
chmod 644 "$FW"

# O mesmo arquivo vale para as duas placas (HDMI e analogica): so o codec que
# casar com a linha [codec] recebe o ajuste.
cat > "$CONF" <<'MODPROBE'
# Acer A515-45: pino 0x19 do ALC256 sem deteccao de presenca (ver ~/.config/dominios/root/extras.d/10-audio-alc256.sh)
options snd-hda-intel patch=acer-a515-45-alc256.fw,acer-a515-45-alc256.fw
MODPROBE
chmod 644 "$CONF"

echo "Aplicado. Depois de reiniciar, confira com:"
echo "  amixer -c1 contents | grep -i 'Headset Mic'     (deve aparecer 'Phantom Jack')"
echo "  som-diagnostico                                (eventos do jack devem ser 0)"
echo "Se o audio ficar estranho, desfaca com: sudo $0 --desfazer"
