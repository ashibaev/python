import os
import dill
import heapq
import time
import shutil
import asyncio
import aiofiles
import io
from multiprocessing import Pool
from contextlib import contextmanager
from multiprocessing import Manager


@contextmanager
def range_open(files, mode, buffering=io.DEFAULT_BUFFER_SIZE):
    opened_files = []
    try:
        opened_files = [open(file, mode, buffering=buffering) for file in files]
        yield opened_files
    finally:
        for file in opened_files:
            file.close()


async def _buffered_print(buffered, output_filename, buffer_size):
    async with aiofiles.open(output_filename, "w", buffering=buffer_size) as out_file:
        await out_file.write("\n".join(buffered) + "\n")
    return os.path.getsize(output_filename)


def split_file(filename, reverse_order, parser, memory_usage, path, loop, statistic=None):
    if statistic:
        statistic.next_state(os.path.getsize(filename))
        statistic.print()
    if memory_usage < 0:
        raise ValueError("Memory usage must be non-negative")
    if loop.is_closed():
        raise ValueError("Loop closed")
    count_of_files = 0
    block_size = 2 ** 16
    count_of_coros = memory_usage // block_size
    coros = set()
    with open(filename, "r", memory_usage) as f:
        while True:
            buffered = f.read(block_size)
            adding = f.readline()
            buffered += adding
            buffered = [line for line in buffered.split("\n") if line]
            buffered.sort(key=parser, reverse=reverse_order)
            coros.add(_buffered_print(buffered, os.path.join(path, str(count_of_files)), block_size))
            count_of_files += 1
            if len(coros) >= count_of_coros:
                done, coros = loop.run_until_complete(asyncio.wait(coros, return_when=asyncio.FIRST_COMPLETED))
                if statistic:
                    for coro in done:
                        statistic.add_printed(coro.result())
                    statistic.print()
            if not adding:
                break
    while coros:
        done, coros = loop.run_until_complete(asyncio.wait(coros, return_when=asyncio.FIRST_COMPLETED))
        if statistic:
            for coro in done:
                statistic.add_printed(coro.result())
                statistic.print()
    return count_of_files


def _split_line(line, sep=" ", field=1, types=""):
    ans = [x for x in line.split(sep) if x]
    n = len(ans)
    m = len(types)
    if field > n:
        raise ValueError("Line have no {0} field\n{1}".format(field, line))
    if field != 1:
        ans = ans[field - 1:] + ans[:field - 1]
    for i in range(min(n, m)):
        if types[i] == 'n':
            try:
                ans[i] = int(ans[i])
            except ValueError:
                raise ValueError("Incorrect type of field.")
    return ans, line


def _merge_files(output_filename, parser, begin, end, buffer_size, path, reverse_order, queue, lock):
    files = [os.path.join(path, str(i)) for i in range(begin, end)]
    parser = dill.loads(parser)
    with range_open(files, "r", buffer_size) as iters:
        buffer_size //= 20
        printed = 0
        buffered = []
        current_size = 0
        append = buffered.append
        for line in heapq.merge(*iters, reverse=reverse_order, key=parser):
            append(line)
            current_size += len(line)
            if current_size > buffer_size:
                with open(output_filename, "a") as f:
                    f.write(''.join(buffered))
                buffered = []
                append = buffered.append
                current_size = 0
                new_printed = os.path.getsize(output_filename)
                with lock:
                    queue.put(new_printed - printed)
                printed = new_printed
        if buffered:
            with open(output_filename, "a") as f:
                f.write(''.join(buffered))
            new_printed = os.path.getsize(output_filename)
            with lock:
                queue.put(new_printed - printed)

    for file in files:
        os.remove(file)


def _get_expected_tree_height(count_of_files, to_merge):
    ans = 0
    cur = 1
    while count_of_files > cur:
        ans += 1
        cur *= to_merge
    return ans


def merge_files(filename, output_filename, count_of_files, buffer_size, parser, path, reverse_order, statistic=None):
    to_merge = 20
    if statistic:
        statistic.next_state(os.path.getsize(filename) * _get_expected_tree_height(count_of_files, to_merge))
        statistic.print()
    left = 0
    right = count_of_files
    parser = dill.dumps(parser)
    while right - left != 1:
        cnt = (right - left) // to_merge + int((right - left) % to_merge != 0)
        with Pool(maxtasksperchild=1000) as pool:
            with Manager() as manager:
                queue = manager.Queue()
                lock = manager.Lock()
                workers = []
                for _ in range(cnt):
                    next_file = os.path.join(path, str(count_of_files))
                    count_of_files += 1
                    workers.append(pool.apply_async(_merge_files,
                                                    args=(next_file, parser, left, min(left + to_merge, right),
                                                          buffer_size // os.cpu_count(),
                                                          path, reverse_order, queue, lock)))
                    left += to_merge
                while not all(worker.ready() for worker in workers):
                    time.sleep(0.1)
                    __print_statistic(lock, queue, statistic)
                __print_statistic(lock, queue, statistic)
        left, right = right, count_of_files
    last_file = os.path.join(path, str(count_of_files - 1))
    shutil.copy(last_file, output_filename)
    os.remove(last_file)
    if statistic:
        statistic.print()


def __print_statistic(lock, queue, statistic):
    with lock:
        cur_sum = 0
        for _ in range(queue.qsize()):
            cur_sum += queue.get()
    if not statistic:
        return
    statistic.add_printed(cur_sum)
    statistic.print()


def out_sort(filename, output_filename, path, reverse_order=False,
             sep=' ', field=1, types="", memory_usage=2 ** 23,
             statistic=None):
    time.clock()
    if statistic:
        statistic.print()
    if field < 1:
        raise ValueError("Incorrect number of field.")
    parser = lambda line: _split_line(line, sep, field, types)
    memory_usage //= 2
    loop = asyncio.get_event_loop()
    count_of_files = split_file(filename,
                                reverse_order=reverse_order,
                                parser=parser,
                                memory_usage=memory_usage,
                                path=path,
                                loop=loop,
                                statistic=statistic)
    buffer_size = int(max(2 ** 20, memory_usage))
    merge_files(filename, output_filename, count_of_files, buffer_size, parser, path, reverse_order, statistic)
    if statistic:
        statistic.next_state(0)
        statistic.print()
