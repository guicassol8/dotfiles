function stm32 --description 'Kill stale CubeIDE, clear workspace lock, ensure xsettingsd, launch under X11'
    pkill -9 -f stm32cubeide
    sleep 0.5
    rm -f ~/STM32CubeIDE/workspace_*/.metadata/.lock

    if not pgrep -x xsettingsd > /dev/null
        xsettingsd &
        disown
        sleep 0.3
    end

    env GDK_BACKEND=x11 ~/st/stm32cubeide_1.19.0/stm32cubeide $argv
end
