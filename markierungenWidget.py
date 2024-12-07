import random

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (QColorDialog,
    QHBoxLayout, QVBoxLayout, QLabel, QPushButton,
    QLineEdit, QWidget
)

from sequenzenmodel import SequenzenModel
from bioinformatik import Markierung

class MarkierungenVerwalten(QWidget):

    markierungEntfernen = Signal(Markierung)
    markierungFarbeSetzen = Signal(Markierung, str)
    markierungUmbenennen = Signal(Markierung, str)
    markierungHinzu = Signal(Markierung)

    def __init__(self, model: SequenzenModel):
        super().__init__()
        self.model = model
        self.model.markierungenChanged.connect(self.updateMarkierungen)
        vbox = QVBoxLayout()
        self.setLayout(vbox)
        btn_plus = QPushButton('+')
        btn_plus.clicked.connect(self._markierungAnhaengen)
        btn_plus.setFixedWidth(40)

        self._frame = QWidget()
        self._vboxframe = QVBoxLayout()
        self._frame.setLayout(self._vboxframe)

        vbox.addWidget(QLabel('Keine gleichen Namen verwenden!'))
        vbox.addWidget(btn_plus)
        vbox.addWidget(self._frame)
        vbox.addStretch(2)

    def updateMarkierungen(self):
        for i in reversed(range(self._vboxframe.count())): 
            self._vboxframe.itemAt(i).widget().deleteLater()
        for markierung in self.model.markierungen():
            mw = MarkierungWidget(markierung)
            self._vboxframe.addWidget(mw)
            mw.markierungRemoved.connect(self._markierungEntfernen)
            mw.markierungFarbeChanged.connect(self.markierungFarbeSetzen.emit)
            mw.markierungNameChanged.connect(self.markierungUmbenennen.emit)

    def _markierungAnhaengen(self):
        farbe = "#"+''.join([random.choice('0123456789ABCDEF') for j in range(6)])
        markierung = Markierung(f'Unbenannt{farbe}',farbe)
        self.markierungHinzu.emit(markierung)

    def _markierungEntfernen(self, mw: 'MarkierungWidget'):
        self.markierungEntfernen.emit(mw.markierung)


class MarkierungWidget(QWidget):

    markierungRemoved = Signal(Markierung)
    markierungFarbeChanged = Signal(Markierung, str)
    markierungNameChanged = Signal(Markierung, str)

    def __init__(self, markierung: Markierung):
        super().__init__()
        self.markierung = markierung
        self.markierung.nameChanged.connect(self.setName)
        self.markierung.farbeChanged.connect(self.setFarbe)
        hbox = QHBoxLayout()
        self.setLayout(hbox)
        self._le_beschreibung = QLineEdit()
        self._le_beschreibung.setMaximumWidth(80)
        self._le_beschreibung.returnPressed.connect(self._beschreibungAktualisieren)
        hbox.addWidget(self._le_beschreibung)

        self._farbchooserbutton = QPushButton('Farbe wählen')
        self._farbchooserbutton.clicked.connect(self._farbauswahl)
        self._farbchooserbutton.setStyleSheet(f'background-color:{self.markierung.farbe()}; padding: 5')
        hbox.addWidget(self._farbchooserbutton)

        entfernebutton = QPushButton('-')
        entfernebutton.setMaximumWidth(25)
        entfernebutton.clicked.connect(self._markierungEntfernen)
        hbox.addWidget(entfernebutton)

        self.setName()

    def setName(self):
        self._le_beschreibung.setText(self.markierung.beschreibung())

    def setFarbe(self):
        self._farbchooserbutton.setStyleSheet(f'background-color:{self.markierung.farbe()};')

    def _beschreibungAktualisieren(self, *args):
        self.markierungNameChanged.emit(self.markierung, self._le_beschreibung.text())

    def _farbauswahl(self):
        farbe = QColorDialog.getColor(self.markierung.farbe())
        if farbe:
            self.markierungFarbeChanged.emit(self.markierung, farbe.name())
            self._farbchooserbutton.setStyleSheet(f'background-color:{farbe.name()};')

    def _markierungEntfernen(self):
        self.markierungRemoved.emit(self)
