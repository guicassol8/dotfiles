--!nonstrict
-- Janela de missoes na area de trabalho. Clicar numa linha marca ou desmarca.
local MISSAO = "$HOME/.config/dominios/bin/missao"
local titulo = noctalia.getConfig("titulo")
local cor    = noctalia.getConfig("cor")
local fonte  = noctalia.getConfig("fonte")
local estado = nil

local function render()
  local familia = (fonte ~= nil and fonte ~= "") and fonte or nil
  local filhos = {
    ui.row({ align = "center", gap = 10 }, {
      ui.glyph({ name = "exclamation-circle", size = 26, color = cor }),
      ui.label({ text = titulo, fontSize = 20, fontWeight = "bold", color = cor, fontFamily = familia }),
    }),
    ui.separator({ color = cor }),
  }
  if estado == nil then
    table.insert(filhos, ui.label({ text = "...", color = "on_surface_variant" }))
  else
    table.insert(filhos, ui.label({ text = estado.data_extenso or "", fontSize = 13, color = "on_surface_variant" }))
    for _, m in ipairs(estado.missoes) do
      table.insert(filhos, ui.row({
        key = m.id, align = "center", gap = 10, paddingV = 4, paddingH = 6, radius = 4,
        onClick = function()
          noctalia.runAsync(MISSAO .. " alternar '" .. m.id .. "' --json", function(res)
            if res.exitCode == 0 then
              local obj = noctalia.json.decode(noctalia.string.trim(res.stdout or ""))
              if type(obj) == "table" and type(obj.missoes) == "table" then estado = obj end
              noctalia.runAsync("noctalia msg plugin local/dominios:comando all refresh")
            end
            render()
          end)
        end,
      }, {
        ui.glyph({ name = m.feita and "square-check" or "square", size = 18, color = m.feita and cor or "outline_variant" }),
        ui.label({ text = m.titulo, fontSize = 15, color = m.feita and "on_surface_variant" or "on_surface", maxLines = 1 }),
      }))
    end
    if #estado.missoes == 0 then
      table.insert(filhos, ui.label({ text = "Nenhuma missão para hoje.", color = "on_surface_variant" }))
    end
    local total = estado.total or 0
    local feitas = estado.feitas or 0
    table.insert(filhos, ui.progress({ progress = total > 0 and feitas / total or 0, height = 6, radius = 3, fill = cor, track = "surface_container" }))
    table.insert(filhos, ui.row({ align = "center", justify = "space_between", gap = 24 }, {
      ui.label({ text = `{feitas}/{total}`, fontSize = 13, color = cor, fontWeight = "bold" }),
      ui.label({ text = `sequência: {estado.sequencia or 0} dia(s)`, fontSize = 12, color = "on_surface_variant" }),
    }))
  end
  desktopWidget.render(ui.column({ gap = 9, minWidth = 400, padding = 22, radius = 3, border = cor, borderWidth = 1.5, fill = "surface/0.58" }, filhos))
end

local function carregar()
  noctalia.runAsync(MISSAO .. " lista --json", function(res)
    if res.exitCode == 0 then
      local obj = noctalia.json.decode(noctalia.string.trim(res.stdout or ""))
      if type(obj) == "table" and type(obj.missoes) == "table" then estado = obj end
    end
    render()
  end)
end

noctalia.setUpdateInterval(60000)

function update() carregar() end

function onIpc(evento, _carga)
  if evento == "refresh" or evento == "atualizar" then carregar() end
end
