import json
import sqlite3
from datetime import datetime, timedelta
from dateutil import parser
from helpers.gmail_helper import GmailHelper

class RuleProcessor:
    """This class handles everything related to rules and their processing."""
    def __init__(self, service):
        """Initializes RuleProcessor object and loads all rules."""
        self.gmail_service = service
        self.rules = self.__load_rules()

    def apply_rules(self, email):
        """Applies all eligible rules to the specified email."""
        for rule in self.rules:
            if self.__evaluate_rule(email, rule):
                self.__execute_rule_actions(email, rule['actions'])
        

    def __load_rules(self):
        """Load rules from the JSON file."""
        with open('rules.json', 'r') as file:
            rules = json.load(file)
        return rules

        
    def __evaluate_rule(self, email, rule):
        """Checks if the specified rule is applicable on the specified email or not."""
        match_count = 0
        for condition in rule['conditions']:
            field, predicate, value = condition['field'], condition['predicate'], condition['value']
            email_value = email[self.__convert_field_to_index(field)]

            if field == 'date_received':
                if self.__evaluate_date_predicate(email_value, predicate, value):
                    match_count += 1
            else:
                if self.__evaluate_string_predicate(email_value, predicate, value):
                    match_count += 1

        return match_count == len(rule['conditions']) if rule['predicate'] == 'All' else match_count > 0

    def __convert_field_to_index(self, field):
        """Convert field name to corresponding email table index."""
        fields = {'id': 0, 'from_email': 1, 'to_email': 2, 'subject': 3, 'date_received': 4}
        return fields[field]

    def __evaluate_string_predicate(self, email_value, predicate, target):
        """Evaluate predicates for string type fields."""
        if predicate == "contains":
            return target in email_value
        elif predicate == "does_not_contains":
            return target not in email_value
        elif predicate == "equals":
            return target == email_value
        elif predicate == "does_not_equals":
            return target != email_value
        else:
            raise ValueError(f"{predicate} - Invalid predicate for string type field")


    def __evaluate_date_predicate(self, email_date_str, predicate, target):
        """Evaluate predicates for date type fields."""
        # Convert email date string to datetime object
        email_date = parser.parse(email_date_str, ignoretz=True)
        current_date = datetime.now(email_date.tzinfo)  # Ensure same timezone

        days = None
        if 'days' in target:
            days = int(target.split()[0])
        elif 'months' in target:
            days = int(target.split()[0])* 30 # Roughly taking one month = 30 days
        else:
            raise ValueError(f"{target} - Invalid time unit in predicate value. Use 'days' or 'months'.")
            
            
        if predicate == 'less_than':
            target_date = current_date - timedelta(days=days)
            return email_date > target_date
        elif predicate == 'greater_than':
            target_date = current_date - timedelta(days=days)
            return email_date < target_date
        else:
            raise ValueError(f"{predicate} - Invalid predicate for date type field.")
            

    def __execute_rule_actions(self, email, actions):
        """Applies all the specified actions on the specified email."""
        for action in actions:
            if action == 'mark_as_unread':
                self.__add_label(email, 'UNREAD')
            elif action == 'mark_as_read':
                self.__remove_label(email, 'UNREAD')
            elif action == 'move_to_starred':
                self.__add_label(email, 'STARRED')
            elif action == 'move_to_important':
                self.__add_label(email, 'IMPORTANT')
            elif action == 'move_to_spam':
                self.__add_label(email, 'SPAM')
            elif action == 'move_to_category_social':
                self.__add_label(email, 'CATEGORY_SOCIAL')
            elif action == 'move_to_inbox':
                self.__add_label(email, 'INBOX')
            else:
                raise ValueError(f"{action} - Invalid rule action.")

    def __add_label(self, email, label):
        """Adds label to email if not already present."""
        label_ids = self.gmail_service.users().messages().get(userId='me', id=email[0]).execute()['labelIds']
        if label not in label_ids:
            self.gmail_service.users().messages().modify(userId='me',id=email[0],body={'addLabelIds': [label]}).execute()

    def __remove_label(self, email, label):
        """Removes label from email if present."""
        label_ids = self.gmail_service.users().messages().get(userId='me', id=email[0]).execute()['labelIds']
        if label in label_ids:
            self.gmail_service.users().messages().modify(userId='me',id=email[0],body={'removeLabelIds': [label]}).execute()


class EmailProcessor:
    """This class handles everything related to emails and their processing."""
    def __init__(self, rule_processor):
        """Initializes EmailProcessor object loads all emails."""
        self.rule_processor = rule_processor
        self.emails = self.__fetch_emails()

    def process_emails(self):
        """Processes each email and sends them to rule_processor"""
        print("===== Processing Emails")
        counter = 0
        for email in self.emails:
            counter += 1
            print(f"===== Processing email {counter}/{len(self.emails)}. Applying rules....")
            self.rule_processor.apply_rules(email)
        
        print("===== All Emails Processed")

    def __fetch_emails(self):
        """Fetches emails from database"""
        print("===== Fetching Emails from database")
        conn = sqlite3.connect('email_database.db')
        c = conn.cursor()
        c.execute('SELECT * FROM emails')
        emails = c.fetchall()
        conn.commit()
        conn.close()
        return emails


if __name__ == '__main__':
    print("!!!!! SCRIPT STARTED - process_emails.py")
    gmail_helper_instance = GmailHelper()
    service = gmail_helper_instance.authenticate_gmail()
    
    rule_processor = RuleProcessor(service)
    email_processor = EmailProcessor(rule_processor)
    email_processor.process_emails()
    print("!!!!! SCRIPT COMPLETED - process_emails.py")
    
    
    
