import os
from typing import ClassVar

import settings
from worlds.AutoWorld import World, WebWorld

from .Client import WildArmsClient  # noqa: F401  (importing registers the BizHawk client)
from .data.specials_table import FASTDRAW_ID_TO_NAME
from .Items import WildArmsItem, item_data, item_table, base_id as item_base_id
from .Locations import location_table
from .Options import WildArmsOptions, wildarms_option_groups
from .Regions import create_regions
from .Rom import WildArmsProcedurePatch
from .Rules import set_rules, set_completion_rules

class WildArmsSettings(settings.Group):
    class RomFile(settings.UserFilePath):
        """File name of the Wild Arms (USA) ROM/disc image"""
        description = "Wild Arms (SCUS-94608) BIN File"
        copy_to = "Wild Arms (USA).bin"
        md5s = [WildArmsProcedurePatch.hash]

    rom_file: RomFile = RomFile(RomFile.copy_to)


class WildArmsWeb(WebWorld):
    option_groups = wildarms_option_groups


class WildArmsWorld(World):
    """
    Wild Arms is a 1996/1997 PlayStation RPG by Sony Computer Entertainment and Media Vision.
    The game follows the adventures of a band of "Dream Chasers", Rudy, Jack, and Cecilia, as they make their way across the desert-like world of Filgaia.
    (https://en.wikipedia.org/wiki/Wild_Arms)
    """
    game = "Wild Arms"
    web = WildArmsWeb()
    settings_key = "wildarms_settings"
    settings: ClassVar[WildArmsSettings]
    options_dataclass = WildArmsOptions
    item_name_to_id = item_table
    location_name_to_id = location_table

    def create_regions(self) -> None:
        create_regions(self)

    def generate_early(self) -> None:
        # Hint number n + 1 stands for technique fast_draw_hint_order[n]; the player sees only the number.
        self.fast_draw_hint_order = self.random.sample(range(len(FASTDRAW_ID_TO_NAME)), len(FASTDRAW_ID_TO_NAME))

    def create_items(self) -> None:
        counts = {name: data.count for name, data in item_data.items()}
        if not self.options.mastered_fast_draws:
            # Each technique's copies are placed as its hint instead, so the pool keeps its size.
            for fast_draw_id, fast_draw_name in FASTDRAW_ID_TO_NAME.items():
                learned = f"<Fast Draw> {fast_draw_name}"
                hint = f"<Fast Draw> Hint {self.fast_draw_hint_order.index(fast_draw_id) + 1}"
                counts[hint], counts[learned] = counts[learned], 0
        for name, count in counts.items():
            self.multiworld.itempool += [self.create_item(name) for _ in range(count)]

    def create_item(self, name: str) -> WildArmsItem:
        data = item_data[name]
        return WildArmsItem(name, data.classification, item_base_id + data.id, self.player)

    def set_rules(self) -> None:
        set_rules(self)
        set_completion_rules(self)

    def fill_slot_data(self):
        return {
            "exp_multiplier": self.options.exp_multiplier.value,
            "gella_multiplier": self.options.gella_multiplier.value,
            "enemy_difficulty": self.options.enemy_difficulty.value,
            "pleasing_garden_fixed": bool(self.options.pleasing_garden_fixed),
            "dark_room_tricks": bool(self.options.dark_room_tricks),
            "risky_treasures": bool(self.options.risky_treasures),
            "mastered_fast_draws": bool(self.options.mastered_fast_draws),
            "fast_draw_hint_order": self.fast_draw_hint_order,
        }

    def generate_output(self, output_directory: str) -> None:
        """Writes this player's .apwildarms patch -- just seed.json, no disc bytes. The real disc
        work happens later, in Rom.py's apply_seed()."""
        import json
        from . import Patcher

        reward_ids, local_names = Patcher.reward_ids_from_world(self)
        seed = Patcher.build_seed_dict(
            pleasing_garden_fixed=bool(self.options.pleasing_garden_fixed),
            exp_multiplier=self.options.exp_multiplier.value,
            gella_multiplier=self.options.gella_multiplier.value,
            game_options={
                "camera_view": self.options.camera_view.value,
                "cursor": self.options.cursor.value,
                "battle_command": self.options.battle_command.value,
            },
            reward_ids=reward_ids,
            local_names=local_names,
            player_name=self.player_name,
            mastered_fast_draws=bool(self.options.mastered_fast_draws),
            enemy_difficulty=self.options.enemy_difficulty.value,
            buffed_apples=self.options.buffed_apples.value,
            open_world=bool(self.options.open_world),
        )
        patch = WildArmsProcedurePatch(player=self.player, player_name=self.player_name)
        patch.write_file("seed.json", json.dumps(seed).encode("utf-8"))
        out_file_name = self.multiworld.get_out_file_name_base(self.player)
        patch.write(os.path.join(output_directory, f"{out_file_name}{patch.patch_file_ending}"))
