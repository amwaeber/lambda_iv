from PyQt5 import QtWidgets


class Separator(QtWidgets.QFrame):

    def __init__(self, parent=None):
        super(Separator, self).__init__(parent)

        self.setFrameShape(QtWidgets.QFrame.HLine)
        self.setFrameShadow(QtWidgets.QFrame.Raised)
