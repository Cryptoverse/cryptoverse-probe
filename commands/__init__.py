from commands import (
    help_command,
    exit_command,
    info_command,
    account_command,
    meta_command,
    nodes_command,
    rules_command,
    probe_command,
    sync_command,
    blocks_command,
    fleets_command,
    galaxy_command
)

ALL_COMMANDS = [
    help_command.HelpCommand,
    exit_command.ExitCommand,
    info_command.InfoCommand,
    account_command.AccountCommand,
    meta_command.MetaCommand,
    nodes_command.NodesCommand,
    rules_command.RulesCommand,
    probe_command.ProbeCommand,
    sync_command.SyncCommand,
    blocks_command.BlocksCommand,
    fleets_command.FleetsCommand,
    galaxy_command.GalaxyCommand
]