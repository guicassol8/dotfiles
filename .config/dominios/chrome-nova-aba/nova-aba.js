// Dominios: nova aba. Le dominio.json e papel.png desta pasta (o comando `dominio`
// copia os dois a cada troca) e transforma os tokens em variaveis CSS.
// Sem framework, sem rede: tudo e arquivo local.
"use strict";

// Por padrao o Chrome deixa o cursor na barra de enderecos quando abre uma aba
// nova, e digitar ali ja busca. Com true, a pagina se recarrega uma vez para
// roubar o foco para a busca daqui; o preco e a barra mostrar o endereco da extensao.
const FOCO_NA_PAGINA = false;

const HEX = /^#[0-9a-f]{6}$/i;
const raiz = document.documentElement;
let aplicado = "";

if (FOCO_NA_PAGINA && globalThis.chrome?.runtime?.id && location.search !== "?foco") {
  location.replace(location.pathname + "?foco");
}

function le(url) {
  // XHR em vez de fetch: funciona igual na extensao e aberto como arquivo solto
  return new Promise((ok, falha) => {
    const x = new XMLHttpRequest();
    x.open("GET", url);
    x.onload = () => {
      try { ok([JSON.parse(x.responseText), x.responseText]); } catch (e) { falha(e); }
    };
    x.onerror = () => falha(new Error("nao deu para ler " + url));
    x.send();
  });
}

function aplica(t, bruto) {
  if (bruto === aplicado) return;
  const novoPapel = aplicado !== "";
  aplicado = bruto;
  const css = raiz.style;
  for (const grupo of ["cor", "ansi"]) {
    for (const [k, v] of Object.entries(t[grupo] || {})) {
      if (HEX.test(v)) css.setProperty(`--${grupo}-${k.replaceAll("_", "-")}`, v);
    }
  }
  for (const [k, v] of Object.entries(t.fonte || {})) {
    if (typeof v === "string") css.setProperty(`--fonte-${k.replaceAll("_", "-")}`, JSON.stringify(v));
  }
  for (const k of ["raio", "borda", "vaos"]) {
    const v = t.forma?.[k];
    if (typeof v === "number") css.setProperty(`--forma-${k}`, v + "px");
  }
  raiz.dataset.dominio = t.dominio || "";
  const texto = (id, v) => { const e = document.getElementById(id); if (e) e.textContent = v || ""; };
  texto("rotulo", t.rotulo);
  // rotulo em kanji: pede as formas japonesas a fonte de reserva
  document.getElementById("rotulo")?.toggleAttribute("lang", false);
  if (/[\u3040-\u30ff\u4e00-\u9fff]/.test(t.rotulo || "")) document.getElementById("rotulo")?.setAttribute("lang", "ja");
  texto("lema", t.lema);
  // modo apresentacao (dominio Neutro): texto da busca sem giria
  const q = document.getElementById("q");
  if (q) q.placeholder = t.modo?.apresentacao ? "Pesquisar ou digitar um endereço" : "Busca aí ou digita um endereço";
  papel(t.dominio || "", novoPapel);
  tema = t;
  raiz.classList.toggle("grim", t.dominio === "grimorio");
  document.getElementById(t.dominio === "grimorio" ? "g-q" : "q")?.focus();
}

// ---- grimorio: estado.json (elemento, nivel, oficios, frase) e cena.png da pasta ----
let tema = {};
let estado = null;
let cenaAtual = "";
const NOMES = { fogo: "Fogo", agua: "Água", terra: "Terra", vento: "Vento", eletricidade: "Eletricidade", "mana-pura": "Mana pura" };
const el$ = id => document.getElementById(id);

function carregaEstado() {
  if (tema.dominio !== "grimorio") return Promise.resolve();
  return le("estado.json").then(([e]) => { estado = e; }, () => { estado = null; }).then(grimorio);
}

function grimorio() {
  const e = estado || {};
  const elemento = NOMES[e.elemento] ? e.elemento : "mana-pura";
  const cor = tema.elementos?.[elemento];
  if (HEX.test(cor || "")) raiz.style.setProperty("--el", cor);
  const g = el$("grim");
  if (g) g.dataset.elemento = elemento;
  const num = v => (typeof v === "number" && isFinite(v) ? v : null);
  const nivel = num(e.nivel), xp = num(e.xp), prox = num(e.xp_proximo);
  const feitos = num(e.oficios_feitos), total = num(e.oficios_total);
  const t = (id, v) => { const x = el$(id); if (x) x.textContent = v; };
  t("g-nivel", nivel ?? "--");
  const fmt = n => n.toLocaleString("pt-BR");
  t("g-xp-t", xp != null && prox ? `${fmt(xp)} / ${fmt(prox)} XP` : "sem dados");
  t("g-titulo", e.titulo || "");
  el$("g-xp")?.style.setProperty("--v", xp != null && prox ? Math.min(100, Math.round(xp / prox * 100)) + "%" : "0%");
  t("g-of-n", feitos != null && total != null ? `${feitos}/${total}` : "--");
  t("g-of-t", feitos == null || total == null ? "sem dados" : feitos >= total && total > 0 ? "Todos os ofícios cumpridos" : `Faltam ${total - feitos} para fechar o dia`);
  const pips = el$("g-pips");
  if (pips) {
    pips.replaceChildren(...Array.from({ length: Math.min(total || 0, 16) }, (_, i) => {
      const p = document.createElement("i");
      if (i < feitos) p.className = "feito";
      return p;
    }));
  }
  t("g-el-nome", NOMES[elemento]);
  t("g-motivo", e.motivo || "");
  const fr = el$("g-frase");
  if (fr) { fr.hidden = !e.frase; t("g-frase-t", e.frase || ""); t("g-frase-a", e.autor || ""); }
  let quando = "";
  if (e.atualizado) {
    const d = new Date(e.atualizado);
    if (!isNaN(d)) quando = "Atualizado às " + d.toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" });
  }
  t("g-atualizado", quando);
  cena(elemento, e.atualizado || "");
  particulas(elemento);
  saudacao();
}

function cena(elemento, versao) {
  const chave = elemento + "|" + versao;
  if (chave === cenaAtual) return;
  cenaAtual = chave;
  const div = el$("g-cena");
  const tenta = urls => {
    if (!urls.length) { div.classList.remove("visivel"); return; }
    const img = new Image();
    img.onload = () => { div.style.backgroundImage = `url("${urls[0]}")`; div.classList.add("visivel"); };
    img.onerror = () => tenta(urls.slice(1));
    img.src = urls[0];
  };
  tenta(["cena.png?v=" + encodeURIComponent(chave), "papel.png?d=grimorio"]);
}

// poucas particulas, so CSS (transform e opacity); nada de laco em JS
let particulasDe = "";
function particulas(elemento) {
  if (particulasDe === elemento) return;
  particulasDe = elemento;
  const caixa = el$("g-particulas");
  if (!caixa) return;
  caixa.className = "g-particulas " + elemento;
  const lento = { agua: 1.5, "mana-pura": 1.3, terra: 1.4, fogo: 0.8 }[elemento] || 1;
  const n = elemento === "eletricidade" ? 7 : 16;
  const r = (a, b) => a + Math.random() * (b - a);
  const filhos = [];
  for (let i = 0; i < n; i++) {
    const p = document.createElement("i");
    const s = p.style;
    s.setProperty("--x", r(2, 98).toFixed(1) + "%");
    s.setProperty("--y", r(8, 80).toFixed(1) + "%");
    s.setProperty("--t", (Math.random() < 0.3 ? 6 : 3) + "px");
    s.setProperty("--d", (r(11, 22) * lento).toFixed(1) + "s");
    s.setProperty("--a", (-r(0, 22)).toFixed(1) + "s");
    s.setProperty("--dx", (r(-6, 6) | 0) + "vw");
    filhos.push(p);
  }
  caixa.replaceChildren(...filhos);
}

function saudacao() {
  const h = new Date().getHours();
  const s = h >= 5 && h < 12 ? "Bom dia" : h >= 12 && h < 18 ? "Boa tarde" : "Boa noite";
  const x = el$("g-saudacao");
  if (x) x.textContent = s + ", conjurador";
}

function papel(chave, trocou) {
  const div = document.getElementById("papel");
  if (!div) return;
  // a chave na URL evita imagem velha em cache quando o dominio muda com a aba aberta
  const url = "papel.png?d=" + encodeURIComponent(chave) + (trocou ? "-" + Date.now() : "");
  const img = new Image();
  img.onload = () => {
    div.style.backgroundImage = `url("${url}")`;
    div.classList.add("visivel");
  };
  img.onerror = () => div.classList.remove("visivel");
  img.src = url;
}

function relogio() {
  const agora = new Date();
  const h = agora.toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" });
  const d = agora.toLocaleDateString("pt-BR", { weekday: "long", day: "numeric", month: "long" });
  for (const [id, v] of [["relogio", h], ["g-relogio", h], ["data", d], ["g-data", d]]) {
    const x = document.getElementById(id);
    if (x) x.textContent = v;
  }
  saudacao();
  setTimeout(relogio, 60000 - (agora.getSeconds() * 1000 + agora.getMilliseconds()) + 20);
}

function busca(ev) {
  ev.preventDefault();
  const q = ev.currentTarget.querySelector("input").value.trim();
  if (!q) return;
  if (/^[a-z][a-z0-9+.-]*:\/\//i.test(q) || /^(localhost|[\w-]+(\.[\w-]+)+)(:\d+)?(\/\S*)?$/i.test(q)) {
    location.assign(/^[a-z][a-z0-9+.-]*:\/\//i.test(q) ? q : "https://" + q);
  } else if (globalThis.chrome?.search?.query) {
    chrome.search.query({ text: q, disposition: "CURRENT_TAB" });   // buscador padrao do navegador
  } else {
    console.info("dominios: fora da extensao nao tem chrome.search; busca ignorada:", q);
  }
}

function carrega() {
  return le("dominio.json")
    .then(([t, bruto]) => aplica(t, bruto))
    .then(carregaEstado)
    .catch(e => console.warn("dominios:", e.message))
    .finally(() => raiz.classList.add("pronto"));
}

document.addEventListener("DOMContentLoaded", () => {
  relogio();
  carrega();
  for (const [f, i] of [["busca", "q"], ["g-busca", "g-q"]]) {
    const campo = document.getElementById(i);
    document.getElementById(f).addEventListener("submit", busca);
    campo.addEventListener("keydown", ev => { if (ev.key === "Escape") campo.value = ""; });
  }
  // foca o campo que esta visivel (o do grimorio so aparece depois do dominio.json)
  document.getElementById("q").focus();
});

// dominio trocado com a aba ja aberta: confere de novo quando ela volta a aparecer
document.addEventListener("visibilitychange", () => { if (!document.hidden) carrega(); });
