from tetris_client import GameClient
import logging
import numpy as np
import math
from datetime import datetime
import time
from typing import Text
from tetris_client import TetrisAction
from tetris_client import Board


logging.basicConfig(format="%(asctime)s %(levelname)s:%(message)s", level=logging.INFO)


def turn(gcb: Board) -> TetrisAction:
    t1 = datetime.now()
    global shapeCoord
    global sBoard
    sBoard = []
    shapeCoord = {
        '.': ((0, 0), (0, 0), (0, 0), (0, 0)),
        'I':    ((0, -1), (0, 0), (0, 1), (0, 2)),
        'L':    ((0, -1), (0, 0), (0, 1), (1, 1)),
        'J':    ((0, -1), (0, 0), (0, 1), (-1, 1)),
        'T':    ((0, -1), (0, 0), (0, 1), (1, 0)),
        'O':    ((0, 0), (0, -1), (1, 0), (1, -1)),
        'S':    ((0, 0), (0, -1), (-1, 0), (1, -1)),
        'Z':    ((0, 0), (0, -1), (1, 0), (-1, -1))
    }

    CurrentShape = gcb.get_current_figure_type()
    NextShape = gcb.get_future_figures()[0]
    CurrentPos=gcb.get_current_figure_point().get_x()
    BoardSize = 18

    pastBoard = sBoard
    sBoard = list(gcb.to_string()[6:].replace('\n', ''))
    sBoard[:BoardSize * 5] = ['.']*(BoardSize * 5)
    # if pastBoard == sBoard and sBoard != []:
    #     time.sleep(1)
    #     return [TetrisAction.ACT_3, TetrisAction.ACT]

    BestSolution = []
    RotationOptions = {
            'I': (0, 1),
            'L': (0, 1, 2, 3),
            'J': (0, 1, 2, 3),
            'T': (0, 1),
            'O': (0,),
            'S': (0, 1),
            'Z': (0, 1)
    }
    RotationCurrentShapeRange = RotationOptions[CurrentShape]
    RotationNextShapeRange = RotationOptions[NextShape]

    for RotationCurrentShapePoint in RotationCurrentShapeRange:
        minX, maxX= getBorders(RotationCurrentShapePoint, CurrentShape)
        for RotationCurrentShapePos in range(-minX, BoardSize - maxX):
            board = predictionBoard(RotationCurrentShapePoint, RotationCurrentShapePos, sBoard, CurrentShape, BoardSize)
            for d1 in RotationNextShapeRange:
                minX, maxX = getBorders(d1, NextShape)
                dropDist = calcNextDropDist(board, d1, range(-minX, BoardSize - maxX), NextShape, BoardSize)
                for x1 in range(-minX, BoardSize - maxX):
                    Solution, maxHeight = FindSolution(np.copy(board), d1, x1, dropDist, NextShape, BoardSize)
                    if not BestSolution or BestSolution[2] < Solution:
                        BestSolution = (RotationCurrentShapePoint, RotationCurrentShapePos, Solution)

    if maxHeight > 14:
        return  [TetrisAction.ACT_0_0]

    turn = [TetrisAction.ACT  for i in range(BestSolution[0])]
    if CurrentShape in ['T']:
        turn = turn + [TetrisAction.ACT]

    shoft = []
    if BestSolution[1] < 9:
        shoft = [TetrisAction.LEFT for i in range(CurrentPos-BestSolution[1])]
    elif BestSolution[1] > 9:
        shoft = [TetrisAction.RIGHT for i in range(BestSolution[1]-CurrentPos)]
    elif CurrentShape in ['O', 'I', 'L']:
        shoft = [TetrisAction.RIGHT]

    #timing = datetime.now().time().microsecond
    #while timing < 300000:
    #    time.sleep(0.1)
    #    timing = datetime.now().time().microsecond

    #return  [TetrisAction.ACT_0_0]
    #print("===", datetime.now() - t1)
    return turn + shoft + [TetrisAction.DOWN]
    #return [TetrisAction.ACT]

def getBorders(direction, shape):
    Coords = getRotatedOffsets(direction, shape)
    Coords = list(Coords)
    return min(list(zip(*Coords))[0]), max(list(zip(*Coords))[0])


def getRotatedOffsets(direction, shape):
    global shapeCoord
    Coords = shapeCoord[shape]
    if direction == 0 or shape == '.':
        return ((x, y) for x, y in Coords)

    if direction == 1:
        return ((-y, x) for x, y in Coords)

    if direction == 2:
        if shape in ('I', 'Z', 'S'):
            return ((x, y) for x, y in Coords)
        else:
            return ((-x, -y) for x, y in Coords)

    if direction == 3:
        if shape in ('I', 'Z', 'S'):
            return ((-y, x) for x, y in Coords)
        else:
            return ((y, -x) for x, y in Coords)

def predictionBoard(RotationCurrentShapePoint, RotationCurrentShapePos, Board, CurrentShape, BoardSize):
    board = np.array(Board).reshape((BoardSize, BoardSize))
    dropDown(board, CurrentShape, RotationCurrentShapePoint, RotationCurrentShapePos, BoardSize)
    return board

def dropDown(data, shape, direction, RotationCurrentShapePos, BoardSize):
    dy = BoardSize - 1
    for x, y in getCoords(direction, RotationCurrentShapePos, 0, shape):
        yy = 0
        while yy + y < BoardSize and (yy + y < 0 or data[(y + yy), x] == '.'):
            yy += 1
        yy -= 1
        if yy < dy:
            dy = yy

    return dropDownByDist(data, shape, direction, RotationCurrentShapePos, dy)

def getCoords(direction, x, y, shape):
    return ((x + xx, y + yy) for xx, yy in getRotatedOffsets(direction, shape))

def dropDownByDist(data, shape, direction, RotationCurrentShapePos, dist):
    for x, y in getCoords(direction, RotationCurrentShapePos, 0, shape):
        data[y + dist, x] = shape
    return data

def calcNextDropDist(data, RotationCurrentShapePoint, xRange, shape, BoardSize):
    res = {}
    for RotationCurrentShapePos in xRange:
        if RotationCurrentShapePos not in res:
            res[RotationCurrentShapePos] = BoardSize - 1
        for x, y in getCoords(RotationCurrentShapePoint, RotationCurrentShapePos, 0, shape):
            yy = 0
            while yy + y < BoardSize and (yy + y < 0 or data[(y + yy), x] == '.'):
                yy += 1
            yy -= 1
            if yy < res[RotationCurrentShapePos]:
                res[RotationCurrentShapePos] = yy
    return res

def FindSolution(step1Board, d1, x1, dropDist, nextShape, BoardSize):

    step1Board = dropDownByDist(step1Board, nextShape, d1, x1, dropDist[x1])

    fullLines, nearFullLines = 0, 0
    roofY = [0] * BoardSize
    holeCandidates = [0] * BoardSize
    holeConfirm = [0] * BoardSize
    vHoles, vBlocks = 0, 0

    for y in range(BoardSize - 1, -1, -1):
        hasHole = False
        hasBlock = False
        for x in range(BoardSize):
            if step1Board[y, x] == '.':
                hasHole = True
                holeCandidates[x] += 1
            else:
                hasBlock = True
                roofY[x] = BoardSize - y
                if holeCandidates[x] > 0:
                    holeConfirm[x] += holeCandidates[x]
                    holeCandidates[x] = 0
                if holeConfirm[x] > 0:
                    vBlocks += 1
        if not hasBlock:
            break
        if not hasHole and hasBlock:
            fullLines += 1
    vHoles = sum([x ** .7 for x in holeConfirm])
    maxHeight = max(roofY) - fullLines

    roofDy = [roofY[i] - roofY[i+1] for i in range(len(roofY) - 1)]

    if len(roofDy) <= 0:
        stdDY = 0
    else:
        stdDY = math.sqrt(sum([y ** 2 for y in roofDy]) / len(roofDy) - (sum(roofDy) / len(roofDy)) ** 2)

    absDy = sum([abs(x) for x in roofDy])
    maxDy = max(roofY) - min(roofY)

    score = fullLines * 1.8 - vHoles * 1.0 - vBlocks * 0.5 - maxHeight ** 1.5 * 0.02 \
         - stdDY * 0.01 - absDy * 0.2 - maxDy * 0.3

    return score, maxHeight

def main(uri: Text):
    gcb = GameClient(uri)
    gcb.run(turn)


if __name__ == "__main__":
    uri = "http://codebattle2020.westeurope.cloudapp.azure.com/codenjoy-contest/board/player/84086rxrvd8vhgv5r6do?code=4906838677825017635&gameName=tetris"
    main(uri)
