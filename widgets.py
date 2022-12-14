import logging
from PySide6.QtCore import Signal
from PySide6.QtGui import QColor

from PySide6.QtWidgets import QGraphicsScene
from pyside6 import BaseDialog, SequenzDialog, LinealDialog, MarkierungenVerwaltenDialog
from pyside6 import basenlaenge, sequenznamewidth, MarkierungItem, SequenzItem, LinealItem

log = logging.getLogger(__name__)

class SequenzenScene(QGraphicsScene):
    """
    Eine Sicht auf die Sequenzen

    Stellt die Sequenzen in einem Canvas dar.

    Reicht Events mit Hilfe von Callbacks an den Hauptdialog weiter.
    """

    painted = Signal()

    fontBase = ('Courier', 14, 'bold')
    fontLineal = ('Courier', 12, 'bold')
    rahmendicke = 20
    abstandMarkierungen = 3

    def __init__(self, parent, sequenzen=None, markierungen=None, versteckt=None, umbruch=False, spaltenzahl=50, zeigeversteckt=False):
        super().__init__(parent)
        self._sequenzen = sequenzen or []
        self._markierungen = markierungen or []
        self._umbruch = umbruch
        self._spaltenzahl = spaltenzahl
        self._versteckt = versteckt or []
        self._zeigeversteckt = zeigeversteckt

        self._ystart = self.rahmendicke
        self._maxlen = 0

        self._linealitem = None
        self._sequenzitems = {}

        self._allesNeuZeichnen()

    def _emptyCanvas(self):
        """Leert die Leinwand"""
        self._linealitem = None
        self._sequenzitems = {}
        self.clear()

    def markierungen(self):
        return self._markierungen

    def sequenzen(self):
        return self._sequenzen

    def versteckt(self):
        return self._versteckt

    def setMarkierungen(self, markierungen):
        self._markierungen = markierungen
        self._allesNeuZeichnen()

    def setVersteckt(self, versteckt):
        self._versteckt = versteckt
        self._allesNeuZeichnen()

    def setSequenzen(self, sequenzen):
        self._sequenzen = sequenzen
        self._allesNeuZeichnen()

    def setAll(self, sequenzen=None, markierungen=None, versteckt=None):
        self._sequenzen = sequenzen or []
        self._markierungen = markierungen or []
        self._versteckt = versteckt or []
        self._allesNeuZeichnen()

    def addSequenzen(self, seqarr):
        self._sequenzen += seqarr
        self._allesNeuZeichnen()

    def addVersteckt(self, arr):
        self._versteckt += arr
        self._allesNeuZeichnen()

    def removeVersteckt(self, arr):
        for col in arr:
            col in self._versteckt and self._versteckt.remove(col)
        self._allesNeuZeichnen()
    
    def removeSequenz(self, sequenz):
        self._sequenzen.remove(sequenz)
        self._allesNeuZeichnen()

    def _allesNeuZeichnen(self):
        """Zeichnet alles neu!
        
        * sequenzen: Ein Array des Typs Sequenz
        * markierungen: Ein Array des Typs Markierung
        * umbruch: Boolean. Gibt an, ob die Sequenzen umgebrochen werden sollen.
        * spaltenzahl: Die Zahl der Spalten, falls umgebrochern werden soll.
        * versteckt: Ein Array, das die Spaltennummern enth??lt, die versteckt werden sollen.
        * zeigeversteckt: Boolean. Gibt an, ob die versteckten Spalten ausgeblendet oder ausgegraut werden sollen."""

        self._emptyCanvas()
        self._maxlenBerechnen()
        self._markierungenZeichnen()
        self._verstecktBemerkungZeichnen()
        self._linealZeichnen()

        if not self._sequenzen:
            self._keineSequenzenVorhanden()
            self.painted.emit()
            return
        
        for sequenz in self._sequenzen:
            self._sequenzZeichnen(sequenz, True)
            sequenz.basenchanged.connect(self._sequenzZeichnen)
            sequenz.namechanged.connect(self._sequenzZeichnen)

        self.painted.emit()


    def _sequenzZeichnen(self, sequenz, nopaintedemit=False):
        """Zeichnet eine Sequenz.

        * seqidx: Die Nummer im Sequenzarray self.sequenzen

        Soll nur Aufgerufen, wenn in einer Sequenz Basen hinzugef??gt
        oder entfernt wurden. Oder wenn Basen mit einer anderen Markierung
        markiert wurden. Bei allen anderen Operationen muss sequenzenNeuZeichnen
        aufgerufen werden.
        """

        if self._maxlenBerechnen():
            self._linealZeichnen()

        row = self._sequenzen.index(sequenz)
        if row in self._sequenzitems:
            self.removeItem(self._sequenzitems[row])
        sequenzitem = SequenzItem(self, sequenz)
        self._sequenzitems[row] = sequenzitem


        if not sequenz.basen():
            self._sequenznameZeichnen(sequenzitem, 0, row)
            nopaintedemit or self.painted.emit()
            return

        rotelinieschonda = False
        col = 0
        for basidx in range(len(sequenz.basen())):
            # Weil einige Basen versteckt sein k??nnen, ist die Spalte col
            # nicht mir dem Basenindex basidx identisch.

            base = sequenz.basen()[basidx]

            # Hier wird entschieden, ob die rote Linie f??r versteckte Sequenzen
            # gezeichnet werden soll.
            aktuellversteckt = basidx in self._versteckt
            if aktuellversteckt and not self._zeigeversteckt:
                if not rotelinieschonda:
                    self._baseRoteLinieZeichnen(sequenzitem, col, row)
                    rotelinieschonda = True
                continue

            if self._umbruch and col % self._spaltenzahl == 0 or not self._umbruch and col == 0:
                # Bei einer neuen Zeile muss der Sequenzname neu gezeichnet werden.
                self._sequenznameZeichnen(sequenzitem, col, row)
            
            self._baseZeichnen(sequenzitem, col, row, base, aktuellversteckt)
            col += 1
            rotelinieschonda = False

        nopaintedemit or self.painted.emit()

    def _linealZeichnen(self):
        """Zeichnet das Lineal ??ber den Sequenzen"""
        
        if self._linealitem:
            self.removeItem(self._linealitem)
        self._linealitem = LinealItem(self)
        col = 0
        rotelinieschonda = False
        for i in range(self._maxlen):

            aktuellversteckt = i in self._versteckt
            if aktuellversteckt and not self._zeigeversteckt:
                    if not rotelinieschonda:
                        self._linealRoteLinieZeichnen(self._linealitem, col)
                        rotelinieschonda = True
                    continue

            # Eine Instanz der Klasse Linealtickobjekt zeichnet automatisch das Linealelement
            self._linealtickZeichnen(self._linealitem, i, col, aktuellversteckt)
            col += 1
            rotelinieschonda = False

    def _markierungenZeichnen(self):
        """Zeichnet ??ber der Tabelle der Sequenzen die Markierungen"""

        self._ystart = self.rahmendicke
        if not self._markierungen:
            self._keineMarkierungen()
            return
        
        for markierung in self._markierungen:
            self._markierungZeichnen(markierung)

    def _verstecktBemerkungZeichnen(self):
        """Zeichnet einen Infotext, wenn keine Markierungen vorhanden sind."""

        if not self._versteckt:
            return
        abstand = self.abstandMarkierungen
        x = self.rahmendicke+sequenznamewidth+basenlaenge
        y = self._ystart
        objektid = self.addText('Es gibt versteckte Spalten')
        objektid.setPos(x,y)

        x = self.rahmendicke+sequenznamewidth
        objektid = self.addLine(x, y, x, y+basenlaenge, QColor('red'))
        self._ystart += basenlaenge+abstand


#################################################################
# elementare Funktionen zum Zeichnen
#################################################################

    def _sequenznameZeichnen(self, sequenzitem, col, seqidx):
        """Zeichnet den Sequenznamen
        
        F??r den Sequenznamen wird ein Platz von self.raumFuerSequenznamen reserviert.
        Der Sequenzname wird verk??rzt, falls er zu lang ist"""

        x, y = self._xyBaseFuerColRow(col, seqidx)
        sequenzitem.addName(0, y, self._sequenzclick)

    def _keineSequenzenVorhanden(self):
        """Zeichnet einen Infotext, falls keine Sequenzen vorhanden sind."""

        x = self.rahmendicke
        y = self.rahmendicke
        txt = 'Keine Sequenzen vorhanden. Bitte Sequenz erzeugen, laden oder importieren.'
        objektid = self.addText(txt)
        objektid.setPos(x,y)
        objektid.setTextWidth(sequenznamewidth-10)

    def _baseZeichnen(self, sequenzitem, col, seqidx, base, versteckt):
        """Zeichnet die Base mit dahintergelegten Rechteck, das bei Mouseover gehighlited werden kann."""

        x, y = self._xyBaseFuerColRow(col, seqidx)
        sequenzitem.addBase(x, y, base, versteckt, self._baseclick)

    def _baseRoteLinieZeichnen(self, sequenzitem, basidx, seqidx):
        """Zeichnet die rote Linie einer versteckten Base"""

        x, y = self._xyBaseFuerColRow(basidx, seqidx)
        sequenzitem.addRoteLinie(x, y)

    def _linealtickZeichnen(self, linealitem, idx, col, versteckt):
        """Zeichnet dein Linealtick mit dahintergelegten Rechteck, das bei Mouseover gehighlited werden kann."""

        x, y = self._xyBaseFuerColRow(col, 0)
        linealitem.addTick(x, y, idx, versteckt, self._linealclick)

    def _linealRoteLinieZeichnen(self, linealitem, col):
        """Zeichnet die rote Linie eines versteckten Linealticks"""

        x, y = self._xyLinealFuerCol(col)
        linealitem.addRoteLinie(x, y)

    def _markierungZeichnen(self, markierung):
        x = self.rahmendicke+sequenznamewidth
        y = self._ystart
        MarkierungItem(self, x, y, basenlaenge, self.abstandMarkierungen, markierung)
        self._ystart += basenlaenge+self.abstandMarkierungen

    def _keineMarkierungen(self):
        """Zeichnet einen Infotext, wenn keine Markierungen vorhanden sind."""

        abstand = self.abstandMarkierungen
        x = self.rahmendicke+sequenznamewidth+basenlaenge
        y = self._ystart
        objektid = self.addText('Keine Markierungen vorhanden')
        objektid.setPos(x,y)
        self._ystart += basenlaenge+abstand


#########################################################
# Koordinatenfunktionen
#########################################################

    def _koordinaten(self, col: int, row: int):
        "Wandelt col,row in x,y der Leinwand um"
        return [ col*basenlaenge+sequenznamewidth+self.rahmendicke, row*basenlaenge+self._ystart ]
    
    def _rowMitUmbruchBerechnen(self, col: int, row: int):
        "Berechnet die Zeile, wenn die Sequenzen umgebrochen werden"
        return int(col/self._spaltenzahl) * (len(self._sequenzen)+2.5) + row

    def _colrowHolen(self, baseidx: int, sequenzidx: int):
        "Berechnet aus der Sequenznummer und der Basennummer die Zeile und Spalte"
        if self._umbruch:
            row = self._rowMitUmbruchBerechnen(baseidx, sequenzidx)
            col = baseidx % self._spaltenzahl
        else:
            row = sequenzidx
            col = baseidx
        return (col, row)

    def _xyBaseFuerColRow(self, col, row):
        """
        Gibt die Leinwand-XY-Koordinaten f??r eine Base zur??ck.
        Es handelt sich um die linke, obere Ecke einer Basenbox.
        """

        (col2,row2) = self._colrowHolen(col, row)
        row2 += 2
        return self._koordinaten(col2, row2)

    def _xyLinealFuerCol(self, col):
        """
        Gibt die Leinwand-XY-Koordinaten f??r ein Linealtick zur??ck.
        Es handelt sich um die linke, obere Ecke einer Linealbox.
        """

        (col2,row2) = self._colrowHolen(col, 0)
        return self._koordinaten(col2, row2)

    def _maxlenBerechnen(self) -> bool:
        """
        Schaut, ob sich die Maximall??nge aller Sequenzen
        ge??ndert hat. Falls das der Fall ist, wird True
        zur??ckgegeben.
        """

        maxlen = 0
        for sequenz in self._sequenzen:
            seqlen = len(sequenz.basen())
            if maxlen < seqlen:
                maxlen = seqlen
        if maxlen != self._maxlen:
            self._maxlen = maxlen
            return True
        return False

##########################################
# Dialogcallbacks
##########################################

    def _baseclick(self, base):
        dlg = BaseDialog(base, self._markierungen)
        dlg.exec()

    def _sequenzclick(self,sequenz):
        dlg = SequenzDialog(self, sequenz)
        dlg.exec()

    def _linealclick(self, spalte):
        dlg = LinealDialog(self, spalte)
        dlg.exec()

    def _markierungenVerwalten(self):
        dlg = MarkierungenVerwaltenDialog(self._markierungen)
        dlg.exec()
        for seq in self._sequenzen:
            seq.checkMarkierungen(self._markierungen)
        self._allesNeuZeichnen()

####################################################
# Slots
####################################################

    def verstecktStateTrigger(self, checked):
        if checked:
            self._zeigeversteckt = True
        else:
            self._zeigeversteckt = False
        self._allesNeuZeichnen()

    def umbruchTrigger(self, checked):
        if checked:
            self._umbruch = True
        else:
            self._umbruch = False
        self._allesNeuZeichnen()

    def spaltenzahlTrigger(self, anzahl):
        self._spaltenzahl = anzahl
        self._allesNeuZeichnen()

    def markierungenTrigger(self):
        self._markierungenVerwalten()