DEFAULT_HULL = {
    'hash': '4a28968dc2cdcdcc4d02d891fb98b11755ee6bf027d49bb5f6c0ab249a37ab68',
    'fleet': None,
    'mass_limit': 5000
}

DEFAULT_CARGO = {
    'hash': '6b6b84a56c470a6bf598e661ac81f106b509c52e73715529311536014fbe45cf',
    'fleet': None,
    'health_limit': 10,
    'mass': 25,
    'mass_limit': 1000
}

DEFAULT_JUMP_DRIVE = {
    'hash': '75e23c09fc113178bddb3eb695a7ade5fab6d7246c5aea71138cdd15472273a1',
    'fleet': None,
    'health_limit': 10,
    'mass': 25,
    'distance_scalar': 1.0,
    'fuel_scalar': 1.0,
    'mass_limit': 5000
}

DEFAULT_VESSEL = {
    'blueprint': DEFAULT_HULL['hash'],
    'modules': [
        {
            'index': 0,
            'module_type': 'jump_drive',
            'blueprint': DEFAULT_JUMP_DRIVE['hash'],
            'delta': False,
            'health': DEFAULT_JUMP_DRIVE['health_limit'],
        },
        {
            'index': 1,
            'module_type': 'cargo',
            'blueprint': DEFAULT_CARGO['hash'],
            'delta': False,
            'health': DEFAULT_CARGO['health_limit'],
            'contents': {
                'fuel': DEFAULT_CARGO['mass_limit']
            }
        }
    ]
}