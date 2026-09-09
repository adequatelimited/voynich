from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class PinnedArtifactHashes(unittest.TestCase):
    EXPECTED = {
        "data/raw/transcriptions/ZL3b-n.txt": "bf5b6d4ac1e3a51b1847a9c388318d609020441ccd56984c901c32b09beccafc",
        "data/raw/transcriptions/GC2a-n.txt": "b09570cb6c993bc2d87134d115e60a978650a8a6495483ddbb1f6005a586096f",
        "data/raw/transcriptions/IT2a-n.txt": "7f27a8b0feed8f6de0a99900df6bf912dd1d295c38e5f830bac8b41c3f536fb5",
        "data/raw/transcriptions/RF1b-e.txt": "e7d3238e35743e06c63367a933909ec37b1e2de7ada3a1b449447eafa1918782",
        "data/raw/transcriptions/RF1b-er.txt": "eb857a1f353b18983fbc25b954e1bbce227a26d99cefabfda9206ff9b57644d2",
        "data/raw/transcriptions/sta1/ZL3b.txt": "8438ba1c45f47fe1d06b5262cbcdf60ce69158a0edbd4dd802612896f3217e2a",
        "data/raw/transcriptions/sta1/GC2a_0.txt": "b39cabbd9c8c8a098bfa9f76e0649291d17d77e1cb4fb0a3351ff7bdc832ace3",
        "data/raw/transcriptions/sta1/IT2a.txt": "215f2d05690828c00bd4ae00d6201df31050adcd81601343b142ae91b9dfeee4",
        "data/raw/iiif/yale-ms-408.json": "c1f12b6ad256b91e1b5c8015c2107de1c2ff24e573f4524c53e8f4004bccfc23",
        "data/raw/external/naibbe-f2675ec/LICENSE": "e8fb5c1110aaa38618eab2013d1e7c5cae343efd21ea9859478df4930f7746bc",
        "data/raw/external/naibbe-f2675ec/README.md": "b9e78e849a3478341d1c3167b7c3ae960e18f57b4857a0297d296adfe480ec99",
        "data/raw/external/naibbe-f2675ec/decrypt_naibbe.py": "1c18514bbaba914989f1961f41a3930b7c1afe81d6db37b07b1dd7d9e6ea3b49",
        "data/raw/external/naibbe-f2675ec/naibbe.py": "3f5e353d2c50f4e6a6b81567ca31cee4f0537a490b6346d054d26661648a6003",
        "data/raw/external/naibbe-f2675ec/references/naibbe_tables.csv": "4e7cfd54b7ec66515d39a51e11ec97e8e19b643b0b189124eebc3982e707dcec",
        "data/raw/external/naibbe-f2675ec/encrypted/examples/endofpaper.txt": "475055654de0049675c26de7550a37426045e4a57ab533cb97677b390e4764d7",
        "data/raw/external/naibbe-f2675ec/decrypted/examples/endofpaper_decrypted.txt": "c89ca7e66548d76728d968a741296405a271000534f6946d76737fafe7a288c6",
        "data/raw/external/naibbe-f2675ec/encrypted/examples/gallic_naibbe.txt": "c813aa51a843a7c399c4707b000155ba615b00ffe34276054a6e2838cfcc8ae2",
        "data/raw/external/naibbe-f2675ec/decrypted/examples/gallic_decrypted.txt": "c439209d7a3f5492e0adb68505316392ea8b5c25ec7b53605c2d43d27d85ce68",
        "data/raw/external/naibbe-f2675ec/encrypted/nathist_output_ciphertext.txt": "9cdf2de12f371ac7efdb2e78713f229ada508286c1717758184238a59cd64326",
        "data/raw/external/naibbe-f2675ec/decrypted/nathist_output_ciphertext_decrypted.txt": "852d1ad67f82d6472c8ef1d99bfa12c62f76f3d37be2623a131f47232b753ca2",
    }

    def test_all_raw_artifact_hashes(self) -> None:
        for relative_path, expected in self.EXPECTED.items():
            with self.subTest(path=relative_path):
                self.assertEqual(sha256((ROOT / relative_path).read_bytes()).hexdigest(), expected)



if __name__ == "__main__":
    unittest.main()
