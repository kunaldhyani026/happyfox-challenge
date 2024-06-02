import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
from process_emails import RuleProcessor, EmailProcessor

class TestRuleProcessor(unittest.TestCase):
    def setUp(self):
        # Mocking the Gmail service
        self.gmail_service = MagicMock()
        self.rule_processor = RuleProcessor(self.gmail_service)

    def test_convert_field_to_index(self):
        self.assertEqual(self.rule_processor._RuleProcessor__convert_field_to_index('id'), 0)
        self.assertEqual(self.rule_processor._RuleProcessor__convert_field_to_index('from_email'), 1)
        self.assertEqual(self.rule_processor._RuleProcessor__convert_field_to_index('to_email'), 2)
        self.assertEqual(self.rule_processor._RuleProcessor__convert_field_to_index('subject'), 3)
        self.assertEqual(self.rule_processor._RuleProcessor__convert_field_to_index('date_received'), 4)

    def test_evaluate_string_predicate_contains(self):
        self.assertTrue(self.rule_processor._RuleProcessor__evaluate_string_predicate("Hello World", "contains", "World"))
        self.assertFalse(self.rule_processor._RuleProcessor__evaluate_string_predicate("Hello World", "contains", "Python"))

    def test_evaluate_string_predicate_does_not_contains(self):
        self.assertTrue(self.rule_processor._RuleProcessor__evaluate_string_predicate("Hello World", "does_not_contains", "Python"))
        self.assertFalse(self.rule_processor._RuleProcessor__evaluate_string_predicate("Hello World", "does_not_contains", "World"))

    def test_evaluate_string_predicate_equals(self):
        self.assertTrue(self.rule_processor._RuleProcessor__evaluate_string_predicate("Hello World", "equals", "Hello World"))
        self.assertFalse(self.rule_processor._RuleProcessor__evaluate_string_predicate("Hello World", "equals", "Hello"))

    def test_evaluate_string_predicate_does_not_equals(self):
        self.assertTrue(self.rule_processor._RuleProcessor__evaluate_string_predicate("Hello World", "does_not_equals", "Python"))
        self.assertFalse(self.rule_processor._RuleProcessor__evaluate_string_predicate("Hello World", "does_not_equals", "Hello World"))

    def test_evaluate_string_predicate_invalid(self):
        with self.assertRaises(ValueError):
            self.rule_processor._RuleProcessor__evaluate_string_predicate("Hello World", "invalid_predicate", "Python")

    def test_evaluate_date_predicate_less_than(self):
        email_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        self.assertTrue(self.rule_processor._RuleProcessor__evaluate_date_predicate(email_date, "less_than", "2 days"))
        self.assertFalse(self.rule_processor._RuleProcessor__evaluate_date_predicate(email_date, "less_than", "1 days"))

    def test_evaluate_date_predicate_greater_than(self):
        email_date = (datetime.now() + timedelta(days=60)).strftime("%Y-%m-%d")
        self.assertFalse(self.rule_processor._RuleProcessor__evaluate_date_predicate(email_date, "greater_than", "1 months"))

    def test_evaluate_date_predicate_invalid(self):
        with self.assertRaises(ValueError):
            self.rule_processor._RuleProcessor__evaluate_date_predicate("2024-06-01", "invalid_predicate", "2 days")

    def test_evaluate_rule_all_predicate(self):
        # Mock email object
        email = [
            1,
            'example@example.com',
            'test@test.com',
            'Test Subject',
            (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
            ]
        # Rule with 'All' predicate
        rule = {
            'predicate': 'All',
            'conditions': [
                {'field': 'from_email', 'predicate': 'equals', 'value': 'example@example.com'},
                {'field': 'subject', 'predicate': 'contains', 'value': 'Test'}
            ]
        }
        self.assertTrue(self.rule_processor._RuleProcessor__evaluate_rule(email, rule))

    def test_evaluate_rule_any_predicate(self):
        # Mock email object
        email = [
            1,
            'example@example.com',
            'test@test.com',
            'Test Subject',
            (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        ]
        # Rule with 'Any' predicate
        rule = {
            'predicate': 'Any',
            'conditions': [
                {'field': 'from_email', 'predicate': 'equals', 'value': 'another@example.com'},
                {'field': 'subject', 'predicate': 'contains', 'value': 'Test'}
            ]
        }
        self.assertTrue(self.rule_processor._RuleProcessor__evaluate_rule(email, rule))

    def test_load_rules(self):
        # Mocking the rules data
        mock_rules_data = [
            {
                'predicate': 'All',
                'conditions': [
                    {'field': 'from_email', 'predicate': 'equals', 'value': 'example@example.com'},
                    {'field': 'subject', 'predicate': 'contains', 'value': 'Test'}
                ],
                'actions': ['mark_as_read', 'move_to_inbox']
            }
        ]

        with patch('builtins.open', unittest.mock.mock_open(read_data='[{"predicate": "All", "conditions": [{"field": "from_email", "predicate": "equals", "value": "example@example.com"}, {"field": "subject", "predicate": "contains", "value": "Test"}], "actions": ["mark_as_read", "move_to_inbox"]}]')):
            rules = self.rule_processor._RuleProcessor__load_rules()

        self.assertEqual(rules, mock_rules_data)

    def test_execute_rule_actions(self):
        self.gmail_service.users().messages().get().execute.return_value = {'labelIds': ['SPAM', 'UNREAD']}
        # Mocking the Gmail service's modify method
        self.gmail_service.users().messages().modify().execute.return_value = {}

        email = [
            1,
            'example@example.com',
            'test@test.com',
            'Test Subject',
            (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        ]
        actions = ['mark_as_read', 'move_to_inbox']
        self.rule_processor._RuleProcessor__execute_rule_actions(email, actions)

        # Assert that modify method is called twice (for mark_as_read and move_to_inbox)
        self.assertEqual(self.gmail_service.users().messages().modify().execute.call_count, 2)

    
    def test_add_label(self):
        # Mocking the labelIds response
        self.gmail_service.users().messages().get().execute.return_value = {'labelIds': ['INBOX', 'UNREAD']}

        email = [
            1,
            'example@example.com',
            'test@test.com',
            'Test Subject',
            (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        ]
        label = 'STARRED'
        self.rule_processor._RuleProcessor__add_label(email, label)

        # Assert that modify method is called once with the expected label
        self.gmail_service.users().messages().modify.assert_called_once_with(userId='me', id=1, body={'addLabelIds': ['STARRED']})

    def test_remove_label(self):
        # Mocking the labelIds response
        self.gmail_service.users().messages().get().execute.return_value = {'labelIds': ['INBOX', 'UNREAD', 'STARRED']}

        email = [
            1,
            'example@example.com',
            'test@test.com',
            'Test Subject',
            (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        ]
        label = 'UNREAD'
        self.rule_processor._RuleProcessor__remove_label(email, label)

        # Assert that modify method is called once with the expected label
        self.gmail_service.users().messages().modify.assert_called_once_with(userId='me', id=1, body={'removeLabelIds': ['UNREAD']})
    
class TestEmailProcessor(unittest.TestCase):
    def setUp(self):
        # Mocking the RuleProcessor
        self.rule_processor = MagicMock()
        self.email_processor = EmailProcessor(self.rule_processor)

    def test_fetch_emails(self):
        # Mocking the database cursor and execute method
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [(1, 'example@example.com', 'example@example.com', 'Test Email', datetime.now().strftime("%Y-%m-%d"))]
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor

        with unittest.mock.patch('sqlite3.connect', return_value=mock_conn):
            emails = self.email_processor._EmailProcessor__fetch_emails()

        self.assertEqual(len(emails), 1)

    def test_process_emails(self):
        # Mocking the email list
        emails = [
            {
                'id': 1,
                'from_email': 'example@example.com',
                'to_email': 'test@test.com',
                'subject': 'Test Subject',
                'date_received': (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
            }
        ]
        self.email_processor.emails = emails
        self.email_processor.process_emails()
        # Assert that apply_rules method of RuleProcessor is called with the email
        self.rule_processor.apply_rules.assert_called_once_with(emails[0])


if __name__ == '__main__':
    unittest.main()
