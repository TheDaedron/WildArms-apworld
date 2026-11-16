"""
Location access rules and the completion condition.
"""

from worlds.generic.Rules import set_rule
from typing import TYPE_CHECKING
from BaseClasses import CollectionState
from .Items import item_data

if TYPE_CHECKING:
    from . import WildArmsWorld

def set_rules(world: "WildArmsWorld") -> None:
    player = world.player
    multiworld = world.multiworld

    # --- Story flags ---
    set_rule(
        multiworld.get_location("defeated_zombie", player),
        lambda state: state.has("Holy Berry", player),
    )
    # 'defeated_nelgaul' has no rule: placed directly in region 'sealed_library'.
    set_rule(
        multiworld.get_location("defeated_magtortous", player),
        lambda state: state.has("Tear", player),
    )
    # 'defeated_belselk_1' has no rule: placed directly in region 'adlehyde_village'.
    # 'defeated_orga_widow' has no rule: placed directly in region 'mount_zenom_inner'.
    # 'defeated_night_gaunt' has no rule: placed directly in region 'cage_tower'.
    # 'defeated_chaos' has no rule: placed directly in region 'maze_of_death'.
    # 'defeated_zed_1' has no rule: placed directly in region 'sweet_candy'.
    set_rule(
        multiworld.get_location("defeated_gigamantis", player),
        lambda state: state.has("Bombs", player),
    )
    # 'defeated_captain_geist' has no rule: placed directly in region 'ghost_ship_inner'.
    # 'defeated_mage_fox' has no rule: placed directly in region 'tripillar'.
    # 'defeated_zed_2' has no rule: placed directly in region 'volcannon_trap'.
    # 'defeated_belselk_2' has no rule: placed directly in region 'volcannon_trap'.
    # 'defeated_boomerang_1' has no rule: placed directly in region 'epitaph_sea'.
    # 'defeated_agaless' has no rule: placed directly in region 'sacred_shrine'.
    # 'defeated_alhazad_1' has no rule: placed directly in region 'sacred_shrine'.
    # 'defeated_lolithia' has no rule: placed directly in region 'photosphere'.
    set_rule(
        multiworld.get_location("defeated_mother", player),
        lambda state: state.has("defeated_lolithia", player),
    )
    # 'defeated_harken_1' has no rule: placed directly in region 'dragon_shrine'.
    # 'defeated_harken_2' has no rule: placed directly in region 'demons_lab'.
    # 'defeated_boomerang_2' has no rule: placed directly in region 'dead_sanctuary'.
    # 'defeated_diablo' has no rule: placed directly in region 'gate_generator'.
    # 'defeated_zeikfried_1' has no rule: placed directly in region 'gate_generator'.
    # 'defeated_elizabeth' has no rule: placed directly in region 'de_le_metalica'.
    # 'defeated_mech_drake' has no rule: placed directly in region 'geminis_corpse'.
    # 'defeated_turask' has no rule: placed directly in region 'pandemonium'.
    # 'defeated_demon_prophet' has no rule: placed directly in region 'pandemonium'.
    # 'defeated_shazam' has no rule: placed directly in region 'pandemonium'.
    # 'defeated_harken_3' has no rule: placed directly in region 'arctica_castle'.
    # 'defeated_boomerang_3' has no rule: placed directly in region 'ka_dingel'.
    # 'defeated_alhazad_2' has no rule: placed directly in region 'ka_dingel'.
    # 'defeated_lucifer' has no rule: placed directly in region 'malduke'.
    # 'defeated_sado' has no rule: placed directly in region 'malduke'.
    # 'defeated_berial' has no rule: placed directly in region 'malduke'.
    # 'defeated_zeikfried_2' has no rule: placed directly in region 'malduke'.
    # 'defeated_motherfried' has no rule: placed directly in region 'malduke'.
    # 'defeated_zeik_tuvai' has no rule: placed directly in region 'malduke'.
    # 'defeated_medea' has no rule: placed directly in region 'ancient_arena'.
    # 'defeated_badnews' has no rule: placed directly in region 'ancient_arena'.
    # 'defeated_javawalk' has no rule: placed directly in region 'ancient_arena'.
    # 'defeated_riversider' has no rule: placed directly in region 'ancient_arena'.
    # 'defeated_angol_moa' has no rule: placed directly in region 'ancient_arena_angel_moa'.
    # 'defeated_barbados' has no rule: placed directly in region 'unreachable'.
    # 'defeated_boomerang_flash' has no rule: placed directly in region 'ancient_arena'.
    # 'defeated_leviathan' has no rule: placed directly in region 'unreachable'.
    # 'defeated_monster_zed' has no rule: placed directly in region 'unreachable'.
    # 'defeated_ragu_ragula' has no rule: placed directly in region 'the_abyss'.
    set_rule(
        multiworld.get_location("can_use_elw_pyramids", player),
        lambda state: state.has("Kizim Fire", player),
    )
    # 'can_sail_inner_sea' has no rule: placed directly in region 'ghost_ship_inner'.
    # 'can_use_earth_golem' has no rule: placed directly in region 'giants_cradle'.
    # 'can_sail_outer_sea' has no rule: placed directly in region 'dragon_shrine'.
    set_rule(
        multiworld.get_location("can_use_protowing", player),
        lambda state: (state.has("Gemini Circ. #1", player) and state.has("Gemini Circ. #2", player)),
    )
    set_rule(
        multiworld.get_location("can_use_gullwing", player),
        lambda state: state.has("Metal Bird", player),
    )

    # --- Location rules ---
    # Adlehyde
    set_rule(multiworld.get_location("[Adlehyde] Big Box - Left Storage, Left", player), lambda state: state.has("Bombs", player))
    set_rule(multiworld.get_location("[Adlehyde] Big Box - Left Storage, Right", player), lambda state: state.has("Bombs", player))
    set_rule(multiworld.get_location("[Adlehyde] Big Box - West of Chapel", player), lambda state: state.has("Bombs", player))
    set_rule(multiworld.get_location("[Adlehyde] Rune - Castle Rune", player), lambda state: state.has("Secret Tool", player))
    # Baskar Village
    set_rule(multiworld.get_location("[Baskar Village] NPC - Chief Gift", player), lambda state: state.has("defeated_orga_widow", player))
    set_rule(multiworld.get_location("[Baskar Village] Rune - Hope Rune", player), lambda state: state.has("Dragon Idol", player))
    # Berry Cave
    set_rule(multiworld.get_location("[Berry Cave] Big Box - Near Entrance", player), lambda state: state.has("Bombs", player))
    set_rule(multiworld.get_location("[Berry Cave] Big Box - Before Bomb Wall", player), lambda state: state.has("Bombs", player))
    set_rule(multiworld.get_location("[Berry Cave] Big Box - After Bomb Wall, West", player), lambda state: state.has("Bombs", player))
    # Curan Abbey
    set_rule(multiworld.get_location("[Curan Abbey] Pickup - Pocket Watch", player), lambda state: state.has("Tear", player))
    # Elw Pyramid
    set_rule(multiworld.get_location("[Elw Pyramid] Chest - Saint Centour East, West Room, Left", player), lambda state: state.has("Grapple", player))
    set_rule(multiworld.get_location("[Elw Pyramid] Chest - Saint Centour East, West Room, Right", player), lambda state: state.has("Grapple", player))
    set_rule(multiworld.get_location("[Elw Pyramid] Chest - Port Timney East, West Room, Left", player), lambda state: state.has("Grapple", player))
    set_rule(multiworld.get_location("[Elw Pyramid] Chest - Port Timney East, West Room, Middle", player), lambda state: state.has("Grapple", player))
    set_rule(multiworld.get_location("[Elw Pyramid] Chest - Port Timney East, West Room, Right", player), lambda state: state.has("Grapple", player))
    set_rule(multiworld.get_location("[Elw Pyramid] Chest - Port Timney East, East Room, Left", player), lambda state: state.has("Grapple", player))
    set_rule(multiworld.get_location("[Elw Pyramid] Chest - Port Timney East, East Room, Middle", player), lambda state: state.has("Grapple", player))
    set_rule(multiworld.get_location("[Elw Pyramid] Chest - Port Timney East, East Room, Right", player), lambda state: state.has("Grapple", player))
    # Epitaph Sea
    set_rule(multiworld.get_location("[Epitaph Sea] Chest - Duplicator", player), lambda state: state.has("Skates", player))
    set_rule(multiworld.get_location("[Epitaph Sea] Chest - Talisman", player), lambda state: state.has("Skates", player))
    # Forest Prison
    set_rule(multiworld.get_location("[Forest Prison] Rune - Life Rune", player), lambda state: state.has("Spirit Key", player))
    # Gemini's Corpse
    set_rule(multiworld.get_location("[Gemini's Corpse] Fast Draw - Cosmic Nova", player), lambda state: state.has("Bombs", player))
    set_rule(multiworld.get_location("[Gemini's Corpse] ARM - Phaser", player), lambda state: state.has("Bombs", player))
    # Ghost Ship
    set_rule(multiworld.get_location("[Ghost Ship] Chest - Right Path Before Grapple", player), lambda state: state.has("Hanpan", player))
    set_rule(multiworld.get_location("[Ghost Ship] Chest - Final Path Across Gap", player), lambda state: state.has("Hanpan", player))
    # Heaven Corridor
    set_rule(multiworld.get_location("[Heaven Corridor] Force - Dual Cast", player), lambda state: state.has("Vase", player))
    # Lolithia's Tomb
    set_rule(multiworld.get_location("[Lolithia's Tomb] Trap Chest - 1st Switch Room", player), lambda state: (state.has("Hanpan", player) or bool(world.options.risky_treasures)))
    set_rule(multiworld.get_location("[Lolithia's Tomb] Trap Chest - After Four Blocks Switch Room", player), lambda state: (state.has("Hanpan", player) or bool(world.options.risky_treasures)))
    set_rule(multiworld.get_location("[Lolithia's Tomb] Trap Chest - 3rd Switch Room, Bottom", player), lambda state: (state.has("Hanpan", player) or bool(world.options.risky_treasures)))
    set_rule(multiworld.get_location("[Lolithia's Tomb] Chest - Bomb Ledge, Right", player), lambda state: state.has("Grapple", player))
    set_rule(multiworld.get_location("[Lolithia's Tomb] NPC - Emma Reward", player), lambda state: state.has("defeated_magtortous", player))
    set_rule(multiworld.get_location("[Lolithia's Tomb] Trap Chest - East Path 2nd Switch Room", player), lambda state: (state.has("Hanpan", player) or bool(world.options.risky_treasures)))
    set_rule(multiworld.get_location("[Lolithia's Tomb] Chest - Lolithia Room, West", player), lambda state: state.has("defeated_magtortous", player))
    set_rule(multiworld.get_location("[Lolithia's Tomb] Chest - Lolithia Room, East", player), lambda state: state.has("defeated_magtortous", player))
    # Maze of Death
    set_rule(multiworld.get_location("[Maze of Death] Boss - Chaos", player), lambda state: state.has("Bombs", player))
    set_rule(multiworld.get_location("[Maze of Death] Chest - Left Path, North Room, Right", player), lambda state: (state.has("Hanpan", player) or bool(world.options.risky_treasures)))
    set_rule(multiworld.get_location("[Maze of Death] Chest - Path to Chaos, West", player), lambda state: state.has("Bombs", player))
    set_rule(multiworld.get_location("[Maze of Death] Chest - Path to Chaos, East", player), lambda state: state.has("Bombs", player))
    set_rule(multiworld.get_location("[Maze of Death] Rune - Death Rune", player), lambda state: state.has("Bombs", player))
    # Memory Temple
    set_rule(multiworld.get_location("[Memory Temple] Chest - Emiko Room, North", player), lambda state: state.has("Hanpan", player))
    # Milama Village
    set_rule(multiworld.get_location("[Milama Village] Big Box - Outside Waterfront House, Right", player), lambda state: state.has("Bombs", player))
    set_rule(multiworld.get_location("[Milama Village] Big Box - Outside Waterfront House, Middle", player), lambda state: state.has("Bombs", player))
    set_rule(multiworld.get_location("[Milama Village] Big Box - Outside Waterfront House, Left", player), lambda state: state.has("Bombs", player))
    set_rule(multiworld.get_location("[Milama Village] Chest - Inside Radar House", player), lambda state: state.has("Wand", player))
    # Mountain Pass
    set_rule(multiworld.get_location("[Mountain Pass] Chest - West Side, In Bushes", player), lambda state: (state.has("Hanpan", player) or bool(world.options.risky_treasures)))
    set_rule(multiworld.get_location("[Mountain Pass] Chest - West Side, Inside Bomb Wall", player), lambda state: state.has("Bombs", player))
    set_rule(multiworld.get_location("[Mountain Pass] Chest - East Side, After Rock", player), lambda state: state.has("Bombs", player))
    set_rule(multiworld.get_location("[Mountain Pass] Chest - West Side, After Rock", player), lambda state: state.has("Bombs", player))
    # Port Timney
    set_rule(multiworld.get_location("[Port Timney] Fast Draw - Trickster", player), lambda state: state.has("Bombs", player))
    set_rule(multiworld.get_location("[Port Timney] Chest - West of Pub", player), lambda state: state.has("Bombs", player))
    set_rule(multiworld.get_location("[Port Timney] NPC - Bartholomew's Gift", player), lambda state: state.has("Crystal Bud", player))
    # Saint Centour
    set_rule(multiworld.get_location("[Saint Centour] Chest - North-West House Basement", player), lambda state: state.has("defeated_night_gaunt", player))
    set_rule(multiworld.get_location("[Saint Centour] Rune - Saint Rune", player), lambda state: state.has("defeated_night_gaunt", player))
    set_rule(multiworld.get_location("[Saint Centour] Chest - West House Basement", player), lambda state: state.has("defeated_night_gaunt", player))
    set_rule(multiworld.get_location("[Saint Centour] Chest - Pub, Left", player), lambda state: state.has("defeated_night_gaunt", player))
    set_rule(multiworld.get_location("[Saint Centour] Chest - Pub, Middle", player), lambda state: state.has("defeated_night_gaunt", player))
    set_rule(multiworld.get_location("[Saint Centour] Chest - Pub, Right", player), lambda state: state.has("defeated_night_gaunt", player))
    set_rule(multiworld.get_location("[Saint Centour] Chest - Outside Item Shop, South", player), lambda state: state.has("defeated_night_gaunt", player))
    set_rule(multiworld.get_location("[Saint Centour] Chest - Outside Inn, North", player), lambda state: state.has("defeated_night_gaunt", player))
    set_rule(multiworld.get_location("[Saint Centour] Chest - Outside Item Shop, East", player), lambda state: state.has("defeated_night_gaunt", player))
    # Sand River
    set_rule(multiworld.get_location("[Sand River] Fast Draw - Heal Blade", player), lambda state: state.has("Lighter", player))
    set_rule(multiworld.get_location("[Sand River] Chest - After Bomb Wall", player), lambda state: state.has("Bombs", player))
    # Secret Passage
    set_rule(multiworld.get_location("[Secret Passage] Chest - 1st Section, Across water", player), lambda state: state.has("Hanpan", player))
    set_rule(multiworld.get_location("[Secret Passage] Chest - 3rd Section, Across water", player), lambda state: state.has("Hanpan", player))
    # Ship Graveyard
    set_rule(multiworld.get_location("[Ship Graveyard] Force - Sonic Vision", player), lambda state: state.has("Bracelet", player))
    set_rule(multiworld.get_location("[Ship Graveyard] Chest - Shipwreck Beach 5", player), lambda state: state.has("defeated_captain_geist", player))
    set_rule(multiworld.get_location("[Ship Graveyard] Chest - Shipwreck Beach 4", player), lambda state: state.has("defeated_captain_geist", player))
    set_rule(multiworld.get_location("[Ship Graveyard] Chest - Shipwreck Beach 3", player), lambda state: state.has("defeated_captain_geist", player))
    set_rule(multiworld.get_location("[Ship Graveyard] Big Box - West of Dan's House 1", player), lambda state: state.has("Bombs", player))
    set_rule(multiworld.get_location("[Ship Graveyard] Big Box - West of Dan's House 2", player), lambda state: state.has("Bombs", player))
    set_rule(multiworld.get_location("[Ship Graveyard] Big Box - North of Dan's House", player), lambda state: state.has("Bombs", player))
    set_rule(multiworld.get_location("[Ship Graveyard] Big Box - North of Item Shop 1", player), lambda state: state.has("Bombs", player))
    set_rule(multiworld.get_location("[Ship Graveyard] Big Box - North of Item Shop 2", player), lambda state: state.has("Bombs", player))
    # Sweet Candy
    set_rule(multiworld.get_location("[Sweet Candy] Boss - Zed 1", player), lambda state: state.has("defeated_zed_1", player))
    set_rule(multiworld.get_location("[Sweet Candy] Rune - Thunder Rune", player), lambda state: state.has("defeated_zed_1", player))
    set_rule(multiworld.get_location("[Sweet Candy] NPC - Bartholomew's Gift", player), lambda state: state.has("defeated_zed_1", player))
    set_rule(multiworld.get_location("[Sweet Candy] NPC - Wedding Gift 1", player), lambda state: state.has("defeated_zed_1", player))
    set_rule(multiworld.get_location("[Sweet Candy] NPC - Wedding Gift 2", player), lambda state: state.has("defeated_zed_1", player))
    set_rule(multiworld.get_location("[Sweet Candy] NPC - Wedding Gift 3", player), lambda state: state.has("defeated_zed_1", player))
    set_rule(multiworld.get_location("[Sweet Candy] NPC - Wedding Gift 4", player), lambda state: state.has("defeated_zed_1", player))
    # Tripillar
    set_rule(multiworld.get_location("[Tripillar] Chest - Blue Virtue", player), lambda state: state.has("Grapple", player))
    set_rule(multiworld.get_location("[Tripillar] Chest - Potion Berry 2", player), lambda state: state.has("Grapple", player))
    set_rule(multiworld.get_location("[Tripillar] Chest - Secret Sign", player), lambda state: state.has("Grapple", player))
    set_rule(multiworld.get_location("[Tripillar] Boss - Mage Fox", player), lambda state: state.has("Grapple", player))
    # Vassim's Lab
    set_rule(multiworld.get_location("[Vassim's Lab] Big Box - Secret Tool", player), lambda state: state.has("Bombs", player))
    # Wandering Isle
    set_rule(multiworld.get_location("[Wandering Isle] Chest - Magic Carrot", player), lambda state: state.has("Hanpan", player))
    set_rule(multiworld.get_location("[Wandering Isle] Chest - Crest Graph", player), lambda state: state.has("Hanpan", player))
    set_rule(multiworld.get_location("[Wandering Isle] Chest - Sioux Poncho", player), lambda state: state.has("Hanpan", player))
    set_rule(multiworld.get_location("[Wandering Isle] Chest - Red Jacket", player), lambda state: state.has("Hanpan", player))


def set_completion_rules(world: "WildArmsWorld") -> None:
    player = world.player

    # Goal: defeated_zeik_tuvai
    world.multiworld.completion_condition[player] = lambda state: state.has("defeated_zeik_tuvai", player)
