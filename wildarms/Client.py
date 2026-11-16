"""
Wild Arms (PS1) live BizHawk client.

Delivers received items by writing RAM directly and reports location checks by polling each location's (address, mask) pair.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import pkgutil
import re
import zlib
from typing import TYPE_CHECKING, Dict, Optional, Set

from Utils import messagebox
from worlds._bizhawk import display_message, get_hash, read, guarded_write, write
from worlds._bizhawk.client import BizHawkClient

from .Locations import location_data, location_table
from .data.items_table import ITEM_NAME_TO_ID as _NATIVE_ITEM_NAME_TO_ID
from .Patcher import VERSION_TEXT_LENGTH, parse_slot_record
from .data.specials_table import ARM_NAME_TO_ID, ARM_STATS, FASTDRAW_NAME_TO_ID, FASTDRAW_MP_COST, FORCE_NAME_TO_ID, MAGIC_NAME_TO_ID

if TYPE_CHECKING:
    from worlds._bizhawk.context import BizHawkClientContext

# When True, delivery and location-check diagnostics are written to the client log.
IS_DEBUG_MODE = False

WILD_ARMS_ROM_HASH = "15102200"

DOMAIN = "MainRAM"

# One unsigned byte holding the current map number.
MAP_NUMBER_ADDRESS = 0x133DDE

# Every address to read each tick (a location's address plus any prereq address), and the (location id, mask, inverted, prereq) entries at each.
# inverted: the bit starts set and the check fires when it clears.
# prereq: an (address, mask) pair that must also be set before the location's bit means anything.
_LOCATIONS_BY_ADDRESS: Dict[int, list] = {}
for _name, _data in location_data.items():
    _prereq = (_data.prereq_address, _data.prereq_mask) if _data.prereq_address else None
    _LOCATIONS_BY_ADDRESS.setdefault(_data.address, []).append((location_table[_name], _data.mask, _data.inverted, _prereq))
_LOCATION_ADDRESSES = sorted(set(_LOCATIONS_BY_ADDRESS) | {
    _data.prereq_address for _data in location_data.values() if _data.prereq_address
})

# Character struct bases for stats, weapon and armor. Tool ownership uses a separate table (TOOL_OWNER_BASE).
CHAR1_BASE = 0x133DE0  # Rudy
CHAR2_BASE = 0x133E14  # Jack
CHAR3_BASE = 0x133E48  # Cecilia

TOOL_SLOT_OFFSETS = (0x07, 0x08, 0x09, 0x0A)  # the four tool-ownership bytes in a struct
TOOL_SLOT_EMPTY = 0xFF

# Tool name (as shown in the game's tool menu and in Items.py) -> tool id.
# Radar and Watch have no pool entry.
TOOL_NAME_TO_ID = {
    "Bombs": 0,
    "Radar": 1,
    "Skates": 2,
    "P. Glove": 3,
    "Hanpan": 4,
    "Lighter": 5,
    "Grapple": 6,
    "Guitar": 7,
    "Tear": 8,
    "Watch": 9,
    "Vase": 10,
    "Wand": 11,
}

# Tool ownership bases: Rudy's tools sit at CHAR2_BASE, Jack's at CHAR3_BASE, Cecilia's one stride past CHAR3_BASE.
CECILIA_TOOL_OWNER_BASE = 0x133E7C
TOOL_OWNER_BASE = {
    0: CHAR2_BASE,   # Bombs
    1: CHAR2_BASE,   # Radar
    2: CHAR2_BASE,   # Skates
    3: CHAR2_BASE,   # P. Glove

    4: CHAR3_BASE,   # Hanpan
    5: CHAR3_BASE,   # Lighter
    6: CHAR3_BASE,   # Grapple
    7: CHAR3_BASE,   # Guitar

    8: CECILIA_TOOL_OWNER_BASE,   # Tear
    9: CECILIA_TOOL_OWNER_BASE,   # Watch
    10: CECILIA_TOOL_OWNER_BASE,  # Vase
    11: CECILIA_TOOL_OWNER_BASE,  # Wand
}

# The tool a character has equipped is a 16-bit slot index (0-3) into that character's four tool slots, stored at +0x0C of the character's own
# struct. This maps each tool table to the struct of the same character.
TOOL_EQUIPPED_OFFSET = 0x0C
TOOL_EQUIPPED_STRUCT = {CHAR2_BASE: CHAR1_BASE, CHAR3_BASE: CHAR2_BASE, CECILIA_TOOL_OWNER_BASE: CHAR3_BASE}

# Equip slots in a character struct: four 16-bit little-endian item ids, 0xFFFF when empty.
WEAPON_SLOT_OFFSET = 0x30
LEFT_HAND_SLOT_OFFSET = 0x32  # unused for writing; Left Hand is granted as an inventory item (NON_EQUIP_PROGRESSIVE)
ARMOR_SLOT_OFFSET = 0x34
HEAD_SLOT_OFFSET = 0x36
EMPTY_EQUIP_SLOT = 0xFFFF

# Progressive chain name -> (character base, slot offset, item ids in tier order).
# Weapon and armor tier 1 is starting gear and is never written, so their first id is tier 2.
PROGRESSIVE_EQUIPMENT = {
    "Progressive Rudy Weapon": (CHAR1_BASE, WEAPON_SLOT_OFFSET,
        (37, 38, 39, 40, 41, 42, 44, 45, 46, 47)),
        # Long Sword, Bastard Sword, Claymore, Bronze Sword, Cross Saber,
        # Night Fencer, Energy Saber, Sword Radius, Silver Blade, Divine Blade
    "Progressive Rudy Armor": (CHAR1_BASE, ARMOR_SLOT_OFFSET,
        (128, 129, 130, 131, 132, 133, 134, 135, 136, 137, 138)),
        # Hard Cloak, Armor Vest, Guard Jacket, Chain Cloak, Metal Jacket,
        # Cross Cloak, Red Jacket, Warrior Vest, Battle Cloak, Assault Coat, Braver Vest
    "Progressive Jack Weapon": (CHAR2_BASE, WEAPON_SLOT_OFFSET,
        (49, 50, 51, 52, 53, 54, 56, 58, 57, 59)),
        # Chrome Blade, Might Blade, Vopal Razor, Crystal Edge, Spirit Blade,
        # Extinction, Black Feral, Violator, Doom Bringer, Juggernaut
    "Progressive Jack Armor": (CHAR2_BASE, ARMOR_SLOT_OFFSET,
        (140, 141, 142, 143, 144, 145, 146, 147, 148, 149, 150)),
        # War Coat, Sun Poncho, Journey Coat, Survive Cape, Dusk Poncho, Blue Wind,
        # Sioux Poncho, Prairie Coat, Dawn Poncho, Jolla Poncho, Jade Wilder
    "Progressive Cecilia Weapon": (CHAR3_BASE, WEAPON_SLOT_OFFSET,
        (61, 62, 63, 64, 65, 66, 68, 69, 70, 71)),
        # Magical Rod, Dream Wand, Prism Stick, Rune Staff, Sorcery Wand,
        # Rainbow Wand, Lunar Rod, Lunatic Wand, Princess Rod, Dist Dims
    "Progressive Cecilia Armor": (CHAR3_BASE, ARMOR_SLOT_OFFSET,
        (152, 153, 154, 155, 156, 157, 158, 159, 160, 161, 162)),
        # White Robe, Mist Blazer, Magus Robe, Protect Cape, Chic Bolero, Ruby Bische,
        # Shining Cape, Mirage Coat, Garnet Coat, Filgaia Robe, Pret-a-porte

    # Left Hand and Head have no starting gear, so their first id is tier 1. Tier 5 of every Left Hand chain is Sheriff Star (id 102).
    "Progressive Rudy Left Hand": (CHAR1_BASE, LEFT_HAND_SLOT_OFFSET,
        (106, 107, 108, 109, 102)),
        # Buckler, Round Shield, Reflex, Metal Shield, Sheriff Star
    "Progressive Jack Left Hand": (CHAR2_BASE, LEFT_HAND_SLOT_OFFSET,
        (112, 113, 114, 115, 102)),
        # Hide Glove, Hard Guard, Gauntlet, Boom Getter, Sheriff Star
    "Progressive Cecilia Left Hand": (CHAR3_BASE, LEFT_HAND_SLOT_OFFSET,
        (121, 122, 123, 124, 102)),
        # Mystic Word, Secret Book, Elder Scroll, Necronomicon, Sheriff Star
    "Progressive Rudy Head": (CHAR1_BASE, HEAD_SLOT_OFFSET,
        (163, 164, 165, 167, 168)),
        # Bandanna, Metal Band, Head Gear, Hyper Gear, Dead Heat
    "Progressive Jack Head": (CHAR2_BASE, HEAD_SLOT_OFFSET,
        (169, 170, 171, 173, 174)),
        # Cowboy Hat, 10gal Hat, My Grand Hat, Sunbird Hat, Texas Number
    "Progressive Cecilia Head": (CHAR3_BASE, HEAD_SLOT_OFFSET,
        (175, 176, 177, 179, 180)),
        # Capuche, Cute Ribbon, Serenade, Blue Ribbon, Ruby Tiara
}

# Chains whose first id is tier 1 instead of tier 2.
NO_STARTING_TIER = frozenset({
    "Progressive Rudy Left Hand", "Progressive Jack Left Hand", "Progressive Cecilia Left Hand",
    "Progressive Rudy Head", "Progressive Jack Head", "Progressive Cecilia Head",
})

# Chains granted into general inventory instead of the equip slot, so each tier received stays available.
NON_EQUIP_PROGRESSIVE = frozenset({
    "Progressive Rudy Left Hand", "Progressive Jack Left Hand", "Progressive Cecilia Left Hand",
})

# Gella is a 32-bit little-endian total.
GELLA_BASE = 0x1341DC
GELLA_RE = re.compile(r"^(\d+) Gella$")

# General inventory: parallel 256-byte id and quantity arrays, slot N at BASE + N. A slot with quantity 0 is empty whatever its id byte holds.
ITEM_ID_BASE = 0x133F4C
ITEM_QTY_BASE = 0x13404C
INVENTORY_SLOT_COUNT = 256

# ARM, Fast Draw and Crest-magic slot arrays. The player can reorder them, so a grant always takes the first empty slot.
SPECIAL_SLOT_EMPTY = 0xFF

# Item names start with these labels, e.g. "<ARM> Prism Ray".
ARM_LABEL = "<ARM> "
FASTDRAW_LABEL = "<Fast Draw> "
FASTDRAW_HINT_LABEL = "<Fast Draw> Hint "
FASTDRAW_HINT_OFFSET = 16  # a Fast Draw slot holding id + 16 is the unmastered hint, shown as ????
SPELL_LABEL = "<Spell> "
FORCE_LABEL = "<Force> "
FORCE_BYTE_BASE = 0x1341EC  # Rudy's Force byte; Jack's and Cecilia's follow at FORCE_BYTE_STRIDE
FORCE_BYTE_STRIDE = 4
FORCE_BITS_PER_CHARACTER = 4

ARM_BASE, ARM_STRIDE, ARM_SLOTS = 0x13414C, 6, 8
FASTDRAW_BASE, FASTDRAW_STRIDE, FASTDRAW_SLOTS = 0x13417C, 2, 16
CREST_BASE, CREST_STRIDE, CREST_SLOTS = 0x13419C, 1, 64

# Save identity record: the first two of the five 18-byte "Best 5 Runners" names, which the game saves and loads with each save file.
# Name 1 holds the seed stamp and name 2 the delivered-item counter. Each name is up to 17 printable characters padded with spaces, then 0x00.
NAME_TABLE_ADDRESS = 0x019A98
NAME_SIZE = 18
RECORD_LENGTH = 2 * NAME_SIZE
COUNTER_TEXT_LENGTH = 8  # 4 hex digits of count, 4 of checksum
STAMP_PREFIX = "WA1"
FRESH_FIRST_NAME = b"ARCHIPELAGO"  # the first name on a new game on the patched disc
VANILLA_FIRST_NAME = b"McDullen"  # the retail default, so a save made without the randomizer
SETUP_DONE_FLAG_ADDRESS, SETUP_DONE_FLAG_MASK = 0x104601,  0x04  # flag 1162, set once new-game setup has finished
SLOT_RECORD_ADDRESS = NAME_TABLE_ADDRESS + 2 * NAME_SIZE  # names 3 and 4: the version text and the slot name
SLOT_RECORD_LENGTH = 2 * NAME_SIZE
AUTH_POLL_SECONDS = 1.0
SETTLE_TICKS = 5  # identical consecutive readings before an error state is acted on


def _name_bytes(text: str) -> bytes:
    return text.ljust(NAME_SIZE - 1).encode("ascii")[:NAME_SIZE - 1] + b"\x00"


def _counter_text(stamp: str, count: int) -> str:
    body = f"{count:04X}"
    return body + f"{zlib.crc32((stamp + body).encode('ascii')) & 0xFFFF:04X}"


def _record_bytes(stamp: str, count: int) -> bytes:
    return _name_bytes(stamp) + _name_bytes(_counter_text(stamp, count))


def _parse_counter(stamp: str, text: str) -> Optional[int]:
    """The delivered-item count in a counter string, or None if the string is malformed or its checksum fails."""
    try:
        count = int(text[:4], 16)
    except ValueError:
        return None
    return count if _counter_text(stamp, count) == text else None


def _seed_stamp(ctx) -> str:
    """The 17-character stamp that identifies this room, team and slot."""
    digest = hashlib.sha256(f"{ctx.server_seed_name}:{ctx.team}:{ctx.slot}".encode("utf-8")).hexdigest()
    return STAMP_PREFIX + digest[:14]


def _installed_version() -> str:
    """The version of the disc changes packaged in this apworld, as the first 12 hex digits."""
    data = json.loads(pkgutil.get_data(__name__, "data/patcher_offsets.json").decode("utf-8"))
    return data["base_version"][:VERSION_TEXT_LENGTH]


# Every native item name -> item id, for items delivered into general inventory. Gella, specials, tools and progressive chains are dispatched before this table is consulted.
GENERAL_ITEM_NAME_TO_ID = dict(_NATIVE_ITEM_NAME_TO_ID)


class WildArmsClient(BizHawkClient):
    """Every delivery goes through guarded_write, so a RAM change mid-read fails the write and the item is retried next tick."""
    game = "Wild Arms"
    system = "PSX"
    patch_suffix = ".apwildarms"

    def __init__(self) -> None:
        super().__init__()
        self.received_item_count = 0
        # Tier count per progressive chain, rebuilt from the received items whenever a matching save is read.
        self.progressive_received: Dict[str, int] = {}
        # Locations already reported, so a check is not re-sent every tick while the server catches up.
        self.locations_sent: Set[int] = set()
        # Item indices whose delivery error has been logged, so a failing item logs once.
        self._logged_delivery_error_indices: Set[int] = set()
        # Last map number sent to data storage; None until the first read of a connection.
        self._published_map: Optional[int] = None
        # Names 1 and 2 of the identity record as last read or written; the guard for counter writes. None until a matching record is read.
        self._record_raw: Optional[bytes] = None
        # Last save-identity state reported, so each change is reported once.
        self._save_state: Optional[str] = None
        # (state, consecutive readings, tick of the last reading) of the identity table.
        self._streak = (None, 0, 0)
        self._tick = 0
        # Set when a delivery already advanced the counter in the same guarded write as the item.
        self._counter_committed = False

    async def validate_rom(self, ctx: "BizHawkClientContext") -> bool:
        try:
            rom_hash = await get_hash(ctx.bizhawk_ctx)
        except Exception:
            return False
        if rom_hash != WILD_ARMS_ROM_HASH:
            return False
        ctx.game = self.game
        ctx.items_handling = 0b111
        ctx.want_slot_data = True
        self._published_map = None
        return True

    async def set_auth(self, ctx: "BizHawkClientContext") -> None:
        """Logs in with the slot name baked into the disc, or falls back to manual auth if the table holds no valid record."""
        # Imported at call time: CommonClient imports worlds, which fails while worlds are still loading.
        from CommonClient import logger

        announced = False
        while True:
            try:
                head, record = await read(ctx.bizhawk_ctx, [(NAME_TABLE_ADDRESS, len(FRESH_FIRST_NAME), DOMAIN),
                                                            (SLOT_RECORD_ADDRESS, SLOT_RECORD_LENGTH, DOMAIN)])
            except Exception:
                return
            head, record = bytes(head), bytes(record)
            parsed = parse_slot_record(record[:NAME_SIZE], record[NAME_SIZE:])
            if parsed is not None:
                slot_name, disc_version = parsed
                ctx.auth = slot_name
                self._diag(f"logging in as {slot_name}")
                if disc_version != _installed_version():
                    logger.warning(
                        f"Wild Arms: this disc was built with different game data ({disc_version}) than the installed apworld ({_installed_version()}). "
                        "Patch the game again with the installed apworld.")
                return
            if head.startswith((STAMP_PREFIX.encode("ascii"), FRESH_FIRST_NAME, VANILLA_FIRST_NAME)):
                logger.info("Wild Arms: this game has no slot name stored on its disc, so the slot name has to be entered.")
                return
            if not announced:
                announced = True
                logger.info("Wild Arms: waiting for the game to load to read the slot name.")
            await asyncio.sleep(AUTH_POLL_SECONDS)

    def _diag(self, msg: str) -> None:
        """Writes a diagnostic line to the client log when IS_DEBUG_MODE is set."""
        if not IS_DEBUG_MODE:
            return
        # Imported at call time: CommonClient imports worlds, which fails while worlds are still loading.
        from CommonClient import logger
        logger.info(f"[WA diag] {msg}")

    async def game_watcher(self, ctx: "BizHawkClientContext") -> None:
        if ctx.slot is None:
            return

        # Imported at call time: CommonClient imports worlds, which fails while worlds are still loading.
        from CommonClient import logger

        # The caller has no exception handling, so an uncaught error here would stop the watcher for the rest of the session. Each step is guarded and logs instead.
        try:
            ready = await self._sync_save_record(ctx, logger)
        except Exception:
            logger.exception("Wild Arms: error reading the save identity record")
            ready = False

        if ready:
            new_items = ctx.items_received[self.received_item_count:]
            if new_items and IS_DEBUG_MODE:
                pending_names = [ctx.item_names.lookup_in_game(it.item, ctx.game) for it in new_items]
                self._diag(f"game_watcher tick: index={self.received_item_count}, {len(new_items)} pending: {pending_names}")
            for item in new_items:
                item_name = ctx.item_names.lookup_in_game(item.item, ctx.game)
                self._counter_committed = False
                try:
                    delivered = await self._deliver_item(ctx, item_name)
                    if delivered and not self._counter_committed:
                        delivered = await self._write_counter(ctx, self.received_item_count + 1)
                except Exception:
                    if self.received_item_count not in self._logged_delivery_error_indices:
                        self._logged_delivery_error_indices.add(self.received_item_count)
                        logger.exception(
                            f"Wild Arms: error delivering {item_name!r} (item index "
                            f"{self.received_item_count}); retrying next tick"
                        )
                    break
                # A failed delivery stops the batch so the same item is retried next tick, in order.
                if not delivered:
                    break
                self.received_item_count += 1

            try:
                await self._check_locations(ctx)
            except Exception:
                logger.exception("Wild Arms: error checking locations")

        try:
            await self._publish_map(ctx)
        except Exception:
            logger.exception("Wild Arms: error publishing current map")

    def _report_save_state(self, state: str, logger, message: str, popup: bool = False) -> None:
        """Reports a save-identity state change once. Only a popup state (a save that cannot be used) is shown to the player; the rest is written to the log in debug mode."""
        if state == self._save_state:
            return
        self._save_state = state
        if popup:
            logger.error(f"Wild Arms: {message}")
            messagebox("Wild Arms", message, error=True)
        else:
            self._diag(message)

    def _settled(self, state: str) -> bool:
        """True once the same state has been read SETTLE_TICKS times in a row."""
        previous, count, last_tick = self._streak
        count = count + 1 if previous == state and last_tick == self._tick - 1 else 1
        self._streak = (state, count, self._tick)
        return count >= SETTLE_TICKS

    async def _sync_save_record(self, ctx: "BizHawkClientContext", logger) -> bool:
        """True once received_item_count is loaded from a save carrying this room's seed stamp. An ARCHIPELAGO table
        only counts as a new game once the setup-done flag is set (the start-of-game script hasn't finished until then);
        error states are reported only after SETTLE_TICKS reads, to ride out the title screen's transient table."""
        if ctx.server_seed_name is None:
            return False
        self._tick += 1
        raw, flag_byte = await read(ctx.bizhawk_ctx, [(NAME_TABLE_ADDRESS, RECORD_LENGTH, DOMAIN),
                                                      (SETUP_DONE_FLAG_ADDRESS, 1, DOMAIN)])
        raw = bytes(raw)
        setup_done = bool(flag_byte[0] & SETUP_DONE_FLAG_MASK)
        stamp = _seed_stamp(ctx)

        if raw.startswith(FRESH_FIRST_NAME):
            if not setup_done:
                self._record_raw = None
                self._report_save_state("loading", logger, "waiting for the game to finish setting up a new game.")
                return False
            record = _record_bytes(stamp, 0)
            if not await guarded_write(ctx.bizhawk_ctx, [(NAME_TABLE_ADDRESS, list(record), DOMAIN)],
                                       [(NAME_TABLE_ADDRESS, list(raw), DOMAIN)]):
                return False
            self._record_raw = record
            self.received_item_count = 0
            self.progressive_received = {}
            self._report_save_state("ready", logger, f"new save stamped for this room ({stamp}); delivering every received item.")
            return True

        if raw.startswith(STAMP_PREFIX.encode("ascii")):
            saved_stamp = raw[:NAME_SIZE - 1].decode("ascii", "replace").rstrip()
            if saved_stamp != stamp:
                self._record_raw = None
                if self._settled("mismatch"):
                    self._report_save_state(
                        "mismatch", logger,
                        f"Seed mismatch! This save belongs to a different seed or slot ({saved_stamp}, expected {stamp}). "
                        "Did you load the wrong save? Nothing will be delivered until a matching save is loaded.", popup=True)
                return False
            counter = raw[NAME_SIZE:NAME_SIZE + COUNTER_TEXT_LENGTH].decode("ascii", "replace")
            count = _parse_counter(stamp, counter)
            if count is None:
                self._record_raw = None
                if self._settled("corrupt"):
                    self._report_save_state(
                        "corrupt", logger,
                        f"The delivered-item counter in this save is unreadable ({counter!r}). Nothing will be delivered.", popup=True)
                return False
            if count > len(ctx.items_received):
                self._record_raw = None
                self._report_save_state("waiting", logger,
                                        f"this save has {count} items delivered; waiting for the server to send them.")
                return False
            if count != self.received_item_count or self._save_state != "ready":
                self.received_item_count = count
                self._rebuild_progressive_received(ctx, count)
                self._diag(f"matching save found, {count} items already delivered")
            self._record_raw = raw[:RECORD_LENGTH]
            self._save_state = "ready"
            return True

        self._record_raw = None
        if raw.startswith(VANILLA_FIRST_NAME):
            if self._settled("vanilla"):
                self._report_save_state(
                    "vanilla", logger,
                    "This save was made without the randomizer (it has the retail identity table). "
                    "Start a new game or load a save made on this disc. Nothing will be delivered.", popup=True)
            return False
        self._report_save_state("loading", logger, "waiting for the game to load a save (the identity table is not a game table yet).")
        return False

    def _rebuild_progressive_received(self, ctx: "BizHawkClientContext", upto: int) -> None:
        counts: Dict[str, int] = {}
        for received in ctx.items_received[:upto]:
            name = ctx.item_names.lookup_in_game(received.item, ctx.game)
            if name in PROGRESSIVE_EQUIPMENT:
                counts[name] = counts.get(name, 0) + 1
        self.progressive_received = counts

    def _counter_ops(self, ctx: "BizHawkClientContext", new_count: int):
        """(writes, guards) that set the stored counter to new_count, for appending to another guarded_write so the
        item and the counter change together."""
        address = NAME_TABLE_ADDRESS + NAME_SIZE
        expected = list(self._record_raw[NAME_SIZE:NAME_SIZE + COUNTER_TEXT_LENGTH])
        text = list(_counter_text(_seed_stamp(ctx), new_count).encode("ascii"))
        return [(address, text, DOMAIN)], [(address, expected, DOMAIN)]

    def _apply_counter_text(self, text) -> None:
        self._record_raw = self._record_raw[:NAME_SIZE] + bytes(text) + self._record_raw[NAME_SIZE + COUNTER_TEXT_LENGTH:]

    async def _write_counter(self, ctx: "BizHawkClientContext", new_count: int) -> bool:
        writes, guards = self._counter_ops(ctx, new_count)
        if not await guarded_write(ctx.bizhawk_ctx, writes, guards):
            return False
        self._apply_counter_text(writes[0][1])
        return True

    async def _roll_back_counter(self, ctx: "BizHawkClientContext") -> None:
        """Puts the stored counter back to received_item_count after a delivery that advanced it did not stick, so the item is delivered again."""
        self._counter_committed = False
        writes, guards = self._counter_ops(ctx, self.received_item_count)
        if await guarded_write(ctx.bizhawk_ctx, writes, guards):
            self._apply_counter_text(writes[0][1])
        else:
            self._diag("counter roll-back failed; the stored counter is one ahead of what was delivered")

    async def _publish_map(self, ctx: "BizHawkClientContext") -> None:
        current = (await read(ctx.bizhawk_ctx, [(MAP_NUMBER_ADDRESS, 1, DOMAIN)]))[0][0]
        if current == self._published_map:
            return
        self._published_map = current
        await ctx.send_msgs([{
            "cmd": "Set",
            "key": f"wildarms_current_map_{ctx.team}_{ctx.slot}",
            "default": 0,
            "want_reply": False,
            "operations": [{"operation": "replace", "value": current}],
        }])

    async def _check_locations(self, ctx: "BizHawkClientContext") -> None:
        read_list = [(addr, 1, DOMAIN) for addr in _LOCATION_ADDRESSES]
        values = await read(ctx.bizhawk_ctx, read_list)
        byte_by_addr = {addr: value[0] for addr, value in zip(_LOCATION_ADDRESSES, values)}

        newly_checked = []
        for addr, byte in byte_by_addr.items():
            # A prereq-only address has no entry of its own.
            for location_id, mask, inverted, prereq in _LOCATIONS_BY_ADDRESS.get(addr, []):
                if prereq is not None:
                    prereq_addr, prereq_mask = prereq
                    if byte_by_addr[prereq_addr] & prereq_mask == 0:
                        continue
                bit_set = (byte & mask) != 0
                if bit_set == inverted:  # normal: checked once set; inverted: checked once cleared
                    continue
                if location_id in ctx.checked_locations or location_id in self.locations_sent:
                    continue
                newly_checked.append(location_id)

        if not newly_checked:
            return

        self._diag(f"_check_locations: {len(newly_checked)} newly checked: {newly_checked}")
        self.locations_sent.update(newly_checked)
        await ctx.send_msgs([{
            "cmd": "LocationChecks",
            "locations": newly_checked,
        }])

    async def _deliver_item(self, ctx: "BizHawkClientContext", item_name: str) -> bool:
        # Order matters: each category is handled before GENERAL_ITEM_NAME_TO_ID so a name shared with a native item never falls through to a plain inventory grant.
        if item_name in PROGRESSIVE_EQUIPMENT:
            return await self._deliver_progressive_equipment(ctx, item_name)

        gella_match = GELLA_RE.match(item_name)
        if gella_match:
            return await self._deliver_gella(ctx, item_name, int(gella_match.group(1)))

        if item_name.startswith(ARM_LABEL) and item_name[len(ARM_LABEL):] in ARM_NAME_TO_ID:
            # After the id: the ATP, HIT% and Capacity upgrade levels, the current bullets (equal to the id's base capacity) and the unused last byte.
            arm_id = ARM_NAME_TO_ID[item_name[len(ARM_LABEL):]]
            return await self._deliver_special(
                ctx, item_name, arm_id, ARM_BASE, ARM_STRIDE, ARM_SLOTS,
                extra_bytes=[0, 0, 0, ARM_STATS[arm_id][1], 0],
            )
        if item_name.startswith(FASTDRAW_HINT_LABEL) and item_name[len(FASTDRAW_HINT_LABEL):].isdigit():
            hint_order = (ctx.slot_data or {}).get("fast_draw_hint_order")
            hint_number = int(item_name[len(FASTDRAW_HINT_LABEL):])
            if not hint_order or not 1 <= hint_number <= len(hint_order):
                return False  # the slot data that says which technique this hint is has not arrived
            fastdraw_id = hint_order[hint_number - 1]
            return await self._deliver_special(
                ctx, item_name, fastdraw_id + FASTDRAW_HINT_OFFSET, FASTDRAW_BASE, FASTDRAW_STRIDE, FASTDRAW_SLOTS,
                extra_bytes=[FASTDRAW_MP_COST[fastdraw_id]], held_values=(fastdraw_id, fastdraw_id + FASTDRAW_HINT_OFFSET),
            )
        if item_name.startswith(FASTDRAW_LABEL) and item_name[len(FASTDRAW_LABEL):] in FASTDRAW_NAME_TO_ID:
            fastdraw_id = FASTDRAW_NAME_TO_ID[item_name[len(FASTDRAW_LABEL):]]
            return await self._deliver_special(
                ctx, item_name, fastdraw_id, FASTDRAW_BASE, FASTDRAW_STRIDE, FASTDRAW_SLOTS,
                extra_bytes=[FASTDRAW_MP_COST[fastdraw_id]],
            )
        if item_name.startswith(SPELL_LABEL) and item_name[len(SPELL_LABEL):] in MAGIC_NAME_TO_ID:
            return await self._deliver_special(
                ctx, item_name, MAGIC_NAME_TO_ID[item_name[len(SPELL_LABEL):]], CREST_BASE, CREST_STRIDE, CREST_SLOTS,
                extra_bytes=[],
            )

        if item_name.startswith(FORCE_LABEL) and item_name[len(FORCE_LABEL):] in FORCE_NAME_TO_ID:
            return await self._deliver_force(ctx, item_name, FORCE_NAME_TO_ID[item_name[len(FORCE_LABEL):]])

        tool_id = TOOL_NAME_TO_ID.get(item_name)
        if tool_id is not None:
            return await self._deliver_tool(ctx, item_name, tool_id)

        if item_name in GENERAL_ITEM_NAME_TO_ID:
            return await self._deliver_general_item(ctx, item_name)

        # An unknown name cannot be delivered by retrying, so it does not block the queue.
        return True

    async def _deliver_tool(self, ctx: "BizHawkClientContext", item_name: str, tool_id: int) -> bool:
        """Adds a tool to its character's four tool slots, then lays the tools out in the game's own order (ascending tool id, empty slots last),
        which is how the game rebuilds a character's tools after any tool change. The equipped-tool slot index follows the equipped tool to its new slot."""
        base = TOOL_OWNER_BASE[tool_id]
        slot_addrs = [(base + off, 1, DOMAIN) for off in TOOL_SLOT_OFFSETS]
        equipped_addr = TOOL_EQUIPPED_STRUCT[base] + TOOL_EQUIPPED_OFFSET
        current = await read(ctx.bizhawk_ctx, slot_addrs + [(equipped_addr, 2, DOMAIN)])
        slots = [b[0] for b in current[:len(TOOL_SLOT_OFFSETS)]]
        equipped_bytes = current[len(TOOL_SLOT_OFFSETS)]

        if tool_id in slots:
            await display_message(ctx.bizhawk_ctx, f"Already have {item_name}")
            return True

        owned = sorted([tool for tool in slots if tool != TOOL_SLOT_EMPTY] + [tool_id])
        if len(owned) > len(TOOL_SLOT_OFFSETS):
            await display_message(ctx.bizhawk_ctx, f"Could not deliver {item_name} (no free tool slot)")
            return False
        new_slots = owned + [TOOL_SLOT_EMPTY] * (len(TOOL_SLOT_OFFSETS) - len(owned))

        # The equipped tool stays equipped: its slot index is looked up again in the new order. An index that pointed at no tool is left alone.
        equipped = int.from_bytes(equipped_bytes, "little")
        equipped_tool = slots[equipped] if equipped < len(slots) else TOOL_SLOT_EMPTY
        new_equipped = new_slots.index(equipped_tool) if equipped_tool != TOOL_SLOT_EMPTY else equipped

        writes = [(slot_addrs[0][0], new_slots, DOMAIN)]
        guards = [(slot_addrs[0][0], bytes(slots), DOMAIN)]
        if new_equipped != equipped:
            writes.append((equipped_addr, list(new_equipped.to_bytes(2, "little")), DOMAIN))
            guards.append((equipped_addr, equipped_bytes, DOMAIN))
        self._diag(f"_deliver_tool({item_name!r}, id={tool_id}): slots {slots} -> {new_slots}, equipped {equipped} -> {new_equipped}")
        ok = await guarded_write(ctx.bizhawk_ctx, writes, guards)
        if ok:
            await display_message(ctx.bizhawk_ctx, f"Received {item_name}!")
        else:
            self._diag(f"_deliver_tool({item_name!r}): guarded_write failed")
        return ok

    async def _deliver_force(self, ctx: "BizHawkClientContext", item_name: str, force_id: int) -> bool:
        """Sets a Force ability's bit in its character's Force byte. force_id is character * 4 + bit."""
        character, bit = divmod(force_id, FORCE_BITS_PER_CHARACTER)
        address = FORCE_BYTE_BASE + FORCE_BYTE_STRIDE * character
        current = (await read(ctx.bizhawk_ctx, [(address, 1, DOMAIN)]))[0][0]
        if current >> bit & 1:
            await display_message(ctx.bizhawk_ctx, f"Already have {item_name}")
            return True
        self._diag(f"_deliver_force({item_name!r}, id={force_id}): byte {address:#x} {current:#04x} -> {current | 1 << bit:#04x}")
        ok = await guarded_write(ctx.bizhawk_ctx, [(address, [current | 1 << bit], DOMAIN)], [(address, bytes([current]), DOMAIN)])
        if ok:
            await display_message(ctx.bizhawk_ctx, f"Received {item_name}!")
        else:
            self._diag(f"_deliver_force({item_name!r}): guarded_write failed")
        return ok

    async def _deliver_special(
        self, ctx: "BizHawkClientContext", item_name: str, special_id: int,
        base: int, stride: int, slots: int, extra_bytes: list, held_values: tuple = None,
    ) -> bool:
        """Grants an ARM, Fast Draw or Crest-magic into the first empty slot of its array. extra_bytes follow the id byte in the same slot. A slot whose first byte is in held_values (default: just special_id) counts as already held."""
        held_values = (special_id,) if held_values is None else held_values
        slot_addrs = [(base + i * stride, 1, DOMAIN) for i in range(slots)]
        current = await read(ctx.bizhawk_ctx, slot_addrs)

        if any(b[0] in held_values for b in current):
            await display_message(ctx.bizhawk_ctx, f"Already have {item_name}")
            return True

        free_slot = next((i for i, b in enumerate(current) if b[0] == SPECIAL_SLOT_EMPTY), None)
        if free_slot is None:
            await display_message(ctx.bizhawk_ctx, f"Could not deliver {item_name} (no free slot)")
            return False

        addr = base + free_slot * stride
        expected = current[free_slot]
        self._diag(f"_deliver_special({item_name!r}, id={special_id}): choosing slot {free_slot} @ {addr:#x}")
        ok = await guarded_write(
            ctx.bizhawk_ctx,
            [(addr, [special_id] + extra_bytes, DOMAIN)],
            [(addr, expected, DOMAIN)],
        )
        if ok:
            await display_message(ctx.bizhawk_ctx, f"Received {item_name}!")
        else:
            self._diag(f"_deliver_special({item_name!r}): guarded_write failed at slot {free_slot}")
        return ok

    async def _deliver_progressive_equipment(self, ctx: "BizHawkClientContext", item_name: str) -> bool:
        base, offset, tier_ids = PROGRESSIVE_EQUIPMENT[item_name]
        count = self.progressive_received.get(item_name, 0) + 1

        if count > len(tier_ids):
            self.progressive_received[item_name] = count
            return True

        new_id = tier_ids[count - 1]
        tier_number = count if item_name in NO_STARTING_TIER else count + 1

        if item_name in NON_EQUIP_PROGRESSIVE:
            ok = await self._grant_general_item_id(ctx, new_id, f"{item_name} (tier {tier_number})")
            if ok:
                self.progressive_received[item_name] = count
            return ok

        # The item being replaced goes into general inventory first, in the same guarded write as the new tier and the counter, so a retry
        # cannot add it twice. A full inventory cannot happen in this game; if it ever did, the new tier is still equipped and the old item is lost.
        addr = base + offset
        equip_bytes, id_bytes, qty_bytes = await read(ctx.bizhawk_ctx, [
            (addr, 2, DOMAIN),
            (ITEM_ID_BASE, INVENTORY_SLOT_COUNT, DOMAIN),
            (ITEM_QTY_BASE, INVENTORY_SLOT_COUNT, DOMAIN),
        ])
        old_id = int.from_bytes(equip_bytes, "little")
        writes = [(addr, [new_id & 0xFF, (new_id >> 8) & 0xFF], DOMAIN)]
        guards = [(addr, list(equip_bytes), DOMAIN)]
        moved = None
        if old_id not in (EMPTY_EQUIP_SLOT, new_id) and old_id < 256:
            moved = self._plan_inventory_add(id_bytes, qty_bytes, old_id)
            if moved is not None:
                writes += moved[1]
                guards += moved[2]
        counter_writes, counter_guards = self._counter_ops(ctx, self.received_item_count + 1)
        self._diag(f"_deliver_progressive_equipment({item_name!r}): slot {old_id:#x} -> {new_id:#x}, old item {'moved to inventory slot ' + str(moved[0]) if moved else 'not moved'}")
        ok = await guarded_write(ctx.bizhawk_ctx, writes + counter_writes, guards + counter_guards)
        if not ok:
            self._diag(f"_deliver_progressive_equipment({item_name!r}): guarded_write failed")
            return False
        self._apply_counter_text(counter_writes[0][1])
        self._counter_committed = True

        # The game can overwrite the inventory slot right after the write, so it is read back; on a mismatch the equip slot goes back to
        # the old item, so the retry moves it again, and the counter is rolled back.
        if moved is not None:
            slot, _writes, _guards, new_qty = moved
            verify_id, verify_qty = await read(ctx.bizhawk_ctx, [(ITEM_ID_BASE + slot, 1, DOMAIN), (ITEM_QTY_BASE + slot, 1, DOMAIN)])
            if verify_id[0] != old_id or verify_qty[0] != new_qty:
                self._diag(f"_deliver_progressive_equipment({item_name!r}): post-write mismatch at inventory slot {slot}")
                await write(ctx.bizhawk_ctx, [(addr, list(equip_bytes), DOMAIN)])
                await self._roll_back_counter(ctx)
                return False

        self.progressive_received[item_name] = count
        await display_message(ctx.bizhawk_ctx, f"Received {item_name} (tier {tier_number})!")
        return True

    async def _deliver_gella(self, ctx: "BizHawkClientContext", item_name: str, amount: int) -> bool:
        addr = GELLA_BASE
        current = (await read(ctx.bizhawk_ctx, [(addr, 4, DOMAIN)]))[0]
        new_total = int.from_bytes(current, "little") + amount
        new_bytes = new_total.to_bytes(4, "little")
        counter_writes, counter_guards = self._counter_ops(ctx, self.received_item_count + 1)
        ok = await guarded_write(
            ctx.bizhawk_ctx,
            [(addr, list(new_bytes), DOMAIN)] + counter_writes,
            [(addr, list(current), DOMAIN)] + counter_guards,
        )
        if ok:
            self._apply_counter_text(counter_writes[0][1])
            self._counter_committed = True
            await display_message(ctx.bizhawk_ctx, f"Received {item_name}!")
        return ok

    async def _deliver_general_item(self, ctx: "BizHawkClientContext", item_name: str) -> bool:
        item_id = GENERAL_ITEM_NAME_TO_ID[item_name]
        return await self._grant_general_item_id(ctx, item_id, item_name)

    @staticmethod
    def _plan_inventory_add(id_bytes, qty_bytes, item_id):
        """(slot, writes, guards, new quantity) that add one of item_id to general inventory, or None when every slot is held. The item stacks onto an
        existing slot with the same id, else takes the first empty slot (quantity 0)."""
        slot = next((i for i in range(INVENTORY_SLOT_COUNT) if id_bytes[i] == item_id and qty_bytes[i] != 0), None)
        if slot is None:
            # Searching from slot 0 matters: the game compacts held items into low slots, so high slots are not safer.
            slot = next((i for i in range(INVENTORY_SLOT_COUNT) if qty_bytes[i] == 0), None)
        if slot is None:
            return None
        new_qty = min(qty_bytes[slot] + 1, 255)
        writes = [(ITEM_ID_BASE + slot, [item_id], DOMAIN), (ITEM_QTY_BASE + slot, [new_qty], DOMAIN)]
        guards = [(ITEM_ID_BASE + slot, [id_bytes[slot]], DOMAIN), (ITEM_QTY_BASE + slot, [qty_bytes[slot]], DOMAIN)]
        return slot, writes, guards, new_qty

    async def _grant_general_item_id(self, ctx: "BizHawkClientContext", item_id: int, display_name: str) -> bool:
        """Adds one of item_id to general inventory, together with the counter advance. display_name is the name shown in the in-game message."""
        id_bytes, qty_bytes = await read(ctx.bizhawk_ctx, [
            (ITEM_ID_BASE, INVENTORY_SLOT_COUNT, DOMAIN),
            (ITEM_QTY_BASE, INVENTORY_SLOT_COUNT, DOMAIN),
        ])

        plan = self._plan_inventory_add(id_bytes, qty_bytes, item_id)
        if plan is None:
            await display_message(ctx.bizhawk_ctx, f"Could not deliver {display_name} (inventory full)")
            return False
        target_slot, add_writes, add_guards, new_qty = plan
        id_addr = ITEM_ID_BASE + target_slot
        qty_addr = ITEM_QTY_BASE + target_slot

        self._diag(
            f"_grant_general_item_id({display_name!r}, item_id={item_id}): choosing slot {target_slot} "
            f"({'existing stack' if id_bytes[target_slot] == item_id and qty_bytes[target_slot] != 0 else 'first free slot'}); "
            f"pre-write this slot reads id={id_bytes[target_slot]} qty={qty_bytes[target_slot]}"
        )

        counter_writes, counter_guards = self._counter_ops(ctx, self.received_item_count + 1)
        ok = await guarded_write(ctx.bizhawk_ctx, add_writes + counter_writes, add_guards + counter_guards)
        if ok:
            self._apply_counter_text(counter_writes[0][1])
            self._counter_committed = True
        else:
            self._diag(f"_grant_general_item_id({display_name!r}): guarded_write failed at slot {target_slot}")
            return False

        # The game can overwrite the slot right after the write, so the slot is read back; a mismatch rolls the counter back and retries the item.
        verify_id, verify_qty = await read(ctx.bizhawk_ctx, [(id_addr, 1, DOMAIN), (qty_addr, 1, DOMAIN)])
        if verify_id[0] != item_id or verify_qty[0] != new_qty:
            self._diag(
                f"_grant_general_item_id({display_name!r}): post-write mismatch at slot {target_slot}, "
                f"wrote id={item_id} qty={new_qty}, read back id={verify_id[0]} qty={verify_qty[0]}"
            )
            await self._roll_back_counter(ctx)
            return False

        await display_message(ctx.bizhawk_ctx, f"Received {display_name}!")
        return True
