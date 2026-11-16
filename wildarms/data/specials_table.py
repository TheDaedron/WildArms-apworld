"""
Wild Arms special-move ID <-> name tables: Rudy's ARMs, Jack's Fast Draws, Cecilia's Magic Spells, and the Force
abilities. Each table's ID is 0-indexed and matches the game's slot-array ordering.
Writing ID N into an empty slot grants the special at that ID.
"""
from typing import Dict, Tuple

ARM_ID_TO_NAME: Dict[int, str] = {
    0: 'Hand Cann.',
    1: 'Prism Ray',
    2: 'Rocket L.',
    3: 'Twin Orbs',
    4: 'Bazooka',
    5: 'Phaser',
    6: 'Wild Bunch',
    7: 'Arch Smash',
}
ARM_NAME_TO_ID: Dict[str, int] = {name: id_ for id_, name in ARM_ID_TO_NAME.items()}

# id -> (hit_rate, capacity, atf), read directly from the on-disc ARM stat table.
ARM_STATS: Dict[int, Tuple[int, int, int]] = {
    0: (85, 8, 10),    # Hand Cannon
    1: (80, 8, 10),    # Prism Ray
    2: (75, 5, 30),    # Rocket Launcher
    3: (75, 5, 25),    # Twin Orbs
    4: (70, 5, 45),    # Bazooka
    5: (85, 8, 70),    # Phaser
    6: (45, 3, 100),   # Wild Bunch
    7: (70, 3, 200),   # Arch Smasher
}


FASTDRAW_ID_TO_NAME: Dict[int, str] = {
    0: 'Psycho Crack',
    1: 'Sonic Buster',
    2: 'Meteor Dive',
    3: 'Trickster',
    4: 'Heal Blade',
    5: 'Divide Shot',
    6: 'Blast Charge',
    7: 'Slash Rave',
    8: 'Soul Breaker',
    9: 'Guilty Blade',
    10: 'Magnum Fang',
    11: 'Shadow Bind',
    12: 'Phazer Zapp',
    13: 'Cosmic Nova',
    14: 'Void',
    15: 'Trump Card',
}
FASTDRAW_NAME_TO_ID: Dict[str, int] = {name: id_ for id_, name in FASTDRAW_ID_TO_NAME.items()}

# id -> MP cost, read directly from the on-disc Fast Draw stat table.
FASTDRAW_MP_COST: Dict[int, int] = {
    0: 4,    # Psycho Crack
    1: 7,    # Sonic Buster
    2: 6,    # Meteor Dive
    3: 5,    # Trickster
    4: 6,    # Heal Blade
    5: 10,   # Divide Shot
    6: 10,   # Blast Charge
    7: 12,   # Slash Rave
    8: 8,    # Soul Breaker
    9: 16,   # Guilty Blade
    10: 14,  # Magnum Fang
    11: 7,   # Shadow Bind
    12: 16,  # Phazer Zapp
    13: 20,  # Cosmic Nova
    14: 20,  # Void
    15: 22,  # Trump Card
}


MAGIC_ID_TO_NAME: Dict[int, str] = {
    0: 'Shield',
    1: 'Protect',
    2: 'Suction',
    3: 'Hide',
    4: 'Revive',
    5: 'Heal',
    6: 'Awaken',
    7: 'Field',
    8: 'Curse',
    9: 'Dark Blow',
    10: 'Light Blow',
    11: 'Rage',
    12: 'Reflect',
    13: 'Air Screen',
    14: 'Escape',
    15: 'Quick',
    16: 'Break',
    17: 'Arm. Down',
    18: 'Slow Down',
    19: 'Sleep',
    20: 'Analyze',
    21: 'Freeze',
    22: 'Dispell',
    23: 'Prison',
    24: 'Flash',
    25: 'Blast',
    26: 'Flame',
    27: 'Confusion',
    28: 'Valkyrie',
    29: 'Spark',
    30: 'Silence',
    31: 'Vortex',
    32: 'Hi-Shield',
    33: 'Life Guard',
    34: 'Hyper',
    35: 'Invisible',
    36: 'Hi-Revive',
    37: 'Hi-Heal',
    38: 'Remedy',
    39: 'Restore',
    40: 'Counter Up',
    41: 'Anti Magic',
    42: 'Bomb',
    43: 'Soul Guard',
    44: 'Hi-Reflect',
    45: 'Lock State',
    46: 'Dummy Doll',
    47: 'Teleport',
    48: 'Hi-Break',
    49: 'Saint',
    50: 'Eraser',
    51: 'Life Drain',
    52: 'Banish',
    53: 'Hi-Freeze',
    54: 'Randomizer',
    55: 'Hi-Prison',
    56: 'Rainbow',
    57: 'Hi-Blast',
    58: 'Hi-Flame',
    59: 'Darkness',
    60: 'MP Drain',
    61: 'Hi-Spark',
    62: 'Lucky Shot',
    63: 'Hi-Vortex',
}
MAGIC_NAME_TO_ID: Dict[str, int] = {name: id_ for id_, name in MAGIC_ID_TO_NAME.items()}


FORCE_ID_TO_NAME: Dict[int, str] = {
    0: 'ARM Lock On',
    1: 'Summon Guardian Rudy',
    2: 'Protector',
    3: 'Fury Shot',
    4: 'Accelerator',
    5: 'Summon Guardian Jack',
    6: 'Sonic Vision',
    7: 'Double Attack',
    8: 'Mystic',
    9: 'Summon Guardian Cecilia',
    10: 'High Guardian',
    11: 'Dual Cast',
}
FORCE_NAME_TO_ID: Dict[str, int] = {name: id_ for id_, name in FORCE_ID_TO_NAME.items()}
STARTING_FORCE_IDS = (0, 4, 8)
