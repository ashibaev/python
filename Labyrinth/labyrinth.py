from location import Location, State


class Neighborhood:
    def in_range(self, location):
        pass

    def __getitem__(self, item):
        pass

    def next_state(self, state):
        if not self.in_range(state.location):
            return
        for next_location in state.location.neighborhood():
            if not self.in_range(next_location):
                continue
            if self[next_location].is_wall and state.bombs > 0:
                yield State(next_location, state.bombs - 1)
            elif not self[next_location].is_wall:
                yield State(next_location, state.bombs)


class Labyrinth3d(Neighborhood):
    """Describes 3d labyrinth"""
    def __init__(self, map_):
        if len(map_) == 0:
            raise ValueError("Map must be non-empty")
        try:
            current = 0
            self.map = []
            for layer in map_:
                self.map.append(Labyrinth(layer, current))
                current += 1
        except:
            raise
        if len({(layer.width, layer.height) for layer in self.map}) != 1:
            raise ValueError("Layers of 3d map must have equal size")
        self.depth = len(map_)
        self.width = self.map[0].width
        self.height = self.map[0].height

    def in_range(self, location):
        return 0 <= location.z < self.depth and self.map[location.z].in_range(location)

    def __getitem__(self, location):
        if not isinstance(location, Location):
            raise TypeError("Labyrinth index must be Location")
        if not self.in_range(location):
            raise IndexError("Out of range")
        return self.map[location.z][location]

    def __str__(self):
        return '\n'.join([str(layer) for layer in self.map])


class Labyrinth(Neighborhood):
    """Describes 2d labyrinth"""
    def __init__(self, map_, layer=0):
        if len(map_) == 0:
            raise ValueError("Map must be non-empty")
        if not isinstance(map_, list) or not isinstance(map_[0], str):
            raise TypeError("Map must be list of str")
        if len({len(row) for row in map_}) != 1:
            raise ValueError("Map must be rectangle")
        if not isinstance(layer, int):
            raise TypeError("Layer must be int")
        self.map = []
        for row in map_:
            self.map.append([LabyrinthObject(cell == '#') for cell in row])
        self.width = len(map_)
        self.height = len(map_[0])
        self.layer = layer

    def in_range(self, location):
        return 0 <= location.x < self.width \
               and 0 <= location.y < self.height \
               and self.layer == location.z

    def __getitem__(self, location):
        if not isinstance(location, Location):
            raise TypeError("Labyrinth index must be Location")
        if not self.in_range(location):
            raise IndexError("Out of range")
        return self.map[location.x][location.y]

    @staticmethod
    def str_line(row):
        return ''.join(['#' if cell.is_wall else '.' for cell in row])

    def __str__(self):
        return '\n'.join([Labyrinth.str_line(row) for row in self.map])

    def __eq__(self, other):
        return self.map == other.map


class LabyrinthObject:
    """It is object of labyrinth: wall or empty space."""
    def __init__(self, is_wall):
        if type(is_wall) is not bool:
            raise TypeError("is_wall param must be bool")
        self.is_wall = is_wall

    def __str__(self):
        return "Wall" if self.is_wall else "Empty"

    def __eq__(self, other):
        return self.is_wall == other.is_wall


class SearchInfo:
    """Information for some search in graph."""
    def __init__(self):
        self.used = set()
        self.dist = dict()
        self.parent = dict()

    def add(self, *args, state=None, parent=None, distance=None):
        if state in self.used:
            raise ValueError("state already used")
        self.used.add(state)
        self.dist[state] = distance
        self.parent[state] = parent
