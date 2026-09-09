# Data provenance

The raw inputs below were retrieved 2026-07-09. They are pinned because their source URLs may be updated in place.

| Local file | Role | Source | SHA-256 |
|---|---|---|---|
| `raw/transcriptions/ZL3b-n.txt` | Primary scholarly transliteration; extended EVA, IVTFF 2.0, version 3b (2025-05-13) | <https://www.voynich.nu/data/ZL3b-n.txt> | `bf5b6d4ac1e3a51b1847a9c388318d609020441ccd56984c901c32b09beccafc` |
| `raw/transcriptions/GC2a-n.txt` | Independent v101 transcription audit | <https://www.voynich.nu/data/GC2a-n.txt> | `b09570cb6c993bc2d87134d115e60a978650a8a6495483ddbb1f6005a586096f` |
| `raw/transcriptions/IT2a-n.txt` | Historical Takahashi/LSI comparison, not the current Takahashi HTML | <https://www.voynich.nu/data/IT2a-n.txt> | `7f27a8b0feed8f6de0a99900df6bf912dd1d295c38e5f830bac8b41c3f536fb5` |
| `raw/transcriptions/RF1b-e.txt` | Derived ZL+GC reference in full extended EVA; not independent evidence | <https://www.voynich.nu/data/RF1b-e.txt> | `e7d3238e35743e06c63367a933909ec37b1e2de7ada3a1b449447eafa1918782` |
| `raw/transcriptions/RF1b-er.txt` | Derived reduced/basic-EVA approximation; retained only for comparison | <https://www.voynich.nu/data/RF1b-er.txt> | `eb857a1f353b18983fbc25b954e1bbce227a26d99cefabfda9206ff9b57644d2` |
| `raw/transcriptions/sta1/ZL3b.txt` | ZL glyph content converted to STA1 without intentional glyph-content loss; source comments are omitted | <https://www.voynich.nu/data/sta/ZL3b.txt> | `8438ba1c45f47fe1d06b5262cbcdf60ce69158a0edbd4dd802612896f3217e2a` |
| `raw/transcriptions/sta1/GC2a_0.txt` | GC converted to STA1 level 0 for cross-transcriber alignment | <https://www.voynich.nu/data/sta/GC2a_0.txt> | `b39cabbd9c8c8a098bfa9f76e0649291d17d77e1cb4fb0a3351ff7bdc832ace3` |
| `raw/transcriptions/sta1/IT2a.txt` | Historical IT comparison transliteration converted to STA1 level 0; reserved as a third-witness check | <https://www.voynich.nu/data/sta/IT2a.txt> | `215f2d05690828c00bd4ae00d6201df31050adcd81601343b142ae91b9dfeee4` |
| `raw/iiif/yale-ms-408.json` | Yale IIIF Presentation 3 image inventory, 213 canvases | <https://collections.library.yale.edu/manifests/2002046> | `c1f12b6ad256b91e1b5c8015c2107de1c2ff24e573f4524c53e8f4004bccfc23` |

## H005 external source-claim pages

| Source | Retrieved | Page update | Retrieved-byte SHA-256 |
|---|---|---|---|
| <https://voynich.nu/q15/index.html> | 2026-07-10 | 2025-06-15 | `25a8bb0083a2c6c09913910c52d03a699091c100294f8fe3c604e3846253f3a7` |
| <https://voynich.nu/q19/index.html> | 2026-07-10 | 2025-06-14 | `119fe32a005723833ec07a313fd87e1cd044a1f685ddd4fdd199e573c1dff1fb` |

These mutable research pages supplied source assertions, not botanical gold or manuscript transcription. They are treated as copyrighted and are not cached or redistributed. The structured 35-claim ledger is `derived/h005-source-anchor-manifest.json`, SHA-256 `f6f6f8edd9b21f5aa1e952e26a6104ad327a15a98e426a1fc4ed8e735b9631c7`.

## H006 methodological sources

The following external documents were retrieved for the frozen H006-FR3-LINE protocol on 2026-07-10. They are byte-hashed but not vendored.

| Source artifact | Role | Retrieved-byte SHA-256 |
|---|---|---|
| [Matlach et al. printable PDF](https://journals.plos.org/plosone/article/file?id=10.1371%2Fjournal.pone.0260948&type=printable) | Primary ligature and three-trit proposal; PLOS article is CC BY | `d4fd94df31e485422c88a07301cc2a6f92227858eadd484426aa9b6977172730` |
| [Matlach et al. S3 figure](https://doi.org/10.1371/journal.pone.0260948.s003) | Published visual component candidates | `d54b5d581ffe57386d96f596aa1e2318961dfd3a12a35f9f0e1e9c07b87f3a7f` |
| [Somogyi 2016 PDF](https://ojs.ppke.hu/verbum/article/download/405/410/609) | Near-date Italian homophonic-key history; not evidence for a ternary block code | `b18ddde02f805180b44946765b6601e9026078c4faaa23fcc2f5447e70d5f843` |
| [Megyesi et al. HistoCrypt 2021 PDF](https://ecp.ep.liu.se/index.php/histocrypt/article/download/165/121/64) | Survey of 700 historical cipher keys; historical constraint only | `252c6e3cf33ede1479f993e37928317dc24ec03a36de0c83da6da6cb84fe0313` |

These sources bound a hypothesis family; they do not supply a Voynich key or plaintext. Matlach et al. explicitly present a hypothetical construction, with component ambiguities and a Trithemius inspiration disclosed around 1500. H006 must therefore distinguish a failure of its frozen line-reset variant from a rejection of historical homophony generally.

## H007 published Naibbe fixed-key inputs

The H007 coverage screen uses selected author files from Michael A. Greshko's
[`naibbe-cipher`](https://github.com/greshko/naibbe-cipher) repository at
commit `f2675ec5dd275268bc64dd48ea64fc0e0e9827a2`. They were retrieved
2026-07-10 and copied byte-for-byte under
`raw/external/naibbe-f2675ec/`. The included `LICENSE` contains the standard MIT text; the pinned upstream
`README.md` additionally describes a citation condition. Both files are retained,
and this contribution cites the associated publication,
<https://doi.org/10.1080/01611194.2025.2566408>.

| Local file below `raw/external/naibbe-f2675ec/` | Role | SHA-256 |
|---|---|---|
| `LICENSE` | Upstream license and citation condition | `e8fb5c1110aaa38618eab2013d1e7c5cae343efd21ea9859478df4930f7746bc` |
| `README.md` | Upstream description, publication, repository, and Zenodo links | `b9e78e849a3478341d1c3167b7c3ae960e18f57b4857a0297d296adfe480ec99` |
| `decrypt_naibbe.py` | Published reverse decoder | `1c18514bbaba914989f1961f41a3930b7c1afe81d6db37b07b1dd7d9e6ea3b49` |
| `naibbe.py` | Published encoder that bounds the mechanism claim | `3f5e353d2c50f4e6a6b81567ca31cee4f0537a490b6346d054d26661648a6003` |
| `references/naibbe_tables.csv` | Published 414-row reverse table | `4e7cfd54b7ec66515d39a51e11ec97e8e19b643b0b189124eebc3982e707dcec` |
| `encrypted/examples/endofpaper.txt` | Author decoder-control ciphertext | `475055654de0049675c26de7550a37426045e4a57ab533cb97677b390e4764d7` |
| `decrypted/examples/endofpaper_decrypted.txt` | Author decoder-control output | `c89ca7e66548d76728d968a741296405a271000534f6946d76737fafe7a288c6` |
| `encrypted/examples/gallic_naibbe.txt` | Author decoder-control ciphertext | `c813aa51a843a7c399c4707b000155ba615b00ffe34276054a6e2838cfcc8ae2` |
| `decrypted/examples/gallic_decrypted.txt` | Author decoder-control output | `c439209d7a3f5492e0adb68505316392ea8b5c25ec7b53605c2d43d27d85ce68` |
| `encrypted/nathist_output_ciphertext.txt` | Author decoder-control ciphertext | `9cdf2de12f371ac7efdb2e78713f229ada508286c1717758184238a59cd64326` |
| `decrypted/nathist_output_ciphertext_decrypted.txt` | Author decoder-control output | `852d1ad67f82d6472c8ef1d99bfa12c62f76f3d37be2623a131f47232b753ca2` |

The table was deliberately designed from Voynich-like forms and distributional
targets. It is therefore a modern fixed-key test object, not independent
historical evidence, an asserted manuscript key, or a plaintext source.

## Terms and attribution

René Zandbergen states that the transliterations collected in the linked tables are made available under CC0 and requests acknowledgment and a link to the source: <https://www.voynich.nu/roadmap.html#cop>. This does not apply to the separately licensed EVA font, which this repository does not redistribute.

The pinned `IT2a-n.txt` is Zandbergen's IVTFF conversion table, not Takeshi Takahashi's separately published HTML transcription. Its inclusion here relies on Zandbergen's stated CC0 grant for the linked transliteration tables; no claim is made about rights in the separate HTML presentation.

Yale's manifest marks access as public but contains a general rights notice rather than a standardized top-level rights URI. Beinecke welcomes use of public-domain material but requires source credit: <https://beinecke.library.yale.edu/research-teaching/copyright-questions>. Do not relabel Yale's scans as CC0. Full-resolution page images are fetched from Yale on demand and kept out of the repository.

The authoritative IVTFF format document is version 2.0.1, document issue 2.0.2 dated 2025-07-08: <https://www.voynich.nu/software/ivtt/IVTFF_format.pdf> (SHA-256 observed 2026-07-09: `7ac9c4a82064763cac8767cca6f661cc4e1b4503ab9342acc03032ddb6939d49`). The parser is a clean implementation from that specification; it does not incorporate the ambiguously licensed IVTT C source.

The STA definition used by the converted files is release 1.03 dated 2025-09-13: <https://www.voynich.nu/data/sta/STA1_def.pdf> (SHA-256 observed 2026-07-09: `85a595aa61936fa103a0f2c11d980e9970e11f98d1f35038f9fc268cc433ada2`). These specifications are mutable external references and are not currently vendored; their observed hashes are recorded to make later drift visible.
