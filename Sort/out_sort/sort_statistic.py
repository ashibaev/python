from enum import IntEnum


class State(IntEnum):
    PENDING = 0
    SPLITTING = 1
    MERGING = 2
    FINISHED = 3


class Statistic:
    def __init__(self, print_function=None):
        self._state = State.PENDING
        self._printed_size = 0
        self._expected_size = 0
        self._printer = print_function

    @property
    def state(self):
        return self._state

    def next_state(self, size):
        if not isinstance(size, int):
            raise ValueError("Incorrect type of argument. Printed and expected sizes can only be integer.")
        if self._state == State.FINISHED:
            return
        self._printed_size = 0
        self._expected_size = size
        self._state = State(self._state.value + 1)

    def add_printed(self, size):
        if not isinstance(size, int):
            raise ValueError("Incorrect type of argument. Printed and expected sizes can only be integer.")
        if self._state == State.FINISHED:
            return
        self._printed_size += size

    def get_finished_part(self):
        if not self._expected_size or self._state == State.FINISHED:
            return 1
        part = self._printed_size / self._expected_size
        return min(part, 1)

    def __str__(self):
        return "Statistic: State is {0}, printed size is {1}, expected is {2}" \
            .format(self._state.name, self._printed_size, self._expected_size)

    def print(self):
        if self._printer:
            self._printer(self)
