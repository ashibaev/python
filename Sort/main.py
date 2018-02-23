import argparse
import sys
import tempfile
import time

from out_sort import out_sort, sort_statistic


def main(argv):
    try:
        with open(argv.input_filename, "r"), open(argv.output_filename, "w"):
            pass
    except FileNotFoundError:
        print("There is no such file.", file=sys.stderr)
        sys.exit(1)
    except PermissionError:
        print("Permission denied.", file=sys.stderr)
        sys.exit(2)
    except Exception:
        print("Something wrong.", file=sys.stderr)
        sys.exit(3)
    try:
        stat = sort_statistic.Statistic(classic_stat_printer)
        with tempfile.TemporaryDirectory() as tempdir:
            out_sort.out_sort(argv.input_filename, argv.output_filename, tempdir,
                              reverse_order=argv.reverse_order, sep=argv.sep,
                              field=argv.field, types=argv.types, memory_usage=argv.memory,
                              statistic=stat)
    except ValueError as err:
        print(err, file=sys.stderr)
        sys.exit(4)


def classic_stat_printer(stat):
    part = stat.get_finished_part() * 100
    cur_str = ["."] * 50
    for i in range(2, 101, 2):
        if part >= i:
            cur_str[i // 2 - 1] = '#'
    print("\r[{0}] {1} - {2:.2f}%".format(''.join(cur_str), stat.state.name, part), end="")
    if stat.state == sort_statistic.State.FINISHED:
        print("\rREADY")


def read_args(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("input_filename", type=str,
                        help="Name of target file.")
    parser.add_argument("output_filename", type=str,
                        help="Name of file for result.")
    parser.add_argument("-r", action="store_true", default=False,
                        help="Reverse order.", dest="reverse_order")
    parser.add_argument("-s", action="store", type=str, default=' ',
                        help="Separator of columns", dest="sep")
    parser.add_argument("-f", action="store", type=int, default=1,
                        help="Key field.", dest="field")
    parser.add_argument("--types", action="store", type=str, dest="types",
                        help="Types of fields starting from key field.", default="")
    parser.add_argument("-m", action="store", type=int, dest="memory", default=2 ** 20)
    result = parser.parse_args(argv)
    result.memory = int(max(result.memory // 3, 2 ** 20))
    types = {"n", "s"}
    for x in result.types:
        if x not in types:
            print("Unrecognized type {0}. Expected n or s.".format(x), file=sys.stderr)
            sys.exit(5)
    return result


if __name__ == "__main__":
    try:
        argv = read_args(sys.argv[1:])
    except ValueError:
        sys.exit(1)
    time.clock()
    main(argv)
    print(time.clock())
