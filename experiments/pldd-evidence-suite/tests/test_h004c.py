from __future__ import annotations

from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import random
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from voynich.h004c import (
    SEED,
    _shuffle_joint_tuples,
    build_discovery_manifest,
    build_zg_skeleton,
    canonical_manifest_bytes,
    render_zg_discovery_markdown,
    run_zg_discovery,
    skeleton_inventory,
    sta_family_slots,
)
from voynich.ivtff import Document, parse_ivtff


def _document(lines: list[str], *, page_id: str = "f1r") -> Document:
    body = [
        "#=IVTFF STA1 2.0 D",
        f"<{page_id}> <! $I=H $L=A $H=1>",
        *lines,
    ]
    return parse_ivtff(("\n".join(body) + "\n").encode("ascii"))


def _locus(number: int, components: list[str], *, markers: tuple[str, str] = ("", "")) -> str:
    return (
        f"<f1r.{number},+P0> "
        f"{markers[0]}{'.'.join(components)}{markers[1]}"
    )


class H004CSlotTests(unittest.TestCase):
    def test_sta_families_preserve_order_and_reject_uncertainty(self) -> None:
        slots = sta_family_slots(
            "D1A1Q2<->A1G1.<!inert>A1H1.[A1:B1].A1,Z1.?.{B1C2}"
        )
        self.assertEqual(len(slots), 7)
        self.assertEqual([slot.family for slot in slots[:3]], ["DAQ", "AG", "AH"])
        self.assertEqual(slots[3].reasons, ("alternative_reading", "malformed_sta_or_residue"))
        self.assertIn("uncertain_space", slots[4].reasons)
        self.assertIn("unknown_sta_glyph", slots[4].reasons)
        self.assertIn("unreadable_glyph", slots[5].reasons)
        self.assertEqual(slots[6].family, "BC")

    def test_malformed_ligature_is_retained_as_an_invalid_slot(self) -> None:
        slots = sta_family_slots("A1.{B1.C1")
        self.assertEqual(len(slots), 3)
        self.assertEqual(slots[0].family, "A")
        self.assertIsNone(slots[1].family)
        self.assertIn("malformed_ligature", slots[1].reasons)


class H004CSkeletonTests(unittest.TestCase):
    def test_exact_ordinal_skeleton_freezes_preceding_ten_ids(self) -> None:
        components = [f"{chr(65 + index)}1" for index in range(12)]
        zl = _document([_locus(1, components, markers=("<%>", "<$>"))])
        gc = _document([_locus(1, components, markers=("<%>", "<$>"))])
        skeleton = build_zg_skeleton(zl, gc)

        self.assertEqual(len(skeleton.positions), 12)
        self.assertEqual(len(skeleton.targets), 2)
        first = skeleton.targets[0]
        self.assertEqual(skeleton.positions[first.position].position_id, ("f1r", 1, 10))
        self.assertEqual(
            [skeleton.positions[index].position_id for index in first.context],
            [("f1r", 1, index) for index in range(10)],
        )

    def test_invalid_slot_retains_ordinal_and_resets_context(self) -> None:
        before = ["A1"] * 5
        after = ["B1"] * 11
        zl_components = before + ["C1,D1"] + after
        gc_components = before + ["C1"] + after
        zl = _document([_locus(1, zl_components)])
        gc = _document([_locus(1, gc_components)])
        skeleton = build_zg_skeleton(zl, gc)

        invalid = skeleton.positions[5]
        self.assertEqual(invalid.position_id, ("f1r", 1, 5))
        self.assertFalse(invalid.valid)
        self.assertEqual(len(skeleton.targets), 1)
        target = skeleton.targets[0]
        self.assertEqual(skeleton.positions[target.position].position_id, ("f1r", 1, 16))
        self.assertEqual(
            [skeleton.positions[index].position_id[2] for index in target.context],
            list(range(6, 16)),
        )

    def test_component_count_mismatch_is_a_hard_gap(self) -> None:
        twelve = ["A1"] * 12
        eleven = ["A1"] * 11
        zl = _document([_locus(1, twelve), _locus(2, twelve), _locus(3, twelve)])
        gc = _document([_locus(1, twelve), _locus(2, eleven), _locus(3, twelve)])
        skeleton = build_zg_skeleton(zl, gc)

        self.assertEqual(len(skeleton.targets), 4)
        self.assertTrue(
            any(
                event["reason"] == "component_count_mismatch"
                and event["locus_number"] == 2
                for event in skeleton.exclusions
            )
        )
        for target in skeleton.targets:
            target_locus = skeleton.positions[target.position].position_id[1]
            self.assertTrue(
                all(
                    skeleton.positions[index].position_id[1] == target_locus
                    for index in target.context
                )
            )

    def test_paragraph_boundary_disagreement_excludes_disputed_positions(self) -> None:
        components = ["A1"] * 12
        zl = _document([_locus(1, components, markers=("<%>", "<$>"))])
        gc = _document([_locus(1, components)])
        skeleton = build_zg_skeleton(zl, gc)

        self.assertFalse(skeleton.positions[0].valid)
        self.assertFalse(skeleton.positions[-1].valid)
        self.assertEqual(len(skeleton.targets), 0)
        self.assertEqual(
            Counter(event["reason"] for event in skeleton.exclusions),
            Counter(
                {
                    "paragraph_start_disagreement": 1,
                    "paragraph_end_disagreement": 1,
                }
            ),
        )

    def test_joint_shuffle_preserves_each_cell_tuple_multiset(self) -> None:
        components_zl = ["A1", "B1"] * 6
        components_gc = ["C1", "D1"] * 6
        skeleton = build_zg_skeleton(
            _document([_locus(1, components_zl)]),
            _document([_locus(1, components_gc)]),
        )
        base = [(position.zl_family, position.gc_family) for position in skeleton.positions]
        shuffled = _shuffle_joint_tuples(base, skeleton.cells, random.Random(SEED))
        for _, indexes in skeleton.cells:
            self.assertEqual(
                Counter(base[index] for index in indexes),
                Counter(shuffled[index] for index in indexes),
            )
        self.assertTrue(all(pair in {("A", "C"), ("B", "D")} for pair in shuffled))

    def test_small_permutation_run_is_deterministic(self) -> None:
        components_zl = ["A1", "B1", "C1"] * 5
        components_gc = ["A1", "D1", "C1"] * 5
        skeleton = build_zg_skeleton(
            _document([_locus(1, components_zl)]),
            _document([_locus(1, components_gc)]),
        )
        first = run_zg_discovery(skeleton, permutations=3)
        second = run_zg_discovery(skeleton, permutations=3)
        self.assertEqual(first, second)
        self.assertFalse(first["pre_it_zg_gate_met"])


class H004CPinnedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.zl = parse_ivtff(
            (ROOT / "data/raw/transcriptions/sta1/ZL3b.txt").read_bytes()
        )
        cls.gc = parse_ivtff(
            (ROOT / "data/raw/transcriptions/sta1/GC2a_0.txt").read_bytes()
        )

    def test_pinned_strict_inventory_fails_frozen_breadth(self) -> None:
        inventory = skeleton_inventory(build_zg_skeleton(self.zl, self.gc))
        self.assertEqual(inventory["pages_with_targets"], 38)
        self.assertEqual(inventory["targets"], 648)
        self.assertEqual(inventory["currier_pages"], {"A": 21, "B": 17})
        self.assertEqual(inventory["currier_targets"], {"A": 174, "B": 474})
        self.assertEqual(inventory["movable_targets"], 614)

    def test_manifest_is_machine_readable_and_explicitly_pre_it(self) -> None:
        protocol_path = ROOT / "notes/hypotheses/H004C-cross-transcription-sta.md"
        manifest = build_discovery_manifest(
            self.zl,
            self.gc,
            protocol_text=protocol_path.read_text(encoding="utf-8"),
            protocol_path=str(protocol_path),
            permutations=1,
        )
        reparsed = json.loads(canonical_manifest_bytes(manifest))
        reserved_it = reparsed["inputs"]["reserved_it_sta1"]
        self.assertFalse(reserved_it["opened_by_this_analysis"])
        self.assertFalse(reserved_it["parsed_by_this_analysis"])
        self.assertFalse(reserved_it["projected_by_this_analysis"])
        self.assertEqual(len(reparsed["skeleton"]["targets"]), 648)
        self.assertFalse(reparsed["zg_discovery"]["pre_it_zg_gate_met"])
        markdown = render_zg_discovery_markdown(reparsed, "0" * 64)
        self.assertIn("did not load IT bytes or project IT event data", markdown)
        self.assertIn("prior integrity/header inspection", markdown)

    def test_production_artifacts_preserve_full_run_and_audit_chronology(self) -> None:
        json_path = ROOT / "results/h004c-zg-discovery-manifest.json"
        markdown_path = ROOT / "results/h004c-zg-discovery.md"
        sidecar_path = ROOT / "results/h004c-zg-discovery-manifest.sha256.txt"
        manifest_bytes = json_path.read_bytes()
        manifest_hash = sha256(manifest_bytes).hexdigest()
        manifest = json.loads(manifest_bytes)

        self.assertEqual(
            sidecar_path.read_text(encoding="ascii"),
            f"{manifest_hash}  {json_path.name}\n",
        )
        self.assertEqual(
            markdown_path.read_text(encoding="utf-8"),
            render_zg_discovery_markdown(manifest, manifest_hash),
        )
        discovery = manifest["zg_discovery"]
        self.assertEqual(discovery["permutations_run"], 9999)
        self.assertFalse(discovery["breadth_gate_met"])
        self.assertFalse(discovery["effect_gate_met"])
        self.assertFalse(discovery["it_event_projection_authorized"])
        self.assertAlmostEqual(
            discovery["witness_results"]["ZL"]["metrics"][
                "C_exact_or_one_edit"
            ]["delta"],
            0.01485529,
        )
        self.assertAlmostEqual(
            discovery["witness_results"]["GC"]["metrics"][
                "U_one_edit_without_exact"
            ]["delta"],
            -0.01243892,
        )
        self.assertTrue(
            manifest["execution_audit"][
                "zg_permutations_completed_after_breadth_failure"
            ]
        )


if __name__ == "__main__":
    unittest.main()
