import unittest

from src.blocks_world import BlockWorldState, IllegalMoveError, InvalidStateError


class StateTests(unittest.TestCase):
    def test_rejects_block_on_itself(self):
        with self.assertRaisesRegex(InvalidStateError, "samym sobie"):
            BlockWorldState((1, 0, 0))

    def test_rejects_nonexistent_support(self):
        with self.assertRaisesRegex(InvalidStateError, "nieistniejącym"):
            BlockWorldState((0, 4, 0))

    def test_rejects_two_blocks_on_one_support(self):
        with self.assertRaisesRegex(InvalidStateError, "tym samym"):
            BlockWorldState((0, 1, 1))

    def test_rejects_cycle(self):
        with self.assertRaisesRegex(InvalidStateError, "cykl"):
            BlockWorldState((2, 1, 0))

    def test_generates_only_basic_moves(self):
        state = BlockWorldState((0, 1, 0, 2, 3))
        self.assertEqual(state.clear_blocks(), {4, 5})
        self.assertEqual(set(state.legal_moves()), {(4, 0), (5, 0)})

    def test_cannot_move_directly_between_blocks(self):
        state = BlockWorldState((0, 1, 0, 2, 3))
        with self.assertRaisesRegex(IllegalMoveError, "wariancie podstawowym"):
            state.apply((4, 5))


if __name__ == "__main__":
    unittest.main()
