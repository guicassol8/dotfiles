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
  const hora = document.getElementById("relogio");
  const data = document.getElementById("data");
  if (hora) hora.textContent = agora.toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" });
  if (data) data.textContent = agora.toLocaleDateString("pt-BR", { weekday: "long", day: "numeric", month: "long" });
  setTimeout(relogio, 60000 - (agora.getSeconds() * 1000 + agora.getMilliseconds()) + 20);
}

function busca(ev) {
  ev.preventDefault();
  const q = document.getElementById("q").value.trim();
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
    .catch(e => console.warn("dominios:", e.message))
    .finally(() => raiz.classList.add("pronto"));
}

document.addEventListener("DOMContentLoaded", () => {
  relogio();
  carrega();
  const q = document.getElementById("q");
  document.getElementById("busca").addEventListener("submit", busca);
  q.addEventListener("keydown", ev => { if (ev.key === "Escape") q.value = ""; });
  q.focus();
});

// dominio trocado com a aba ja aberta: confere de novo quando ela volta a aparecer
document.addEventListener("visibilitychange", () => { if (!document.hidden) carrega(); });
