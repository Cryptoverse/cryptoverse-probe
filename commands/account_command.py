from commands.base_command import BaseCommand
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from models.account_model import AccountModel

class AccountCommand(BaseCommand):

    COMMAND_NAME = 'account'

    def __init__(self, app):
        super(AccountCommand, self).__init__(
            app, 
            self.COMMAND_NAME,
            description = 'Information about local accounts',
            parameter_usages = [
                'None: Retrieve the currently active account',
                '"-l" list all accounts stored in persistent data',
                '"-s <account name>" sets the specified account as acitve',
                '"-c <account name>" creates an account with the specified name'
            ],
            command_handlers = [
                self.get_handler(None, self.on_current_account),
                self.get_handler('-l', self.on_list_accounts),
                self.get_handler('-s', self.on_set_account_active, 1),
                self.get_handler('-c', self.on_create_account, 1)
            ]
        )

    # Events

    def on_current_account(self):
        self.app.database.find_account_active(self.on_find_current_account)

    def on_find_current_account(self, result):
        if result.is_error:
            self.app.callbacks.on_error(result.content)
            return
        account = result.content
        message = 'Using account "%s"\n' % account.name
        message += '\tFleet Hash: %s' % account.get_fleet_name()
        self.app.callbacks.on_output(message)

    def on_list_accounts(self):
        def on_read_all(read_all_result):
            if read_all_result.is_error:
                self.app.callbacks.on_error('Error reading accounts: %s' % read_all_result.content)
            elif read_all_result.content is None or len(read_all_result.content) == 0:
                self.app.callbacks.on_error('No accounts to list')
            else:
                message = 'All Accounts\n'
                for account in read_all_result.content:
                    current_entry = '%s\t - %s\n' % ('[CURR]' if account.active else '', account.name)
                    current_entry += '\t\tFleet Hash: %s\n' % account.get_fleet_name()
                    message += current_entry
                self.app.callbacks.on_output(message)

        self.app.database.account.read_all(None, on_read_all)

    def on_set_account_active(self, name):
        def on_find(find_result):
            if find_result.is_error:
                self.app.callbacks.on_error('Unable to find account "%s"' % name)
            else:
                model = find_result.content
                model.active = True

                def on_write(write_result):
                    if write_result.is_error:
                        self.app.callbacks.on_error('Error writing account: %s' % write_result.content)
                    else:
                        self.app.callbacks.on_output('Account "%s" is now active' % name)

                self.app.database.account.write(model, on_write)

        self.app.database.account.find_account(name, on_find)

    def on_create_account(self, name):
        def on_check_name(name_result):
            if name_result.is_error:
                private_key = rsa.generate_private_key(
                    public_exponent=65537,
                    key_size=2048,
                    backend=default_backend()
                )
                private_serialized = private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption()
                )
                public_serialized = private_key.public_key().public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo
                )

                model = AccountModel()
                model.active = True
                model.name = name
                model.private_key = private_serialized
                model.public_key = public_serialized

                def on_write(write_result):
                    if write_result.is_error:
                        self.app.callbacks.on_error('Error writing account: %s' % write_result.content)
                    else:
                        self.app.callbacks.on_output('Succesfully created account "%s"' % name)

                self.app.database.account.write(model, on_write)
            else:
                self.app.callbacks.on_error('An account with the name "%s" already exists' % name)

        self.app.database.account.find_account(name, on_check_name)
