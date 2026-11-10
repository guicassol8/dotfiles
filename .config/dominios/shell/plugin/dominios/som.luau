--!nonstrict
-- Servico: quando uma notificacao chega pelo D-Bus, toca o som do dominio ativo.
-- Quem decide se toca e o `dominio tocar` (fica calado com musica tocando ou com
-- `dominio som off`). Notificacoes do proprio app "Domínios" ja tem som e sao puladas.
local aguardandoApp = false

local function linha(l)
  if string.find(l, "member=Notify", 1, true) then
    aguardandoApp = true
    return
  end
  if aguardandoApp then
    local app = string.match(l, '^%s*string "(.*)"%s*$')
    if app ~= nil then
      aguardandoApp = false
      if app ~= "Domínios" then
        noctalia.runAsync("$HOME/.config/dominios/bin/dominio tocar notificar")
      end
    end
  end
end

-- Um monitor que sobrou de uma instancia anterior do shell (reinicio, queda) e
-- encerrado antes: o padrao e ancorado, so casa com o processo do proprio monitor.
local FILTRO = [[type='method_call',interface='org.freedesktop.Notifications',member='Notify']]
noctalia.runAsync([[pkill -f "^dbus-monitor --session type='method_call',interface='org.freedesktop.Notifications',member='Notify'$"; true]], function(_res)
  noctalia.runStream('exec stdbuf -oL dbus-monitor --session "' .. FILTRO .. '"', linha)
end)

function update() end
