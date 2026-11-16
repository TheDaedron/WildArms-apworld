from dataclasses import dataclass

from Options import Toggle, DefaultOnToggle, Choice, Range, PerGameCommonOptions, OptionGroup


class DarkRoomTricks(Toggle):
    '''
    Game logic expects you to have the Lighter tool for exploring dark rooms.
    false indicates that the Lighter WILL be expected for dark rooms.
    true indicates that the Lighter WILL NOT be expected for dark rooms.
    '''
    display_name = "Dark Room Tricks"


class RiskyTreasures(Toggle):
    '''
    Game logic expects you to have a safe way to collect treasures without taking damage.
    false indicates that logic will not expect you to take damage to collect treasures.
    true indicates that logic might expect you to take damage to collect treasures.
    '''
    display_name = "Risky Treasures"


class OpenWorld(Toggle):
    '''
    Starts the game with Gullwing and Sweet Candy.
    Game logic is currently unmodified by this choice.
    This option has not been been throughly tested, please safe often.
    '''
    display_name = "Open World"


class PleasingGardenFixed(DefaultOnToggle):
    '''
    Pleasing Garden's location normally changes to a different spot in desert near Ship Graveyard as you walk around
    the world map, and you only know you've found it once the camera starts to zoom in.
    false keeps vanilla behavior.
    true sets the location permanently in a single place (south of the vendor cart).
    '''
    display_name = "Pleasing Garden Fixed"


class MasteredFastDraws(DefaultOnToggle):
    '''
    Changes the behavior of how Archipelago grants Jack's Fast Draw
    false indicates the player must master the Fast Draw by using it in combat
    true indicates a fully mastered Fast Draw upon it being granted
    '''
    display_name = "Mastered Fast Draws"


class ExpMultiplier(Range):
    '''
    Multiplier applied to every enemy's EXP reward.
    '''
    display_name = "EXP Multiplier"
    range_start = 1
    range_end = 20
    default = 5


class GellaMultiplier(Range):
    '''
    Multiplier applied to every enemy's Gella reward.
    '''
    display_name = "Gella Multiplier"
    range_start = 1
    range_end = 20
    default = 5


class BuffedApples(Range):
    '''
    How many points each Apple (Power, Hardy, Mystic and Agile) adds to its respective stat.
    '''
    display_name = "Buffed Apples"
    range_start = 1
    range_end = 9
    default = 5


class EnemyDifficulty(Range):
    '''
    Multiplier, as a percentage, of the stats of all enemies.
    '''
    display_name = "Enemy Difficulty"
    range_start = 50
    range_end = 500
    default = 100


class CameraView(Choice):
    '''
    The camera view the game starts with. This can be changed in the game's options menu.
    motion_view = Motion View
    quarter_view = Quarter View
    side_view = Side View
    front_view = Front View
    '''
    display_name = "Camera View"
    option_motion_view = 0
    option_quarter_view = 1
    option_side_view = 2
    option_front_view = 3
    default = 0


class Cursor(Choice):
    '''
    How the menu cursor behaves when a menu is reopened. This can be changed in the game's options menu.
    return = The cursor returns to the top
    memory = The cursor remembers its last position
    '''
    display_name = "Menu Cursor"
    option_return = 0
    option_memory = 1
    default = 0


class BattleCommand(Choice):
    '''
    How the battle command cursor behaves. This can be changed in the game's options menu.
    neutral = The battle command cursor will start in the "middle" position
    fixed   = The battle command cursor will stay in a fixed position
    '''
    display_name = "Battle Command"
    option_neutral = 0
    option_fixed = 1
    default = 0


@dataclass
class WildArmsOptions(PerGameCommonOptions):
    dark_room_tricks: DarkRoomTricks
    risky_treasures: RiskyTreasures
    open_world: OpenWorld
    exp_multiplier: ExpMultiplier
    gella_multiplier: GellaMultiplier
    buffed_apples: BuffedApples
    enemy_difficulty: EnemyDifficulty
    mastered_fast_draws: MasteredFastDraws
    pleasing_garden_fixed: PleasingGardenFixed
    camera_view: CameraView
    cursor: Cursor
    battle_command: BattleCommand


# Shown as collapsible sections on the WebHost's player-options page and in generated YAMLs
# (Options.OptionGroup, read via WildArmsWeb.option_groups in __init__.py). Every option must be
# listed in exactly one group here, or it defaults into an auto-added "Game Options" group instead.
wildarms_option_groups = [
    OptionGroup("Logic Modifiers", [
        OpenWorld,
        DarkRoomTricks,
        RiskyTreasures,
    ]),

    OptionGroup("Quality of Life", [
        PleasingGardenFixed,
        MasteredFastDraws,
    ]),

    OptionGroup("Game Balance", [
        ExpMultiplier,
        GellaMultiplier,
        BuffedApples,
        EnemyDifficulty,
    ]),

    OptionGroup("Convenience Settings", [
        CameraView,
        Cursor,
        BattleCommand,
    ]),
]
