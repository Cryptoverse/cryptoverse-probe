from commands import (
    help_command,
    exit_command,
    info_command,
    account_command,
    meta_command,
    node_command,
    rules_command
)

ALL_COMMANDS = [
    help_command.HelpCommand,
    exit_command.ExitCommand,
    info_command.InfoCommand,
    account_command.AccountCommand,
    meta_command.MetaCommand,
    node_command.NodeCommand,
    rules_command.RulesCommand
]