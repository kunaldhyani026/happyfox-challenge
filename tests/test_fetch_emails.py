import unittest
from unittest.mock import patch
import sqlite3
from fetch_emails import fetch_emails, save_emails
from helpers.gmail_helper import GmailHelper

class TestFetchEmailsScript(unittest.TestCase):
    
    @patch('fetch_emails.GmailHelper')
    def test_fetch_emails(self, MockGmailHelper):
        mock_service = MockGmailHelper().authenticate_gmail()
        mock_service.users().messages().list().execute.return_value = {
            'messages': [{'id': '1'}, {'id': '2'}, {'id': '3'}]
        }

        folder = 'INBOX'
        messages = fetch_emails(mock_service, folder)
        self.assertEqual(len(messages), 3)
        self.assertEqual(messages, [{'id': '1'}, {'id': '2'}, {'id': '3'}])

    @patch('fetch_emails.GmailHelper')
    @patch('sqlite3.connect')
    def test_save_emails(self, mock_sqlite_connect, MockGmailHelper):
        mock_service = MockGmailHelper().authenticate_gmail()
        mock_service.users().messages().get().execute.side_effect = [
            {
                'id': '1',
                'payload': {
                    'headers': [
                        {'name': 'From', 'value': 'alice@example.com'},
                        {'name': 'To', 'value': 'bob@example.com'},
                        {'name': 'Subject', 'value': 'Hello'},
                        {'name': 'Date', 'value': 'Sat, 01 Jun 2024 11:10:09 GMT'}
                    ]
                }
            },
            {
                'id': '2',
                'payload': {
                    'headers': [
                        {'name': 'From', 'value': 'charlie@example.com'},
                        {'name': 'To', 'value': 'dave@example.com'},
                        {'name': 'Subject', 'value': 'Hi'},
                        {'name': 'Date', 'value': 'Sun, 02 Jun 2024 12:20:19 GMT'}
                    ]
                }
            }
        ]

        mock_conn = mock_sqlite_connect.return_value
        mock_cursor = mock_conn.cursor.return_value

        messages = [{'id': '1'}, {'id': '2'}]
        save_emails(mock_service, messages)

        mock_cursor.execute.assert_any_call(
            '''CREATE TABLE IF NOT EXISTS emails
                 (id TEXT PRIMARY KEY, from_email TEXT, to_email TEXT, subject TEXT, date_received TEXT)''')

        mock_cursor.execute.assert_any_call(
            'INSERT OR IGNORE INTO emails (id, from_email, to_email, subject, date_received) VALUES (?, ?, ?, ?, ?)',
            ('1', 'alice@example.com', 'bob@example.com', 'Hello', 'Sat, 01 Jun 2024 11:10:09 GMT'))

        mock_cursor.execute.assert_any_call(
            'INSERT OR IGNORE INTO emails (id, from_email, to_email, subject, date_received) VALUES (?, ?, ?, ?, ?)',
            ('2', 'charlie@example.com', 'dave@example.com', 'Hi', 'Sun, 02 Jun 2024 12:20:19 GMT'))

        mock_conn.commit.assert_called_once()
        mock_conn.close.assert_called_once()

if __name__ == '__main__':
    unittest.main()
