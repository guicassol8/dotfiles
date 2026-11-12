import QtQuick

// Rotulo: legenda curta em pixel (NIVEL, MANA, CLASSE). Sempre em maiusculas.
TextoPixel {
    tipo: "rotulo"
    color: _janela ? _janela.tintaSuave : Tema.textoSuave
    font.capitalization: Font.AllUppercase
}
