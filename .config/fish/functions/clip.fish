function clip --wraps='xclip -selection clipboard'
    if test (count $argv) -gt 0
        wl-copy < $argv[1]
    else
        wl-copy
    end
end
