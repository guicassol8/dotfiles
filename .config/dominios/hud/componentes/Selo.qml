import QtQuick

// Selo: escudo de rank, de E a S.   Selo { rank: "B" }
Figura {
    property string rank: "E"
    readonly property string _r: "edcbas".indexOf(rank.toLowerCase()) >= 0 ? rank.toLowerCase() : "e"
    fonte: "selo-" + _r
}
