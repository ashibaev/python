import sys

from collections import namedtuple
from heapq import *
from labyrinth import Labyrinth3d, SearchInfo
from location import Location, State


def read_args(argv):
    """Check arguments for correctness and parse them."""
    ConsoleArgs = namedtuple("ConsoleArgs", ["help", "filename", "start", "end", "bombs"])
    if "--help" in argv and argv[1] == "--help" or "-h" in argv and argv[1] == "-h":
        return ConsoleArgs(help=True, filename=None, start=None, end=None, bombs=None)
    if len(argv) != 9:
        print("Incorrect arguments. Print --help or -h for more information.")
        raise ValueError
    other_args = list(map(int, argv[2:]))
    other_args = [x - 1 for x in other_args]
    return ConsoleArgs(help=False,
                       filename=argv[1],
                       start=Location(*other_args[0:3]),
                       end=Location(*other_args[3:6]),
                       bombs=other_args[-1] + 1)


def solve(labyrinth, start, end, bombs):
    """Find path from start to end in labyrinth with bombs"""
    start_state = State(start, bombs)
    info = SearchInfo()
    heap = []
    heappush(heap, (bombs, 0, start_state))
    info.add(state=start_state, parent=None, distance=0)
    while len(heap) != 0:
        current = heappop(heap)[2]
        if current.location == end:
            info.final_state = current
            return info
        for state in labyrinth.next_state(current):
            if state not in info.used:
                info.add(state=state, parent=current, distance=info.dist[current] + 1)
                heappush(heap, (-state.bombs, info.dist[state], state))
    return None


def read_labyrinth(filename):
    """Read labyrinth from file"""
    try:
        with open(filename, "r") as f:
            temp_map = [line.strip() for line in f]
        temp_map = '\n'.join(temp_map)
        temp_map = [layer.split() for layer in temp_map.split("\n\n")]
    except:
        raise
    else:
        return Labyrinth3d(temp_map)


def print_help():
    """Print information about program."""
    print("Find path in labyrinth in file 'filename',",
          "from cell 'start' to cell 'end' with count of bombs='bombs'.",
          "Example: main.py input.txt 1 1 0 2 2 0 3",
          "From (1, 1, 0) to (2, 2, 0) with 3 bombs",
          "Symbol '#' is wall, other - empty space",
          "Example of labyrinth 2 * 2 * 2:",
          "",
          "#.",
          "..",
          "",
          ".#",
          "..",
          sep="\n")


def find_path(labyrinth, info):
    """By labyrinth and SearchInfo find path and draw it in map of labyrinth"""
    answer = []
    for layer in (str(layer).split() for layer in labyrinth.map):
        answer.append([list(line) for line in layer])
    current_state = info.final_state
    while current_state:
        location = current_state.location
        if answer[location.z][location.x][location.y] == '.':
            answer[location.z][location.x][location.y] = 'X'
        else:
            answer[location.z][location.x][location.y] = 'B'
        current_state = info.parent[current_state]
    result = []
    for layer in answer:
        for line in layer:
            result.append(''.join(line))
        result.append("")
    result.pop()
    return result


def main(args):
    if args.help:
        print_help()
        exit(0)
    try:
        labyrinth = read_labyrinth(args.filename)
    except FileNotFoundError or NotADirectoryError:
        print("There is no such file / Permission denied.")
        exit(1)
    except OSError:
        print("Some problems with OS.")
        exit(1)
    except ValueError:
        print("Incorrect content of file. Print --help or -h for more information.")
        exit(1)
    else:
        info = solve(labyrinth, args.start, args.end, args.bombs)
        if not info:
            print("There is no path")
        else:
            path = find_path(labyrinth, info)
            print(*path, sep="\n")


if __name__ == "__main__":
    try:
        args = read_args(sys.argv)
    except ValueError:
        exit(1)
    else:
        main(args)
