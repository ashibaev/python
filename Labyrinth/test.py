import unittest

from labyrinth import Labyrinth, LabyrinthObject, Labyrinth3d, SearchInfo
from location import Location, State
from main import read_args, read_labyrinth, find_path, solve, print_help


class LocationTests(unittest.TestCase):
    def test_init(self):
        location = Location(1, 2)
        self.assertEqual(location.x, 1)
        self.assertEqual(location.y, 2)

    def test_wrong_init(self):
        self.assertRaises(TypeError, Location, 'x', 1)

    def test_neighborhood(self):
        loc = Location(2, 2)
        neighbors = []
        for next_location in loc.neighborhood():
            neighbors.append(next_location)
        expected = [Location(2, 1), Location(1, 2), Location(3, 2),
                    Location(2, 3), Location(2, 2, -1), Location(2, 2, 1)]
        self.assertSequenceEqual(sorted(neighbors), sorted(expected))

    def test_lt(self):
        a = Location(1, 2)
        b = Location(1, 3)
        c = Location(2, 3)
        self.assertTrue(a < b)
        self.assertTrue(b < c)
        self.assertTrue(a < c)

    def test_str(self):
        location = Location(2, 3)
        self.assertEqual(str(location), "Location: 2 3 0.")

    def test_equal_location_has_same_hash(self):
        first = Location(1, 2)
        second = Location(1, 2)
        self.assertEqual(hash(first), hash(second))

    def test_equals(self):
        a = Location(1, 2)
        b = Location(1, 2)
        c = Location(2, 3)
        self.assertEqual(a, b)
        self.assertNotEqual(a, c)


class SearchInfoTests(unittest.TestCase):
    def test_init(self):
        info = SearchInfo()
        self.assertSetEqual(info.used, set())
        self.assertDictEqual(info.parent, dict())
        self.assertDictEqual(info.dist, dict())

    def test_add(self):
        info = SearchInfo()
        info.add(state=1, parent=2, distance=3)
        info.add(state=2, parent=1, distance=0)
        self.assertSetEqual(info.used, {1, 2})
        self.assertDictEqual(info.dist, {1: 3, 2: 0})
        self.assertDictEqual(info.parent, {1: 2, 2: 1})

    def test_double_add(self):
        info = SearchInfo()
        info.add(1, 2, 3)
        self.assertRaises(ValueError, info.add, 1, 2, 3)


class LabyrinthObjectTests(unittest.TestCase):
    def test_init_wall(self):
        wall = LabyrinthObject(True)
        self.assertTrue(wall.is_wall)

    def test_init_empty(self):
        empty = LabyrinthObject(False)
        self.assertFalse(empty.is_wall)

    def test_wrong_init(self):
        self.assertRaises(TypeError, LabyrinthObject, 1)

    def test_str(self):
        wall = LabyrinthObject(True)
        self.assertEqual(str(wall), "Wall")
        empty = LabyrinthObject(False)
        self.assertEqual(str(empty), "Empty")

    def test_equal(self):
        wall1 = LabyrinthObject(True)
        wall2 = LabyrinthObject(True)
        self.assertEqual(wall1, wall2)


class StateTests(unittest.TestCase):
    def test_init(self):
        location = Location(1, 1)
        bombs = 10
        state = State(location, bombs)
        self.assertEqual(state.location, location)
        self.assertEqual(state.bombs, bombs)

    def test_wrong_init(self):
        location = Location(1, 1)
        bombs = 1
        self.assertRaises(TypeError, State, location, "1")
        self.assertRaises(TypeError, State, 1, bombs)

    def test_str(self):
        state = State(Location(1, 2), 3)
        self.assertEqual(str(state), "State: Location: 1 2 0. Count of bombs: 3")

    def test_equals(self):
        location = Location(1, 2)
        bombs = 3
        first = State(location, bombs)
        second = State(location, bombs)
        self.assertEqual(first, second)
        second.bombs += 1
        self.assertNotEqual(first, second)

    def test_hash(self):
        location = Location(1, 2)
        bombs = 3
        first = State(location, bombs)
        second = State(location, bombs)
        self.assertEqual(hash(first), hash(second))

    def test_lt(self):
        first = State(Location(1, 2), 3)
        second = State(Location(1, 2), 4)
        self.assertLess(first, second)


class LabyrinthTest(unittest.TestCase):
    def test_init(self):
        map_ = ["#..",
                "..."]
        labyrinth = Labyrinth(map_)
        expected_map = [[LabyrinthObject(True), LabyrinthObject(False), LabyrinthObject(False)],
                        [LabyrinthObject(False), LabyrinthObject(False), LabyrinthObject(False)]]
        self.assertEqual(labyrinth.width, 2)
        self.assertEqual(labyrinth.height, 3)
        self.assertEqual(labyrinth.map, expected_map)

    def test_wrong_init(self):
        map_ = []
        self.assertRaises(ValueError, Labyrinth, map_)
        map_.append(["x"])
        self.assertRaises(TypeError, Labyrinth, map_)
        map_ = ["...",
                "#."]
        self.assertRaises(ValueError, Labyrinth, map_)
        self.assertRaises(TypeError, Labyrinth, ["#"], "1")

    def test_in_range(self):
        map_ = ["...",
                "###"]
        location = Location(1, 2)
        out_of_range_location = Location(0, 3)
        labyrinth = Labyrinth(map_)
        self.assertTrue(labyrinth.in_range(location))
        self.assertFalse(labyrinth.in_range(out_of_range_location))

    def test_getitem(self):
        map_ = [".#.",
                "##.",
                ".#."]
        labyrinth = Labyrinth(map_)
        wall = LabyrinthObject(True)
        empty = LabyrinthObject(False)
        for x in range(3):
            for y in range(3):
                current = labyrinth[Location(x, y)]
                if y == 1 or x == 1 and y == 0:
                    self.assertEqual(current, wall)
                else:
                    self.assertEqual(current, empty)
        self.assertRaises(TypeError, labyrinth.__getitem__, 1)
        self.assertRaises(IndexError, labyrinth.__getitem__, Location(-1, 1))

    def check_next_state(self, labyrinth, state, expected):
        next_states = []
        for next_state in labyrinth.next_state(state):
            next_states.append(next_state)
        self.assertEqual(expected,
                         sorted(next_states,
                                key=lambda state: state.location))

    def test_next_state(self):
        map_ = ["...",
                "#.#",
                "###"]
        labyrinth = Labyrinth(map_)
        location = Location(1, 1)
        out_of_range_location = Location(0, 4)
        state = State(out_of_range_location, 1)
        self.check_next_state(labyrinth, state, [])
        expected_next_states = [State(Location(0, 1), 1),
                                State(Location(1, 0), 0),
                                State(Location(1, 2), 0),
                                State(Location(2, 1), 0)]
        state = State(location, 1)
        self.check_next_state(labyrinth, state, expected_next_states)
        state = State(Location(0, 0), 1)
        self.check_next_state(labyrinth, state, expected_next_states[0:2])

    def test_str_row(self):
        wall = LabyrinthObject(True)
        empty = LabyrinthObject(False)
        map_ = [wall, empty, wall]
        self.assertEqual(Labyrinth.str_line(map_), "#.#")

    def test_str(self):
        map_ = ["...",
                "#.#",
                "###"]
        labyrinth = Labyrinth(map_)
        self.assertEqual('\n'.join(map_), str(labyrinth))


class Labyrinth3dTests(unittest.TestCase):
    def test_init(self):
        map_ = ["...",
                "#.#",
                "###"]
        layer = Labyrinth(map_)
        labyrinth = Labyrinth3d([map_, map_])
        self.assertEqual(labyrinth.depth, 2)
        self.assertEqual(labyrinth.width, 3)
        self.assertEqual(labyrinth.height, 3)
        self.assertEqual(labyrinth.map, [layer, layer])

    def test_wrong(self):
        self.assertRaises(ValueError, Labyrinth3d, [])
        self.assertRaises(ValueError, Labyrinth3d, [["#"], [".."]])
        self.assertRaises(ValueError, Labyrinth3d, [[]])
        self.assertRaises(TypeError, Labyrinth3d, [1])

    def test_in_range(self):
        map_ = ["...",
                "#.#",
                "###"]
        labyrinth = Labyrinth3d([map_, map_])
        location = Location(1, 2, 1)
        out_of_range_location = Location(1, 2, 2)
        self.assertTrue(labyrinth.in_range(location))
        self.assertFalse(labyrinth.in_range(out_of_range_location))

    def test_str(self):
        map_ = ["...",
                "#.#",
                "###"]
        layer = Labyrinth(map_)
        labyrinth = Labyrinth3d([map_, map_])
        self.assertEqual(str(labyrinth), str(layer) + "\n" + str(layer))

    def test_getitem(self):
        map_ = ["#.",
                "#."]
        wall = LabyrinthObject(True)
        empty = LabyrinthObject(False)
        labyrinth = Labyrinth3d([map_, map_])
        self.assertRaises(TypeError, labyrinth.__getitem__, 1)
        self.assertRaises(IndexError, labyrinth.__getitem__, Location(-1, 1, 0))
        for x in range(2):
            for y in range(2):
                for z in range(2):
                    location = Location(x, y, z)
                    if y == 0:
                        self.assertEqual(wall, labyrinth[location])
                    else:
                        self.assertEqual(empty, labyrinth[location])


class ReadArgsTests(unittest.TestCase):
    def test_right_arguments(self):
        argv = ["", "--help"]
        args = read_args(argv)
        self.assertTrue(args.help)
        argv = ["", "input.txt", "1", "2", "3", "4", "5", "6", "7"]
        args = read_args(argv)
        self.assertFalse(args.help)
        self.assertEqual(args.filename, "input.txt")
        self.assertEqual(args.start, Location(0, 1, 2))
        self.assertEqual(args.end, Location(3, 4, 5))
        self.assertEqual(args.bombs, 7)

    def check_wrong(self, argv):
        self.assertRaises(ValueError, read_args, argv)

    def test_wrong_arguments(self):
        self.check_wrong(["", "help"])
        self.check_wrong(["", "1", "2"])
        self.check_wrong(["x"] * 7)
        self.check_wrong(["x"] * 9)


class LabyrinthReadTests(unittest.TestCase):
    def test_wrong_file(self):
        self.assertRaises(FileNotFoundError, read_labyrinth, 'x')

    def test_incorrect_file(self):
        self.assertRaises(ValueError, read_labyrinth, "wrong_input.txt")

    def test_correct(self):
        map_ = ["##########",
                "#..#.....#",
                "#..#.....#",
                "#.#......#",
                "#..#.....#",
                "#........#",
                "##########"]
        labyrinth = Labyrinth3d([map_])
        result = read_labyrinth("test_input.txt")
        self.assertEqual(labyrinth.map, result.map)
        self.assertEqual(labyrinth.height, result.height)
        self.assertEqual(labyrinth.width, result.width)
        self.assertEqual(labyrinth.depth, result.depth)


class FindPathTests(unittest.TestCase):
    @staticmethod
    def get_info(locations, final_state):
        info = SearchInfo()
        info.final_state = final_state
        states = [State(location, 0) for location in locations]
        states = [None] + states
        for i in range(1, len(states)):
            info.add(state=states[i], parent=states[i - 1], distance=(i - 1))
        return info

    def test_empty(self):
        map_ = ["..",
                ".."]
        labyrinth = Labyrinth3d([map_, map_])
        info = self.get_info([Location(0, 0, 0),
                              Location(1, 0, 0),
                              Location(1, 1, 0),
                              Location(1, 1, 1)],
                             State(Location(1, 1, 1), 0))
        expected = ['X.',
                    'XX',
                    '',
                    '..',
                    '.X']
        self.assertEqual(find_path(labyrinth, info), expected)

    def test_bombs(self):
        map_ = [["....",
                 "####",
                 "...."],
                ["####",
                 "....",
                 "####"]]
        labyrinth = Labyrinth3d(map_)
        info = self.get_info([Location(0, 0, 0),
                              Location(1, 0, 0),
                              Location(1, 0, 1),
                              Location(1, 1, 1),
                              Location(1, 2, 1),
                              Location(2, 2, 1)],
                             State(Location(2, 2, 1), 0))
        expected = ["X...",
                    "B###",
                    "....",
                    '',
                    "####",
                    "XXX.",
                    "##B#"]
        self.assertEqual(find_path(labyrinth, info), expected)


class SolveTests(unittest.TestCase):
    @staticmethod
    def get_info(locations, final_state):
        info = SearchInfo()
        info.final_state = final_state
        states = [State(location, 0) for location in locations]
        states = [None] + states
        for i in range(1, len(states)):
            info.add(state=states[i], parent=states[i - 1], distance=(i - 1))
        return info

    def test_empty(self):
        map_ = ["...",
                "...",
                "..."]
        labyrinth = Labyrinth3d([map_, map_])
        info = self.get_info([Location(0, 0, 0),
                              Location(0, 0, 1),
                              Location(0, 1, 1),
                              Location(0, 2, 1),
                              Location(1, 2, 1),
                              Location(2, 2, 1)],
                             State(Location(2, 2, 1), 0))
        solve_info = solve(labyrinth, Location(0, 0, 0), Location(2, 2, 1), 0)
        path = find_path(labyrinth, solve_info)
        expected = find_path(labyrinth, info)
        self.assertEqual(path, expected)

    def test_easy(self):
        map_ = [[".#",
                 "#."],
                ["..",
                 ".."]]
        labyrinth = Labyrinth3d(map_)
        info = self.get_info([Location(0, 0, 0),
                              Location(0, 0, 1),
                              Location(0, 1, 1),
                              Location(1, 1, 1),
                              Location(1, 1, 0)],
                             State(Location(1, 1, 0), 0))
        solve_info = solve(labyrinth, Location(0, 0, 0), Location(1, 1, 0), 0)
        path = find_path(labyrinth, solve_info)
        expected = find_path(labyrinth, info)
        self.assertEqual(path, expected)

    def test_no_path(self):
        map_ = ["....",
                "####",
                "...."]
        labyrinth = Labyrinth3d([map_])
        self.assertIsNone(solve(labyrinth, Location(0, 0), Location(2, 2), 0))

    def test_economy(self):
        map_ = [[".......",
                 "######.",
                 "......."]]
        labyrinth = Labyrinth3d(map_)
        info = solve(labyrinth, Location(0, 0), Location(2, 0), 1)
        expected = ["XXXXXXX",
                    "######X",
                    "XXXXXXX"]
        self.assertEqual(find_path(labyrinth, info), expected)

    def test_hard(self):
        map_ = ["........",
                "###..#..",
                "...#.#.#",
                "....#..#",
                ".....#..",
                "........"]
        labyrinth = Labyrinth3d([map_])
        info = solve(labyrinth, Location(0, 0), Location(5, 0), 10)
        expected = ["XXXXXXX.",
                    "###..#X.",
                    "...#.#X#",
                    "....#.X#",
                    ".....#X.",
                    "XXXXXXX."]
        self.assertEqual(find_path(labyrinth, info), expected)

    def test_bomb_hard(self):
        map_ = ["........",
                "###..#..",
                "#.######",
                "...##..#",
                ".#...#..",
                "........"]
        labyrinth = Labyrinth3d([map_])
        info = solve(labyrinth, Location(0, 0), Location(5, 0), 10)
        expected = ["XX......",
                    "#B#..#..",
                    "#X######",
                    "XX.##..#",
                    "X#...#..",
                    "X......."]
        self.assertEqual(find_path(labyrinth, info), expected)


if __name__ == '__main__':
    unittest.main()
