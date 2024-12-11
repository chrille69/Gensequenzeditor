
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QFontMetrics, QPen
from PySide6.QtWidgets import QGraphicsLineItem, QGraphicsRectItem, QGraphicsTextItem, QGraphicsSimpleTextItem, QGraphicsItem

from bioinformatik import Base, Sequenz, Markierung
from sequenzenmodel import SequenzenModel, SequenzenViewModel

basefont = QFont()
basefont.setFamily('Courier')
basefont.setBold(QFont.Bold)
basefont.setPointSize(13)
basefm = QFontMetrics(basefont)
seqfont = QFont()
seqfont.setFamily('Helvetica')
seqfont.setPointSize(12)
seqfm = QFontMetrics(seqfont)
basenlaenge = 20
brushversteckt = QColor('lightgray')
brushhighlight = QColor('lightblue')
penhighlight = QColor('red')
sequenznamewidth = 200
umbruchgap = 2.5
rahmendicke = 20

def xyFromColSeqidx(col, seqidx, spaltenzahl, lenseq, umbruch):
    if umbruch:
        x = basenlaenge * (col % spaltenzahl) + sequenznamewidth + basenlaenge
        y = basenlaenge * (int(col / spaltenzahl) * (lenseq + umbruchgap)+ seqidx)
    else:
        x = basenlaenge * col + sequenznamewidth + basenlaenge
        y = basenlaenge * seqidx
    return x, y

def deleteItemArray(itemarray: list[QGraphicsItem]):
    while itemarray:
        item = itemarray.pop()
        item.setParentItem(None)


class SequenzItem(QGraphicsRectItem):

    def __init__(self, parent, sequenz: Sequenz, model: SequenzenModel, viewmodel: SequenzenViewModel, linealitem: 'LinealItem'):
        super().__init__(parent)
        self._sequenz = sequenz
        self._model = model
        self._viewmodel = viewmodel
        self._linealitem = linealitem
        self._seqidx = self.model.sequenzen.index(self.sequenz)
        self._baseitems: list[BaseItem] = []
        self._nameitems: list[SequenznameItem] = []

        self.viewmodel.spaltenzahlChanged.connect(self.umbrechen)
        self.viewmodel.umbruchChanged.connect(self.umbrechen)
        self.viewmodel.zeigeverstecktChanged.connect(self.umbrechen)
        self.model.verstecktAdded.connect(self.versteckeBasen)
        self.model.verstecktRemoved.connect(self.enttarneBasen)
        self.sequenz.basenRenewed.connect(self.erzeugeBasen)
        self.sequenz.basenInserted.connect(self.insertBasenItems)
        self.sequenz.basenRemoved.connect(self.removeBasenItems)

        self.erzeugeNamen()
        self.erzeugeBasen()

    @property
    def model(self):
        return self._model

    @property
    def viewmodel(self):
        return self._viewmodel
    
    @property
    def sequenz(self) -> Sequenz:
        return self._sequenz

    @property
    def seqidx(self) -> Sequenz:
        return self._seqidx

    def versteckeBasen(self, idxlist: list[int]):
        for index in idxlist:
            self._baseitems[index].versteckt = True
        self.setBasenPos()

    def enttarneBasen(self, idxlist: list[int]):
        for index in idxlist:
            self._baseitems[index].versteckt = False
        self.setBasenPos()

    def umbrechen(self, *arg):
        self.erzeugeNamen()
        self.setBasenPos()

    def erzeugeNamen(self):
        deleteItemArray(self._nameitems)

        colanzahl = len(self.sequenz.basen) - len(self.model.versteckt)
        anzahl = 1
        if self.viewmodel.umbruch:
            anzahl = int(colanzahl / self.viewmodel.spaltenzahl) + 1
        for idx in range(anzahl):
            x, y = xyFromColSeqidx(idx*self.viewmodel.spaltenzahl, self.seqidx, self.viewmodel.spaltenzahl, len(self.model.sequenzen), self.viewmodel.umbruch)
            self._nameitems.append(SequenznameItem(self, 0, y, self.sequenz))

    def erzeugeBasen(self):
        deleteItemArray(self._baseitems)

        for base in self.sequenz.basen:
            self._baseitems.append(BaseItem(self, base))
        self.setBasenPos()

    def setBasenPos(self):
        col = 0
        for basidx in range(len(self._baseitems)):
            # Weil einige Basen versteckt sein können, ist die Spalte col
            # nicht mir dem Basenindex basidx identisch.

            baseitem = self._baseitems[basidx]
            x, y = xyFromColSeqidx(col, self.seqidx, self.viewmodel.spaltenzahl, len(self.model.sequenzen), self.viewmodel.umbruch)
            baseitem.setPos(x, y)

            # Hier wird entschieden, ob das Item versteckt werden soll.
            aktuellversteckt = basidx in self.model.versteckt
            if aktuellversteckt and not self.viewmodel.zeigeversteckt:
                baseitem.setVisible(False)
                continue
            else:
                baseitem.setVisible(True)

            col += 1

    def insertBasenItems(self, pos: int, basen: list[Base]):
        self._baseitems[pos:pos] = [BaseItem(self, base) for base in basen]
        self.setBasenPos()
        self._linealitem.erzeugeTicks()

    def removeBasenItems(self, pos: int, basen: list[Base]):
        anzahl = len(basen)
        for baseitem in self._baseitems[pos:pos+anzahl]:
            baseitem.setParentItem(None)
        self._baseitems[pos:pos+anzahl] = []
        self.setBasenPos()
        self._linealitem.erzeugeTicks()

class SequenznameItem(QGraphicsRectItem):

    def __init__(self, parent, x: int, y: int, sequenz: Sequenz):
        super().__init__ (x, y, sequenznamewidth, basenlaenge, parent)
        self._x = x
        self._y = y
        self._sequenz = sequenz
        self.setBrush(Qt.NoBrush)
        self.setPen(Qt.NoPen)
        self.gtxt = QGraphicsSimpleTextItem(self)
        self.gtxt.setFont(seqfont)
        self.setName()
        self._sequenz.nameChanged.connect(self.setName)
        self.setAcceptHoverEvents(True)

    def setName(self):
        text = self.kurzName()
        self.gtxt.setText(text)
        w = seqfm.horizontalAdvance(text)
        self.gtxt.setPos(self._x+sequenznamewidth-w, self._y+basenlaenge/2-seqfm.height()/2)

    def kurzName(self) -> str:
        txt = self._sequenz.name
        w = seqfm.horizontalAdvance(txt)
        while w > sequenznamewidth:
            txt = txt[:-1]
            w = seqfm.horizontalAdvance(txt)
        if self._sequenz.name != txt:
            txt = txt[:-3]+'...'
        return txt

    def hoverEnterEvent(self, event):
        self.setBrush(brushhighlight)

    def hoverLeaveEvent(self, event):
        self.setBrush(Qt.NoBrush)

    def mousePressEvent(self, *args):
        self.scene().sequenzNameClicked.emit(self.parentItem().sequenz)


class BaseItem(QGraphicsRectItem):

    def __init__(self, parent, base: Base):
        super().__init__(0, 0, basenlaenge, basenlaenge, parent)
        self._base = base
        self._versteckt = False
        self.brush = Qt.NoBrush
        self.setBoxfarbe()
        self.setPen(Qt.NoPen)
        gchar = QGraphicsSimpleTextItem(base.char, self)
        gchar.setFont(basefont)
        gcharw = basefm.horizontalAdvance(base.char)
        gcharh = basefm.height()
        gchar.setPos(basenlaenge/2-gcharw/2, basenlaenge/2-gcharh/2)
        gchar.setBrush(QColor(base.getCharFarbe()))
        self.setAcceptHoverEvents(True)
        base.changed.connect(self.setBoxfarbe)

    @property
    def base(self):
        return self._base
    
    @property
    def versteckt(self):
        return self._versteckt
    
    @versteckt.setter
    def versteckt(self, value):
        self._versteckt = value
        self.setBoxfarbe()

    def setBoxfarbe(self):
        boxfarbe = self._base.getBoxFarbe()
        if boxfarbe:
            self.brush = QColor(boxfarbe)
        else:
            self.brush = Qt.NoBrush
        if self.versteckt:
            self.brush = brushversteckt
        self.setBrush(self.brush)
        
    def hoverEnterEvent(self, event):
        self.setBrush(brushhighlight)

    def hoverLeaveEvent(self, event):
        self.setBrush(self.brush)

    def mousePressEvent(self, *args):
        self.scene().baseClicked.emit(self._base)


class LinealItem(QGraphicsRectItem):
    def __init__(self, parent, model: SequenzenModel, viewmodel: SequenzenViewModel):
        super().__init__(parent)
        self._model = model
        self._viewmodel = viewmodel
        self._ticks: list[LinealtickItem] = []

        self.viewmodel.spaltenzahlChanged.connect(self.setTicksPos)
        self.viewmodel.umbruchChanged.connect(self.setTicksPos)
        self.viewmodel.zeigeverstecktChanged.connect(self.setTicksPos)
        self.model.verstecktAdded.connect(self.versteckeTicks)
        self.model.verstecktRemoved.connect(self.enttarneTicks)

        self.erzeugeTicks()


    @property
    def model(self):
        return self._model

    @property
    def viewmodel(self):
        return self._viewmodel

    def erzeugeTicks(self):
        deleteItemArray(self._ticks)

        for idx in range(self.model.maxlen):
            self._ticks.append(LinealtickItem(self, idx))
        self.setTicksPos()
        
    def versteckeTicks(self, idxlist: list[int]):
        for index in idxlist:
            self._ticks[index].versteckt = True
        self.setTicksPos()

    def enttarneTicks(self, idxlist: list[int]):
        for index in idxlist:
            self._ticks[index].versteckt = False
        self.setTicksPos()

    def setTicksPos(self):
        col = 0
        for tickidx in range(len(self._ticks)):
            tickitem = self._ticks[tickidx]
            x, y = xyFromColSeqidx(col, -2, self.viewmodel.spaltenzahl, len(self.model.sequenzen), self.viewmodel.umbruch)
            tickitem.setPos(x, y)

            aktuellversteckt = tickitem.versteckt
            if aktuellversteckt and not self.viewmodel.zeigeversteckt:
                tickitem.setVisible(False)
                continue
            else:
                tickitem.setVisible(True)

            col += 1


class LinealtickItem(QGraphicsRectItem):

    def __init__(self, parent: LinealItem, idx: int):
        super().__init__(0, 0, basenlaenge, 2*basenlaenge, parent)
        self._idx = idx
        self._versteckt = False
        self.brush = Qt.NoBrush
        self.setPen(Qt.NoPen)
        self.setBoxfarbe()
        self.setZValue(-10)
        nummer = idx+1
        marke = '∙'
        gcharh = 0
        if nummer%10 == 0:
            marke = '|'
            gcharh = basefm.descent()
            gnummer = QGraphicsSimpleTextItem(str(nummer), self)
            gnummer.setFont(basefont)
            gnummerw = basefm.horizontalAdvance(str(nummer))
            gnummer.setPos(basenlaenge/2-gnummerw/2, basenlaenge/2-gcharh-4)
        gchar = QGraphicsSimpleTextItem(marke, self)
        gchar.setFont(basefont)
        gcharw = basefm.horizontalAdvance(marke)
        gchar.setPos(basenlaenge/2-gcharw/2, basenlaenge)
        self.setAcceptHoverEvents(True)

    @property
    def idx(self):
        return self._idx
    
    @property
    def versteckt(self):
        return self._versteckt
    
    @versteckt.setter
    def versteckt(self, value):
        self._versteckt = value
        self.setBoxfarbe()

    def setBoxfarbe(self):
        if self.versteckt:
            self.brush = brushversteckt
        else:
            self.brush = Qt.NoBrush
        self.setBrush(self.brush)
        
    def hoverEnterEvent(self, event):
        self.setBrush(brushhighlight)

    def hoverLeaveEvent(self, event):
        self.setBrush(self.brush)

    def mousePressEvent(self, *args):
        self.scene().linealClicked.emit(self._idx)


class RotelinieItem(QGraphicsLineItem):

    def __init__(self, parent: LinealItem, x: int, y: int, length: int):
        super().__init__(x, y, x, y+length, parent)
        pen = QPen(QColor('red'))
        pen.setWidth(3)
        self.setPen(pen)
        self.setZValue(10)


class MarkierungItem(QGraphicsRectItem):

    def __init__(self, parent, vorgänger: 'MarkierungItem', markierung: Markierung):
        super().__init__(parent)
        self.markierung = markierung
        self.vorgänger = vorgänger
        self.setRect(0, 0, basenlaenge, 20)
        self.setPen(Qt.NoPen)
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.nameItem = QGraphicsTextItem(self)
        self.nameItem.setDefaultTextColor(QColor('black'))
        self.nameItem.setFont(seqfont)
        self.nameItem.setPos(basenlaenge, 0)
        self.setFarbe()
        self.setName()
        self.setX(True)
        self.markierung.farbeChanged.connect(self.setFarbe)
        self.markierung.nameChanged.connect(self.setName)
        if self.vorgänger:
            self.vorgänger.nameItem.document().contentsChanged.connect(self.setX)
    
    def sceneRight(self):
        "Gibt den x-Wert der rechten Kante des Items zurück."

        rect = self.sceneBoundingRect()
        textrect = self.nameItem.boundingRect()
        return rect.x() + rect.width() + basenlaenge + textrect.width() - sequenznamewidth
    
    def setX(self, nosignal: bool = False):
        "Setzt auf der Grundlage des Vorgängers die x-Position."

        x = 0
        if self.vorgänger:
            x = self.vorgänger.sceneRight()
        self.setPos(x, 0)
        nosignal or self.nameItem.document().contentsChanged.emit()

    def setFarbe(self):
        "Setzt die Farbe auf Grundlage der Markerung."

        self.setBrush(QColor(self.markierung.farbe))

    def setName(self):
        "Setzt den Text auf Grundlage der Beschreibung der Markierung."

        self.nameItem.setPlainText(self.markierung.beschreibung)

