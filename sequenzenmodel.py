
import logging
from PySide6.QtCore import Signal, QObject
from bioinformatik import Sequenz, Markierung

log = logging.getLogger(__name__)

class SequenzenModel(QObject):

    sequenzenChanged = Signal()
    markierungenChanged = Signal()
    verstecktChanged = Signal()

    def __init__(self, parent: QObject, sequenzen: list[Sequenz] = None, markierungen: list[Markierung] = None, versteckt: list[range] = None):
        super().__init__(parent)
        self._sequenzen = sequenzen or []
        self._markierungen = markierungen or []
        self._versteckt = versteckt or []

    def sequenzen(self) -> list[Sequenz]:
        return self._sequenzen

    def markierungen(self) -> list[Markierung]:
        return self._markierungen

    def versteckt(self) -> list[bool]:
        return self._versteckt

    def getAllCopy(self):
        return self._sequenzen.copy(), self._markierungen.copy(), self.versteckt.copy()
    
    def setAll(self, sequenzen: list[Sequenz] = None, markierungen: list[Markierung] = None, versteckt: list[range] = None):
        self._sequenzen = sequenzen or []
        self._markierungen = markierungen or []
        self._versteckt = versteckt or []
        self.sequenzenChanged.emit()
        self.markierungenChanged.emit()

    def addSequenzen(self, seqarr: list[Sequenz]):
        self._sequenzen += seqarr
        self.sequenzenChanged.emit()

    def removeSequenzen(self, sequenzen: list[Sequenz]):
        for sequenz in sequenzen:
            self._sequenzen.remove(sequenz)
        self.sequenzenChanged.emit()

    def addMarkierungen(self, markarr: list[Markierung]):
        self._markierungen += markarr
        self.markierungenChanged.emit()

    def removeMarkierung(self, markierung: Markierung):
        self._markierungen.remove(markierung)
        self.markierungenChanged.emit()

    def addVersteckt(self, arr: list[range]):
        self._versteckt += arr
        self.verstecktChanged.emit()

    def removeVersteckt(self, arr: list[range]):
        for col in arr:
            col in self._versteckt and self._versteckt.remove(col)
        self.verstecktChanged.emit()
