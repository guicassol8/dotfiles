function stm32 --wraps='~/st/stm32cubeide_1.19.0/stm32cubeide' --wraps='env GDK_BACKEND=x11 ~/st/stm32cubeide_1.19.0/stm32cubeide' --description 'alias stm32=env GDK_BACKEND=x11 ~/st/stm32cubeide_1.19.0/stm32cubeide'
    env GDK_BACKEND=x11 ~/st/stm32cubeide_1.19.0/stm32cubeide $argv
end
