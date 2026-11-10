--!nonstrict
-- Painel do HUD de agentes: sessoes do Claude Code, memoria e pressao.
-- Os dados vem de `agentes --json` (~/.config/dominios/bin/agentes).
local AGENTES = "$HOME/.config/dominios/bin/agentes"
local dados = nil
local aviso = "carregando..."
local aberto = false
local ocupado = false

local function gib(mb)
  return string.gsub(string.format("%.1f", (mb or 0) / 1024), "%.", ",") .. " GiB"
end

local function render()
  local filhos = {
    ui.row({ align = "center", gap = 10 }, {
      ui.glyph({ name = "robot", size = 24, color = "primary" }),
      ui.label({ text = "AGENTES", fontSize = 17, fontWeight = "bold", color = "primary", flexGrow = 1 }),
      ui.button({ glyph = "x", variant = "ghost", controlSize = "sm", onClick = "fechar" }),
    }),
    ui.separator({}),
  }
  if dados == nil then
    table.insert(filhos, ui.label({ text = aviso, color = "on_surface_variant", maxLines = 4 }))
    table.insert(filhos, ui.spacer({ flexGrow = 1 }))
  else
    local total = math.max(1, dados.total_mb or 1)
    local usado = total - (dados.disponivel_mb or 0)
    local cor = "primary"
    if dados.classe == "aviso" then cor = "secondary" elseif dados.classe == "critico" then cor = "error" end
    table.insert(filhos, ui.column({ gap = 6 }, {
      ui.row({ justify = "space_between" }, {
        ui.label({ text = "Memória", fontSize = 13, color = "on_surface_variant" }),
        ui.label({ text = `{gib(usado)} de {gib(total)}  ·  livre {gib(dados.disponivel_mb)}`, fontSize = 13 }),
      }),
      ui.progress({ progress = math.min(1, usado / total), height = 10, radius = 5, fill = cor, track = "surface_container" }),
      ui.row({ justify = "space_between" }, {
        ui.label({ text = `swap {gib(dados.swap_usado_mb)} de {gib(dados.swap_total_mb)}`, fontSize = 12, color = "on_surface_variant" }),
        ui.label({ text = "pressão " .. string.gsub(string.format("%.1f", dados.pressao or 0), "%.", ","), fontSize = 12, color = cor }),
      }),
    }))
    table.insert(filhos, ui.separator({}))
    local linhas = {}
    for _, s in ipairs(dados.sessoes or {}) do
      table.insert(linhas, ui.row({ key = tostring(s.pid), align = "center", gap = 10, paddingV = 7, paddingH = 10, radius = 8, fill = "surface_container/0.55" }, {
        ui.glyph({ name = "terminal-2", size = 16, color = "primary" }),
        ui.label({ text = tostring(s.projeto or "?"), fontSize = 14, flexGrow = 1, maxLines = 1 }),
        ui.label({ text = tostring(s.tempo or ""), fontSize = 12, color = "on_surface_variant" }),
        ui.label({ text = gib(s.mem_mb), fontSize = 13, color = "tertiary" }),
      }))
    end
    if #linhas == 0 then
      table.insert(linhas, ui.label({ text = "Nenhuma sessão do Claude Code rodando.", color = "on_surface_variant" }))
    end
    table.insert(filhos, ui.scroll({ flexGrow = 1, gap = 6 }, linhas))
    table.insert(filhos, ui.label({ text = `{#(dados.sessoes or {})} sessão(ões)  ·  {gib(dados.total_mem_mb)} no total`, fontSize = 12, color = "on_surface_variant" }))
  end
  panel.render(ui.column({ flexGrow = 1, gap = 12 }, filhos))
end

local function carregar()
  if ocupado then return end
  ocupado = true
  local aceito = noctalia.runAsync(AGENTES .. " --json", function(res)
    ocupado = false
    if res.exitCode == 0 then
      local obj = noctalia.json.decode(noctalia.string.trim(res.stdout or ""))
      if type(obj) == "table" then dados = obj else dados = nil; aviso = "resposta inesperada do comando agentes" end
    else
      dados = nil
      aviso = "o comando agentes falhou: " .. noctalia.string.trim(res.stderr or "")
    end
    if aberto then render() end
  end)
  if not aceito then ocupado = false end
end

noctalia.setUpdateInterval(2000)

function update()
  if aberto then carregar() end   -- so consulta com o painel aberto
end

function fechar() panel.close() end

function onOpen(_contexto)
  aberto = true
  render()
  carregar()
end

function onClose()
  aberto = false
end
