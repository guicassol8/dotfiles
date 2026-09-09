function stm32cubeide --description 'Kill stale CubeIDE processes and launch clean under X11'
    pkill -9 -f stm32cubeide
    env GDK_BACKEND=x11 /opt/st/stm32cubeide_1.19.0/stm32cubeide $argv
end
