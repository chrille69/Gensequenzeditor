
from PySide6.QtGui import QUndoCommand
from bioinformatik import Sequenz, Markierung, Base
from sequenzenmodel import SequenzenModel


class AddSequenzenCommand(QUndoCommand):

    def __init__(self, model:SequenzenModel, sequenzen: list[Sequenz]):
        super(AddSequenzenCommand, self).__init__('Sequenzen hinzu')
        self.model = model
        self.sequenzen = sequenzen

    def redo(self):
        self.model.addSequenzen(self.sequenzen)

    def undo(self):
        self.model.removeSequenzen(self.sequenzen)


class RemoveSequenzenCommand(QUndoCommand):

    def __init__(self, model: SequenzenModel, sequenzen: list[Sequenz]):
        super(RemoveSequenzenCommand, self).__init__('Sequenzen entfernt')
        self.model = model
        self.sequenzen = sequenzen

    def redo(self):
        self.model.removeSequenzen([self.sequenzen])

    def undo(self):
        self.model.addSequenzen([self.sequenzen])


class RenameSequenzCommand(QUndoCommand):

    def __init__(self, sequenz: Sequenz, nameneu: str):
        super(RenameSequenzCommand, self).__init__('Sequenz umbenannt '+nameneu)
        self.sequenz = sequenz
        self.nameneu = nameneu
        self.namealt = sequenz.name()

    def redo(self):
        self.sequenz.setName(self.nameneu)

    def undo(self):
        self.sequenz.setName(self.namealt)


class AminosaeureSequenzCommand(QUndoCommand):

    def __init__(self, sequenz: Sequenz):
        super(AminosaeureSequenzCommand, self).__init__('Sequenz in Aminos. '+sequenz.name())
        self.sequenz = sequenz
        self.basenalt = sequenz.basen()
        self.basenneu = sequenz.inAminosaeure()

    def redo(self):
        self.sequenz.setBasen(self.basenneu)

    def undo(self):
        self.sequenz.setBasen(self.basenalt)


class InsertLeerBaseCommand(QUndoCommand):

    def __init__(self, base: Base, anzahl: int):
        super(InsertLeerBaseCommand, self).__init__('Insert leer')
        index = base.getIndexInSequenz()
        self.sequenz = base.sequenz()
        self.basenalt = self.sequenz.basen()
        self.basenneu = self.sequenz.insertLeer(index, anzahl)

    def redo(self):
        self.sequenz.setBasen(self.basenneu)

    def undo(self):
        self.sequenz.setBasen(self.basenalt)


class MarkiereBasenCommand(QUndoCommand):

    def __init__(self, base: Base, anzahl: int, markierung: Markierung):
        super(MarkiereBasenCommand, self).__init__('Basen markiert')
        index = base.getIndexInSequenz()
        sequenz = base.sequenz()
        neu_markiert = sequenz.basen()[index:index+anzahl]
        self.basen_mark_alt = {}
        self.basen_mark_neu = {}
        for b in sequenz.basen():
            self.basen_mark_alt[b] = b.markierung()
            self.basen_mark_neu[b] = b.markierung()
            if b in neu_markiert:
                self.basen_mark_neu[b] = markierung

    def redo(self):
        for b in self.basen_mark_neu:
            b.setMarkierung(self.basen_mark_neu[b])

    def undo(self):
        for b in self.basen_mark_alt:
            b.setMarkierung(self.basen_mark_alt[b])


class EntferneBaseCommand(QUndoCommand):

    def __init__(self, base: Base, anzahl: int):
        super(EntferneBaseCommand, self).__init__('Entferne Basen')
        index = base.getIndexInSequenz()
        self.sequenz = base.sequenz()
        self.basenalt = self.sequenz.basen()
        self.basenneu = self.sequenz.entferneBasen(index, anzahl)

    def redo(self):
        self.sequenz.setBasen(self.basenneu)

    def undo(self):
        self.sequenz.setBasen(self.basenalt)


class InsertBaseCommand(QUndoCommand):

    def __init__(self, base: Base, seqtext: int):
        super(InsertBaseCommand, self).__init__('Insert Basen')
        index = base.getIndexInSequenz()
        self.sequenz = base.sequenz()
        self.basenalt = self.sequenz.basen()
        self.basenneu = self.sequenz.insertBasenString(index, seqtext)

    def redo(self):
        self.sequenz.setBasen(self.basenneu)

    def undo(self):
        self.sequenz.setBasen(self.basenalt)


class RemoveMarkierungCommand(QUndoCommand):

    def __init__(self, model: SequenzenModel, markierung: Markierung):
        super(RemoveMarkierungCommand, self).__init__('Markierung entfernt '+markierung.beschreibung())
        self.model = model
        self.markierung = markierung

    def redo(self):
        self.markierung.deleted.emit()
        self.model.removeMarkierung(self.markierung)

    def undo(self):
        self.model.addMarkierungen([self.markierung])


class AddMarkierungCommand(QUndoCommand):

    def __init__(self, model: SequenzenModel, markierung: Markierung):
        super(AddMarkierungCommand, self).__init__('Markierung hinzu '+markierung.beschreibung())
        self.model = model
        self.markierung = markierung

    def redo(self):
        self.model.addMarkierungen([self.markierung])

    def undo(self):
        self.model.removeMarkierung(self.markierung)


class changeColorMarkierungCommand(QUndoCommand):

    def __init__(self, markierung: Markierung, farbe: str):
        super(changeColorMarkierungCommand, self).__init__('Markierung Farbe '+farbe)
        self.markierung = markierung
        self.farbeneu = farbe
        self.farbealt = markierung.farbe()

    def redo(self):
        self.markierung.setFarbe(self.farbeneu)

    def undo(self):
        self.markierung.setFarbe(self.farbealt)


class changeBeschreibungMarkierungCommand(QUndoCommand):

    def __init__(self, markierung: Markierung, name: str):
        super(changeBeschreibungMarkierungCommand, self).__init__('Markierung Name '+name)
        self.markierung = markierung
        self.nameneu = name
        self.namealt = markierung.beschreibung()

    def redo(self):
        self.markierung.setBeschreibung(self.nameneu)

    def undo(self):
        self.markierung.setBeschreibung(self.namealt)


class VerstecktCommand(QUndoCommand):

    def __init__(self, model: SequenzenModel, versteckt: list[bool]):
        super(VerstecktCommand, self).__init__('Verstecken')
        self.model = model
        self.versteckt = versteckt

    def redo(self):
        self.model.addVersteckt(self.versteckt)

    def undo(self):
        self.model.removeVersteckt(self.versteckt)


class EnttarnenCommand(QUndoCommand):

    def __init__(self, model: SequenzenModel, enttarnen: list[bool]):
        super(EnttarnenCommand, self).__init__('Enttarnen')
        self.model = model
        self.enttarnen = enttarnen

    def redo(self):
        self.model.removeVersteckt(self.enttarnen)

    def undo(self):
        self.model.addVersteckt(self.enttarnen)


class SetAllCommand(QUndoCommand):

    def __init__(self, model: SequenzenModel, *all: tuple[list[Sequenz], list[Markierung], list[bool]]):
        super(SetAllCommand, self).__init__('Enttarnen')
        self.model = model
        self.allneu = all
        self.allalt = self.model.getAllCopy()

    def redo(self):
        self.model.setAll(*self.allneu)

    def undo(self):
        self.model.setAll(*self.allalt)
