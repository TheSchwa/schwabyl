#!/usr/bin/env python

import pickle
import datetime as dt

class Tracker(object):

  INC_RATE = 0.25
  DEC_RATE = 0.25
  MINIMUM = 0*60
  MAXIMUM = 7*24*60*60

  def __init__(self):
    self.matrix = {}
    self.pending = {}
    self.last = {}

  def load(self,fname):
    try:
      with open(fname,'rb') as f:
        self.matrix = pickle.load(f)
    except:
      self.matrix = {}

  def save(self,fname):
    with open(fname,'wb') as f:
      pickle.dump(self.matrix,f,-1)

  # @param t (float) seconds since epoch
  # @param name (str) name of the owner
  # @param state ('+','-') whether arrived ('+') or left ('-')
  def update(self,t,name,state):
    if name in self.pending:
      if self.pending[name][0]!=state:
        old = self.pending[name][1]
        if (t-old>self.MINIMUM or state=='-') and t-old<self.MAXIMUM:
          t = (t if state=='+' else t-3*60)
          (old,new) = self.normalize(old,t)
          self.matrix_update(name,state,old,new)
    self.pending[name] = (state,t)

  def normalize(self,left,back):
    (left,back) = (self.round(left),self.round(back))
    if back==left:
      back += dt.timedelta(0,0,0,0,30)
    return (left,back)

  def round(self,t):
    return dt.datetime.fromtimestamp(1800*round(t/1800))

  def matrix_update(self,name,state,old,new):
    if name not in self.matrix:
      self.matrix[name] = [[50 for x in range(0,7)] for x in range(0,48)]
    matrix = self.matrix[name]

    (r1,c1) = self.time2index(old)
    (r2,c2) = self.time2index(new)

    (row,col) = (r1,c1)
    while row!=r2 or col!=c2:
      if not ((name in self.last) and (('-',row,col)==self.last[name])):
        self.inc(matrix,state,row,col)
        self.last[name] = (state,row,col)
      (row,col) = self.next(row,col)

  def time2index(self,t):
    return (2*t.hour+(t.minute==30),t.weekday())

  def next(self,row,col):
    return ((row+1)%48,(col+(row==47))%7)

  def inc(self,matrix,state,row,col):
    if state=='-':
      matrix[row][col] += self.INC_RATE*(100-matrix[row][col])
    elif state=='+':
      matrix[row][col] -= self.DEC_RATE*matrix[row][col]
