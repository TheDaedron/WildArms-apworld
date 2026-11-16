import json
import os

from settings import get_settings
from worlds.Files import APProcedurePatch, APPatchExtension

USHASH = "19f6de83eb8b7525d7bf8eb27566ce30"


class WildArmsProcedurePatch(APProcedurePatch):
    game = "Wild Arms"
    hash = USHASH
    patch_file_ending = ".apwildarms"
    # The patched output expects both a .bin and a .cue, but we want the emulator to open the .cue file.
    result_file_ending = ".cue"

    procedure = [
        ("apply_seed", ["seed.json"]),
    ]

    @classmethod
    def get_source_data(cls) -> bytes:
        with open(get_settings().wildarms_settings.rom_file, "rb") as infile:
            return bytes(infile.read())

    def patch(self, target: str) -> None:
        # The base class writes the disc image to the .cue path. Move it to .bin, then write the .cue file.
        super().patch(target)

        bin_path = target[:-len(self.result_file_ending)] + ".bin"
        os.rename(target, bin_path)

        bin_name = os.path.basename(bin_path)
        cue_text = (
            f'FILE "{bin_name}" BINARY\n'
            "  TRACK 01 MODE2/2352\n"
            "    INDEX 01 00:00:00\n"
        )
        with open(target, "w", encoding="utf-8") as outfile:
            outfile.write(cue_text)


class WildArmsPatchExtension(APPatchExtension):
    game = "Wild Arms"

    @staticmethod
    def apply_seed(caller: WildArmsProcedurePatch, rom: bytes, seed_file: str) -> bytes:
        """Builds the patched disc from seed.json + the player's disc (`rom`). Patcher imported here to dodge a
        circular import."""
        from . import Patcher

        seed = json.loads(caller.get_file(seed_file).decode("utf-8"))
        if seed.get("format") != Patcher.SEED_FORMAT:
            raise RuntimeError(
                f"seed.json has format {seed.get('format')!r}, but this Wild Arms apworld only understands "
                f"format {Patcher.SEED_FORMAT}. Install the Wild Arms apworld version this patch was generated with.")
        installed_version, _ = Patcher.load_base_runs()
        if seed["base_version"] != installed_version:
            raise RuntimeError(
                f"This patch was generated with a different Wild Arms apworld version "
                f"(patch {seed['base_version'][:12]}, installed {installed_version[:12]}). "
                f"Install the same Wild Arms apworld version used to generate this patch.")
        edits = Patcher.compute_seed_edits(seed)
        disc = bytearray(rom)
        return bytes(Patcher.apply_edits_to_disc(disc, edits))
