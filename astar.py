import numpy as np


def calculate_h(x, y, goal_x, goal_y):
    return np.sqrt((x - goal_x)**2 + (y - goal_y)**2)


class Cell:
    def __init__(self, x, y, g, goal_x, goal_y, parent, h=None):
        self.x = x
        self.y = y
        self.g = g
        self.h = h
        if h == None:
            self.h = calculate_h(x, y, goal_x, goal_y)
        self.f = self.g+self.h
        self.parent = parent

    def __repr__(self):
        return str(self.x)+", "+str(self.y)+"\n"+str(self.parent)


def find_smallest(liste):
    smallest = 0
    for i, cell in enumerate(liste):
        if cell.f < liste[smallest].f:
            smallest = i
    return smallest


def inside(grid, x, y):
    if 0 <= x < len(grid):
        if 0 <= y < len(grid[0]):
            return True
    return False


def find_path(grid, x1, y1, x2, y2):
    closedl = np.zeros((len(grid), len(grid[0])))
    openl = [Cell(x1, y1, 0, None, None, None, 0)]
    opena = np.full((len(grid), len(grid[0])), float('inf'))

    while len(openl) > 0:
        q = openl.pop(find_smallest(openl))
        closedl[q.x][q.y] = True
        nexts = (
            Cell(q.x, q.y-1, q.g+1, x2, y2, q), Cell(q.x+1, q.y, q.g+1, x2, y2, q),
            Cell(q.x, q.y-1, q.g+1, x2, y2, q), Cell(q.x-1, q.y, q.g+1, x2, y2, q),
            Cell(q.x+1, q.y-1, q.g+1.4142135623730951, x2, y2, q), Cell(q.x+1, q.y+1, q.g+1.4142135623730951, x2, y2, q),
            Cell(q.x-1, q.y+1, q.g+1.4142135623730951, x2, y2, q), Cell(q.x-1, q.y-1, q.g+1.4142135623730951, x2, y2, q)
        )
        for cell in nexts:
            if cell.x == x2 and cell.y == y2:
                return cell
            if inside(grid, cell.x, cell.y) and not grid[cell.x][cell.y] and not closedl[cell.x][cell.y]:
                if opena[cell.x][cell.y] == float('inf') or opena[cell.x][cell.y] > cell.f:
                    opena[cell.x][cell.y] = cell.f
                    openl.append(cell)
    return False
