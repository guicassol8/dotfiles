--!nonstrict
-- Painel das missoes diarias. Le e altera o estado pelo comando `missao`
-- (~/.config/dominios/bin/missao), que e a fonte da verdade.
local MISSAO = "$HOME/.config/dominios/bin/missao"
local estado = nil
local aviso = "carregando..."

local function atualizaBarra()
  noctalia.runAsync("noctalia msg plugin local/dominios:comando all refresh")
end

local function recebe(res)
  if res.exitCode ~= 0 then
    estado = nil
    aviso = "o comando missao falhou: " .. noctalia.string.trim(res.stderr or "")
    return false
  end
  local obj = noctalia.json.decode(noctalia.string.trim(res.stdout or ""))
  if type(obj) ~= "table" or type(obj.missoes) ~= "table" then
    estado = nil
    aviso = "resposta inesperada do comando missao"
    return false
  end
  estado = obj
  return true
end

local render

local function carregar()
  noctalia.runAsync(MISSAO .. " lista --json", function(res)
    recebe(res)
    render()
  end)
end

local function alternar(id)
  noctalia.runAsync(MISSAO .. " alternar '" .. id .. "' --json", function(res)
    if recebe(res) then atualizaBarra() end
    render()
  end)
end

render = function()
  local filhos = {
    ui.row({ align = "center", gap = 10 }, {
      ui.glyph({ name = "swords", size = 24, color = "primary" }),
      ui.column({ gap = 0, flexGrow = 1 }, {
        ui.label({ text = "MISSÕES DIÁRIAS", fontSize = 17, fontWeight = "bold", color = "primary" }),
        ui.label({ text = estado and estado.data_extenso or "", fontSize = 12, color = "on_surface_variant" }),
      }),
      ui.button({ glyph = "x", variant = "ghost", controlSize = "sm", onClick = "fechar" }),
    }),
    ui.separator({}),
  }
  if estado == nil then
    table.insert(filhos, ui.label({ text = aviso, color = "on_surface_variant", maxLines = 4 }))
    table.insert(filhos, ui.spacer({ flexGrow = 1 }))
  else
    local linhas = {}
    for _, m in ipairs(estado.missoes) do
      table.insert(linhas, ui.row({
        key = m.id, align = "center", gap = 10, paddingV = 8, paddingH = 10, radius = 8,
        fill = m.feita and "primary/0.12" or "surface_container/0.55",
        onClick = function() alternar(m.id) end,
      }, {
        ui.glyph({ name = m.feita and "square-check" or "square", size = 18, color = m.feita and "primary" or "outline_variant" }),
        ui.label({ text = m.titulo, fontSize = 14, color = m.feita and "on_surface_variant" or "on_surface", flexGrow = 1, maxLines = 1 }),
      }))
    end
    if #linhas == 0 then
      table.insert(linhas, ui.label({ text = "Nenhuma missão para hoje.", color = "on_surface_variant" }))
    end
    table.insert(filhos, ui.scroll({ flexGrow = 1, gap = 6 }, linhas))
    local total = estado.total or 0
    local feitas = estado.feitas or 0
    table.insert(filhos, ui.progress({ progress = total > 0 and feitas / total or 0, height = 8, radius = 4, fill = "primary", track = "surface_container" }))
    table.insert(filhos, ui.row({ align = "center", justify = "space_between" }, {
      ui.label({ text = `{feitas} de {total} concluídas`, fontSize = 12, color = "on_surface_variant" }),
      ui.label({ text = `sequência: {estado.sequencia or 0}  ·  recorde: {estado.melhor or 0}`, fontSize = 12, color = "tertiary" }),
    }))
  end
  panel.render(ui.column({ flexGrow = 1, gap = 12 }, filhos))
end

function fechar() panel.close() end

function onOpen(_contexto)
  render()
  carregar()
end
