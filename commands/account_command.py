from commands.base_command import BaseCommand
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from models.account_model import AccountModel

class AccountCommand(BaseCommand):

    def __init__(self, app):
        super(AccountCommand, self).__init__(
            app, 
            'account',
            description = 'Information about local accounts',
            parameter_usages = [
                'None: Retrieve the currently active account',
                '"-l" list all accounts stored in persistent data',
                '"-s <account name>" sets the specified account as acitve',
                '"-c <account name>" creates an account with the specified name'
            ]
        )

    def on_command(self, *args):
        parameter_count = len(args)
        if parameter_count == 0:
            self.on_current_account()
        elif args[0] == '-l':
            self.on_list_accounts()
        elif args[0] == '-s':
            if parameter_count == 2:
                self.on_set_account_active(args[1])
            else:
                raise ValueError('Invalid number of parameters for "-s"')
        elif args[0] == '-c':
            if parameter_count == 2:
                self.on_create_account(args[1])
            else:
                raise ValueError('Invalid number of parameters for "-c"')
        else:
            self.app.callbacks.on_error('Command "account" does not recognize parameter "%s"' % args[0])
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
        pass

    def on_set_account_active(self, name):
        pass

    # Create Account Begin

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
                # public_lines = public_serialized.splitlines()
                # public_shrunk = ''
                # for line in range(1, len(public_lines) - 1):
                #     public_shrunk += public_lines[line].strip('\n')
                
                model = AccountModel()
                model.active = True
                model.name = name
                model.private_key = private_serialized
                model.public_key = public_serialized

                def on_save(save_result):
                    if save_result.is_error:
                        self.app.callbacks.on_error('Error saving account: %s' % save_result.content)
                    else:
                        self.app.callbacks.on_output('Succesfully created account "%s"' % name)

                self.app.database.account.write(model, on_save)
            else:
                self.app.callbacks.on_error('An account with the name "%s" already exists' % name)
        
        self.app.database.account.find_account(name, on_check_name)



    # Create Account End