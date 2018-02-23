from random import randint


def generate_random_string(length):
    answer = ""
    for i in range(length):
        answer += chr(33 + randint(0, 90))
    return answer


def gen_tuple(types):
    return tuple(str(randint(0, 100)) if t == "n" else generate_random_string(20) for t in types)


def gen_str(types):
    return '    '.join(gen_tuple(types)) + "\n"


def generate_random_file(size, filename, types="s"):
    cur_len = len(gen_str(types))
    count_of_lines = (size + cur_len - 1) // cur_len
    with open(filename, "w", buffering=2 ** 16) as f:
        for _ in range(count_of_lines):
            f.write(gen_str(types))
        f.flush()
    return count_of_lines


def generate_file(size, filename, types="s"):
    with open(filename, "w", buffering=2 ** 16) as f:
        line = gen_str(types)
        count_of_lines = (size + len(line) - 1) // len(line)
        for _ in range(count_of_lines):
            f.write(line)
    return count_of_lines


def check_file(filename, parser, reverse_order):
    prev_line = None
    count_of_line = 0
    with open(filename, "r") as file:
        for line in file:
            if line:
                count_of_line += 1
            if prev_line and line:
                parsed_line = parser(line)
                parsed_prev = parser(prev_line)
                if parsed_prev != parsed_line and (parsed_prev < parsed_line) == reverse_order:
                    return 0
            prev_line = line
    return count_of_line


def main():
    size = 5 * 2 ** 20
    for i in range(size, 21 * size, size):
        generate_random_file(i, str(i), "nnssn")


if __name__ == '__main__':
    main()
