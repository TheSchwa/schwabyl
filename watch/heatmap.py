#!/usr/bin/env python
#
# Usage:
#
#   ./heatmap.py NAME [FILE]
#
# Example:
#
#   ./heatmap.py jon
#
# Joshua Haas
# 2017/02/16

import sys,pickle
from PyQt4 import QtCore,QtGui

################################################################################
# Main
################################################################################

import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)

def main(name,fname):
  app = QtGui.QApplication(sys.argv)
  table = QtGui.QTableView()
  model = MatrixModel(None)
  model.load_matrix(fname,name)
  table.setModel(model)
  table.verticalHeader().setDefaultSectionSize(16)
  table.horizontalHeader().setDefaultSectionSize(60)
  table.resize(500,800)
  table.show()
  sys.exit(app.exec_())

################################################################################
# HeatMap Model
################################################################################

class MatrixModel(QtCore.QAbstractTableModel):

  def __init__(self,parent):
    super(MatrixModel,self).__init__(parent)

    self.font = QtGui.QFont()
    self.font.setPixelSize(10)

  def load_matrix(self,fname,name):
    with open(fname,'rb') as f:
      self.matrix = pickle.load(f)[name]

  def rowCount(self,parent):
    return len(self.matrix)

  def columnCount(self,parent):
    return len(self.matrix[0])

  def data(self,index,role):
    if role==QtCore.Qt.DisplayRole:
      return round(self.matrix[index.row()][index.column()],2)
    if role==QtCore.Qt.FontRole:
      return self.font
    if role==QtCore.Qt.TextAlignmentRole:
      return QtCore.Qt.AlignCenter
    if role==QtCore.Qt.BackgroundRole:
      return self.get_color(self.matrix[index.row()][index.column()])
    return QtCore.QVariant()

  def headerData(self,section,orientation,role):
    if role==QtCore.Qt.DisplayRole:
      if orientation==QtCore.Qt.Horizontal:
        return ('mon','tue','wed','thu','fri','sat','sun')[section]
      else:
        hr = section/2
        m = 'A'
        if hr==0:
          hr = 12
        if hr>12:
          hr -= 12
          m = 'P'
        return '%.2d:%.2d %sM' % (hr,(30 if section%2 else 0),m)
    return QtCore.QVariant()

  def get_color(self,p):
    hue = 0 if p<=50 else 120
    sat = 255*abs(p-50)/50
    return QtGui.QBrush(QtGui.QColor.fromHsv(hue,sat,255))

################################################################################
# Main
################################################################################

if __name__ == '__main__':
  main(sys.argv[1],sys.argv[2] if len(sys.argv)>2 else 'log.pickle')
