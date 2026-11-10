source /usr/share/cachyos-fish-config/cachyos-config.fish

# overwrite greeting
# potentially disabling fastfetch
#function fish_greeting
#    # smth smth
#end
set -gx SSH_AUTH_SOCK ~/.ssh/agent.sock
set -gx SSH_AUTH_SOCK ~/.ssh/agent.sock

# The next line updates PATH for the Google Cloud SDK.
if [ -f '/home/guicassol/google-cloud-sdk/path.fish.inc' ]; . '/home/guicassol/google-cloud-sdk/path.fish.inc'; end

# >>> dominios >>>
test -r /home/guicassol/.config/dominios/fish/init.fish; and source /home/guicassol/.config/dominios/fish/init.fish
# <<< dominios <<<
