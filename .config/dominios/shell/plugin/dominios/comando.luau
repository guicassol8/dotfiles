--!nonstrict
-- Widget de barra: roda um comando de tempos em tempos e mostra a saida.
-- Saida aceita: texto puro (linha 1 = rotulo, resto = dica) ou um objeto JSON com
-- texto, texto_curto (barra vertical), dica, glifo (nome Tabler) e cor (papel ou #hex).
local comando   = noctalia.getConfig("command")
local intervalo = noctalia.getConfig("interval")
local glifo     = noctalia.getConfig("glyph")
local corTexto  = noctalia.getConfig("text_color")
local aoClicar  = noctalia.getConfig("click_command")
local aoDireito = noctalia.getConfig("right_command")
local esconder  = noctalia.getConfig("hide_when_empty")
local ocupado   = false
local vertical  = false

local function aplica(saida)
  saida = noctalia.string.trim(saida or "")
  local texto, dica, g, c = saida, nil, glifo, corTexto
  if string.sub(saida, 1, 1) == "{" then
    local obj = noctalia.json.decode(saida)
    if type(obj) == "table" then
      texto = tostring(obj.texto or obj.text or "")
      if vertical and obj.texto_curto ~= nil then texto = tostring(obj.texto_curto) end
      dica = obj.dica or obj.tooltip
      g = obj.glifo or obj.glyph or g
      -- com glifo proprio do shell, tira o glifo Nerd Font que o comando poe no inicio do texto
      if (obj.glifo or obj.glyph) ~= nil then
        texto = string.gsub(texto, "^[\xEE-\xF4][\x80-\xBF]+%s*", "")
      end
      c = obj.cor or obj.color or c
    end
  else
    local nl = string.find(saida, "\n", 1, true)
    if nl then
      texto = string.sub(saida, 1, nl - 1)
      dica = string.sub(saida, nl + 1)
    end
  end
  if g ~= nil and g ~= "" then barWidget.setGlyph(g) end
  barWidget.setText(texto)
  if c ~= nil and c ~= "" then
    barWidget.setColor(c, "script")
    barWidget.setGlyphColor(c, "script")
  end
  if dica ~= nil and dica ~= "" then barWidget.setTooltip(dica) end
  barWidget.setVisible(not (esconder and texto == ""))
end

local function atualiza()
  if ocupado or comando == nil or comando == "" then return end
  vertical = barWidget.isVertical()
  ocupado = true
  local aceito = noctalia.runAsync(comando, function(res)
    ocupado = false
    if res.exitCode == 0 then
      aplica(res.stdout)
    else
      aplica('{"texto":"!","cor":"error","dica":"o comando falhou"}')
    end
  end)
  if not aceito then ocupado = false end
end

noctalia.setUpdateInterval(math.max(1, intervalo or 10) * 1000)

function update() atualiza() end

function onClick()
  if aoClicar ~= nil and aoClicar ~= "" then noctalia.runAsync(aoClicar) end
end

function onRightClick()
  if aoDireito ~= nil and aoDireito ~= "" then noctalia.runAsync(aoDireito) end
end

function onIpc(evento, carga)
  if evento == "refresh" or evento == "atualizar" then
    atualiza()
  elseif evento == "set" then
    aplica(carga)
  end
end
