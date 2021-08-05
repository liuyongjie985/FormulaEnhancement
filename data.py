from PyQt5.QtGui import *
from PyQt5.QtCore import *
import json
import numpy as np


class StrokePoint:
    def __init__(self, x, y, force, timestamp):
        # basic feature
        self.x = x
        self.y = y
        self.force = force
        self.timestamp = timestamp
        self.angle = 0
        self.endpoint = 0

    def qp(self, xo=0, yo=0):
        """返回 QPoint 对象"""
        return QPoint(int(round(self.x + xo)), int(round(self.y + yo)))

    def xy(self, xo=0, yo=0):
        """返回 ndarray 对象"""
        return np.array([self.x + xo, self.y + yo])

    def __str__(self):
        return 'StrokePoint(%d,%d)' % (self.x, self.y)

    def __repr__(self):
        return str(self)

    def set_flag(self, flag):
        self.flag = flag


class Stroke(list):
    def __init__(self, points=None):
        if points is None:
            points = []
        self.extend(points)
        self.segment = []
        self.label = 0
        self.brect = None

    def add_brect(self):
        if len(self) != 0:
            x1 = min(p.x for p in self)
            x2 = max(p.x for p in self)
            y1 = min(p.y for p in self)
            y2 = max(p.y for p in self)
            rect = x1, y1, x2 - x1, y2 - y1
            self.brect = rect
            return rect


def load_file(path):
    """读取 json 文件"""
    strokes = []
    try:
        j = json.load(open(path))
    except Exception:
        return strokes
    for ss in j:
        for s in ss['strokes']:
            stroke = Stroke()
            for p in s:
                # 列表前面加星号作用是将列表解开成两个独立的参数，传入函数
                # def add(a, b):
                #     return a + b
                # data = [4, 3]
                # add(*data)
                # equals to print add(4, 3)
                point = StrokePoint(*p)
                stroke.append(point)
            strokes.append(stroke)
    return strokes
