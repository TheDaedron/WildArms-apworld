"""
generate_output() calls build_seed_dict()/reward_ids_from_world() to write seed.json.
Rom.py's apply_seed() calls compute_seed_edits()/apply_edits_to_disc() to turn seed.json plus a disc into patched
bytes.
"""
import hashlib
import json
import pkgutil
import struct
import zlib
from typing import Optional, Tuple

from .cdrom_ecc import patch_sector_user_data
from .data.items_table import ITEM_NAME_TO_ID

# pkgutil works inside a zipped .apworld. load_base_runs() combines these digests in this order.
_BASE_EDITS_RESOURCES = ("data/patch/scripts.bin", "data/patch/rewards.bin", "data/patch/exe.bin")
_DATA_RESOURCE_DIR = "data"

_SECTOR_RAW = 2352
_HEADER = 0x18
_SECTOR_DATA = 2048

EXP_MAX = 0xffff
GELLA_MAX = 0xffff
# The largest value each scaled enemy stat is raised to. 
# PRY is a percentage, the maximum should be 99 so the party can have a chance to hit.
HP_MAX = 0xFFFF
MP_MAX = 0xFFF
ATP_MAX = 0xFFF
DFP_MAX = 0xFFF
MGR_MAX = 0xFFF
SOR_MAX = 0xFFF
RES_MAX = 0xFFF
PRY_MAX = 0x63
ENEMY_STAT_MAX = {"hp": HP_MAX, "mp": MP_MAX, "atp": ATP_MAX, "dfp": DFP_MAX, "mgr": MGR_MAX, "sor": SOR_MAX, "res": RES_MAX, "pry": PRY_MAX}
AP_ITEM_ID = 21
GELLA_ITEM_ID = 93
FAST_DRAW_HINT_TOOLTIP = "Hint from ????"  # the tooltip of every unmastered Fast Draw, when the Option is set.

# Bump if seed.json's shape changes.
SEED_FORMAT = 1


# Slot name record in runner names 3 and 4 of the save table.
# Name 3 holds the record format, the first 12 hex digits of the disc changes' version and a 4-hex checksum of the
# version text and the slot name
# Name 4 holds the slot name. Each name is up to 17 printable characters (Archipelago enforced restriction) padded with
# spaces, then 0x00.
RUNNER_NAME_SIZE = 18
RECORD_FORMAT = "1"
VERSION_TEXT_LENGTH = 12
MAX_SLOT_NAME_LENGTH = RUNNER_NAME_SIZE - 1


def _slot_checksum(version_text: str, slot_name: str) -> str:
    return f"{zlib.crc32((version_text + slot_name).encode('ascii')) & 0xFFFF:04X}"


def _padded(text: str) -> bytes:
    return text.ljust(RUNNER_NAME_SIZE - 1).encode("ascii") + b"\x00"


def _is_printable_ascii(text: str) -> bool:
    return all(0x20 <= ord(c) <= 0x7E for c in text)


def slot_record_bytes(base_version: str, slot_name: str) -> Tuple[bytes, bytes]:
    """The 18-byte contents of name 3 and name 4. Raises ValueError for a slot name the table cannot hold."""
    if not slot_name or len(slot_name) > MAX_SLOT_NAME_LENGTH or not _is_printable_ascii(slot_name):
        raise ValueError(
            f"The slot name {slot_name!r} cannot be stored on the disc: "
            f"it must be 1 to {MAX_SLOT_NAME_LENGTH} printable ASCII characters.")
    version_text = RECORD_FORMAT + base_version[:VERSION_TEXT_LENGTH]
    return _padded(version_text + _slot_checksum(version_text, slot_name)), _padded(slot_name)


def parse_slot_record(version_name: bytes, slot_name: bytes) -> Optional[Tuple[str, str]]:
    """(slot name, 12-hex version) from the raw bytes of names 3 and 4, or None when they are not a valid record."""
    try:
        version_field = version_name[:RUNNER_NAME_SIZE - 1].decode("ascii")
        slot = slot_name[:RUNNER_NAME_SIZE - 1].split(b"\x00")[0].decode("ascii").rstrip(" ")
    except UnicodeDecodeError:
        return None
    version_text = version_field[:1 + VERSION_TEXT_LENGTH]
    if not version_field.startswith(RECORD_FORMAT) or not slot or not _is_printable_ascii(slot):
        return None
    if version_field[1 + VERSION_TEXT_LENGTH:] != _slot_checksum(version_text, slot):
        return None
    return slot, version_text[1:]


def _load_json(name, base_version):
    data = json.loads(pkgutil.get_data(__name__, f"{_DATA_RESOURCE_DIR}/{name}").decode("utf-8"))
    if data["base_version"] != base_version:
        raise RuntimeError(f"{name} does not match the packaged disc changes ({data['base_version'][:12]} vs {base_version[:12]}); reinstall the apworld")
    return data


def load_base_runs():
    """(version, [(abs_offset, bytes), ...]), merged from the three patch files. Each file is a
    32-byte digest then its payload; raises if a payload doesn't match the digest. version is sha256
    of all three digests, always in this order."""
    digests = []
    runs = []
    for resource in _BASE_EDITS_RESOURCES:
        blob = pkgutil.get_data(__name__, resource)
        digest, payload = blob[:32], blob[32:]
        if hashlib.sha256(payload).digest() != digest:
            raise RuntimeError(f"{resource} is damaged; reinstall the apworld")
        digests.append(digest)
        pos = 0
        while pos < len(payload):
            abs_offset, length = struct.unpack_from("<IH", payload, pos)
            pos += 6
            runs.append((abs_offset, payload[pos:pos + length]))
            pos += length
    version = hashlib.sha256(b"".join(digests)).hexdigest()
    return version, runs


def resolve_reward_id(item_name, item_player, slot):
    """The reward id written for a location: an item keeps its own id when it belongs to this slot, a Gella tier shows
    the Gella icon, anything else shows the generic AP item. Always an icon-safe value, since this is also what the on-
    ground sprite reads directly as an item id with no safety net. Whether a same-slot ARM/Fast Draw/Force/Progressive/
    Spell/Tool item shows its name is handled entirely separately."""
    if item_player == slot and item_name in ITEM_NAME_TO_ID:
        return ITEM_NAME_TO_ID[item_name]
    if item_name is not None and item_name.endswith(" Gella"):
        return GELLA_ITEM_ID
    return AP_ITEM_ID


def reward_ids_from_world(world):
    """(reward_ids, local_names) from the filled multiworld.
    reward_ids: location name -> reward id (locations with no item are left out), always a value from
    resolve_reward_id().
    local_names: location name -> buffer text, for every location whose var[1] buffer is fully covered
    (local_names.json's "buffers" vs "copy_counts"). The stripped display name for a same-slot ARM/Fast Draw/Force/
    Progressive/Spell/Tool item (local_named_item_names, from local_names.json's "item_names"), otherwise the literal
    "AP Item" whenever resolve_reward_id() resolved to the generic placeholder (AP_ITEM_ID). A Gella-tier item (local
    or not) resolves to GELLA_ITEM_ID instead, so it is deliberately left out. It should never show generic text.
    compute_seed_edits() packs each one into that location's map's shared text pool AND flips its own wrapper's
    var[1] literal on, which is what makes item_grant show it."""
    from .Locations import location_data

    version, _ = load_base_runs()
    local_names_data = _load_json("local_names.json", version)
    local_named_item_names = local_names_data["item_names"]
    local_name_buffers = local_names_data["buffers"]
    copy_counts = local_names_data["copy_counts"]

    reward_ids, local_names = {}, {}
    for name in location_data:
        item = world.multiworld.get_location(name, world.player).item
        if item is None:
            continue
        reward_id = resolve_reward_id(item.name, item.player, world.player)
        reward_ids[name] = reward_id
        if len(local_name_buffers.get(name, [])) < copy_counts.get(name, 0):
            continue
        if item.player == world.player and item.name in local_named_item_names:
            local_names[name] = local_named_item_names[item.name]
        elif reward_id == AP_ITEM_ID:
            local_names[name] = "AP Item"
    return reward_ids, local_names


def _set_bytes(edits, offsets, data):
    if len(offsets) != len(data):
        raise ValueError(f"{len(offsets)} offsets for {len(data)} bytes")
    for off, b in zip(offsets, data):
        edits[off] = b


def _expand_runs(runs):
    """Flat, ascending list of absolute offsets from [[start, length], ...]. A chunk can be more than one run when it
    straddles a CD sector's 280-byte EDC/ECC/spare gap."""
    return [start + i for start, length in runs for i in range(length)]


def _u16(start):
    """The 2 absolute offsets of a little-endian u16 write, given its low byte's own offset."""
    return [start, start + 1]


def compute_seed_edits(seed):
    """The base bins plus every seed-specific write, as {abs_offset: byte}. Local names get packed as plain ASCII into
    each map's shared text pool. The WA1 charset matches ASCII for every character we use."""
    options = seed.get("options", {})
    pleasing_garden_fixed = options["pleasing_garden_fixed"]
    exp_multiplier = options["exp_multiplier"]
    gella_multiplier = options["gella_multiplier"]
    enemy_difficulty = options.get("enemy_difficulty", 100)
    buffed_apples = options.get("buffed_apples", 1)
    mastered_fast_draws = options.get("mastered_fast_draws", True)
    open_world = options.get("open_world", False)
    game_options = options.get("game_options") or {}
    slot_name = seed.get("slot_name")
    reward_ids = seed.get("reward_ids") or {}
    local_names = seed.get("local_names") or {}

    version, base_runs = load_base_runs()
    reward_targets = _load_json("reward_targets.json", version)["locations"]
    local_names_data = _load_json("local_names.json", version)
    local_name_buffers = local_names_data["buffers"]
    local_name_pools = local_names_data["pools"]
    enemies = _load_json("enemy_tables.json", version)["enemies"]
    offsets = _load_json("patcher_offsets.json", version)

    # Every field above ships as compactly as its shape allows (a fixed-length u16 write keeps only its low byte's
    # offset, a longer run is run-length encoded). Expand each back to the flat offset lists the rest of this function
    # already works with.
    for copies in local_name_buffers.values():
        for copy in copies:
            copy["var1"] = _u16(copy["var1"])
    for chunks in local_name_pools.values():
        for chunk in chunks:
            chunk["offsets"] = _expand_runs(chunk["runs"])
    for enemy in enemies:
        for stat, starts in enemy["stat_offsets"].items():
            enemy["stat_offsets"][stat] = [_u16(start) for start in starts]
    offsets["save_identity"] = {name: _expand_runs(runs) for name, runs in offsets["save_identity"].items()}
    offsets["pleasing_garden"]["offsets"] = _expand_runs(offsets["pleasing_garden"]["runs"])
    offsets["open_world"]["offsets"] = _expand_runs(offsets["open_world"]["runs"])
    offsets["fast_draw_hint_text"] = [_expand_runs(runs) for runs in offsets["fast_draw_hint_text"]]

    edits = {}
    # base bins first, everything below just overwrites it in the same dict
    for abs_offset, data in base_runs:
        for i, b in enumerate(data):
            edits[abs_offset + i] = b

    if slot_name is not None:
        identity_offsets = offsets["save_identity"]
        version_name, slot_name_field = slot_record_bytes(version, slot_name)
        _set_bytes(edits, identity_offsets["version_name"], version_name)
        _set_bytes(edits, identity_offsets["slot_name"], slot_name_field)

    if not mastered_fast_draws:
        for tooltip_offsets in offsets["fast_draw_hint_text"]:
            if len(FAST_DRAW_HINT_TOOLTIP) > len(tooltip_offsets):
                raise ValueError(f"{FAST_DRAW_HINT_TOOLTIP!r} does not fit in a {len(tooltip_offsets)}-byte tooltip.")
            # Padded with spaces: the strings are stored back to back, so the terminator and the length stay as they were.
            _set_bytes(edits, tooltip_offsets, FAST_DRAW_HINT_TOOLTIP.ljust(len(tooltip_offsets)).encode("ascii"))

    for stat_field_low_byte in offsets["buffed_apples"]["stat_fields"]:
        _set_bytes(edits, _u16(stat_field_low_byte), struct.pack("<H", buffed_apples))
    for digit_offset in offsets["buffed_apples"]["tooltip_digits"]:
        _set_bytes(edits, [digit_offset], str(buffed_apples).encode("ascii"))

    if pleasing_garden_fixed:
        _set_bytes(edits, offsets["pleasing_garden"]["offsets"], bytes.fromhex(offsets["pleasing_garden"]["bytes"]))

    if open_world:
        _set_bytes(edits, offsets["open_world"]["offsets"], bytes.fromhex(offsets["open_world"]["bytes"]))

    for name, value in (game_options or {}).items():
        _set_bytes(edits, [offsets["game_options"][name]], bytes([value]))

    for enemy in enemies:
        # Modifies the XP and Gella values according to player settings.
        new_xp = min(enemy["xp"] * exp_multiplier, EXP_MAX)
        _set_bytes(edits, enemy["stat_offsets"]["xp"][0], struct.pack("<H", new_xp))
        new_gella = min(enemy["gella"] * gella_multiplier, GELLA_MAX)
        _set_bytes(edits, enemy["stat_offsets"]["gella"][0], struct.pack("<H", new_gella))

        # Modifies the enemy stat values according to the player settings. enemy_difficulty is a percentage
        # 100 = 1x of vanilla, 150 = 1.5x of vanilla.
        for stat, max_value in ENEMY_STAT_MAX.items():
            if enemy[stat] == 0:
                continue
            new_value = min(max(enemy[stat] * enemy_difficulty // 100, 1), max_value)
            for offsets_of_field in enemy["stat_offsets"][stat]:
                _set_bytes(edits, offsets_of_field, struct.pack("<H", new_value))

    for location_name, reward_id in reward_ids.items():
        for write_start in reward_targets.get(location_name, []):
            _set_bytes(edits, _u16(write_start), struct.pack("<H", reward_id))

    # No container, grant, or trap chest gets a pre-reserved buffer: every local-name-capable map shares one tightly-
    # packed text pool (local_names.json's "pools"), built from whatever free space every wrapper on that map actually
    # left, and every enabled name on that map is packed into it back to back here, at the one point a generation
    # knows which objects need a name and how long each one's text really is. A trap chest's own stub already points at
    # its shared str-variant unconditionally (structural, seed-independent), so its copy here needs nothing beyond the
    # plain pooled "var1" write every other copy already gets.
    pooled_by_map = {}
    for location_name, display_name in (local_names or {}).items():
        data = display_name.encode("ascii") + b"\x00"
        for copy in local_name_buffers.get(location_name, []):
            pooled_by_map.setdefault(copy["map_number"], []).append((copy["var1"], data))

    for map_number, items in pooled_by_map.items():
        # Biggest chunk first (always the magicblock2 leftover) so names land sequentially in that one chunk.
        chunks = sorted(local_name_pools.get(str(map_number), []), key=lambda c: -len(c["offsets"]))
        chunk_used = [0] * len(chunks)
        for var1_offsets, data in items:
            for chunk_index, chunk in enumerate(chunks):
                start = chunk_used[chunk_index]
                # Address 0 is the exact sentinel the native var[1] dispatch reads as "no name". A chunk whose script-
                # address start sits within 0xFFFF bytes of the next 64K boundary can wrap to an in-use address to
                # 0 here, which would show the generic placeholder even though the text itself packed correctly right
                # next to it.
                if (chunk["start"] + start) & 0xFFFF == 0:
                    start += 1
                remaining = len(chunk["offsets"]) - start
                if remaining < len(data):
                    continue
                _set_bytes(edits, chunk["offsets"][start:start + len(data)], data)
                computed_addr = (chunk["start"] + start) & 0xFFFF
                _set_bytes(edits, var1_offsets, struct.pack("<H", computed_addr))
                chunk_used[chunk_index] = start + len(data)
                break

    return edits


def apply_edits_to_disc(disc, edits):
    """Applies `edits` ({abs_offset: byte}) to `disc` in place, recomputing EDC/ECC for each sector
    that actually changed. Raises if an edit falls outside a sector's user-data window."""
    touched_sectors = {}
    for abs_offset, b in edits.items():
        sector_idx, off_in_sector = divmod(abs_offset, _SECTOR_RAW)
        if not (_HEADER <= off_in_sector < _HEADER + _SECTOR_DATA):
            raise ValueError(f"seed edit at {abs_offset:#x} lands outside a sector's user data")
        if sector_idx not in touched_sectors:
            sector_start = sector_idx * _SECTOR_RAW
            touched_sectors[sector_idx] = bytes(disc[sector_start:sector_start + _SECTOR_RAW])
        disc[abs_offset] = b

    for sector_idx, original_sector in touched_sectors.items():
        sector_start = sector_idx * _SECTOR_RAW
        new_user = bytes(disc[sector_start + _HEADER:sector_start + _HEADER + _SECTOR_DATA])
        if new_user == original_sector[_HEADER:_HEADER + _SECTOR_DATA]:
            continue  # nothing actually changed in this sector
        disc[sector_start:sector_start + _SECTOR_RAW] = patch_sector_user_data(bytearray(original_sector), new_user)

    return disc


def build_seed_dict(pleasing_garden_fixed, exp_multiplier, gella_multiplier, reward_ids, player_name,
                    game_options=None, mastered_fast_draws=True, enemy_difficulty=100, open_world=False,
                    local_names=None, buffed_apples=1):
    """Builds the seed.json dict Rom.py's apply_seed() reads back every per-player choice reward_ids/local_names come
    straight from reward_ids_from_world(). base_version is what catches a mismatched apworld install at apply time."""
    version, _ = load_base_runs()
    return {
        "format": SEED_FORMAT,
        "base_version": version,
        "slot_name": player_name,
        "options": {
            "pleasing_garden_fixed": pleasing_garden_fixed,
            "exp_multiplier": exp_multiplier,
            "gella_multiplier": gella_multiplier,
            "enemy_difficulty": enemy_difficulty,
            "buffed_apples": buffed_apples,
            "mastered_fast_draws": mastered_fast_draws,
            "open_world": open_world,
            "game_options": game_options or {},
        },
        "reward_ids": reward_ids or {},
        "local_names": local_names or {},
    }
