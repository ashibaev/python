import itertools


class Location:
    """Location describes position of cell in labyrinth"""
    def __init__(self, x, y, z=0):
        if not isinstance(x, int) or not isinstance(y, int) or not isinstance(z, int):
            raise TypeError("Arguments must be int")
        self.x = x
        self.y = y
        self.z = z

    def __lt__(self, other):
        return (self.x, self.y, self.z) < (other.x, other.y, other.z)

    def neighborhood(self):
        """Generate neighbors of Location"""
        d = range(-1, 2)
        for x, y, z in filter(lambda x: abs(x[0]) + abs(x[1]) + abs(x[2]) == 1,
                              itertools.product(d, d, d)):
            yield Location(self.x + x, self.y + y, self.z + z)

    def __str__(self):
        return "Location: {0} {1} {2}.".format(self.x, self.y, self.z)

    def __hash__(self):
        return hash((self.x, self.y, self.z))

    def __eq__(self, other):
        return (self.x, self.y, self.z) == (other.x, other.y, other.z)


class State:
    """State describes current condition: current location and count of bombs."""
    def __init__(self, location, bombs):
        if not isinstance(location, Location):
            raise TypeError("location must be Location")
        if not isinstance(bombs, int):
            raise TypeError("bombs must be int")
        self.location = location
        self.bombs = bombs

    def __str__(self):
        return "State: {0} Count of bombs: {1}" \
            .format(self.location, self.bombs)

    def __hash__(self):
        return hash(self.location) ^ 397 + self.bombs

    def __eq__(self, other):
        return self.location == other.location and self.bombs == other.bombs

    def __lt__(self, other):
        return (self.location, self.bombs) < (other.location, other.bombs)
