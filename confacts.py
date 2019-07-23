import boto3
import os
import sys
import tempfile
from subprocess import call
from boto3.dynamodb.conditions import Key

class ConfactsApi:
    def __init__(self):
        self.table = boto3.resource('dynamodb').Table('confacts')

    def get_all_confact_names(self):
        response = self.table.scan(
            ProjectionExpression='#n',
            ExpressionAttributeNames={ '#n': 'name' }
        )
        return [item['name'] for item in response['Items']]

    def get_confact(self, name):
        response = self.table.get_item(
            Key={
                'name': name
            }
        )
        return response['Item']['info']

    def query_confact(self, name):
        response = self.table.query(
            KeyConditionExpression=Key('name').eq(name)
        )
        return response['Items']

    def create_new_confact(self, name):
        response = self.table.put_item(
            Item={
                'name': name,
            }
        )
        # print(response)

    def update_confact(self, name, text):
        response = self.table.update_item(
            Key={
                'name': name
            },
            UpdateExpression='set info = :i',
            ExpressionAttributeValues={
                ':i': text
            },
            ReturnValues='UPDATED_NEW'
        )
        # print(response)

    def delete_confact(self, name):
        pass

class ConfactsMenu:
    def __init__(self):
        self.client = ConfactsApi()
        self.current_state = 'main'
        self.states = {
            'main': self.main_menu,
            'get_all': self.get_all_menu,
            'view_contact': self.selected_contact_menu,
            'modify_contact': self.modify_contact_menu,
            'query_contact': self.query_contact_menu,
            'create_contact': self.create_contact_menu,
        }
        self.selected_contact = ''

    def update_current_state(self, new_state):
        self.current_state = new_state

    def main_menu(self):
        print('\n-- Confacts Main Menu --')
        print('0. Get list of contacts')
        print('1. Query a specific contact')
        print('2. Create a new contact')

        choice = input('\nSelect a choice (e.g. 1, 2, 3) or press Enter to quit --> ')
        if len(choice) == 0:
            self.update_current_state('quit')
        else:
            choice = int(choice)
            if choice == 0:
                self.update_current_state('get_all')
            elif choice == 1:
                self.update_current_state('query_contact')
            elif choice == 2:
                self.update_current_state('create_contact')
            else:
                print('\nError: invalid choice specified, please try again')

    def get_all_menu(self):
        print('\n-- Your contacts --')
        contact_names = self.client.get_all_confact_names()
        if len(contact_names) == 0:
            print('Nothing to see here!')
            input('\nPress Enter to go back to the main menu --> ')
            self.update_current_state('main')
            return
        for idx, name in enumerate(contact_names):
            print(f'{idx}. {name}')
        choice = input('\nSelect a contact to view or press Enter to return to the main menu --> ')
        if len(choice) == 0:
            self.update_current_state('main')
        else:
            choice = int(choice)
            if 0 <= choice < len(contact_names):
                self.update_current_state('view_contact')
                self.selected_contact = contact_names[choice]
            else:
                print('\nError: invalid choice specified, please try again')

    def selected_contact_menu(self):
        print(f'\n-- Confact for {self.selected_contact} --')
        contact_info = self.client.get_confact(self.selected_contact)
        print(contact_info, end='')
        print('-- End Confact --')
        choice = input('\nWould you like to modify this confact? (y/n) --> ')
        if len(choice) > 0 and choice == 'y':
            self.update_current_state('modify_contact')
            self.contact_info = contact_info
        else:
            self.update_current_state('main')

    def modify_contact_menu(self):
        EDITOR = os.environ.get('EDITOR','vim')
        with tempfile.NamedTemporaryFile(suffix='.tmp') as tf:
            tf.write(self.contact_info.encode())
            tf.flush()
            call([EDITOR, tf.name])

            tf.seek(0)
            contact_info_binary = tf.read()
            self.contact_info = contact_info_binary.decode()

        print('\n-- Begin Contact Info --')
        print(self.contact_info, end='')
        print('-- End Contact Info --')
        choice = input('\nCommit changes? (y/n) --> ')
        if len(choice) > 0 and choice == 'y':
            self.client.update_confact(self.selected_contact, self.contact_info)
        self.update_current_state('view_contact')

    def query_contact_menu(self):
        print(f'\n-- Query a Contact --')
        name_query = input('\nPlease enter the name of the contact you\'d like to query --> ')
        if len(self.client.query_confact(name_query)) > 0:
            self.selected_contact = name_query
            self.update_current_state('view_contact')
        else:
            print('No contact was found with that name. Returning to main menu.')
            self.update_current_state('main')

    def create_contact_menu(self):
        print(f'\n-- Create a Contact --')
        name = input('\nContact name --> ')

        self.selected_contact = name
        self.contact_info = ''

        self.client.create_new_confact(name)
        self.update_current_state('modify_contact')

    def delete_contact_menu(self):
        pass

    def run(self):
        while self.current_state != 'quit':
            self.states[self.current_state]()
        print('Bye!')

if __name__ == '__main__':
    confacts = ConfactsMenu()
    confacts.run()

