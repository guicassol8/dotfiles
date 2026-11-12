import QtQuick

// Campo de texto (usuário ou senha). Cor, fonte e forma vêm de `t` (tokens do domínio).
FocusScope {
    id: campo

    required property var t
    property alias texto: entrada.text
    property bool senha: false
    property bool erro: false
    property bool travado: false
    readonly property int recuo: Math.max(t.px(14), Math.min(t.raio, Math.round(height / 2)))

    signal aceito()

    implicitWidth: t.px(320)
    implicitHeight: t.px(t.estilo.campo_altura)
    activeFocusOnTab: true

    // moldura de pixel (tela de título do Grimório): contorno, filete de 1 pixel e miolo escuro
    Item {
        id: pixel

        readonly property int g: campo.t.px(3)

        visible: campo.t.pixel
        anchors.fill: parent

        Entalhe {
            anchors.fill: parent
            g: pixel.g
            cor: Qt.darker(campo.t.cor.fundo, 1.7)
        }

        Entalhe {
            anchors.fill: parent
            anchors.margins: pixel.g
            g: pixel.g
            cor: campo.erro ? campo.t.cor.erro : entrada.activeFocus ? campo.t.cor.primaria : campo.t.cor.contorno
        }

        Rectangle {
            anchors.fill: parent
            anchors.margins: 2 * pixel.g
            color: Qt.darker(campo.t.cor.superficie, 1.35)
        }

        Rectangle {
            x: 2 * pixel.g
            y: 2 * pixel.g
            width: parent.width - 4 * pixel.g
            height: pixel.g
            color: Qt.darker(campo.t.cor.fundo, 1.5)
        }
    }

    Rectangle {
        visible: !campo.t.pixel
        anchors.fill: parent
        radius: Math.min(campo.t.raio, height / 2)
        color: Qt.alpha(campo.t.cor.superficie2, 0.88)
        border.width: campo.t.borda
        border.color: campo.erro ? campo.t.cor.erro
                    : entrada.activeFocus ? campo.t.cor.primaria
                    : campo.t.cor.contorno
    }

    TextInput {
        id: entrada

        anchors.fill: parent
        anchors.leftMargin: campo.recuo
        anchors.rightMargin: campo.recuo
        focus: true
        clip: true
        readOnly: campo.travado
        verticalAlignment: TextInput.AlignVCenter
        horizontalAlignment: campo.t.centro ? TextInput.AlignHCenter : TextInput.AlignLeft
        color: campo.t.cor.texto
        selectionColor: campo.t.cor.primaria
        selectedTextColor: campo.t.cor.sobre_primaria
        font.family: campo.t.ui
        font.weight: campo.t.pesoUi
        font.pixelSize: campo.t.px(campo.t.estilo.texto_tamanho)
        font.letterSpacing: campo.senha ? campo.t.px(3) : 0
        echoMode: campo.senha ? TextInput.Password : TextInput.Normal
        passwordCharacter: campo.t.txt.ponto_senha
        inputMethodHints: Qt.ImhNoPredictiveText | Qt.ImhNoAutoUppercase
                          | (campo.senha ? Qt.ImhSensitiveData : Qt.ImhNone)
        selectByMouse: true
        onAccepted: campo.aceito()
    }
}
