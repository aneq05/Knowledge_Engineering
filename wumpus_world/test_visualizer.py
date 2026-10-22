"""Sprawdza integrację gry z regułami, Clingo, cofaniem i lokalnym HTTP."""

import json
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from visualizer import Game, Server


class GameTests(unittest.TestCase):
    def test_initial_knowledge_is_not_the_hidden_map(self):
        state = Game().state()
        self.assertEqual({(c['x'], c['y']) for c in state['cells'] if c['safe']}, {(1, 2), (2, 1)})
        self.assertIn('no_breeze(1,1).', state['facts'])
        self.assertNotIn('wumpus(1,3)', state['facts'])

    def test_bump_and_manual_empty_actions_stay_in_sync(self):
        g = Game()
        for action in ('right', 'forward', 'grab', 'climb'):
            state = g.act(action)
        self.assertEqual(g.world.pos, (1, 1))
        self.assertEqual(g.agent.gold_carried, 0)
        # CLIMB on the entrance ends the game even without gold.
        self.assertTrue(state['done'])
        self.assertEqual(state['score'], -4)
        g.undo()
        self.assertFalse(g.world.done)
        self.assertEqual(g.agent.pos, g.world.pos)

    def test_shot_is_recorded_once_and_undo_restores_wumpus(self):
        g = Game()
        g.act('left')
        state = g.act('shoot')
        self.assertTrue(state['percept']['scream'])
        self.assertEqual(state['effect']['path'], [(1, 2), (1, 3)])
        self.assertEqual(len(g.agent.kb.shots), 1)
        self.assertEqual(state['arrows'], 0)
        g.act('agent')
        self.assertEqual(len(g.agent.kb.shots), 1)
        g.undo()
        g.undo()
        self.assertIn((1, 3), g.world.live_wumpuses)
        self.assertEqual(g.world.arrows, 1)
        self.assertFalse(g.agent.kb.shots)

    def test_no_ammunition_does_not_add_shot(self):
        g = Game()
        g.act('shoot')
        g.act('shoot')
        self.assertEqual(len(g.agent.kb.shots), 1)
        self.assertEqual(g.world.arrows_used, 1)
        self.assertEqual(g.agent.arrows, 0)

    def test_death_does_not_mark_pit_as_safely_visited(self):
        g = Game()
        g.act('forward')
        state = g.act('forward')
        self.assertFalse(state['alive'])
        self.assertNotIn((3, 1), g.agent.kb.visited)
        with self.assertRaises(ValueError):
            g.act('left')
        g.undo()
        self.assertTrue(g.world.alive)
        self.assertEqual(g.world.pos, (2, 1))

    def test_manual_grab_only_collects_real_gold(self):
        g = Game()
        # Bezpieczna droga do złota w AIMA: E, N, N.
        for action in ('forward', 'left', 'forward', 'forward', 'grab', 'grab'):
            g.act(action)
        self.assertEqual(g.world.gold_carried, 1)
        self.assertEqual(g.agent.gold_carried, 1)
        self.assertFalse(g.percept.glitter)
        self.assertEqual(g.world.score(), -6)  # punkty za złoto dopiero po wyjściu

    def test_agent_completes_aima_after_manual_actions(self):
        g = Game()
        for action in ('right', 'forward', 'left', 'grab'):
            g.act(action)
        for _ in range(150):
            if g.world.done:
                break
            g.act('agent')
            self.assertEqual(g.agent.pos, g.world.pos)
            self.assertEqual(g.agent.direction, g.world.direction)
        self.assertTrue(g.world.climbed)
        self.assertTrue(g.world.alive)
        self.assertEqual(g.world.gold_carried, 1)
        self.assertGreater(g.world.score(), 900)

    def test_counting_example_prefers_safer_route(self):
        outcomes = {}
        for strategy in ('risky', 'counting'):
            g = Game('counting', strategy)
            for _ in range(150):
                if g.world.done:
                    break
                g.act('agent')
            outcomes[strategy] = (g.world.alive, g.world.climbed, g.world.gold_carried)
        self.assertEqual(outcomes['risky'][0], False)
        self.assertEqual(outcomes['counting'], (True, True, 1))

    def test_random_seed_is_reproducible(self):
        self.assertEqual(Game('random', seed=42).world.config, Game('random', seed=42).world.config)


class HttpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = Server(('127.0.0.1', 0))
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f'http://127.0.0.1:{cls.server.server_port}'

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def post(self, path, payload, origin=None):
        headers = {'Content-Type': 'application/json'}
        if origin:
            headers['Origin'] = origin
        request = Request(self.base + path, json.dumps(payload).encode(), headers)
        with urlopen(request, timeout=10) as response:
            return json.load(response)

    def test_static_and_game_endpoints(self):
        for path, mime in (('/', 'text/html'), ('/app.js', 'text/javascript'), ('/style.css', 'text/css')):
            with urlopen(self.base + path, timeout=10) as response:
                self.assertEqual(response.status, 200)
                self.assertEqual(response.headers.get_content_type(), mime)
                self.assertGreater(len(response.read()), 100)
        self.post('/api/new', {'scenario': 'aima', 'strategy': 'safe'})
        state = self.post('/api/action', {'action': 'forward'}, self.base)
        self.assertEqual(state['pos'], [2, 1])
        self.assertEqual(self.post('/api/undo', {})['pos'], [1, 1])

    def test_rejects_invalid_action_and_foreign_origin(self):
        with self.assertRaises(HTTPError) as error:
            self.post('/api/action', {'action': 'teleport'})
        self.assertEqual(error.exception.code, 400)
        with self.assertRaises(HTTPError) as error:
            self.post('/api/action', {'action': 'forward'}, 'https://example.org')
        self.assertEqual(error.exception.code, 403)


if __name__ == '__main__':
    unittest.main()
