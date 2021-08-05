# encoding=utf-8
import math
import random
import json
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from data import Stroke, StrokePoint
import os
import numpy as np
import shutil


# from .draw_utils import *


def _getw(p1, p2):
    wscale = 1 + (p1.force + p2.force) / 2 * 0.001
    return 5 * wscale


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
                point = StrokePoint(*p)
                stroke.append(point)
            strokes.append(stroke)
    return strokes


def load_line_file(path):
    """读取 jpk 文本行对应的json 文件"""
    line_strokes = []
    try:
        j = json.load(open(path))
    except Exception:
        return line_strokes
    for ss in j:
        stroke = Stroke()
        for p in ss:
            point = StrokePoint(*p)
            stroke.append(point)
        line_strokes.append(stroke)
    return line_strokes


def save_json(strokes, fn):
    file = open(fn, 'w')
    new_strokes = []
    for stroke in strokes:
        new_stroke = []
        for p in stroke:
            # point = [int(p.x), int(p.y), p.force, p.flag]
            # print("p.x,p.y", p.x, p.y, type(p.x), type(p.y))
            point = [int(p.x), int(p.y), p.force, p.timestamp]
            new_stroke.append(point)
        new_strokes.append(new_stroke)
    data1 = {'strokes': new_strokes}
    data = [data1]
    # print("data",data,type(data))
    json.dump(data, file)


def save_line_json(line_strokes, fn):
    file = open(fn, 'w')
    new_strokes = []
    for stroke in line_strokes:
        new_stroke = []
        for p in stroke:
            # point = [int(p.x), int(p.y), p.force, p.flag]
            # print("p.x,p.y", p.x, p.y, type(p.x), type(p.y))
            point = [int(p.x), int(p.y), p.force, p.timestamp]
            new_stroke.append(point)
        new_strokes.append(new_stroke)
    # data1 = {'strokes': new_strokes}
    # data = [data1]
    # print("data",data,type(data))
    json.dump(new_strokes, file)


def draw_stroke_meta(painter, stroke, color):
    if len(stroke) == 0:
        return

    for p1, p2 in zip(stroke, stroke[1:]):
        path = QPainterPath()
        path.moveTo(p1.x, p1.y)
        path.lineTo(p2.x, p2.y)
        w = _getw(p1, p2)
        painter.setPen(QPen(color, w))
        painter.drawPath(path)

    for p in stroke:
        # painter.setPen(QPen(Qt.red, (1 + p.force / 500) * 5))
        painter.setPen(QPen(Qt.red, 5))
        painter.drawPoint(p.qp())


def draw_strokes_meta(pixmap, strokes, color=Qt.black):
    """绘制 strokes 的元数据,显示出笔迹点和相邻笔迹点之间的连线"""
    painter = QPainter(pixmap)
    for stroke in strokes:
        draw_stroke_meta(painter, stroke, color)
    painter.end()


def draw_stroke_baseline(pixmap, painter, stroke, color):
    if len(stroke) == 0:
        return
    for p1, p2 in zip(stroke, stroke[1:]):
        path = QPainterPath()
        path.moveTo(p1.x, p1.y)
        path.lineTo(p2.x, p2.y)
        # print("p1.x, p1.y", p1.x, p1.y)
        # print("p2.x, p2.y", p2.x, p2.y)
        w = _getw(p1, p2)
        painter.setPen(QPen(color, w))
        painter.drawPath(path)


def draw_strokes_baseline(pixmap, strokes, color=Qt.black):
    """绘制 strokes 的 baseline"""
    painter = QPainter(pixmap)

    # bound = [520, 480, 3600, 5240]
    # # bound = [480, 480, 5120, 7440]
    # lineNum = 20
    # lineInterval = (bound[3] - bound[1]) / lineNum
    # x1 = bound[0]
    # x2 = bound[2]
    # painter.setRenderHint(QPainter.Antialiasing)
    # for i in range(lineNum + 1):
    #     y = int(bound[1] + i * lineInterval)
    #     path = QPainterPath()
    #     path.moveTo(QPoint(x1, y))
    #     path.lineTo(QPoint(x2, y))
    #     if i == 0 or i == lineNum:
    #         w = 2
    #     else:
    #         w = 1
    #     painter.setPen(QPen(Qt.black, w))
    #     painter.drawPath(path)
    # font = QFont('Decorative', 100)
    # painter.setFont(font)
    # painter.drawText(2700, 340, "Date:")
    painter.translate(100, 100)
    for stroke in strokes:
        draw_stroke_baseline(pixmap, painter, stroke, color)
    painter.end()


def z_score(traceid2xy):
    u_x_numerator = 0
    u_x_denominator = 0
    u_y_numerator = 0
    u_y_denominator = 0
    for i, stroke in enumerate(traceid2xy):
        for j, point in enumerate(stroke):

            if j == 0:
                continue
            L = ((point.x - stroke[j - 1].x) ** 2 + (point.y - stroke[j - 1].y) ** 2) ** 0.5
            u_x_numerator += L * (point.x + stroke[j - 1].x) / 2
            u_x_denominator += L
            u_y_numerator += L * (point.y + stroke[j - 1].y) / 2
            u_y_denominator += L
    u_x = u_x_numerator / (u_x_denominator + 1e-8)
    u_y = u_y_numerator / (u_y_denominator + 1e-8)
    delta_x_numerator = 0
    delta_x_denominator = 0
    for i, stroke in enumerate(traceid2xy):
        for j, point in enumerate(stroke):
            if j == 0:
                continue
            L = ((point.x - stroke[j - 1].x) ** 2 + (point.y - stroke[j - 1].y) ** 2) ** 0.5
            delta_x_numerator += L / 3 * (
                    (point.x - u_x) ** 2 + (stroke[j - 1].x - u_x) ** 2 + (stroke[j - 1].x - u_x) * (point.x - u_x))
            delta_x_denominator += L

    delta_x = (delta_x_numerator / (delta_x_denominator + 1e-8)) ** 0.5

    for i, ss in enumerate(traceid2xy):
        stroke = Stroke()
        for j, point in enumerate(ss):
            print("point.x", point.x)
            point.x = (point.x - u_x) / delta_x
            point.y = (point.y - u_y) / delta_x


def draw_stroke_zscore(pixmap, painter, stroke, color):
    if len(stroke) == 0:
        return
    for p1, p2 in zip(stroke, stroke[1:]):
        path = QPainterPath()
        path.moveTo(p1.x * 1000, p1.y * 1000)
        path.lineTo(p2.x * 1000, p2.y * 1000)
        print("p1.x, p1.y", p1.x * 1000, p1.y * 1000)
        print("p2.x, p2.y", p2.x * 1000, p2.y * 1000)
        w = _getw(p1, p2)
        # painter.translate(-2000, -2000)
        painter.setPen(QPen(color, w))
        painter.drawPath(path)


def draw_strokes_zscore(pixmap, strokes, color=Qt.black):
    """绘制 strokes 的 baseline"""
    painter = QPainter(pixmap)
    painter.translate(2000, 2000)
    # 对笔画中的所有点进行zscore归一化
    z_score(strokes)

    for stroke in strokes:
        draw_stroke_zscore(pixmap, painter, stroke, color)
    painter.end()


def visualizeLines(line):
    new_traceid2xy = []
    # 将每一行单独进行可视化
    if len(line) == 0:
        pass
    ymin, ymax = 99999, -99999
    xmin, xmax = 99999, -99999
    for stroke in line:
        for p in stroke[1:]:
            ymin = min(ymin, p.y)
            ymax = max(ymax, p.y)
            xmin = min(xmin, p.x)
            xmax = max(xmax, p.x)
    height = ymax - ymin + 1
    width = xmax - xmin + 1 + 60
    print("number of strokes: %d, height=%d, width=%d" % (len(line), height, width))

    # 渲染每个笔画
    for ss in line:
        stroke = Stroke()
        for point in ss:
            stroke.append(StrokePoint(point.x - xmin + 30, point.y - ymin, point.force,
                                      point.timestamp))

        new_traceid2xy.append(stroke)
    return new_traceid2xy


def draw_stroke_visul(pixmap, painter, stroke, color):
    if len(stroke) == 0:
        return
    for p1, p2 in zip(stroke, stroke[1:]):
        path = QPainterPath()
        path.moveTo(p1.x, p1.y)
        path.lineTo(p2.x, p2.y)
        print("p1.x, p1.y", p1.x, p1.y)
        print("p2.x, p2.y", p2.x, p2.y)
        w = _getw(p1, p2)
        # painter.translate(-2000, -2000)
        painter.setPen(QPen(color, w))
        painter.drawPath(path)


def draw_strokes_visul(pixmap, strokes, color=Qt.black):
    """绘制 strokes 的 baseline"""
    painter = QPainter(pixmap)
    # painter.translate(2000,2000)
    # 对笔画中的所有点进行zscore归一化
    strokes = visualizeLines(strokes)

    for stroke in strokes:
        draw_stroke_visul(pixmap, painter, stroke, color)
    painter.end()


def add_length(stroke):
    # 沿着笔画最后两个点的方向增加长度
    if len(stroke) > 1:
        point_end = stroke[-1]
        point_ = stroke[-2]
        p_end = point_end.xy()
        p_ = point_.xy()
        l = 0
        for p1, p2 in zip(stroke, stroke[1:]):
            l += ((p1.x - p2.x) ** 2 + (p1.y - p2.y) ** 2) ** 0.5
        l_ = ((p_[0] - p_end[0]) ** 2 + (p_[1] - p_end[1]) ** 2) ** 0.5
        if l == 0:
            m = 0
        else:
            m = max(1 - l_ / l, 0)
        k = random.randint(1, len(stroke) // 15 + 1)
        while k:
            point1 = stroke[-1]
            point2 = stroke[-2]
            p1 = point1.xy()
            p2 = point2.xy()
            ipoint = StrokePoint((1 + m) * p1[0] - (m) * p2[0], (1 + m) * p1[1] - (m) * p2[1], point1.force,
                                 point1.timestamp + 1)
            stroke.append(ipoint)
            k -= 1


def cut_length(stroke):
    # 去除笔画最后几个点
    if len(stroke) >= 10:
        k = min(2, len(stroke) // 10)
        for i in range(k):
            stroke.pop()


def draw_stroke_lengthchange(pixmap, painter, stroke, f, color):
    if len(stroke) == 0:
        return
    # 单个笔画加长，缩短
    # 绘制出原始的笔画轨迹
    for p1, p2 in zip(stroke, stroke[1:]):
        path = QPainterPath()
        path.moveTo(p1.x, p1.y)
        path.lineTo(p2.x, p2.y)
        w = _getw(p1, p2)
        painter.setPen(QPen(Qt.black, 10))
        painter.drawPath(path)
    if f == 0:
        add_length(stroke)
    if f == 1:
        cut_length(stroke)
    if f >= 2:
        a = random.randint(0, 9)
        if a >= 4:
            add_length(stroke)
        elif a <= 3:
            cut_length(stroke)
    for p1, p2 in zip(stroke, stroke[1:]):
        path = QPainterPath()
        path.moveTo(p1.x, p1.y)
        path.lineTo(p2.x, p2.y)
        w = _getw(p1, p2)
        painter.setPen(QPen(Qt.red, 5))
        painter.drawPath(path)


def draw_strokes_lengthchange(pixmap, strokes, color=Qt.black):
    """绘制 strokes 的 lengthchange"""
    painter = QPainter(pixmap)
    # 笔画加长、缩短、随机加长或缩短
    f = random.randint(0, 4)
    f = 2
    print("f", f)
    for stroke in strokes:
        draw_stroke_lengthchange(pixmap, painter, stroke, f, color)
    painter.end()


def gen_stroke_lengthchange(stroke, f):
    if len(stroke) == 0:
        return []
    # 单个笔画加长，缩短
    if f == 0:
        add_length(stroke)
    if f == 1:
        cut_length(stroke)
    if f >= 2:
        a = random.randint(0, 9)
        if a >= 4:
            add_length(stroke)
        elif a <= 3:
            cut_length(stroke)


def gen_strokes_lengthchange(strokes):
    """生成 strokes 的 lengthchange，随机对笔画进行加长或者缩短"""
    f = random.randint(0, 4)
    for stroke in strokes:
        gen_stroke_lengthchange(stroke, f)


def draw_stroke_all_rotate(pixmap, painter, stroke, degree, color):
    if len(stroke) == 0:
        return
    # 绘制出原始的笔画轨迹
    for p1, p2 in zip(stroke, stroke[1:]):
        path = QPainterPath()
        path.moveTo(p1.x, p1.y)
        path.lineTo(p2.x, p2.y)
        w = _getw(p1, p2)
        painter.setPen(QPen(Qt.black, 10))
        painter.drawPath(path)
    # 对笔画进行整体旋转
    # degree = random.randint(15, 15)
    f = random.randint(0, 1)
    if f == 0:
        p0 = stroke[0]
        x = p0.x
        y = p0.y
    else:
        sum_x, sum_y = 0, 0
        for p in stroke:
            sum_x += p.x
            sum_y += p.y
        x = sum_x / len(stroke)
        y = sum_y / len(stroke)
    for p in stroke[1:]:
        l = ((p.x - x) ** 2 + (p.y - y) ** 2) ** 0.5
        if p.x == x:
            if p.y >= y:
                angle = math.pi / 2
            else:
                angle = - math.pi / 2
        else:
            angle = math.atan((p.y - y) / (p.x - x))
        if p.x - x < 0:
            angle += math.pi
        angle = ((angle * 180 / math.pi) + degree) * math.pi / 180
        p.x = int(x + l * math.cos(angle))
        p.y = int(y + l * math.sin(angle))

    for p1, p2 in zip(stroke, stroke[1:]):
        path = QPainterPath()
        path.moveTo(p1.x, p1.y)
        path.lineTo(p2.x, p2.y)
        w = _getw(p1, p2)
        painter.setPen(QPen(Qt.red, 5))
        painter.drawPath(path)


def draw_strokes_all_rotate(pixmap, strokes, color=Qt.black):
    """绘制 strokes 的 all_rotate,对笔画进行整体旋转"""
    painter = QPainter(pixmap)
    # degree = random.randint(-15, 15)
    # print("degree", degree)
    f1 = random.randint(0, 1)
    if f1 == 0:
        degree = random.randint(-10, -1)
    if f1 == 1:
        degree = random.randint(1, 10)
    # degree = 5
    print("degree", degree)
    for stroke in strokes:
        draw_stroke_all_rotate(pixmap, painter, stroke, degree, color)
    painter.end()


def gen_stroke_all_rotate(stroke, degree):
    if len(stroke) == 0:
        return
    # 对笔画进行整体旋转
    # degree = random.randint(15, 15)
    f = random.randint(0, 1)
    if f == 0:
        p0 = stroke[0]
        x = p0.x
        y = p0.y
    else:
        sum_x, sum_y = 0, 0
        for p in stroke:
            sum_x += p.x
            sum_y += p.y
        x = sum_x / len(stroke)
        y = sum_y / len(stroke)
    for p in stroke[1:]:
        l = ((p.x - x) ** 2 + (p.y - y) ** 2) ** 0.5
        if p.x == x:
            if p.y >= y:
                angle = math.pi / 2
            else:
                angle = - math.pi / 2
        else:
            angle = math.atan((p.y - y) / (p.x - x))
        if p.x - x < 0:
            angle += math.pi
        angle = ((angle * 180 / math.pi) + degree) * math.pi / 180
        p.x = int(x + l * math.cos(angle))
        p.y = int(y + l * math.sin(angle))


def gen_strokes_all_rotate(strokes):
    """绘制 strokes 的 all_rotate,对笔画进行整体旋转"""
    f1 = random.randint(0, 1)
    if f1 == 0:
        degree = random.randint(-10, -1)
    if f1 == 1:
        degree = random.randint(1, 10)
    for stroke in strokes:
        gen_stroke_all_rotate(stroke, degree)


###############################################################################
# rotate transformation
def draw_stroke_all_rotate_1(pixmap, painter, stroke, degree, color):
    if len(stroke) == 0:
        return
    # 绘制出原始的笔画轨迹
    for p1, p2 in zip(stroke, stroke[1:]):
        path = QPainterPath()
        path.moveTo(p1.x, p1.y)
        path.lineTo(p2.x, p2.y)
        w = _getw(p1, p2)
        painter.setPen(QPen(Qt.black, 10))
        painter.drawPath(path)
    # 对笔画进行旋转变换
    # degree = random.randint(0, 20)
    for p in stroke:
        x = p.x
        y = p.y
        p.x = x * math.cos(degree * math.pi / 180) + y * math.sin(degree * math.pi / 180)
        p.y = x * math.sin(degree * math.pi / 180) + y * math.cos(degree * math.pi / 180)

    for p1, p2 in zip(stroke, stroke[1:]):
        path = QPainterPath()
        path.moveTo(p1.x, p1.y)
        path.lineTo(p2.x, p2.y)
        w = _getw(p1, p2)
        painter.setPen(QPen(Qt.red, 5))
        painter.drawPath(path)


def draw_strokes_all_rotate_1(pixmap, strokes, color=Qt.black):
    """绘制 strokes 的 rotate_1,对笔画进行旋转变换"""
    painter = QPainter(pixmap)
    # 角度值
    degree = 0
    f1 = random.randint(0, 1)
    if f1 == 0:
        degree = random.randint(-10, -1)
    if f1 == 1:
        degree = random.randint(1, 10)
    # degree = 5
    print("degree", degree)
    for stroke in strokes:
        draw_stroke_all_rotate_1(pixmap, painter, stroke, degree, color)
    painter.end()


def gen_stroke_all_rotate_1(stroke, degree):
    if len(stroke) == 0:
        return
    # 对笔画进行旋转变换
    # degree = random.randint(0, 20)
    for p in stroke:
        x = p.x
        y = p.y
        p.x = x * math.cos(degree * math.pi / 180) + y * math.sin(degree * math.pi / 180)
        p.y = x * math.sin(degree * math.pi / 180) + y * math.cos(degree * math.pi / 180)


def gen_strokes_all_rotate_1(strokes):
    """绘制 strokes 的 rotate_1,对笔画进行旋转变换"""

    f1 = random.randint(0, 1)
    if f1 == 0:
        degree = random.randint(-10, -1)
    if f1 == 1:
        degree = random.randint(1, 10)
    print("degree", degree)
    for stroke in strokes:
        gen_stroke_all_rotate_1(stroke, degree)


def draw_stroke_rotate(pixmap, painter, stroke, color):
    if len(stroke) == 0:
        return
    # 绘制出原始的笔画轨迹
    for p1, p2 in zip(stroke, stroke[1:]):
        path = QPainterPath()
        path.moveTo(p1.x, p1.y)
        path.lineTo(p2.x, p2.y)
        w = _getw(p1, p2)
        painter.setPen(QPen(Qt.black, 10))
        painter.drawPath(path)
    # 对笔画进行旋转
    degree = random.randint(-10, 10)
    print("degree", degree)
    f = random.randint(0, 1)
    if f == 0:
        p0 = stroke[0]
        x = p0.x
        y = p0.y
    else:
        sum_x, sum_y = 0, 0
        for p in stroke:
            sum_x += p.x
            sum_y += p.y
        x = sum_x / len(stroke)
        y = sum_y / len(stroke)
    for p in stroke[1:]:
        l = ((p.x - x) ** 2 + (p.y - y) ** 2) ** 0.5
        if p.x == x:
            if p.y >= y:
                angle = math.pi / 2
            else:
                angle = - math.pi / 2
        else:
            angle = math.atan((p.y - y) / (p.x - x))
        if p.x - x < 0:
            angle += math.pi
        angle = ((angle * 180 / math.pi) + degree) * math.pi / 180
        p.x = int(x + l * math.cos(angle))
        p.y = int(y + l * math.sin(angle))

    for p1, p2 in zip(stroke, stroke[1:]):
        path = QPainterPath()
        path.moveTo(p1.x, p1.y)
        path.lineTo(p2.x, p2.y)
        w = _getw(p1, p2)
        painter.setPen(QPen(Qt.red, 5))
        painter.drawPath(path)


def draw_strokes_rotate(pixmap, strokes, color=Qt.black):
    """绘制 strokes 的 rotate"""
    painter = QPainter(pixmap)
    for stroke in strokes:
        draw_stroke_rotate(pixmap, painter, stroke, color)
    painter.end()


def gen_stroke_rotate(stroke):
    if len(stroke) == 0:
        return []
    # 对笔画进行旋转
    degree = random.randint(-10, 10)
    f = random.randint(0, 1)
    if f == 0:
        p0 = stroke[0]
        x = p0.x
        y = p0.y
    else:
        sum_x, sum_y = 0, 0
        for p in stroke:
            sum_x += p.x
            sum_y += p.y
        x = sum_x / len(stroke)
        y = sum_y / len(stroke)

    for p in stroke[1:]:
        l = ((p.x - x) ** 2 + (p.y - y) ** 2) ** 0.5
        if p.x == x:
            if p.y >= y:
                angle = math.pi / 2
            else:
                angle = - math.pi / 2
        else:
            angle = math.atan((p.y - y) / (p.x - x))
        if p.x - x < 0:
            angle += math.pi

        angle = ((angle * 180 / math.pi) + degree) * math.pi / 180
        p.x = int(x + l * math.cos(angle))
        p.y = int(y + l * math.sin(angle))


def gen_strokes_rotate(strokes):
    """绘制 strokes 的 rotate"""
    for stroke in strokes:
        gen_stroke_rotate(stroke)


def draw_stroke_scale(pixmap, painter, stroke, scale, color):
    if len(stroke) == 0:
        return
    # 绘制出原始的笔画轨迹
    for p1, p2 in zip(stroke, stroke[1:]):
        path = QPainterPath()
        path.moveTo(p1.x, p1.y)
        path.lineTo(p2.x, p2.y)
        w = _getw(p1, p2)
        painter.setPen(QPen(Qt.black, 10))
        painter.drawPath(path)
    # 对笔画进行缩放
    # 计算笔画中的中心点
    sum_x, sum_y = 0, 0
    for p in stroke:
        sum_x += p.x
        sum_y += p.y
    x = sum_x / len(stroke)
    y = sum_y / len(stroke)
    for p in stroke:
        p.x = x + scale * (p.x - x)
        p.y = y + scale * (p.y - y)

    for p1, p2 in zip(stroke, stroke[1:]):
        path = QPainterPath()
        path.moveTo(p1.x, p1.y)
        path.lineTo(p2.x, p2.y)
        w = _getw(p1, p2)
        painter.setPen(QPen(Qt.red, 5))
        painter.drawPath(path)


def draw_strokes_scale(pixmap, strokes, color=Qt.black):
    """绘制 strokes 的 scale，对笔画进行缩放"""
    painter = QPainter(pixmap)
    scale = random.uniform(0.7, 1.3)
    print("scale", scale)
    for stroke in strokes:
        draw_stroke_scale(pixmap, painter, stroke, scale, color)
    painter.end()


def gen_stroke_scale(stroke, scale):
    if len(stroke) == 0:
        return
    # 对笔画进行缩放
    # 计算笔画中的中心点
    sum_x, sum_y = 0, 0
    for p in stroke:
        sum_x += p.x
        sum_y += p.y
    x = sum_x / len(stroke)
    y = sum_y / len(stroke)
    for p in stroke:
        p.x = x + scale * (p.x - x)
        p.y = y + scale * (p.y - y)


def gen_strokes_scale(strokes):
    """绘制 strokes 的 scale，对笔画进行缩放"""
    scale = random.uniform(0.7, 1.3)
    for stroke in strokes:
        gen_stroke_scale(stroke, scale)


def draw_stroke_gaussian_noisy(pixmap, painter, stroke, mean, sigma, color):
    if len(stroke) == 0:
        return
    # 绘制出原始的笔画轨迹
    for p1, p2 in zip(stroke, stroke[1:]):
        path = QPainterPath()
        path.moveTo(p1.x, p1.y)
        path.lineTo(p2.x, p2.y)
        w = _getw(p1, p2)
        painter.setPen(QPen(Qt.black, 10))
        painter.drawPath(path)
    # 对笔画中的所有轨迹点加高斯噪音
    # mean = random.uniform(0, 1)
    # sigma = random.uniform(1, 2)
    for p in stroke:
        dx = random.gauss(mean, sigma)
        dy = random.gauss(mean, sigma)
        p.x += dx
        p.y += dy
        # print("dx,dy", dx, dy)

    for p1, p2 in zip(stroke, stroke[1:]):
        path = QPainterPath()
        path.moveTo(p1.x, p1.y)
        path.lineTo(p2.x, p2.y)
        w = _getw(p1, p2)
        painter.setPen(QPen(Qt.red, 5))
        painter.drawPath(path)


def draw_strokes_gaussian_noisy(pixmap, strokes, color=Qt.black):
    """绘制 strokes 的 gaussianNoisy，对笔画中的所有轨迹点加高斯噪音"""
    painter = QPainter(pixmap)
    mean = random.uniform(0, 1)
    sigma = random.uniform(1, 2)
    print("mean,sigma", mean, sigma)
    for stroke in strokes:
        draw_stroke_gaussian_noisy(pixmap, painter, stroke, mean, sigma, color)
    painter.end()


def gen_stroke_gaussian_noisy(stroke, mean, sigma):
    if len(stroke) == 0:
        return
    for p in stroke:
        dx = random.gauss(mean, sigma)
        dy = random.gauss(mean, sigma)
        p.x += dx
        p.y += dy


def gen_strokes_gaussian_noisy(strokes):
    """绘制 strokes 的 gaussianNoisy，对笔画中的所有轨迹点加高斯噪音"""
    mean = random.uniform(0, 1)
    sigma = random.uniform(1, 2)
    for stroke in strokes:
        gen_stroke_gaussian_noisy(stroke, mean, sigma)


def draw_stroke_unsuit_ratio(pixmap, painter, stroke, color=Qt.black):
    if len(stroke) == 0:
        return
    # 绘制原始的笔画轨迹
    for p1, p2 in zip(stroke, stroke[1:]):
        path = QPainterPath()
        path.moveTo(p1.x, p1.y)
        path.lineTo(p2.x, p2.y)
        w = _getw(p1, p2)
        painter.setPen(QPen(Qt.black, 10))
        painter.drawPath(path)
    # 对每个笔画随机进行移动
    x, y, width, height = stroke.add_brect()
    radio = random.uniform(-0.15, 0.15)
    w_scale = width * radio
    h_scale = height * radio
    for p in stroke:
        p.x += w_scale
        p.y += h_scale

    for p1, p2 in zip(stroke, stroke[1:]):
        path = QPainterPath()
        path.moveTo(p1.x, p1.y)
        path.lineTo(p2.x, p2.y)
        w = _getw(p1, p2)
        painter.setPen(QPen(Qt.red, 5))
        painter.drawPath(path)


def draw_strokes_unsuit_ratio(pixmap, strokes):
    """绘制 strokes 的 unsuit_ratio,对每个笔画随机进行移动"""
    painter = QPainter(pixmap)
    for stroke in strokes:
        draw_stroke_unsuit_ratio(pixmap, painter, stroke)
    painter.end()


def gen_stroke_unsuit_ratio(stroke):
    if len(stroke) == 0:
        return []
    # 对每个笔画随机进行移动
    x, y, width, height = stroke.add_brect()
    radio = random.uniform(-0.15, 0.15)
    w_scale = width * radio
    h_scale = height * radio
    for p in stroke:
        p.x += w_scale
        p.y += h_scale


def gen_strokes_unsuit_ratio(strokes):
    """绘制 strokes 的 unsuit_ratio,对每个笔画随机进行移动"""
    for stroke in strokes:
        gen_stroke_unsuit_ratio(stroke)


def draw_stroke_turn(pixmap, painter, stroke, color):
    if len(stroke) == 0:
        return
    # 绘制出原始的笔画轨迹
    for p1, p2 in zip(stroke, stroke[1:]):
        path = QPainterPath()
        path.moveTo(p1.x, p1.y)
        path.lineTo(p2.x, p2.y)
        w = _getw(p1, p2)
        painter.setPen(QPen(Qt.black, 10))
        painter.drawPath(path)
    # 产生不协调的转折，笔画弯折
    # 笔画中每个点的移动值递增或递减
    x_, y_, width, height = stroke.add_brect()
    radio = random.uniform(0.01, 0.012)
    l = 0
    for p1, p2 in zip(stroke, stroke[1:]):
        l += ((p1.x - p2.x) ** 2 + (p1.y - p2.y) ** 2) ** 0.5
    change = 0
    t = min(max(height, width) * radio, l / 80, 12 / len(stroke))
    c = random.randint(0, 1)
    for p in stroke:
        if c == 0:
            p.y += int(change + t)
            p.x += int(change + t)
            change += t
        else:
            p.y += int(change - t)
            p.x += int(change - t)
            change -= t

    for p1, p2 in zip(stroke, stroke[1:]):
        path = QPainterPath()
        path.moveTo(p1.x, p1.y)
        path.lineTo(p2.x, p2.y)
        w = _getw(p1, p2)
        painter.setPen(QPen(Qt.red, 5))
        painter.drawPath(path)


def draw_strokes_turn(pixmap, strokes, color=Qt.black):
    """绘制 strokes 的 turn，笔画中每个点的移动值递增或递减"""
    painter = QPainter(pixmap)
    for stroke in strokes:
        draw_stroke_turn(pixmap, painter, stroke, color)
    painter.end()


def gen_stroke_turn(stroke):
    if len(stroke) == 0:
        return []
    # 产生不协调的转折，笔画弯折
    # 笔画中每个点的移动值递增或递减
    x_, y_, width, height = stroke.add_brect()
    radio = random.uniform(0.01, 0.012)
    l = 0
    for p1, p2 in zip(stroke, stroke[1:]):
        l += ((p1.x - p2.x) ** 2 + (p1.y - p2.y) ** 2) ** 0.5
    change = 0
    t = min(max(height, width) * radio, l / 80, 12 / len(stroke))
    c = random.randint(0, 1)
    for p in stroke:
        if c == 0:
            p.y += int(change + t)
            p.x += int(change + t)
            change += t
        else:
            p.y += int(change - t)
            p.x += int(change - t)
            change -= t


def gen_strokes_turn(strokes):
    """绘制 strokes 的 turn,笔笔画中每个点的移动值递增或递减"""
    for stroke in strokes:
        gen_stroke_turn(stroke)


def draw_stroke_distort_random_point(pixmap, painter, stroke, color):
    if len(stroke) == 0:
        return
    # 绘制出原始的笔画轨迹
    for p1, p2 in zip(stroke, stroke[1:]):
        path = QPainterPath()
        path.moveTo(p1.x, p1.y)
        path.lineTo(p2.x, p2.y)
        w = _getw(p1, p2)
        painter.setPen(QPen(Qt.black, 10))
        painter.drawPath(path)
    # 产生不协调的转折，笔画弯折
    # 对笔画中的某些点进行移动，产生毛刺
    l = 0
    for p1, p2 in zip(stroke, stroke[1:]):
        l += ((p1.x - p2.x) ** 2 + (p1.y - p2.y) ** 2) ** 0.5
    radio = random.uniform(-0.1, 0.1)
    x_, y_, width, height = stroke.add_brect()
    h_scale = height * radio
    w_scale = width * radio
    for p in stroke:
        c = random.randint(0, 7)
        if c <= 1:
            f = random.randint(0, 1)
            if f == 0:
                p.y += min(l / 75, h_scale)
            if f == 1:
                p.y -= min(l / 75, h_scale)

    for p1, p2 in zip(stroke, stroke[1:]):
        path = QPainterPath()
        path.moveTo(p1.x, p1.y)
        path.lineTo(p2.x, p2.y)
        w = _getw(p1, p2)
        painter.setPen(QPen(Qt.red, 5))
        painter.drawPath(path)


def draw_strokes_distort_random_point(pixmap, strokes, color=Qt.black):
    """绘制 strokes 的 distort_random_point，笔画中的点随机沿y轴上下移动一定的值"""
    painter = QPainter(pixmap)
    for stroke in strokes:
        draw_stroke_distort_random_point(pixmap, painter, stroke, color)
    painter.end()


def gen_stroke_distort_random_point(stroke):
    if len(stroke) == 0:
        return []
    # 产生不协调的转折，笔画弯折
    # 对笔画中的某些点进行移动，产生毛刺
    l = 0
    for p1, p2 in zip(stroke, stroke[1:]):
        l += ((p1.x - p2.x) ** 2 + (p1.y - p2.y) ** 2) ** 0.5
    radio = random.uniform(-0.1, 0.1)
    x_, y_, width, height = stroke.add_brect()
    h_scale = height * radio
    w_scale = width * radio
    for p in stroke:
        c = random.randint(0, 7)
        if c <= 1:
            f = random.randint(0, 1)
            if f == 0:
                p.y += min(l / 75, h_scale)
            if f == 1:
                p.y -= min(l / 75, h_scale)


def gen_strokes_distort_random_point(strokes):
    """绘制 strokes 的 distort_random_point,笔画中的点随机沿y轴上下移动一定的值"""
    for stroke in strokes:
        gen_stroke_distort_random_point(stroke)


##################################################
# detect corner point + distort
# different handwriting styles
from scipy.spatial.distance import pdist


def cal_Curvature(stroke):
    pre_k = 0
    for i in range(1, len(stroke) - 1):
        x = (stroke[i].x - stroke[i - 1].x, stroke[i].y - stroke[i - 1].y)
        y = (stroke[i + 1].x - stroke[i].x, stroke[i + 1].y - stroke[i].y)
        d = 1 - pdist([x, y], 'cosine')
        sin = np.sqrt(1 - d ** 2)
        dis = np.sqrt((stroke[i - 1].x - stroke[i + 1].x) ** 2 + (stroke[i - 1].y - stroke[i + 1].y) ** 2)
        if dis != 0:
            k = 2 * sin / dis
        else:
            k = 0
        # if (i != 1 and (pre_k / k) > 1.2):
        if k != 1 and k > 0.02:
            stroke[i].endpoint = 1
        pre_k = k
        print("center point numebr: " + str(i) + " curvature: " + str(k) + " is endpoint? " + str(stroke[i].endpoint))


def cal_near_curva(stroke):
    n_curva = []
    n_curva.append(0)
    if len(stroke) > 20:
        k = 5
    else:
        k = int(len(stroke) / 4)
    if len(stroke) > 2:
        for i in range(1, len(stroke) - 1):
            # k = min(10, i)
            # k = min(k, len(stroke) - i - 1)
            if i + k < len(stroke):
                x_fd = stroke[i + k].x - stroke[i].x
                y_fd = stroke[i + k].y - stroke[i].y
            else:
                x_fd = stroke[-1].x - stroke[i].x
                y_fd = stroke[-1].y - stroke[i].y
            if i - k >= 0:
                x_bd = stroke[i - k].x - stroke[i].x
                y_bd = stroke[i - k].y - stroke[i].y
            else:
                x_bd = stroke[0].x - stroke[i].x
                y_bd = stroke[0].y - stroke[i].y
            x_c = abs(x_fd + x_bd)
            y_c = abs(y_fd + y_bd)
            n_curva.append(max(x_c, y_c))
    n_curva.append(0)
    # print("stroke length: " + str(len(stroke)) + "n_curva length: " + str(len(n_curva)))
    for i in range(1, len(stroke) - 1):
        if i + k < len(stroke) and i - k >= 0:
            if n_curva[i] >= max(n_curva[i - k:i + k + 1]) and n_curva[i] >= k:
                stroke[i].endpoint = 1
        elif i + k < len(stroke):
            if n_curva[i] >= max(n_curva[0:i + k + 1]) and n_curva[i] >= k:
                stroke[i].endpoint = 1
        elif i - k >= 0:
            if n_curva[i] >= max(n_curva[i - k:len(stroke)]) and n_curva[i] >= k:
                stroke[i].endpoint = 1
        else:
            if n_curva[i] >= max(n_curva[0:len(stroke)]) and n_curva[i] >= k:
                stroke[i].endpoint = 1


def detect_corner_points(stroke):
    # the average bending value of region of support
    curva = []
    curva.append(0)
    # the length of region of support
    n_curva = []
    n_curva.append(0)

    if len(stroke) > 2:
        for i in range(1, len(stroke) - 1):
            # bending value of region of support
            temp_bend = []
            flag = 0
            for k in range(1, len(stroke) - 1):
                if i + k < len(stroke):
                    x_fd = stroke[i + k].x - stroke[i].x
                    y_fd = stroke[i + k].y - stroke[i].y
                else:
                    pro = sum(temp_bend) / len(temp_bend)
                    curva.append(pro)
                    n_curva.append(len(temp_bend))
                    flag = 1
                    break

                if i - k >= 0:
                    x_bd = stroke[i - k].x - stroke[i].x
                    y_bd = stroke[i - k].y - stroke[i].y
                else:
                    pro = sum(temp_bend) / len(temp_bend)
                    curva.append(pro)
                    n_curva.append(len(temp_bend))
                    flag = 1
                    break

                x_c = abs(x_fd + x_bd)
                y_c = abs(y_fd + y_bd)
                temp_bend.append(max(x_c, y_c))
                # print("temp_bend", temp_bend)
                if len(stroke) == 3:
                    pro = sum(temp_bend) / len(temp_bend)
                    curva.append(pro)
                    n_curva.append(len(temp_bend))
                    flag = 1
                if k > 1:
                    if temp_bend[k - 2] < max(x_c, y_c):
                        pro = sum(temp_bend) / len(temp_bend)
                        curva.append(pro)
                        n_curva.append(len(temp_bend))
                        flag = 1
                        break
            if flag == 0:
                pro = sum(temp_bend) / len(temp_bend)
                curva.append(pro)
                n_curva.append(len(temp_bend))

    curva.append(0)
    n_curva.append(0)
    # print("stroke length: " + str(len(stroke)))
    # print("the average bending value of region of support: ", curva)
    # print("the length of region of support: ", n_curva)

    eplison = 30
    for p in stroke:
        p.endpoint = 1
    for i in range(0, len(stroke)):
        if curva[i] < eplison:
            stroke[i].endpoint = 0
        if i - 1 >= 0 and curva[i] < curva[i - 1]:
            stroke[i].endpoint = 0
        if i + 1 < len(stroke) and curva[i] < curva[i + 1]:
            stroke[i].endpoint = 0
        if i - 1 >= 0 and curva[i] == curva[i - 1] and n_curva[i] < n_curva[i - 1]:
            stroke[i].endpoint = 0
        if i + 1 < len(stroke) and curva[i] == curva[i + 1] and n_curva[i] <= n_curva[i + 1]:
            stroke[i].endpoint = 0


def draw_stroke_corner(pixmap, painter, stroke, color):
    if len(stroke) == 0:
        return
    # 绘制出原始的笔画轨迹
    for p1, p2 in zip(stroke, stroke[1:]):
        path = QPainterPath()
        path.moveTo(p1.x, p1.y)
        path.lineTo(p2.x, p2.y)
        w = _getw(p1, p2)
        painter.setPen(QPen(Qt.black, w))
        painter.drawPath(path)

    # cal_near_curva(stroke)
    # cal_Curvature(stroke)
    detect_corner_points(stroke)

    for p in stroke:
        if p.endpoint == 1:
            painter.setPen(QPen(Qt.red, (1 + p.force / 500) * 5))
            painter.drawPoint(p.qp())


def draw_strokes_corner(pixmap, strokes, color=Qt.black):
    """绘制 strokes 的 corner,检测笔画中的拐点"""
    painter = QPainter(pixmap)
    for stroke in strokes:
        draw_stroke_corner(pixmap, painter, stroke, color)
    painter.end()


def draw_stroke_distort_corner_point(pixmap, painter, stroke, color):
    if len(stroke) == 0:
        return
    # 绘制出原始的笔画轨迹
    for p1, p2 in zip(stroke, stroke[1:]):
        path = QPainterPath()
        path.moveTo(p1.x, p1.y)
        path.lineTo(p2.x, p2.y)
        # print("p1.x,p1.y", p1.x, p1.y)
        w = _getw(p1, p2)
        painter.setPen(QPen(Qt.black, 10))
        painter.drawPath(path)
    # 检测笔画中的拐点
    detect_corner_points(stroke)
    # 对笔画中的点进行扭曲
    temp_corner = []
    temp_corner_1 = []
    ratio = 5
    t1 = random.uniform(-2, 2)
    t2 = random.uniform(-2, 2)
    for i in range(len(stroke)):
        if stroke[i].endpoint == 1:
            x1 = stroke[i].x
            y1 = stroke[i].y
            temp_corner.append([x1, y1])
            stroke[i].x = x1 + ratio * t1
            stroke[i].y = y1 + ratio * t2
            temp_corner_1.append([stroke[i].x, stroke[i].y])
        # if len(temp_corner) == 2:
        #     for j in range(i - 1, -1, -1):
        #         print("temp_corner", temp_corner, j)
        #         print("stroke[j].x", stroke[j].x, type(stroke[j].x))
        #         print("temp_corner[0][0]", temp_corner[0][0], type(temp_corner[0][0]))
        #         if stroke[j].x == temp_corner_1[0][0] and stroke[j].y == temp_corner_1[0][1]:
        #             del temp_corner[0]
        #             del temp_corner_1[0]
        #             print("---------temp_corner", temp_corner)
        #             break
        #         else:
        #             print("stroke[j].x,stroke[j].y", stroke[j].x, stroke[j].y)
        #             dis_x = temp_corner[0][0] - temp_corner[1][0]
        #             dis_y = temp_corner[0][1] - temp_corner[1][1]
        #             d_ij = math.sqrt(dis_x ** 2 + dis_y ** 2)
        #
        #             dis_x = temp_corner[0][0] - stroke[j].x
        #             dis_y = temp_corner[0][1] - stroke[j].y
        #             d_ik = math.sqrt(dis_x ** 2 + dis_y ** 2)
        #             print("d_ij,d_ik / max(d_ij,1)", d_ij, d_ik / max(d_ij, 1))
        # stroke[j].x = temp_corner[0][0] + (stroke[j].x - temp_corner[0][0]) * d_ik / max(d_ij, 200)
        # stroke[j].y = temp_corner[0][1] + (stroke[j].y - temp_corner[0][1]) * d_ik / max(d_ij, 200)

        # stroke[j].x = temp_corner_1[0][0] + (temp_corner_1[1][0] - temp_corner_1[0][0]) * d_ik / max(d_ij, 200)
        # stroke[j].y = temp_corner_1[0][1] + (temp_corner_1[1][1] - temp_corner_1[0][1]) * d_ik / max(d_ij, 200)
        # print("------stroke[j].x,stroke[j].y", stroke[j].x, stroke[j].y)

        # stroke[j].x = temp_corner_1[0][0] + (stroke[j].x - temp_corner[0][0]) * d_ik / max(d_ij, 200)
        # stroke[j].y = temp_corner_1[0][1] + (stroke[j].y - temp_corner[0][1]) * d_ik / max(d_ij, 200)

        # stroke[j].x = (temp_corner_1[1][0] * (stroke[j].x - temp_corner[0][0]) + temp_corner_1[0][0] * (
        #         temp_corner[1][0] - stroke[j].x)) / max(temp_corner[1][0] - temp_corner[0][0], 100)
        # stroke[j].y = (temp_corner_1[1][1] * (stroke[j].y - temp_corner[0][1]) + temp_corner_1[0][1] * (
        #         temp_corner[1][1] - stroke[j].y)) / max(temp_corner[1][1] - temp_corner[0][1], 100)
        #
        # print("------stroke[j].x,stroke[j].y", stroke[j].x, stroke[j].y)
    for p1, p2 in zip(stroke, stroke[1:]):
        path = QPainterPath()
        path.moveTo(p1.x, p1.y)
        path.lineTo(p2.x, p2.y)
        w = _getw(p1, p2)
        painter.setPen(QPen(Qt.red, 5))
        painter.drawPath(path)


def draw_strokes_distort_corner_point(pixmap, strokes, color=Qt.black):
    """绘制 strokes 的 distort，对笔画中的点进行扭曲"""
    painter = QPainter(pixmap)
    # ratio = 5
    # t1 = random.uniform(-2, 2)
    # t2 = random.uniform(-2, 2)
    for stroke in strokes:
        draw_stroke_distort_corner_point(pixmap, painter, stroke, color)
    painter.end()


def gen_stroke_distort_corner_point(stroke):
    if len(stroke) == 0:
        return
    # 检测笔画中的拐点
    detect_corner_points(stroke)
    # 对笔画中的点进行扭曲
    ratio = 5
    t1 = random.uniform(-2, 2)
    t2 = random.uniform(-2, 2)
    for i in range(len(stroke)):
        if stroke[i].endpoint == 1:
            x1 = stroke[i].x
            y1 = stroke[i].y
            stroke[i].x = x1 + ratio * t1
            stroke[i].y = y1 + ratio * t2


def gen_strokes_distort_corner_point(strokes):
    """绘制 strokes 的 distort，对笔画中的点进行扭曲"""
    for stroke in strokes:
        gen_stroke_distort_corner_point(stroke)


def _dis(p0, p1):
    """返回两个 qpoint 的距离和水平垂直的分量, ndarray 的距离可以用 np 计算"""
    dis_x = p1.x - p0.x
    dis_y = p1.y - p0.y
    return math.sqrt(dis_x ** 2 + dis_y ** 2), dis_x, dis_y


def get_degree_via_point(p1, p2):
    diff_x = p2.x - p1.x
    diff_y = p2.y - p1.y
    z = math.sqrt(diff_x ** 2 + diff_y ** 2)
    if z == 0:
        return 10
    sin = -diff_y / z
    cos = diff_x / z
    return get_degree_via_sincos(sin, cos)


def get_degree_via_sincos(sin, cos):
    """给定坐标的 sin, cos 返回对应的角度，角度是 0-35"""
    if sin > 0.98481:
        # 80-90 90-100
        return 8 if cos > 0 else 9
    elif sin > 0.93969:
        # 70-80 100-110
        return 7 if cos > 0 else 10
    elif sin > 0.86603:
        # 60-70 110-120
        return 6 if cos > 0 else 11
    elif sin > 0.76604:
        # 50-60 120-130
        return 5 if cos > 0 else 12
    elif sin > 0.64279:
        # 40-50 130-140
        return 4 if cos > 0 else 13
    elif sin > 0.5:
        # 30-40 140-150
        return 3 if cos > 0 else 14
    elif sin > 0.34202:
        # 20-30 150-160
        return 2 if cos > 0 else 15
    elif sin > 0.17365:
        # 10-20 160-170
        return 1 if cos > 0 else 16
    elif sin > 0:
        # 0-10 170-180
        return 0 if cos > 0 else 17
    elif sin > -0.17365:
        # 350-360 180-190
        return 35 if cos > 0 else 18
    elif sin > -0.34202:
        # 340-350 190-200
        return 34 if cos > 0 else 19
    elif sin > -0.5:
        # 330-340 200-210
        return 33 if cos > 0 else 20
    elif sin > -0.64279:
        # 320-330 210-220
        return 32 if cos > 0 else 21
    elif sin > -0.76604:
        # 310-320 220-230
        return 31 if cos > 0 else 22
    elif sin > -0.86603:
        # 300-310 230-240
        return 30 if cos > 0 else 23
    elif sin > -0.93969:
        # 290-300 240-250
        return 29 if cos > 0 else 24
    elif sin > -0.98481:
        # 280-290 250-260
        return 28 if cos > 0 else 25
    else:
        # 270-280 260-270
        return 27 if cos > 0 else 26


def draw_strokes_link(pixmap, strokes):
    """绘制 strokes 的 link,即连笔"""
    # 生成连笔
    # 绘出原始的笔迹
    painter = QPainter(pixmap)
    for stroke in strokes:
        for p1, p2 in zip(stroke, stroke[1:]):
            path = QPainterPath()
            path.moveTo(p1.x, p1.y)
            path.lineTo(p2.x, p2.y)
            w = _getw(p1, p2)
            painter.setPen(QPen(Qt.black, 10))
            painter.drawPath(path)
    index = 0
    while index < len(strokes) - 1:
        stroke1 = strokes[index]
        stroke2 = strokes[index + 1]
        if len(stroke1) == 0:
            index += 1
            continue
        # 计算stroke2的倾斜角度
        link_point = stroke2[0]
        endpoint = stroke2[0]
        for p in stroke2[1:]:
            endpoint = p
            if math.sqrt((p.x - stroke2[0].x) ** 2 + (p.y - stroke2[0].y) ** 2) > 20:
                break
        link_degree = get_degree_via_point(stroke2[0], endpoint)

        # 判断是否需要生成连笔
        dis, dis_x, dis_y = _dis(stroke1[-1], link_point)
        if 20 < dis < 40:
            # 判断连笔是直线还是曲线
            # 计算stroke1的倾斜角度
            startpoint = stroke1[-1]
            for p in stroke1[::-1]:
                startpoint = p
                if math.sqrt((p.x - stroke1[-1].x) ** 2 + (p.y - stroke1[-1].y) ** 2) > 20:
                    break
            degree = get_degree_via_point(startpoint, stroke1[-1])

            # path = QPainterPath()
            # w = _getw(stroke1[-1], link_point)
            if abs(degree - link_degree) <= 3:
                # 绘制直线的连笔
                # painter.setPen(QPen(Qt.red, w))
                # path.moveTo(stroke1[-1].x, stroke1[-1].y)
                # path.lineTo(link_point.x, link_point.y)
                # painter.drawPath(path)
                # 合并笔画stroke1和stroke2
                new_stroke = Stroke(stroke1 + stroke2)
                del strokes[index]
                del strokes[index]
                strokes.insert(index, new_stroke)
            else:
                # 使用曲线的连笔
                sin = dis_x / dis
                cos = dis_y / dis
                radio = random.uniform(0.6, 0.9)
                if 0 <= link_degree < 18:
                    control1_px = stroke1[-1].x + dis_x * radio + random.uniform(0, dis / 2) * cos
                    control1_py = stroke1[-1].y + dis_y * radio - random.uniform(0, dis / 2) * sin
                else:
                    control1_px = stroke1[-1].x + dis_x * radio - random.uniform(0, dis / 2) * cos
                    control1_py = stroke1[-1].y + dis_y * radio + random.uniform(0, dis / 2) * sin
                new_stroke = Stroke()
                for i in range(1, 5):
                    t = i * 0.2
                    b1x = (1 - t) * stroke1[-1].x + t * control1_px
                    b1y = (1 - t) * stroke1[-1].y + t * control1_py
                    b2x = (1 - t) * control1_px + t * link_point.x
                    b2y = (1 - t) * control1_py + t * link_point.y
                    new_stroke.append(StrokePoint((1 - t) * b1x + t * b2x, (1 - t) * b1y + t * b2y,
                                                  (stroke1[-1].force + link_point.force) / 2,
                                                  (stroke1[-1].timestamp + link_point.timestamp) / 2))
                # 绘制曲线的连笔
                # painter.setPen(QPen(Qt.blue, w))
                # path.moveTo(stroke1[-1].x, stroke1[-1].y)
                # path.lineTo(new_stroke[0].x, new_stroke[0].y)
                # painter.drawPath(path)
                # for p1, p2 in zip(new_stroke, new_stroke[1:]):
                #     path = QPainterPath()
                #     path.moveTo(p1.x, p1.y)
                #     path.lineTo(p2.x, p2.y)
                #     painter.drawPath(path)
                # path.moveTo(new_stroke[-1].x, new_stroke[-1].y)
                # path.lineTo(link_point.x, link_point.y)
                # painter.drawPath(path)
                # 合并笔迹点
                total_stroke = Stroke(stroke1 + new_stroke + stroke2)
                del strokes[index]
                del strokes[index]
                strokes.insert(index, total_stroke)
                # path.cubicTo(stroke1[-1].x, stroke1[-1].y, control1_px, control1_py, link_point.x, link_point.y)
                # painter.drawPath(path)
                # print("贝塞尔")
        index += 1

    # 绘出加入连笔的笔迹
    for stroke in strokes:
        for p1, p2 in zip(stroke, stroke[1:]):
            path = QPainterPath()
            path.moveTo(p1.x, p1.y)
            path.lineTo(p2.x, p2.y)
            w = _getw(p1, p2)
            painter.setPen(QPen(Qt.red, 5))
            painter.drawPath(path)
    painter.end()


def gen_strokes_link(strokes):
    """绘制 strokes 的 link,即连笔"""
    # 生成连笔
    index = 0
    while index < len(strokes) - 1:
        stroke1 = strokes[index]
        stroke2 = strokes[index + 1]
        if len(stroke1) == 0:
            index += 1
            continue
        # 计算stroke2的倾斜角度
        link_point = stroke2[0]
        endpoint = stroke2[0]
        for p in stroke2[1:]:
            endpoint = p
            if math.sqrt((p.x - stroke2[0].x) ** 2 + (p.y - stroke2[0].y) ** 2) > 20:
                break
        link_degree = get_degree_via_point(stroke2[0], endpoint)

        # 判断是否需要生成连笔
        dis, dis_x, dis_y = _dis(stroke1[-1], link_point)
        if 20 < dis < 40:
            # 判断连笔是直线还是曲线
            # 计算stroke1的倾斜角度
            startpoint = stroke1[-1]
            for p in stroke1[::-1]:
                startpoint = p
                if math.sqrt((p.x - stroke1[-1].x) ** 2 + (p.y - stroke1[-1].y) ** 2) > 20:
                    break
            degree = get_degree_via_point(startpoint, stroke1[-1])
            if abs(degree - link_degree) <= 3:
                # 合并笔画stroke1和stroke2
                new_stroke = Stroke(stroke1 + stroke2)
                del strokes[index]
                del strokes[index]
                strokes.insert(index, new_stroke)
            else:
                # 使用曲线的连笔
                sin = dis_x / dis
                cos = dis_y / dis
                radio = random.uniform(0.6, 0.9)
                if 0 <= link_degree < 18:
                    control1_px = stroke1[-1].x + dis_x * radio + random.uniform(0, dis / 2) * cos
                    control1_py = stroke1[-1].y + dis_y * radio - random.uniform(0, dis / 2) * sin
                else:
                    control1_px = stroke1[-1].x + dis_x * radio - random.uniform(0, dis / 2) * cos
                    control1_py = stroke1[-1].y + dis_y * radio + random.uniform(0, dis / 2) * sin
                new_stroke = Stroke()
                for i in range(1, 5):
                    t = i * 0.2
                    b1x = (1 - t) * stroke1[-1].x + t * control1_px
                    b1y = (1 - t) * stroke1[-1].y + t * control1_py
                    b2x = (1 - t) * control1_px + t * link_point.x
                    b2y = (1 - t) * control1_py + t * link_point.y
                    new_stroke.append(StrokePoint((1 - t) * b1x + t * b2x, (1 - t) * b1y + t * b2y,
                                                  (stroke1[-1].force + link_point.force) / 2,
                                                  (stroke1[-1].timestamp + link_point.timestamp) / 2))
                # 合并笔迹点
                total_stroke = Stroke(stroke1 + new_stroke + stroke2)
                del strokes[index]
                del strokes[index]
                strokes.insert(index, total_stroke)
        index += 1


# shear transformation
def draw_stroke_shear(pixmap, painter, stroke, degree, f, color):
    if len(stroke) == 0:
        return
    # 绘制出原始的笔画轨迹
    for p1, p2 in zip(stroke, stroke[1:]):
        path = QPainterPath()
        path.moveTo(p1.x, p1.y)
        path.lineTo(p2.x, p2.y)
        w = _getw(p1, p2)
        painter.setPen(QPen(Qt.black, 10))
        painter.drawPath(path)
    # 对笔画进行剪切变换
    # degree = random.randint(1, 7)
    # f = random.randint(0, 1)
    for p in stroke:
        if f == 0:
            p.x += p.y * math.tan(degree * math.pi / 180)
        if f == 1:
            p.y += p.x * math.tan(degree * math.pi / 180)
        if f == 2:
            x = p.x
            y = p.y
            p.x += y * math.tan(degree * math.pi / 180)
            p.y += x * math.tan(degree * math.pi / 180)

    for p1, p2 in zip(stroke, stroke[1:]):
        path = QPainterPath()
        path.moveTo(p1.x, p1.y)
        path.lineTo(p2.x, p2.y)
        w = _getw(p1, p2)
        painter.setPen(QPen(Qt.red, 5))
        painter.drawPath(path)


def draw_strokes_shear(pixmap, strokes, color=Qt.black):
    """绘制 strokes 的 shear,对笔画进行剪切变换"""
    painter = QPainter(pixmap)
    # 角度值
    degree = 0
    f1 = random.randint(0, 1)
    if f1 == 0:
        degree = random.randint(-10, -1)
    if f1 == 1:
        degree = random.randint(1, 10)
    # x/y剪切变换
    f = random.randint(0, 2)
    for stroke in strokes:
        draw_stroke_shear(pixmap, painter, stroke, degree, f, color)
    painter.end()


def gen_stroke_shear(stroke, degree, f):
    if len(stroke) == 0:
        return
    # 对笔画进行剪切变换
    for p in stroke:
        if f == 0:
            p.x += p.y * math.tan(degree * math.pi / 180)
        if f == 1:
            p.y += p.x * math.tan(degree * math.pi / 180)
        if f == 2:
            x = p.x
            y = p.y
            p.x += y * math.tan(degree * math.pi / 180)
            p.y += x * math.tan(degree * math.pi / 180)


def gen_strokes_shear(strokes):
    """绘制 strokes 的 shear,对笔画进行剪切变换"""
    # 角度值
    degree = 0
    f1 = random.randint(0, 1)
    if f1 == 0:
        degree = random.randint(-10, -1)
    if f1 == 1:
        degree = random.randint(1, 10)
    # x/y剪切变换
    f = random.randint(0, 2)
    for stroke in strokes:
        gen_stroke_shear(stroke, degree, f)


##########################
# 新增透视变换
# perspective transformation
def draw_stroke_perspective(pixmap, painter, stroke, degree, f, color):
    if len(stroke) == 0:
        return
    # 绘制出原始的笔画轨迹
    print("yuanshi")
    for p1, p2 in zip(stroke, stroke[1:]):
        path = QPainterPath()
        print("p1.x, p1.y", p1.x, p1.y)
        print("p2.x, p2.y", p2.x, p2.y)
        path.moveTo(p1.x, p1.y)
        path.lineTo(p2.x, p2.y)
        w = _getw(p1, p2)
        painter.setPen(QPen(Qt.black, 10))
        painter.drawPath(path)
    # 对笔画进行透视变换
    # degree = random.randint(1, 7)
    # f = random.randint(0, 1)
    print("----------------------")
    for p in stroke:
        if f == 0:
            x = p.x
            y = p.y
            p.x = (2 / 3) * (x + 0.5 * math.cos(4 * (degree * math.pi / 180) * ((x - 0.5) / 1)))
            p.y = (2 / 3) * y * (math.sin((90 - degree) * math.pi / 180) - (y * math.sin(degree * math.pi / 180) / 1))
        if f == 1:
            x = p.x
            y = p.y
            # p.x = (2 / 3) * x * (math.sin((90 - degree) * math.pi / 180) - (x * math.sin(degree * math.pi / 180) / 10))
            # p.y = (2 / 3) * (y + 50 * math.cos(4 * (degree * math.pi / 180) * ((y - 50) / 10)))
            p.x = (2 / 3) * x * (math.sin((90 - degree) * math.pi / 180) - (x * math.sin(degree * math.pi / 180) / 1))
            p.y = (2 / 3) * (y + 0.5 * math.cos(4 * (degree * math.pi / 180) * ((y - 0.5) / 1)))

    for p1, p2 in zip(stroke, stroke[1:]):
        path = QPainterPath()
        print("p1.x, p1.y", p1.x, p1.y)
        print("p2.x, p2.y", p2.x, p2.y)
        path.moveTo(p1.x, p1.y)
        path.lineTo(p2.x, p2.y)

        w = _getw(p1, p2)
        painter.setPen(QPen(Qt.red, 5))
        painter.drawPath(path)


def draw_strokes_perspective(pixmap, strokes, color=Qt.black):
    """绘制 strokes 的 perspective,对笔画进行透视变换"""
    painter = QPainter(pixmap)
    # 角度值
    degree = 0
    f1 = random.randint(0, 1)
    if f1 == 0:
        degree = random.randint(-6, -1)
    if f1 == 1:
        degree = random.randint(1, 6)
    # x/y透视变换
    f = random.randint(0, 1)
    # f = 1
    # degree = 3
    # painter.translate(2000, 2000)
    z_score(strokes)
    for stroke in strokes:
        draw_stroke_perspective(pixmap, painter, stroke, degree, f, color)
    painter.end()


def gen_stroke_perspective(stroke, degree, f):
    if len(stroke) == 0:
        return

    # 对笔画进行透视变换
    # degree = random.randint(1, 7)
    # f = random.randint(0, 1)
    for p in stroke:
        if f == 0:
            x = p.x
            y = p.y
            p.x = (2 / 3) * (x + 0.5 * math.cos(4 * (degree * math.pi / 180) * ((x - 0.5) / 1)))
            p.y = (2 / 3) * y * (math.sin((90 - degree) * math.pi / 180) - (y * math.sin(degree * math.pi / 180) / 1))
        if f == 1:
            x = p.x
            y = p.y
            # p.x = (2 / 3) * x * (math.sin((90 - degree) * math.pi / 180) - (x * math.sin(degree * math.pi / 180) / 10))
            # p.y = (2 / 3) * (y + 50 * math.cos(4 * (degree * math.pi / 180) * ((y - 50) / 10)))
            p.x = (2 / 3) * x * (math.sin((90 - degree) * math.pi / 180) - (x * math.sin(degree * math.pi / 180) / 1))
            p.y = (2 / 3) * (y + 0.5 * math.cos(4 * (degree * math.pi / 180) * ((y - 0.5) / 1)))
        print("p.x", p.x)
        print("p.y", p.y)


def gen_strokes_perspective(strokes):
    """绘制 strokes 的 perspective,对笔画进行透视变换"""

    # 角度值
    degree = 0
    f1 = random.randint(0, 1)
    if f1 == 0:
        degree = random.randint(-6, -1)
    if f1 == 1:
        degree = random.randint(1, 6)
    # x/y透视变换
    f = random.randint(0, 1)
    # f = 1
    # degree = 3
    # painter.translate(2000, 2000)
    z_score(strokes)
    for stroke in strokes:
        gen_stroke_perspective(stroke, degree, f)


##########################
# 新增收缩变换
# perspective transformation
def draw_stroke_shrink(pixmap, painter, stroke, degree, f, color):
    if len(stroke) == 0:
        return
    # 绘制出原始的笔画轨迹
    for p1, p2 in zip(stroke, stroke[1:]):
        path = QPainterPath()
        path.moveTo(p1.x, p1.y)
        path.lineTo(p2.x, p2.y)
        print("p1.x, p1.y", p1.x, p1.y)
        print("p2.x, p2.y", p2.x, p2.y)
        w = _getw(p1, p2)
        painter.setPen(QPen(Qt.black, 10))
        painter.drawPath(path)
    print("----------------------")
    # 对笔画进行收缩变换
    # degree = random.randint(1, 7)
    # f = random.randint(0, 1)
    for p in stroke:
        if f == 0:
            x = p.x
            p.x = p.y * (math.sin((90 - degree) * math.pi / 180) - (x * math.sin(degree * math.pi / 180) / 1))
        if f == 1:
            y = p.y
            p.y = p.x * (math.sin((90 - degree) * math.pi / 180) - (y * math.sin(degree * math.pi / 180) / 1))

    for p1, p2 in zip(stroke, stroke[1:]):
        path = QPainterPath()
        path.moveTo(p1.x, p1.y)
        path.lineTo(p2.x, p2.y)
        print("p1.x, p1.y", p1.x, p1.y)
        print("p2.x, p2.y", p2.x, p2.y)
        w = _getw(p1, p2)
        painter.setPen(QPen(Qt.red, 5))
        painter.drawPath(path)


def draw_strokes_shrink(pixmap, strokes, color=Qt.black):
    """绘制 strokes 的 shrink,对笔画进行收缩变换"""
    painter = QPainter(pixmap)
    # 角度值
    degree = 0
    f1 = random.randint(0, 1)
    if f1 == 0:
        degree = random.randint(-6, -1)
    if f1 == 1:
        degree = random.randint(1, 6)
    # x/y透视变换
    f = random.randint(0, 1)
    # f = 1
    # degree = 3
    z_score(strokes)
    for stroke in strokes:
        draw_stroke_shrink(pixmap, painter, stroke, degree, f, color)
    painter.end()


def gen_stroke_shrink(stroke, degree, f):
    if len(stroke) == 0:
        return

    # 对笔画进行收缩变换
    # degree = random.randint(1, 7)
    # f = random.randint(0, 1)
    for p in stroke:
        if f == 0:
            x = p.x
            p.x = p.y * (math.sin((90 - degree) * math.pi / 180) - (x * math.sin(degree * math.pi / 180) / 100))
        if f == 1:
            y = p.y
            p.y = p.x * (math.sin((90 - degree) * math.pi / 180) - (y * math.sin(degree * math.pi / 180) / 100))


def gen_strokes_shrink(strokes):
    """绘制 strokes 的 shrink,对笔画进行收缩变换"""

    # 角度值
    degree = 0
    f1 = random.randint(0, 1)
    if f1 == 0:
        degree = random.randint(-6, -1)
    if f1 == 1:
        degree = random.randint(1, 6)
    # x/y透视变换
    f = random.randint(0, 1)
    # f = 1
    # degree = 3
    z_score(strokes)
    for stroke in strokes:
        gen_stroke_shrink(stroke, degree, f)


###################################################################
# 模仿笔画的停顿，增加重复点

# 给笔画中的点增加角度属性
def add_angle(stroke):
    """给 stroke 增加 angle 属性"""
    stroke[0].angle = 0
    stroke[-1].angle = 0
    for p1, p0, p2 in zip(stroke, stroke[1:], stroke[2:]):
        p0.angle = get_angle_via_point(p1, p0, p2)


def get_angle_via_point(p1, p0, p2, abs=True):
    """如果设置了 abs，不考虑 angle 的顺逆时针，返回 0-18"""
    degree1 = get_degree_via_point(p0, p1)
    degree2 = get_degree_via_point(p0, p2)
    angle = get_angle_via_degree(degree1, degree2, abs)
    return angle


def get_angle_via_degree(degree1, degree2, abs=True):
    """如果设置了 abs，不考虑 angle 的顺逆时针，返回 0-18"""
    angle = degree2 - degree1
    if angle < 0:
        angle += 36
    if abs:
        if angle > 18:
            angle = 36 - angle
    return angle


def search_index(stroke, x, y, time, offset):
    index = offset
    while index < len(stroke):
        if stroke[index].x == x and stroke[index].y == y and stroke[index].timestamp == time:
            return index
        else:
            index += 1


def draw_stroke_small_angle(pixmap, painter, stroke, color):
    # 绘制出原始的笔画轨迹
    for p1, p2 in zip(stroke, stroke[1:]):
        path = QPainterPath()
        path.moveTo(p1.x, p1.y)
        path.lineTo(p2.x, p2.y)
        w = _getw(p1, p2)
        painter.setPen(QPen(Qt.black, w))
        painter.drawPath(path)
    # 给笔画中的轨迹点增加角度属性
    add_angle(stroke)

    for p in stroke:
        # print("p.angle", p.angle)
        if p.angle <= 4:
            painter.setPen(QPen(Qt.red, 5))
            painter.drawPoint(p.qp())


def draw_strokes_small_angle(pixmap, strokes, color=Qt.black):
    """绘制 strokes 的 small_angle,检测笔画中的角度小的点"""
    painter = QPainter(pixmap)
    for stroke in strokes:
        draw_stroke_small_angle(pixmap, painter, stroke, color)
    painter.end()


def draw_stroke_overlap_point(pixmap, painter, stroke, color):
    # 绘制出原始的笔画轨迹
    for p1, p2 in zip(stroke, stroke[1:]):
        path = QPainterPath()
        path.moveTo(p1.x, p1.y)
        path.lineTo(p2.x, p2.y)
        w = _getw(p1, p2)
        painter.setPen(QPen(Qt.black, 10))
        painter.drawPath(path)
    # 给笔画中的轨迹点增加角度属性
    add_angle(stroke)
    # 笔画的起点、终点以及角度比较小的点
    overlap_points = [stroke[0]]
    for p in stroke[1:-1]:
        if p.angle <= 4:
            overlap_points.append(p)
    overlap_points.append(stroke[-1])
    max_insert_number = 4
    insert_number = random.randint(0, max_insert_number)
    real_index = -insert_number
    for index, overlap_point in enumerate(overlap_points):
        real_index = search_index(stroke, overlap_point.x, overlap_point.y, overlap_point.timestamp,
                                  real_index + insert_number)
        p = stroke[real_index]
        for i in range(0, insert_number):
            new_p = StrokePoint(p.x + random.randint(-3, 3), p.y + random.randint(-3, 3), p.force, p.timestamp)
            stroke.insert(real_index, new_p)

    # 生成更多的点
    # for p in stroke:
    #     painter.setPen(QPen(Qt.red, 5))
    #     painter.drawPoint(p.qp())

    for p1, p2 in zip(stroke, stroke[1:]):
        path = QPainterPath()
        path.moveTo(p1.x, p1.y)
        path.lineTo(p2.x, p2.y)
        w = _getw(p1, p2)
        painter.setPen(QPen(Qt.red, 5))
        painter.drawPath(path)


def draw_strokes_overlap_point(pixmap, strokes, color=Qt.black):
    """绘制 strokes 的 overlap_point,模仿人写字时的停顿，增加更多的停顿笔迹点"""
    painter = QPainter(pixmap)
    for stroke in strokes:
        draw_stroke_overlap_point(pixmap, painter, stroke, color)
    painter.end()


def gen_stroke_overlap_point(stroke):
    # 给笔画中的轨迹点增加角度属性
    add_angle(stroke)
    # 笔画的起点、终点以及角度比较小的点
    overlap_points = [stroke[0]]
    for p in stroke[1:-1]:
        if p.angle <= 4:
            overlap_points.append(p)
    overlap_points.append(stroke[-1])
    max_insert_number = 4
    insert_number = random.randint(0, max_insert_number)
    real_index = -insert_number
    for index, overlap_point in enumerate(overlap_points):
        real_index = search_index(stroke, overlap_point.x, overlap_point.y, overlap_point.timestamp,
                                  real_index + insert_number)
        p = stroke[real_index]
        for i in range(0, insert_number):
            new_p = StrokePoint(p.x + random.randint(-3, 3), p.y + random.randint(-3, 3), p.force, p.timestamp)
            stroke.insert(real_index, new_p)


def gen_strokes_overlap_point(strokes):
    """绘制 strokes 的 overlap_point,模仿人写字时的停顿，增加更多的停顿笔迹点"""
    for stroke in strokes:
        gen_stroke_overlap_point(stroke)


def draw_stroke_big_angle(pixmap, painter, stroke, color):
    # 绘制出原始的笔画轨迹
    for p1, p2 in zip(stroke, stroke[1:]):
        path = QPainterPath()
        path.moveTo(p1.x, p1.y)
        path.lineTo(p2.x, p2.y)
        w = _getw(p1, p2)
        painter.setPen(QPen(Qt.black, w))
        painter.drawPath(path)
    # 给笔画中的轨迹点增加角度属性
    add_angle(stroke)

    for p in stroke:
        print("p.angle", p.angle)
        if p.angle >= 15:
            painter.setPen(QPen(Qt.red, 5))
            painter.drawPoint(p.qp())


def draw_strokes_big_angle(pixmap, strokes, color=Qt.black):
    """绘制 strokes 的 big_angle,模仿人书写太快时，采样的点变少的情况；检测笔画中的角度较大的点（即书写比较快的笔迹点）"""
    painter = QPainter(pixmap)
    for stroke in strokes:
        draw_stroke_big_angle(pixmap, painter, stroke, color)
    painter.end()


def draw_stroke_dropout_point(pixmap, painter, stroke, color):
    # 绘制出原始的笔画轨迹
    for p1, p2 in zip(stroke, stroke[1:]):
        path = QPainterPath()
        path.moveTo(p1.x, p1.y)
        path.lineTo(p2.x, p2.y)
        w = _getw(p1, p2)
        painter.setPen(QPen(Qt.black, 10))
        painter.drawPath(path)
    # 给笔画中的轨迹点增加角度属性
    add_angle(stroke)

    # 笔画中角度比较大的点
    drop_set_all = []
    for p in stroke:
        if p.angle >= 15:
            drop_set_all.append(p)

    ratio = random.uniform(0.3, 0.6)
    drop_num = min(int(len(drop_set_all) * ratio), len(stroke) // 5)
    print("len(drop_set_all) * ratio", int(len(drop_set_all) * ratio))
    print("len(stroke) // 5", len(stroke) // 5)
    # 从满足条件的点中随机选取部分点，并将其移除
    drop_set = random.sample(drop_set_all, drop_num)
    for drop_point in drop_set:
        stroke.remove(drop_point)

    # 丢弃某些点
    # for p in stroke:
    #     painter.setPen(QPen(Qt.red, 5))
    #     painter.drawPoint(p.qp())

    for p1, p2 in zip(stroke, stroke[1:]):
        path = QPainterPath()
        path.moveTo(p1.x, p1.y)
        path.lineTo(p2.x, p2.y)
        w = _getw(p1, p2)
        painter.setPen(QPen(Qt.red, 5))
        painter.drawPath(path)


def draw_strokes_dropout_point(pixmap, strokes, color=Qt.black):
    """绘制 strokes 的 dropout_point，随机丢弃某些点"""
    painter = QPainter(pixmap)
    for stroke in strokes:
        draw_stroke_dropout_point(pixmap, painter, stroke, color)
    painter.end()


def gen_stroke_dropout_point(stroke):
    # 给笔画中的轨迹点增加角度属性
    add_angle(stroke)

    # 笔画中角度比较大的点
    drop_set_all = []
    for p in stroke:
        if p.angle >= 15:
            drop_set_all.append(p)

    ratio = random.uniform(0.3, 0.6)
    drop_num = min(int(len(drop_set_all) * ratio), len(stroke) // 5)

    # 从满足条件的点中随机选取部分点，并将其移除
    drop_set = random.sample(drop_set_all, drop_num)
    for drop_point in drop_set:
        stroke.remove(drop_point)


def gen_strokes_dropout_point(strokes):
    """绘制 strokes 的 dropout_point，随机丢弃某些点"""
    for stroke in strokes:
        gen_stroke_dropout_point(stroke)


def draw_strokes_repeat_stroke(pixmap, strokes):
    """模仿人书写时的涂改操作repeat_stroke，在原有笔画上加上微小的移动，重复生成笔画"""
    painter = QPainter(pixmap)
    # for stroke in strokes:
    #     for p1, p2 in zip(stroke, stroke[1:]):
    #         path = QPainterPath()
    #         path.moveTo(p1.x, p1.y)
    #         path.lineTo(p2.x, p2.y)
    #         w = _getw(p1, p2)
    #         painter.setPen(QPen(Qt.black, 10))
    #         painter.drawPath(path)

    for index, stroke in enumerate(strokes):
        f = random.randint(0, 9)
        if f <= 1:
            x, y, width, height = stroke.add_brect()
            radio = random.uniform(-0.05, 0.05)
            print("radio", radio)
            w_scale = int(width * radio)
            h_scale = int(height * radio)
            new_stroke = Stroke([StrokePoint(p.x + w_scale, p.y + h_scale, p.force, p.timestamp) for p in stroke])
            strokes.insert(index, new_stroke)

    for stroke in strokes:
        for p1, p2 in zip(stroke, stroke[1:]):
            path = QPainterPath()
            path.moveTo(p1.x, p1.y)
            path.lineTo(p2.x, p2.y)
            w = _getw(p1, p2)
            painter.setPen(QPen(Qt.red, 5))
            painter.drawPath(path)


def gen_strokes_repeat_stroke(strokes):
    """模仿人书写时的涂改操作repeat_stroke，在原有笔画上加上微小的移动，重复生成笔画"""
    for index, stroke in enumerate(strokes):
        f = random.randint(0, 9)
        if f <= 1:
            x, y, width, height = stroke.add_brect()
            radio = random.uniform(-0.05, 0.05)
            w_scale = int(width * radio)
            h_scale = int(height * radio)
            new_stroke = Stroke([StrokePoint(p.x + w_scale, p.y + h_scale, p.force, p.timestamp) for p in stroke])
            strokes.insert(index, new_stroke)


def draw_strokes_total(pixmap, strokes):
    """绘制 strokes 的 total,即将多种规则进行混合"""
    painter = QPainter(pixmap)
    # for stroke in strokes:
    #     if len(stroke) == 0:
    #         continue
    #     # 绘制出原始的笔画轨迹
    #     for p1, p2 in zip(stroke, stroke[1:]):
    #         path = QPainterPath()
    #         path.moveTo(p1.x, p1.y)
    #         path.lineTo(p2.x, p2.y)
    #         w = _getw(p1, p2)
    #         painter.setPen(QPen(Qt.black, 10))
    #         painter.drawPath(path)
    # 随机选择每个规则使用的顺序

    # 针对所有笔画的规则
    rules_num_all = 7
    rules_all = [i for i in range(rules_num_all)]
    random.shuffle(rules_all)
    for i in rules_all:
        if i == 0:
            # 对笔画进行加长，缩短
            a0 = random.randint(0, 4)
            if a0 == 0:
                gen_strokes_lengthchange(strokes)
        if i == 1:
            # 生成连笔
            a1 = random.randint(0, 4)
            if a1 >= 2:
                gen_strokes_link(strokes)
        if i == 2:
            # 加入重复笔画
            a2 = random.randint(0, 9)
            if a2 == 0:
                gen_strokes_repeat_stroke(strokes)
        if i == 3:
            # 对所有的笔画进行整体缩放
            a3 = random.randint(0, 4)
            if a3 == 0:
                gen_strokes_scale(strokes)
        if i == 4:
            # 对所有的笔画进行整体旋转
            a4 = random.randint(0, 9)
            if a4 == 0:
                gen_strokes_all_rotate(strokes)
            if a4 == 1:
                gen_strokes_all_rotate_1(strokes)
        if i == 5:
            # 对所有的笔画进行剪切变换
            a5 = random.randint(0, 9)
            if a5 == 0:
                gen_strokes_shear(strokes)
        if i == 6:
            # 对所有的笔画加入高斯噪音
            a6 = random.randint(0, 9)
            if a6 == 0:
                gen_strokes_gaussian_noisy(strokes)

    # 针对单一笔画的规则
    rules_num_single = 7
    rules_single = [i for i in range(rules_num_single)]
    # random.shuffle(rules_single)

    for stroke in strokes:
        random.shuffle(rules_single)
        for i in rules_single:
            if i == 0:
                # 加入重复的停顿点
                a0 = random.randint(0, 9)
                if a0 == 0:
                    gen_stroke_overlap_point(stroke)
            if i == 1:
                # 随机丢弃点
                a1 = random.randint(0, 9)
                if a1 == 0:
                    gen_stroke_dropout_point(stroke)
            if i == 2:
                # 产生不协调的转折，笔画弯折
                # 笔画中每个点的移动值递增或递减
                a2 = random.randint(0, 19)
                if a2 == 0:
                    gen_stroke_turn(stroke)
            if i == 3:
                # 随机扭曲笔画中的点
                a3 = random.randint(0, 19)
                if a3 == 0:
                    gen_stroke_distort_random_point(stroke)
            if i == 4:
                # 扭曲笔画中的拐点
                a4 = random.randint(0, 19)
                if a4 == 0:
                    gen_stroke_distort_corner_point(stroke)
            if i == 5:
                # 对每个笔画随机进行移动
                a5 = random.randint(0, 19)
                if a5 == 0:
                    gen_stroke_unsuit_ratio(stroke)
            if i == 6:
                # 单个笔画旋转，倾斜
                a6 = random.randint(0, 19)
                if a6 == 0:
                    gen_stroke_rotate(stroke)

    # 绘出加入各种规则和连笔的笔迹
    for stroke in strokes:
        if len(stroke) == 0:
            continue
        for p1, p2 in zip(stroke, stroke[1:]):
            path = QPainterPath()
            path.moveTo(p1.x, p1.y)
            path.lineTo(p2.x, p2.y)
            w = _getw(p1, p2)
            painter.setPen(QPen(Qt.red, 5))
            painter.drawPath(path)
    painter.end()


def gen_strokes_total(strokes):
    """绘制 strokes 的 total,即将多种规则进行混合"""
    # 随机选择每个规则使用的顺序

    # 针对所有笔画的规则
    rules_num_all = 7
    rules_all = [i for i in range(rules_num_all)]
    random.shuffle(rules_all)
    for i in rules_all:
        if i == 0:
            # 对笔画进行加长，缩短
            a0 = random.randint(0, 4)
            if a0 == 0:
                gen_strokes_lengthchange(strokes)
        if i == 1:
            # 生成连笔
            a1 = random.randint(0, 4)
            if a1 >= 2:
                gen_strokes_link(strokes)
        if i == 2:
            # 加入重复笔画
            a2 = random.randint(0, 9)
            if a2 == 0:
                gen_strokes_repeat_stroke(strokes)
        if i == 3:
            # 对所有的笔画进行整体缩放
            a3 = random.randint(0, 4)
            if a3 == 0:
                gen_strokes_scale(strokes)
        if i == 4:
            # 对所有的笔画进行整体旋转
            a4 = random.randint(0, 9)
            if a4 == 0:
                gen_strokes_all_rotate(strokes)
            if a4 == 1:
                gen_strokes_all_rotate_1(strokes)
        if i == 5:
            # 对所有的笔画进行剪切变换
            a5 = random.randint(0, 9)
            if a5 == 0:
                gen_strokes_shear(strokes)
        if i == 6:
            # 对所有的笔画加入高斯噪音
            a6 = random.randint(0, 9)
            if a6 == 0:
                gen_strokes_gaussian_noisy(strokes)

    # 针对单一笔画的规则
    rules_num_single = 7
    rules_single = [i for i in range(rules_num_single)]
    # random.shuffle(rules_single)

    for stroke in strokes:
        random.shuffle(rules_single)
        for i in rules_single:
            if i == 0:
                # 加入重复的停顿点
                a0 = random.randint(0, 9)
                if a0 == 0:
                    gen_stroke_overlap_point(stroke)
            if i == 1:
                # 随机丢弃点
                a1 = random.randint(0, 9)
                if a1 == 0:
                    gen_stroke_dropout_point(stroke)
            if i == 2:
                # 产生不协调的转折，笔画弯折
                # 笔画中每个点的移动值递增或递减
                a2 = random.randint(0, 19)
                if a2 == 0:
                    gen_stroke_turn(stroke)
            if i == 3:
                # 随机扭曲笔画中的点
                a3 = random.randint(0, 19)
                if a3 == 0:
                    gen_stroke_distort_random_point(stroke)
            if i == 4:
                # 扭曲笔画中的拐点
                a4 = random.randint(0, 19)
                if a4 == 0:
                    gen_stroke_distort_corner_point(stroke)
            if i == 5:
                # 对每个笔画随机进行移动
                a5 = random.randint(0, 19)
                if a5 == 0:
                    gen_stroke_unsuit_ratio(stroke)
            if i == 6:
                # 单个笔画旋转，倾斜
                a6 = random.randint(0, 19)
                if a6 == 0:
                    gen_stroke_rotate(stroke)


def cal_strokes_points(strokes):
    points = [len(s) for s in strokes]
    message = 'strokes: %d | points: %d' % (len(strokes), sum(points))
    print(message)


if __name__ == '__main__':
    ori_dirname = "/ssd2/exec/houqi/HMER/math143647_dataset/math143647_json/"
    gen_dirname = "/ssd2/exec/houqi/HMER/math143647_dataset/math143647_da_json/"

    caption_path = "/ssd2/exec/houqi/HMER/jpk_labeled_dataset/jpk_train_caption_75031.txt"
    caption_da_path = "/ssd2/exec/houqi/HMER/jpk_labeled_dataset/jpk_train_caption_75031_da.txt"

    if not os.path.exists(gen_dirname):
        os.mkdir(gen_dirname)
    genVersions = ['lengthchange', "all_rotate", "all_rotate_1", 'rotate', "scale", "gaussian_noisy",
                   'unsuit_ratio', 'turn', 'distort_random_point', "distort_corner_point",
                   "link", "shear", "overlap_point", "dropout_point", "repeat_stroke",
                   "total"]

    begin = 0
    end = 21
    with open(caption_path, 'r') as fr, open(caption_da_path, 'w') as fw:
        lines = fr.readlines()
        for line in lines:

            content = line.strip().split()
            print("content", content)
            name = content[0]
            label = ' '.join(content[1:])
            json_name = name + ".json"
            ori_filename = os.path.join(ori_dirname, json_name)
            a = random.randint(begin, end)
            print(a)
            gen_name = name + '_' + genVersions[min(a, 15)]

            gen_json_name = name + '_' + genVersions[min(a, 15)] + '.json'

            gen_filename = os.path.join(gen_dirname, gen_json_name)
            strokes = load_line_file(ori_filename)
            cal_strokes_points(strokes)
            if a == 0:
                print("gen strokes lengthchange...")
                gen_strokes_lengthchange(strokes)

            if a == 1:
                print("gen strokes all_rotate...")
                gen_strokes_all_rotate(strokes)

            if a == 2:
                print("gen strokes all_rotate_1...")
                gen_strokes_all_rotate_1(strokes)

            if a == 3:
                print("gen strokes rotate...")
                gen_strokes_rotate(strokes)

            if a == 4:
                print("gen strokes scale...")
                gen_strokes_scale(strokes)

            if a == 5:
                print("gen strokes gaussian_noisy...")
                gen_strokes_gaussian_noisy(strokes)

            if a == 6:
                print("gen strokes unsuit_ratio...")
                gen_strokes_unsuit_ratio(strokes)

            if a == 7:
                print("gen strokes turn...")
                gen_strokes_turn(strokes)

            if a == 8:
                print("gen strokes distort_random_point...")
                gen_strokes_distort_random_point(strokes)

            if a == 9:
                print("gen strokes distort_corner_point ...")
                gen_strokes_distort_corner_point(strokes)

            if a == 10:
                print("gen strokes link...")
                gen_strokes_link(strokes)

            if a == 11:
                print("gen strokes shear...")
                gen_strokes_shear(strokes)

            if a == 12:
                print("gen strokes overlap_point...")
                gen_strokes_overlap_point(strokes)

            if a == 13:
                print("gen strokes dropout_point...")
                gen_strokes_dropout_point(strokes)

            if a == 14:
                print("gen strokes repeat_stroke...")
                gen_strokes_repeat_stroke(strokes)

            if a >= 15:
                print("gen strokes total...")
                gen_strokes_total(strokes)

            cal_strokes_points(strokes)
            message = 'export file: %s -> %s' % (ori_filename, gen_filename)
            print(message)
            # save_json(strokes, gen_filename)
            save_line_json(strokes, gen_filename)
            fw.write(gen_name + " " + label + "\n")
