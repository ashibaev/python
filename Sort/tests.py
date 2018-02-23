import asyncio
import os
import tempfile
import unittest
from out_sort.sort_statistic import State
from out_sort.sort_statistic import Statistic
import out_sort.out_sort as out_sort
from utils import file_generator


class StatisticTest(unittest.TestCase):
    def test_next_state_raises_exception(self):
        stat = Statistic(None)
        self.assertRaises(ValueError, stat.next_state, 1.0)
        self.assertRaises(ValueError, stat.next_state, "a")
        self.assertRaises(ValueError, stat.next_state, set())

    def test_init(self):
        stat = Statistic(None)
        self.assertEqual(0, stat._expected_size)
        self.assertEqual(0, stat._printed_size)
        self.assertEqual(State.PENDING, stat._state)

    def test_next_state(self):
        stat = Statistic(None)
        self.assertEqual(State.PENDING, stat._state)
        stat.next_state(10)
        stat.add_printed(5)
        self.assertEqual(State.SPLITTING, stat._state)
        self.assertEqual(5, stat._printed_size)
        self.assertEqual(10, stat._expected_size)
        stat.next_state(1)
        self.assertEqual(State.MERGING, stat._state)
        self.assertEqual(0, stat._printed_size)
        stat.next_state(1)
        self.assertEqual(State.FINISHED, stat._state)
        stat.next_state(2)
        self.assertEqual(State.FINISHED, stat._state)

    def test_add_printed(self):
        stat = Statistic(None)
        self.assertRaises(ValueError, stat.add_printed, 1.1)
        self.assertRaises(ValueError, stat.add_printed, '1')
        self.assertRaises(ValueError, stat.add_printed, set())
        stat.add_printed(10)
        self.assertEqual(10, stat._printed_size)
        stat.next_state(1)
        stat.next_state(1)
        stat.next_state(1)
        self.assertEqual(0, stat._printed_size)
        stat.add_printed(10)
        self.assertEqual(0, stat._printed_size)

    def test_get_finished_part(self):
        stat = Statistic(None)
        self.assertAlmostEqual(1, stat.get_finished_part(), delta=10 ** (-5))
        stat.next_state(100)
        for i in range(100):
            self.assertAlmostEqual(i * 0.01, stat.get_finished_part(), delta=10 ** (-5))
            stat.add_printed(1)
        self.assertAlmostEqual(1, stat.get_finished_part(), delta=10 ** (-5))


class SplitLineTest(unittest.TestCase):
    def set_parser(self, sep=' ', field=1, types=''):
        self.parser = lambda line: out_sort._split_line(line, sep, field, types)

    def test_default(self):
        self.set_parser()
        line = "ab cd\n"
        self.assertEqual((["ab", "cd\n"], line), self.parser(line))

    def test_fields(self):
        self.set_parser(field=2)
        line = "ab cd\n"
        self.assertEqual((["cd\n", "ab"], line), self.parser(line))
        self.assertRaises(ValueError, self.parser, "ab")

    def test_sep(self):
        self.set_parser(sep="...")
        line = "ab cd"
        self.assertEqual(([line], line), self.parser(line))
        line = "a...b"
        self.assertEqual((["a", "b"], line), self.parser(line))
        line = "a..."
        self.assertEqual((["a"], line), self.parser(line))
        line = " ... \n"
        self.assertEqual(([" ", " \n"], line), self.parser(line))
        self.assertRaises(ValueError, self.parser, "...")

    def test_types(self):
        self.set_parser(types="sn")
        line = "a 12"
        self.assertEqual((["a", 12], line), self.parser(line))
        self.set_parser(types="an")
        self.assertEqual((["a", 12], line), self.parser(line))
        line = "1 2"
        self.assertEqual((["1", 2], line), self.parser(line))
        self.assertRaises(ValueError, self.parser, "a b")


class RangeOpenTest(unittest.TestCase):
    def test(self):
        with tempfile.TemporaryDirectory() as tempdir:
            files = [os.path.join(tempdir, "temp" + str(i)) for i in range(10)]
            with out_sort.range_open(files, "w") as iters:
                for file in iters:
                    self.assertFalse(file.closed)
            for file in iters:
                self.assertTrue(file.closed)


class ExpectedTreeHeightTest(unittest.TestCase):
    def testSimple(self):
        self.assertEqual(0, out_sort._get_expected_tree_height(1, 2))
        self.assertEqual(0, out_sort._get_expected_tree_height(1, 3))
        self.assertEqual(1, out_sort._get_expected_tree_height(2, 3))
        self.assertEqual(1, out_sort._get_expected_tree_height(5, 11))
        self.assertEqual(2, out_sort._get_expected_tree_height(12, 11))
        self.assertEqual(2, out_sort._get_expected_tree_height(121, 11))
        self.assertEqual(3, out_sort._get_expected_tree_height(122, 11))


class SplitFileTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dir = tempfile.TemporaryDirectory()
        cls.rev_dir = tempfile.TemporaryDirectory()
        cls.path = cls.dir.name
        cls.rev_path = cls.rev_dir.name
        filename = os.path.join(cls.path, "test_input")
        reversed_file = os.path.join(cls.rev_path, "test_input_reversed")
        file_generator.generate_random_file(2 ** 20, filename)
        file_generator.generate_random_file(2 ** 20, reversed_file)
        cls.parser = lambda line: out_sort._split_line(line)
        loop = asyncio.get_event_loop()
        result = out_sort.split_file(filename,
                                     reverse_order=False,
                                     parser=cls.parser,
                                     memory_usage=10 ** 6,
                                     path=cls.path,
                                     loop=loop)
        result_reversed = out_sort.split_file(reversed_file,
                                              reverse_order=True,
                                              parser=cls.parser,
                                              memory_usage=10 ** 6,
                                              path=cls.rev_path,
                                              loop=loop)
        cls.results = result, result_reversed
        loop.close()

    @classmethod
    def tearDownClass(cls):
        cls.dir.cleanup()

    def testCountOfFiles(self):
        self.assertEqual(2 ** 4, SplitFileTest.results[0])
        self.assertEqual(2 ** 4, SplitFileTest.results[1])

    @staticmethod
    def checker(reverse_order, path):
        for i in range(16):
            current = os.path.join(path, str(i))
            if not os.path.exists(current):
                continue
            if not file_generator.check_file(current, SplitFileTest.parser, reverse_order):
                return False
        return True

    def testSorted(self):
        self.assertTrue(SplitFileTest.checker(False, SplitFileTest.path))

    def testReversedSorted(self):
        self.assertTrue(SplitFileTest.checker(True, SplitFileTest.rev_path))


class MergeFilesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dir = tempfile.TemporaryDirectory()
        cls.rev_dir = tempfile.TemporaryDirectory()
        cls.path = cls.dir.name
        cls.rev_path = cls.rev_dir.name
        cls.parser = lambda line: out_sort._split_line(line)
        cls.lines = 0
        for i in range(40):
            cls.lines += file_generator.generate_file(2 ** 16, os.path.join(cls.path, str(i)))
            file_generator.generate_file(2 ** 16, os.path.join(cls.rev_path, str(i)))

    @classmethod
    def tearDownClass(cls):
        cls.dir.cleanup()
        cls.rev_dir.cleanup()

    def testSorted(self):
        filename = os.path.join(MergeFilesTest.path, "filename")
        out_sort.merge_files("", filename, 40, 1000000, MergeFilesTest.parser, MergeFilesTest.path, False, None)
        self.assertEqual(MergeFilesTest.lines, file_generator.check_file(filename, MergeFilesTest.parser, False))

    def testReversed(self):
        filename = os.path.join(MergeFilesTest.rev_path, "filename")
        out_sort.merge_files("", filename, 40, 1000000, MergeFilesTest.parser, MergeFilesTest.rev_path, True, None)
        self.assertEqual(MergeFilesTest.lines, file_generator.check_file(filename, MergeFilesTest.parser, True))
