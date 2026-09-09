from __future__ import annotations

from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from voynich.iiif import load_canvases, serializable_index
from voynich.ivtff import parse_ivtff


class YaleManifestTests(unittest.TestCase):
    def test_manifest_inventory_and_f1r(self) -> None:
        canvases = load_canvases(ROOT / "data/raw/iiif/yale-ms-408.json")
        document = parse_ivtff((ROOT / "data/raw/transcriptions/ZL3b-n.txt").read_bytes())
        valid_page_ids = {page.page_id for page in document.pages}
        index = serializable_index(canvases, valid_page_ids)
        self.assertEqual(len(canvases), 213)
        self.assertEqual(
            index["simple_folios"]["f1r"]["image_service_id"],
            "https://collections.library.yale.edu/iiif/2/1006076",
        )
        self.assertNotIn("fRos", index["simple_folios"])
        self.assertTrue(set(index["simple_folios"]).issubset(valid_page_ids))
        self.assertEqual(
            index["unmapped_simple_canvas_labels"],
            ["67r", "67v", "68r", "68v", "90r", "95v"],
        )


if __name__ == "__main__":
    unittest.main()
