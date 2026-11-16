"""
Mode 2 Form 1 sector EDC (CRC32) and ECC (P/Q parity) recomputation, so a patched MODE2/2352 sector passes the checksum check. Ported from WildArmsBelselkBash's CdRomEcc.cs and CdRomEccTables.cs.
"""
import json
import pkgutil

# pkgutil reads the file from inside a zipped .apworld as well as from a folder.
_tables = json.loads(pkgutil.get_data(__name__, "cdrom_ecc_tables.json"))
EDC_CRC_TABLE = _tables["edc_crc_table"]
L2SQ = _tables["l2sq"]

MASK32 = 0xFFFFFFFF


def crc32(data: bytes) -> int:
    result = 0
    for value in data:
        result = (EDC_CRC_TABLE[(result ^ value) & 0xFF] ^ (result >> 8)) & MASK32
    return result


def _encode_l2p(data: bytearray) -> bytearray:
    L2Raw = 0x800
    L2P = 43 * 2 * 2
    base_index = 0
    p_index = 4 + L2Raw + 4 + 8
    target_size = p_index + L2P
    new_data = bytearray(data) + bytearray(max(0, target_size - len(data)))
    for i in range(43):
        a = 0
        b = 0
        index = base_index
        for j in range(19, 43):
            a ^= L2SQ[j][new_data[index]]
            b ^= L2SQ[j][new_data[index + 1]]
            index += 2 * 43
        new_data[p_index] = (a >> 8) & 0xFF
        new_data[p_index + 43 * 2] = a & 0xFF
        new_data[p_index + 1] = (b >> 8) & 0xFF
        new_data[p_index + 43 * 2 + 1] = b & 0xFF
        base_index += 2
        p_index += 2
    return new_data


def _encode_l2q(data: bytearray) -> bytearray:
    L2Raw = 0x800
    L2P = 43 * 2 * 2
    L2Q = 26 * 2 * 2
    base_index = 0
    q_index = 4 + L2Raw + 4 + 8 + L2P
    mod_index = q_index
    target_size = q_index + L2Q
    new_data = bytearray(data) + bytearray(max(0, target_size - len(data)))
    for i in range(26):
        a = 0
        b = 0
        index = base_index
        for j in range(43):
            a ^= L2SQ[j][new_data[index]]
            b ^= L2SQ[j][new_data[index + 1]]
            index = (index + 2 * 44) % mod_index
        new_data[q_index] = (a >> 8) & 0xFF
        new_data[q_index + 26 * 2] = a & 0xFF
        new_data[q_index + 1] = (b >> 8) & 0xFF
        new_data[q_index + 26 * 2 + 1] = b & 0xFF
        base_index += 2 * 43
        q_index += 2
    return new_data


def get_edc_ecc(data: bytes):
    """(edc: 4 bytes, ecc: 0x114 bytes) freshly computed from data[0x10:0x818] of a full 0x930 (2352) byte
    raw sector (sync+header+subheader+userdata+...)."""
    assert len(data) >= 0x818, "need at least sync+header+subheader+userdata"
    bytes_to_hash = bytes(data[0x10:0x818])
    edc_val = crc32(bytes_to_hash)

    # The ECC covers the EDC bytes, so the new EDC goes in before the ECC range is read.
    new_data = bytearray(data[:0x818]) + edc_val.to_bytes(4, "little")

    data_to_encode = bytearray(0x820)
    data_to_encode[4:4 + (0x81C - 0x10)] = new_data[0x10:0x81C]

    temp = _encode_l2p(data_to_encode)
    temp = _encode_l2q(temp)

    ecc = bytes(temp[len(temp) - 0x114:])
    edc = edc_val.to_bytes(4, "little")
    return edc, ecc


def patch_sector_user_data(sector: bytearray, new_user_data: bytes) -> bytearray:
    """sector with its user data replaced by new_user_data and EDC/ECC recomputed to match, leaving sync/header/subheader untouched."""
    assert len(sector) == 2352
    assert len(new_user_data) == 2048
    out = bytearray(sector)
    out[0x18:0x818] = new_user_data
    edc, ecc = get_edc_ecc(bytes(out))
    out[0x818:0x81C] = edc
    out[0x81C:0x930] = ecc
    return out
