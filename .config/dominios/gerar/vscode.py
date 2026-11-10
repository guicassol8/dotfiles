#!/usr/bin/env python3
"""Empacota os temas do VS Code como extensao local e instala.

  gerar/vscode.py                 monta o .vsix, instala e liga os temas ao _build/
  gerar/vscode.py --montar        so monta o .vsix e mostra o caminho
  gerar/vscode.py --ligar         so refaz os links dos temas na extensao instalada
  gerar/vscode.py --pasta <dir>   usa outra pasta de extensoes (para testar)

A extensao (dominios.dominios-tema) contribui um tema por dominio, com o rotulo
"Domínio: <nome>", o mesmo texto que bin/dominio grava em workbench.colorTheme.
Uma pasta solta em ~/.vscode/extensions nao e registrada pelo VS Code atual (ele
so confia no extensions.json), por isso a instalacao passa por um .vsix e por
`code --install-extension`.

Depois de instalar, cada themes/<dominio>.json da extensao vira um link para
_build/<dominio>/vscode-tema.json: `dominio construir` ja atualiza o VS Code, e
como os temas levam `_watch`, a janela aberta recarrega as cores na hora.
"""
import json
import os
import shutil
import subprocess
import sys
import tomllib
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape, quoteattr

RAIZ = Path(__file__).resolve().parent.parent
BUILD = RAIZ / "_build"
TOKENS = tomllib.loads((RAIZ / "dominios.toml").read_text())
ORDEM = TOKENS["ordem"]["lista"] + TOKENS["ordem"].get("extras", [])   # todos, inclusive fora do ciclo
EDITORA, NOME, VERSAO = "dominios", "dominios-tema", "1.0.0"
IDENT = f"{EDITORA}.{NOME}"
TEMA = "vscode-tema.json"
CACHE = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "dominios"
DESCRICAO = "Os domínios do desktop como temas do VS Code. Gerado por ~/.config/dominios/gerar/vscode.py."


def manifesto():
    return {
        "name": NOME,
        "displayName": "Domínios",
        "description": DESCRICAO,
        "version": VERSAO,
        "publisher": EDITORA,
        "engines": {"vscode": "^1.70.0"},
        "categories": ["Themes"],
        "contributes": {"themes": [
            {"label": f"Domínio: {TOKENS[d]['nome']}", "uiTheme": "vs-dark",
             "path": f"./themes/{d}.json", "_watch": True}
            for d in ORDEM]},
    }


def vsixmanifest():
    return f"""<?xml version="1.0" encoding="utf-8"?>
<PackageManifest Version="2.0.0" xmlns="http://schemas.microsoft.com/developer/vsx-schema/2011">
  <Metadata>
    <Identity Language="pt-BR" Id={quoteattr(NOME)} Version={quoteattr(VERSAO)} Publisher={quoteattr(EDITORA)}/>
    <DisplayName>Domínios</DisplayName>
    <Description xml:space="preserve">{escape(DESCRICAO)}</Description>
    <Tags>theme,color-theme</Tags>
    <Categories>Themes</Categories>
    <GalleryFlags>Public</GalleryFlags>
    <Properties>
      <Property Id="Microsoft.VisualStudio.Code.Engine" Value="^1.70.0"/>
      <Property Id="Microsoft.VisualStudio.Code.ExtensionDependencies" Value=""/>
      <Property Id="Microsoft.VisualStudio.Code.ExtensionPack" Value=""/>
      <Property Id="Microsoft.VisualStudio.Code.ExtensionKind" Value="ui,workspace"/>
      <Property Id="Microsoft.VisualStudio.Code.LocalizedLanguages" Value=""/>
    </Properties>
  </Metadata>
  <Installation>
    <InstallationTarget Id="Microsoft.VisualStudio.Code"/>
  </Installation>
  <Dependencies/>
  <Assets>
    <Asset Type="Microsoft.VisualStudio.Code.Manifest" Path="extension/package.json" Addressable="true"/>
    <Asset Type="Microsoft.VisualStudio.Services.Content.Details" Path="extension/README.md" Addressable="true"/>
  </Assets>
</PackageManifest>
"""


TIPOS = """<?xml version="1.0" encoding="utf-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension=".json" ContentType="application/json"/><Default Extension=".md" ContentType="text/markdown"/><Default Extension=".vsixmanifest" ContentType="text/xml"/></Types>
"""

LEIAME = """# Domínios

Um tema por domínio do desktop. Quem escolhe o tema é o comando `dominio`:
a cada troca ele grava `workbench.colorTheme` no settings.json do VS Code.

As cores vêm de `~/.config/dominios/dominios.toml` pelo modelo
`modelos/vscode-tema.json`. Para mudar algo, edite lá e rode `dominio construir`.
Para reinstalar a extensão (por exemplo depois de criar um domínio novo), rode
`python3 ~/.config/dominios/gerar/vscode.py`.
"""


def montar():
    faltando = [d for d in ORDEM if not (BUILD / d / TEMA).exists()]
    if faltando:
        sys.exit(f"vscode: falta {TEMA} em _build/ para {', '.join(faltando)}. Rode `dominio construir`.")
    CACHE.mkdir(parents=True, exist_ok=True)
    saida = CACHE / f"{NOME}-{VERSAO}.vsix"
    with zipfile.ZipFile(saida, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", TIPOS)
        z.writestr("extension.vsixmanifest", vsixmanifest())
        z.writestr("extension/package.json", json.dumps(manifesto(), ensure_ascii=False, indent=2) + "\n")
        z.writestr("extension/README.md", LEIAME)
        for d in ORDEM:
            z.write(BUILD / d / TEMA, f"extension/themes/{d}.json")
    return saida


def pasta_instalada(extensoes):
    """Pasta da extensao segundo o extensions.json do VS Code (ou a mais nova que casar)."""
    try:
        for item in json.loads((extensoes / "extensions.json").read_text()):
            if item.get("identifier", {}).get("id", "").lower() == IDENT:
                p = extensoes / item.get("relativeLocation", "")
                if item.get("relativeLocation") and p.is_dir():
                    return p
    except (OSError, ValueError):
        pass
    achadas = sorted(p for p in extensoes.glob(f"{IDENT}-*") if (p / "package.json").exists())
    return achadas[-1] if achadas else None


def ligar(extensoes):
    pasta = pasta_instalada(extensoes)
    if not pasta:
        sys.exit(f"vscode: extensao {IDENT} nao esta instalada em {extensoes}")
    (pasta / "themes").mkdir(exist_ok=True)
    for d in ORDEM:
        alvo, link = BUILD / d / TEMA, pasta / "themes" / f"{d}.json"
        if link.is_symlink() and os.readlink(link) == str(alvo):
            continue
        tmp = link.with_name(link.name + ".tmp")
        tmp.unlink(missing_ok=True)
        tmp.symlink_to(alvo)
        os.replace(tmp, link)
    return pasta


def instalar(vsix, extensoes, padrao):
    code = shutil.which("code")
    if not code:
        sys.exit("vscode: comando `code` nao encontrado")
    cmd = [code, "--install-extension", str(vsix), "--force"]
    if not padrao:
        cmd += ["--extensions-dir", str(extensoes)]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if r.returncode:
        sys.exit(f"vscode: instalacao falhou\n{r.stdout}{r.stderr}")


def main(argv):
    extensoes, padrao = Path.home() / ".vscode/extensions", True
    if "--pasta" in argv:
        extensoes, padrao = Path(argv[argv.index("--pasta") + 1]).resolve(), False
    if "--ligar" in argv:
        print(ligar(extensoes))
        return
    vsix = montar()
    if "--montar" in argv:
        print(vsix)
        return
    instalar(vsix, extensoes, padrao)
    print(f"instalado: {ligar(extensoes)}")


if __name__ == "__main__":
    main(sys.argv[1:])
