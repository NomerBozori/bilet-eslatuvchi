import os
import tempfile
import unittest
from unittest.mock import patch
import bot


class BotTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.old_db = bot.DB_PATH
        bot.DB_PATH = os.path.join(self.tmp.name, 'test.db')
        bot.init_db()
        self.messages = []
        self.mock_send = patch.object(bot, 'send', side_effect=lambda chat, text: self.messages.append((chat, text)))
        self.mock_send.start()

    def tearDown(self):
        self.mock_send.stop()
        bot.DB_PATH = self.old_db
        self.tmp.cleanup()

    def message(self, text, chat=1):
        bot.handle_message({'chat': {'id': chat, 'type': 'private'}, 'text': text})

    def test_intervals(self):
        self.assertEqual(bot.parse_interval(' 2 SOAT '), 7200)
        self.assertEqual(bot.parse_interval('1 hafta'), 604800)
        for value in ('0 daqiqa', '366 kun', '1 soniya', 'abc'):
            self.assertIsNone(bot.parse_interval(value))

    def test_create_and_delete_own_only(self):
        self.message('Bilet olish')
        self.message('notoʻgʻri')
        with bot.connect() as db:
            self.assertEqual(db.execute('SELECT count(*) FROM reminders').fetchone()[0], 0)
        self.message('2 soat')
        self.message('/delete 1', chat=2)
        with bot.connect() as db:
            self.assertEqual(db.execute('SELECT text, interval_seconds FROM reminders').fetchone(), ('Bilet olish', 7200))
        self.message('/list')
        self.assertTrue(any('Bilet olish' in text for _, text in self.messages))
        self.message('/delete 1')
        with bot.connect() as db:
            self.assertEqual(db.execute('SELECT count(*) FROM reminders').fetchone()[0], 0)

    def test_cancel_and_group(self):
        self.message('Matn')
        self.message('/cancel')
        bot.handle_message({'chat': {'id': -1, 'type': 'group'}, 'text': 'ignored'})
        with bot.connect() as db:
            self.assertEqual(db.execute('SELECT count(*) FROM conversations').fetchone()[0], 0)


if __name__ == '__main__':
    unittest.main()
