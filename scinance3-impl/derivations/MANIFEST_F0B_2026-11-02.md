# F0b-Manifest: Herleitungs-, Review- und Pruefskripte der Akte (A1, A2 Teil A/B, H27, HFRV, H33, Bilanz, H32) byte-identisch gesichert (Stand 2026-11-02)

Rolle: Bau/Kartierung. Auftrag F0b (Option (a) des Orchestrators: byte-identische Kopien, Pins bleiben gueltig, Sandbox-Pfade bleiben stehen und werden in der README dokumentiert). Nichts im Repo geaendert, nichts committet, kein Skript ausgefuehrt (nur `python3 -I -X pycache_prefix=<tmp> -m py_compile` auf den Kopien und `bash -n`), keine Parquet-/Pickle-/Siegeldatei geoeffnet, keine Marktdaten kopiert. Vorpruefung: `scratchpad/prd_review/f0/F0_MANIFEST.md` Abschnitt 4.2/4.3.

Gestagte Kopien (Zielpfad relativ zum Repo-Wurzel darunter):
- `scratchpad/prd_review/f0b/stage/scinance3-impl/{derivations,verify}/...`  (Pflichtumfang)
- `scratchpad/prd_review/f0b/stage_optional/scinance3-impl/{derivations,verify}/...`  (Abschnitt 3: ungepinnt/unreferenziert oder ausserhalb der Themenliste, vom Orchestrator zu entscheiden)
- README-Vorschlaege als Dateien: `scratchpad/prd_review/f0b/readme_vorschlaege/<Zielordner>/README.md` (Text auch in Abschnitt 6; absichtlich nicht in `stage/`)

Alle Pfade dieses Manifests: `scratchpad/` = `/tmp/claude-0/-home-user-scinance/632fbebe-92f6-553b-ba2e-14f1a2521e17/scratchpad/`.

## 0. Zahlen und Befunde vorab

| Groesse | Wert |
|---|---|
| Plan-Eintraege (Kandidaten) | 155 |
| gestaged in `stage/` (Pflichtumfang) | 133 (110 .py, 7 .sh, 16 .md) |
| gestaged in `stage_optional/` | 21 |
| nicht gestaged wegen Hygiene-Regel | 1 (`pdf_belege/period.py`: Nicht-ASCII, Zeilen 12-13; optional-Kandidat) |
| byte-identisch (sha256 Quelle = sha256 Kopie) | 154 von 154 |
| `py_compile` / `bash -n` auf den Kopien | 128 von 128 .py OK; 7 von 7 .sh OK; kein `__pycache__` in `stage*/` |
| Akten-Pins auf Skripte (JSON-Felder und Review-Tabellen, ohne Teil C) | 76 Eintraege = 60 distinkte (Name, sha256); 59 davon im Scratchpad, 1 (`power_p1.py`) im Repo |
| Pins mit auffindbarer Scratch-Datei und sha256-Treffer | 59 von 59 (alle gestaged); verloren: 0 |
| distinkte gepinnte Skript-sha256 unter den gestagten Dateien | 59 (dazu 4 Fassung-1-Skripte, deren sha256 nur im nicht committeten Fassung-1-JSON stehen) |
| echte Hygiene-Treffer in gestagten Dateien | 0 (Muster-Treffer von Hand als Falsch-Positive geklaert, Abschnitt 5) |
| Werte der drei `HARVEST_S3_*`-Variablen (auch Hostanteil des Endpunkts) | 0 Treffer in 343 Dateien (189 Kandidaten, beide Stage-Baeume) |
| Nicht-ASCII / CRLF in gestagten Dateien | 0 / 0 |
| Dateien mit Sandbox-Pfaden (`/tmp/claude-0/...`) / (`/home/user/...`) / (`.claude/worktrees`) | 59 / 70 / 6 von 154 |

**Befund 1: Kein Pin ist verloren.** Jeder in den Akten per sha256 gepinnte Skriptname (A1 14, A2-Teil-A/B 8, H27 11, HFRV 9 und 3 mit Ueberschneidung, H32 3, H33 1, Bilanz 1, dazu die per gekuerztem Hash gepinnten Review-Skripte H27 8, HFRV 5, Bilanz 2, H33 1) liegt im Sitzungs-Scratchpad und hat dort die gepinnte sha256 (bei gekuerzten Pins: Praefix und Suffix). Einzige Ausnahme im Scratchpad: `power_p1.py` liegt im Repo (`src/bybit_edge/research/power_p1.py`, sha256 stimmt mit dem Pin 74a8dede... ueberein). Details Abschnitt 4.

**Befund 2: Die Review- und Orchestrator-Skripte sind nicht per sha256 gepinnt**, nur die Ergebnisdateien (z.B. `rv_sigma.json e7b85dd0...`). Ausnahmen mit Skript-Pin: H27-Review (8), HFRV-Review (5), Bilanz-Review (2), H33-Review (1). Die uebrigen (A1-, A2-, H32-Review, Orchestrator) sind nur per Namen in der Akte genannt und deshalb als solche vermerkt (Spalte Pin/Verweis: `Name`).

**Befund 3: Die Fassung-1-Skripte der A2-Vorarbeit (`a2v_common`, `a2v_sigma30`, `a2v_build`, `run_all.sh`) unterscheiden sich von den gepinnten Fassung-2-Skripten** (andere sha256) und erzeugten die in der Akte genannten Fassung-1-Ergebnisse (`a2_vorarbeit.json 2bd1ad7e...`, `work/*.json f3559cc8.../7e98d022.../552bf0d1...`). Sie liegen im Scratchpad in `a2_vorarbeit/f1_snapshot/`; ihre sha256 stehen nur in der nicht committeten Fassung-1-JSON (dort geprueft: alle fuenf Skripte stimmen). Gestaged unter `derivations/a2/teilAB/fassung1/`. `a2v_oi.py` und `a2v_power.py` sind in beiden Fassungen byte-gleich.

**Befund 4: Layout-Abhaengigkeit.** `a2v_common.py` und `hfrv_common.py` laden ihre Module und Daten ueber Geschwisterordner des Sitzungs-Scratchpads (`hfrv_herleitung/`, `hf_data/raw/`, `hcache/`, `panel/`, `harvest_client/`). Weil die Kopien byte-identisch bleiben, laufen sie in einem Repo-Layout (`derivations/<thema>/`) nur, wenn dieses Layout nachgebaut wird; das steht in den README-Vorschlaegen. Fuer HFRV sind `h27_common.py`, `h27_series.py`, `nuisance.py`, `power_h27.py` als Dubletten (gleiche sha256) in `derivations/hfrv/` und `derivations/h27/` gestaged, weil `hfrv_common.py` sie per `sys.path` aus dem eigenen Ordner laedt.

**Befund 5: Lauf-Skripte mit Seiteneffekt.** `a2v_build.py`, `a1_consolidate.py`, `bilanz_census.py`, `nuisance_hfrv.py`, `a2_census.py` schreiben per Voreinstellung in die committeten Akten-JSON; die `run/*.sh` des H-32-Pilots schreiben nach `state/runs/` (Pilot ist einmalig, DEC-99 (3)/DEC-101 E10). Die README-Vorschlaege warnen davor.

## 1. Methode (kurz)

1. Pin-Inventar: alle `sha256`-Felder und Review-Tabellen in `state/*.md`, `state/*.json`, `state/herleitung_*/` (ohne `state/runs/`) gelesen; Skriptnamen und Hashes gegen `sha256` aller Textdateien des Scratchpads (1.436 Dateien ohne Caches, Parquet, `harvest_client/`, `hcache/`) gehalten, zusaetzlich jedes Hex-Token >= 6 der Akte als Praefix oder Suffix.
2. Kandidaten: Pins, dazu in der Akte namentlich genannte Skripte der Themenordner und die `SPEC_*.md` der Themen; ungepinnte und unreferenzierte Hilfsdateien nur nach `stage_optional/`.
3. Hygiene je Datei vor dem Staging (Werkzeug `scratchpad/prd_review/f0/_tools/hygiene_scan.py` unveraendert, Ausgabe nur Datei:Zeile:Art): Hostnamen, URLs, IP, S3-/Endpunkt-/Bucket-Woerter, Umgebungsvariablen, Zugangsdaten-Woerter, Schluessel-aehnliche Zeichenfolgen, E-Mail, Modell-Produktnamen, Pfade mit anderen Nutzern, Nicht-ASCII. Zusatz: Werte von `HARVEST_S3_ENDPOINT`/`_ACCESS_KEY`/`_SECRET_KEY` (und Hostanteil) als Suchnadeln, unabhaengig davon ein zweiter Lauf ueber alle 343 Dateien: 0 Treffer. Jeder Treffer ausser Sandbox-Pfaden wurde von Hand geprueft (Abschnitt 5); ein unbekannter Treffer haette das Staging verhindert.
4. Kopie per `shutil.copyfile` (byte-identisch), danach sha256 der Kopie gegen Quelle geprueft; `py_compile` mit ausgelagertem Bytecode-Cache.
5. Nicht gestaged: JSON/CSV/Log-Ausgaben (DEC-103 N1 (2c)), Parquet, Pickles, `tables.md`, Entwurfs-/Dubletten-Dateien (Abschnitt 4.2).

Legende Spalte Pin/Verweis: `PIN <Akte-Datei>:<Zeile> [64]` = volle sha256 in der Akte; `[8+Suffix]` = gekuerzt Praefix...Suffix, beide stimmen; `[8]` = nur Praefix; `Name <Datei>:<Zeile> (+n)` = nur per Dateiname in der Akte genannt (erste Fundstelle in den Akte-Dokumenten desselben Themas, n weitere; Namen wie `run_all.sh`, `keyscan.py`, `rv_power.py` kommen themenuebergreifend vor, die Zuordnung ergibt sich aus dem Ordnerpfad `scratchpad/<ordner>/` in der Akte); `-` = weder gepinnt noch genannt (Spec oder Verzeichnis-Verweis). Spalte Hygiene: `rein` = kein Treffer; `Sandbox: tmp n, home m, wt k` = Zeilen mit `/tmp/claude-0/...`, `/home/user/...`, `.claude/worktrees` (bekannte, unschaedliche Sandbox-Pfade); `FP` = Muster-Treffer, von Hand als Falsch-Positiv geklaert (Abschnitt 5).

## 2. Gestagte Dateien (`stage/`, Pflichtumfang)

### `derivations/a1/` (15 Dateien)

| # | Quelle (scratchpad/) | Ziel (scinance3-impl/) | sha256 | Pin / Verweis in der Akte | Hygiene |
|---|---|---|---|---|---|
| 1 | `a1_herleitung/a1_common.py` | `derivations/a1/a1_common.py` | `dbe0bdb6c03a0a63ca332c12ec4900593a783ef26557706532e1bab59f11b289` | PIN herleitung_a1/feasibility.json:6 [64] | Sandbox: tmp 3, home 2; FP: Name HARVEST/os.environ |
| 2 | `a1_herleitung/a1_model.py` | `derivations/a1/a1_model.py` | `a62e33c4faa713217ff4b547db7afb1893ccc3613a9ada3753c9f91eb59790c6` | PIN herleitung_a1/feasibility.json:7 [64] | rein |
| 3 | `a1_herleitung/a1_window_census.py` | `derivations/a1/a1_window_census.py` | `15717992e1981084cebe960cccc53edee2b10331513ef321023d8bb3e08fe4d0` | PIN herleitung_a1/feasibility.json:8 [64] | Sandbox: tmp 1 |
| 4 | `a1_herleitung/a1_nuisance.py` | `derivations/a1/a1_nuisance.py` | `c8c8ba1a7d33c6eb8f88e94f081e77ee0404fb628fbf52785c540e5faeb29257` | PIN herleitung_a1/feasibility.json:9 [64] | Sandbox: tmp 1 |
| 5 | `a1_herleitung/a1_formation_sensitivity.py` | `derivations/a1/a1_formation_sensitivity.py` | `cd3ab1d8fc13c5f6e455d0204d088e085f371416498f6220c121eca2214ba199` | PIN herleitung_a1/feasibility.json:10 [64] | Sandbox: tmp 1 |
| 6 | `a1_herleitung/a1_power.py` | `derivations/a1/a1_power.py` | `58118a46ff9a35607635b55456a28680097e59ab43552bcf7eea5b9ee3ec33a5` | PIN herleitung_a1/feasibility.json:11 [64] | Sandbox: tmp 1 |
| 7 | `a1_herleitung/a1_kill4_ci.py` | `derivations/a1/a1_kill4_ci.py` | `723cafe5e6dc2ade141a2615f0a9acc1dddb5ae652383867285aab561ac46175` | PIN herleitung_a1/feasibility.json:12 [64] | Sandbox: tmp 1 |
| 8 | `a1_herleitung/a1_psi_by_class.py` | `derivations/a1/a1_psi_by_class.py` | `7635b33302bc0642e4d60ab9fd8132eda3aebc8395e75a3dfe5e484944f663b5` | PIN herleitung_a1/feasibility.json:13 [64] | Sandbox: tmp 1 |
| 9 | `a1_herleitung/a1_selfcheck.py` | `derivations/a1/a1_selfcheck.py` | `327cd0b6a124833fc8763aaa65d36b969457c3e0c7354c1d1da17a0628fa5a3d` | PIN herleitung_a1/feasibility.json:14 [64] | Sandbox: tmp 1 |
| 10 | `a1_herleitung/a1_check_factor.py` | `derivations/a1/a1_check_factor.py` | `e02d7bf762d9c487a9c8b8b6ba1437cea7d5d89315e40bfc7bc1d8198b03b410` | PIN herleitung_a1/feasibility.json:15 [64] | Sandbox: tmp 1 |
| 11 | `a1_herleitung/a1_bookkeeping.py` | `derivations/a1/a1_bookkeeping.py` | `2f338465a4fd0922dbe23e5178a863e76da60ab9a2958fd9da51bb348222f17e` | PIN herleitung_a1/feasibility.json:16 [64] | Sandbox: tmp 1 |
| 12 | `a1_herleitung/a1_explore.py` | `derivations/a1/a1_explore.py` | `240b0a6195816119eba4facfe7221ddd69fe25ece367f1cdd84c2e941a31a2ab` | PIN herleitung_a1/feasibility.json:17 [64] | Sandbox: tmp 1 |
| 13 | `a1_herleitung/a1_consolidate.py` | `derivations/a1/a1_consolidate.py` | `953d6f05722bfce0b0f328cef9c0d5497a471e571cb0404cf2ae814f52a3cfa9` | PIN herleitung_a1/feasibility.json:18 [64] | Sandbox: tmp 1 |
| 14 | `a1_herleitung/run_all.sh` | `derivations/a1/run_all.sh` | `511f8db9c637d8b898b48a2d8e871b6049c995c9595493a8fc08910150e4f603` | PIN herleitung_a1/feasibility.json:19 [64] | Sandbox: tmp 1 |
| 15 | `SPEC_A1_herleitung.md` | `derivations/a1/SPEC_A1_herleitung.md` | `af192bb32a52826daa82afb2e65a1a72d6bbbaf100c07427d13a160e79b663cd` | - | Sandbox: tmp 3, home 2 |

### `verify/a1/` (6 Dateien)

| # | Quelle (scratchpad/) | Ziel (scinance3-impl/) | sha256 | Pin / Verweis in der Akte | Hygiene |
|---|---|---|---|---|---|
| 16 | `a1_review/rv_load.py` | `verify/a1/rv_load.py` | `f82a810bb51ac4cdecc7d73a0e156b05d9b23c70b1d73f36ace8597cd953a6ed` | Name herleitung_a1/REVIEW_A1.md:5 (+2) | Sandbox: tmp 1, home 1 |
| 17 | `a1_review/rv_formation.py` | `verify/a1/rv_formation.py` | `21a6f3e552ad8fb2ade44f7a4e259ee1c9e3d0b139c12c916422526fd15cbb16` | Name herleitung_a1/REVIEW_A1.md:5 (+2) | Sandbox: tmp 1, home 1 |
| 18 | `a1_review/rv_nuisance.py` | `verify/a1/rv_nuisance.py` | `b6b544fb018fcd102af6b6b3a4f1b273a7ee6c1c3c47c52ffb7c8af25405203c` | Name herleitung_a1/REVIEW_A1.md:5 (+1) | Sandbox: tmp 1 |
| 19 | `a1_review/rv_power.py` | `verify/a1/rv_power.py` | `d25ed2b6919af416f97fc5dc1ee14f99458676476cb148827f7e58b3f92aaedc` | Name herleitung_a1/REVIEW_A1.md:5 (+3) | Sandbox: tmp 1 |
| 20 | `a1_review/rv_wp7_zerofill.py` | `verify/a1/rv_wp7_zerofill.py` | `8c360a226389a41fe17514a18ee34d967bf922332dc9a285a48938a5d3f0045a` | Name herleitung_a1/REVIEW_A1.md:6 (+2) | Sandbox: tmp 1, home 1 |
| 21 | `SPEC_A1_review.md` | `verify/a1/SPEC_A1_review.md` | `57d532ae8e102195f0ed9366c8298b50a9fabf5df5fe981dfb291d617ff954de` | - | Sandbox: tmp 3, home 1 |

### `derivations/a2/teilAB/` (11 Dateien)

| # | Quelle (scratchpad/) | Ziel (scinance3-impl/) | sha256 | Pin / Verweis in der Akte | Hygiene |
|---|---|---|---|---|---|
| 22 | `a2_vorarbeit/a2v_common.py` | `derivations/a2/teilAB/a2v_common.py` | `fb3a9d9cde6028e66ead13923da516b684f44abba8f969334a5eadc50fc3f85c` | PIN herleitung_a2/a2_vorarbeit.json:25 [64] | Sandbox: home 2 |
| 23 | `a2_vorarbeit/a2v_oi.py` | `derivations/a2/teilAB/a2v_oi.py` | `cf4f5e7767f6513ce5443b1cd1aa5a8f3527aabea37af6b022bfded409410ab6` | PIN herleitung_a2/a2_vorarbeit.json:26 [64] | rein |
| 24 | `a2_vorarbeit/a2v_sigma30.py` | `derivations/a2/teilAB/a2v_sigma30.py` | `69db88ede9a03d71ced763777c744dd6cc43f1041f574ce438ea744bd55dcbf7` | PIN herleitung_a2/a2_vorarbeit.json:27 [64] | FP: Muster-FP |
| 25 | `a2_vorarbeit/a2v_power.py` | `derivations/a2/teilAB/a2v_power.py` | `6e299a39f86b28fa33becb39870e248d259e5be01414389dac45400eaf9585d8` | PIN herleitung_a2/a2_vorarbeit.json:28 [64] | rein |
| 26 | `a2_vorarbeit/a2v_fut.py` | `derivations/a2/teilAB/a2v_fut.py` | `12e50a91499a0370305bf90556de46057344dd74030af12e2152d0ee89df7526` | PIN herleitung_a2/a2_vorarbeit.json:29 [64] | rein |
| 27 | `a2_vorarbeit/a2v_corr2.py` | `derivations/a2/teilAB/a2v_corr2.py` | `cafa20a1f96f6596b1bbb6955cbe1f21c52a4937f6788d061ed9e31215a90524` | PIN herleitung_a2/a2_vorarbeit.json:30 [64] | rein |
| 28 | `a2_vorarbeit/a2v_konj.py` | `derivations/a2/teilAB/a2v_konj.py` | `a228ea74b12f6c610d5d171129ac8f5e73226cbf865406066c74c9830af9988f` | PIN herleitung_a2/a2_vorarbeit.json:31 [64] | rein |
| 29 | `a2_vorarbeit/a2v_build.py` | `derivations/a2/teilAB/a2v_build.py` | `0fe8bffc84218a597fc9bccb0ebfb3fb7c0ea7b47e631033adc5c95ed887444d` | PIN herleitung_a2/a2_vorarbeit.json:32 [64] | Sandbox: home 1 |
| 30 | `a2_vorarbeit/run_all.sh` | `derivations/a2/teilAB/run_all.sh` | `009df2075f317e6f8f6f5a16e36c12ba37a47e6ae7208c9d518a041b7fc200b1` | Name herleitung_a2/NUISANCE_SIGMA30.md:415 (+5) | rein |
| 31 | `SPEC_A2_vorarbeit.md` | `derivations/a2/teilAB/SPEC_A2_vorarbeit.md` | `6365f314d2d83628358b50277a5f46fb00b3a97bdcb56a640971b120e177c2bf` | Name herleitung_a2/REVIEW_A2_VORARBEIT.md:11 | Sandbox: tmp 4, home 1 |
| 32 | `SPEC_A2_auflagen.md` | `derivations/a2/teilAB/SPEC_A2_auflagen.md` | `38742ff5bc78bfb3c696b189b9ff68b98b4ab23c801fc6c07ed4846a22d61890` | - | Sandbox: tmp 2 |

### `derivations/a2/teilAB/fassung1/` (4 Dateien)

| # | Quelle (scratchpad/) | Ziel (scinance3-impl/) | sha256 | Pin / Verweis in der Akte | Hygiene |
|---|---|---|---|---|---|
| 33 | `a2_vorarbeit/f1_snapshot/a2v_common.py` | `derivations/a2/teilAB/fassung1/a2v_common.py` | `96518126530ae91afc0a2d185c8cc8f3e18a1844d0fb0cb0daba014ed6e2e2d3` | Name herleitung_a2/NUISANCE_SIGMA30.md:73 (+5) | Sandbox: home 2 |
| 34 | `a2_vorarbeit/f1_snapshot/a2v_sigma30.py` | `derivations/a2/teilAB/fassung1/a2v_sigma30.py` | `553d51ac3466d08c6a6d11643bc7c56961ff877e34eda270eb537aa3edf26fdb` | Name herleitung_a2/NUISANCE_SIGMA30.md:398 (+7) | FP: Muster-FP |
| 35 | `a2_vorarbeit/f1_snapshot/a2v_build.py` | `derivations/a2/teilAB/fassung1/a2v_build.py` | `df3b940046f63b24ed9c06c0ab82ed473f4396bc717b10e0c1c1f04dc0b303b8` | Name herleitung_a2/NUISANCE_SIGMA30.md:416 (+3) | Sandbox: home 1 |
| 36 | `a2_vorarbeit/f1_snapshot/run_all.sh` | `derivations/a2/teilAB/fassung1/run_all.sh` | `656e06014464122b0851e4a4a3b9726c49951b39c8b76c8295b9a7e9b08ff76f` | Name herleitung_a2/NUISANCE_SIGMA30.md:415 (+5) | rein |

### `verify/a2/teilAB/` (15 Dateien)

| # | Quelle (scratchpad/) | Ziel (scinance3-impl/) | sha256 | Pin / Verweis in der Akte | Hygiene |
|---|---|---|---|---|---|
| 37 | `a2_review/rv_sigma.py` | `verify/a2/teilAB/rv_sigma.py` | `4abd3ad0d7a5348ff6cd93db5f4300395bca918bf16f7cc2215828d537cf10ef` | Name herleitung_a2/REVIEW_A2_VORARBEIT.md:39 (+3) | Sandbox: tmp 1, home 1 |
| 38 | `a2_review/rv_power.py` | `verify/a2/teilAB/rv_power.py` | `5383696c771f8cfac09acbbc679c563150951cbd12fe9bd951b0a1b5414ae1b3` | Name herleitung_a2/REVIEW_A2_VORARBEIT.md:55 (+2) | Sandbox: tmp 1, home 1 |
| 39 | `a2_review/rv_oi.py` | `verify/a2/teilAB/rv_oi.py` | `917a3c574e1e51f3e2d21f7d9469e148b9c49c91a5e542c62757cecf85096121` | Name herleitung_a2/REVIEW_A2_VORARBEIT.md:41 (+2) | Sandbox: tmp 1 |
| 40 | `a2_review/rv_fut.py` | `verify/a2/teilAB/rv_fut.py` | `878c008568bc026a832b9bc52670c776d07e1118c6cb0f933a1415688bc05102` | Name herleitung_a2/REVIEW_A2_VORARBEIT.md:57 (+1) | Sandbox: tmp 1 |
| 41 | `a2_review/rv_timing.py` | `verify/a2/teilAB/rv_timing.py` | `0aa9c0fcd4a511e41904cf950490a45f29695cb9b7562e396bd6ad42bcd93c8c` | Name herleitung_a2/REVIEW_A2_VORARBEIT.md:40 (+1) | Sandbox: tmp 1 |
| 42 | `a2_review/rv_did.py` | `verify/a2/teilAB/rv_did.py` | `b90f80d2249e05685741b6aafff0433c90f4c1c68a9ae4b56a9d5c8937819e27` | Name herleitung_a2/REVIEW_A2_VORARBEIT.md:59 (+1) | rein |
| 43 | `a2_review/rv_band.py` | `verify/a2/teilAB/rv_band.py` | `e69b0ab3d3db339efbfc0f0f1d7bb5218eac883c991ff844bb85914397f86a90` | Name herleitung_a2/REVIEW_A2_VORARBEIT.md:43 (+1) | rein |
| 44 | `a2_review/cmp_sigma.py` | `verify/a2/teilAB/cmp_sigma.py` | `21182f28078f6935722e2fc7085b6f52138143c47dc526d92024a86a11310b37` | Name herleitung_a2/REVIEW_A2_VORARBEIT.md:67 (+1) | Sandbox: home 1 |
| 45 | `a2_review/keyscan.py` | `verify/a2/teilAB/keyscan.py` | `ac3f012c1b1a79839565507dbf9c9dfe20a43b83d6768ce625fcf6333b527fe2` | Name herleitung_a2/REVIEW_A2_VORARBEIT.md:39 (+1) | rein |
| 46 | `a2_review/pathscan.py` | `verify/a2/teilAB/pathscan.py` | `fb35dd8e4efa59b454ec60c04cbf08958af7e5d73fc264d7b789dda0af3f6720` | Name herleitung_a2/REVIEW_A2_VORARBEIT.md:39 (+1) | rein |
| 47 | `a2_review/guardtest.py` | `verify/a2/teilAB/guardtest.py` | `0041980dfa511fc7364314ccd306393400d45f5d9f10696b2d97c3c06869825e` | Name herleitung_a2/REVIEW_A2_VORARBEIT.md:52 (+1) | Sandbox: tmp 1 |
| 48 | `SPEC_A2_review.md` | `verify/a2/teilAB/SPEC_A2_review.md` | `a2870b77a31eac6bf8ec8a5f099ecd8913b4dfbd48fda831bbbb168f2aaa2aaa` | - | Sandbox: tmp 2, home 2 |
| 49 | `orch_check/a2_fut_check.py` | `verify/a2/teilAB/a2_fut_check.py` | `a6cbee0df792cc85ecd25666fca358b6ef5ea7b05646c0cc8af4e6dadd36449b` | Name herleitung_a2/NACHRECHNUNG_ORCHESTRATOR.md:22 | Sandbox: tmp 1 |
| 50 | `orch_check/a2_joint_check.py` | `verify/a2/teilAB/a2_joint_check.py` | `7d8d40a279bf81ef41ac74cfa0b5009f141d703583753730535def441de0557e` | Name herleitung_a2/NACHRECHNUNG_ORCHESTRATOR.md:22 | rein |
| 51 | `orch_check/a2_spot.py` | `verify/a2/teilAB/a2_spot.py` | `a2a87d2aace2a50c99d10870a376c34267bb6f73ba1314e3a090fd74a84db0f3` | Name herleitung_a2/NACHRECHNUNG_ORCHESTRATOR.md:3 | Sandbox: tmp 1 |

### `derivations/h27/` (12 Dateien)

| # | Quelle (scratchpad/) | Ziel (scinance3-impl/) | sha256 | Pin / Verweis in der Akte | Hygiene |
|---|---|---|---|---|---|
| 52 | `h27_herleitung/h27_common.py` | `derivations/h27/h27_common.py` | `4093396d3183f9b6e591e3faa0777ef32c234d8e32b943be3956a8c507e085ee` | PIN herleitung_h27/feasibility.json:9528 [64]; herleitung_h27/feasibility.json:9672 [64] (+4) | FP: harvest_data-Import |
| 53 | `h27_herleitung/h27_series.py` | `derivations/h27/h27_series.py` | `d3c9d339e655c059d739a900d61e6f439fe8378486c6b518973fffff641bc826` | PIN herleitung_h27/feasibility.json:9529 [64]; herleitung_hfrv/nuisance_hfrv.json:17610 [64] (+1) | FP: S3-Variable-FP |
| 54 | `h27_herleitung/nuisance.py` | `derivations/h27/nuisance.py` | `33e3f89a189463330e2762d8500bfa37b7ba69f1820dec964c8b6720f02a7009` | PIN herleitung_h27/feasibility.json:9530 [64]; herleitung_hfrv/nuisance_hfrv.json:17614 [64] (+1) | Sandbox: home 1; FP: S3-Variable-FP |
| 55 | `h27_herleitung/nullworld.py` | `derivations/h27/nullworld.py` | `3e7044883561f27e3ba9a58d2d99929616b2cbb7ac9e2076f127c6de3e5ee372` | PIN herleitung_h27/feasibility.json:9531 [64] | FP: S3-Variable-FP |
| 56 | `h27_herleitung/power_h27.py` | `derivations/h27/power_h27.py` | `d65c8579457aecb0cfa03ff3e4b82ec9af597c6f51199265e52864397162bb5b` | PIN herleitung_h27/feasibility.json:9533 [64]; herleitung_hfrv/nuisance_hfrv.json:17616 [64] (+1) | Sandbox: home 1; FP: S3-Variable-FP |
| 57 | `h27_herleitung/panel_coverage.py` | `derivations/h27/panel_coverage.py` | `7d6db01c2f7ce4d6f2f549eaa9d136a2916f27d8bcfbd0e263858a4d3f15f22e` | PIN herleitung_h27/feasibility.json:9532 [64]; herleitung_h27/feasibility.json:9673 [64] | rein |
| 58 | `h27_herleitung/catalog_check.py` | `derivations/h27/catalog_check.py` | `72fe11167ce5efafdc25459460242a9d6d95af403e560b41a7bbd14459d2dbdd` | PIN herleitung_h27/feasibility.json:9524 [64]; herleitung_h27/feasibility.json:9671 [64] | FP: harvest_data-Import, Muster-FP, S3-Variable-FP |
| 59 | `h27_herleitung/catalog_check2.py` | `derivations/h27/catalog_check2.py` | `bd07c94c62bf8be783e9756ae1aa84a410224829a4ebc008cf4988a8942b4a63` | PIN herleitung_h27/feasibility.json:9525 [64] | FP: harvest_data-Import, Muster-FP |
| 60 | `h27_herleitung/conv_check.py` | `derivations/h27/conv_check.py` | `86f2003c94e042a943f60e83b38664ccd2bb1afbf6a45e112ed5a96fe65879b7` | PIN herleitung_h27/feasibility.json:9526 [64] | rein |
| 61 | `h27_herleitung/dvol_probe.py` | `derivations/h27/dvol_probe.py` | `7e6ef6b06ad2e3e972bcd02ce0b9372668a1c4f9798a8450e95c0d83ea8b8a53` | PIN herleitung_h27/feasibility.json:9527 [64] | rein |
| 62 | `h27_herleitung/schema_probe_stream.py` | `derivations/h27/schema_probe_stream.py` | `bce42a8192fddad6ab6ce6dfaf88174cd51ae0b31cada28d3d9980431e0c2c9f` | PIN herleitung_h27/feasibility.json:9534 [64]; herleitung_h27/feasibility.json:9674 [64] | FP: S3-Variable-FP |
| 63 | `SPEC_H27_herleitung.md` | `derivations/h27/SPEC_H27_herleitung.md` | `ba83ec87f85a89ba535d8952c03dcb2162e133e2673d4bedaf7350146d896104` | Name herleitung_h27/REVIEW_H27.md:5 | Sandbox: tmp 3, home 1; FP: Name HARVEST/os.environ, harvest_data-Import, S3-Variable-FP |

### `verify/h27/` (9 Dateien)

| # | Quelle (scratchpad/) | Ziel (scinance3-impl/) | sha256 | Pin / Verweis in der Akte | Hygiene |
|---|---|---|---|---|---|
| 64 | `h27_review/rv_common.py` | `verify/h27/rv_common.py` | `bd8880ab8405048a20f4d18bb17ca3b9c6f8d8c7a9bbf0cd65d4b289bb59b147` | PIN herleitung_h27/REVIEW_H27.md:294 [8+Suffix] | FP: S3-Variable-FP |
| 65 | `h27_review/nuisance_review.py` | `verify/h27/nuisance_review.py` | `ffd9469d7a3c9b95c50261bcdc3ceae0427807843973344bb6f58b1312faa63a` | PIN herleitung_h27/REVIEW_H27.md:295 [8+Suffix] | Sandbox: home 1; FP: S3-Variable-FP |
| 66 | `h27_review/nullworld_review.py` | `verify/h27/nullworld_review.py` | `82a801813d24286b3f42f97e9bab2adb89dae797346a63ab22c7abe7ab1ff267` | PIN herleitung_h27/REVIEW_H27.md:296 [8+Suffix] | FP: S3-Variable-FP |
| 67 | `h27_review/noise_share.py` | `verify/h27/noise_share.py` | `a4f4f14ed0f4434afe8143b34f0babb0c6c14c81ca48e0730b789253b8b7627c` | PIN herleitung_h27/REVIEW_H27.md:297 [8+Suffix] | rein |
| 68 | `h27_review/power_review.py` | `verify/h27/power_review.py` | `e45e41025a9ef60db7c004ee6a19cb90f53da88dcd10be885909f4415b4c1cb2` | PIN herleitung_h27/REVIEW_H27.md:298 [8+Suffix] | Sandbox: home 1; FP: S3-Variable-FP |
| 69 | `h27_review/conv_review.py` | `verify/h27/conv_review.py` | `8ffd90a0964e823c75edcec2143d9b6dfa56f0d27c61e52a55e2855af9be7deb` | PIN herleitung_h27/REVIEW_H27.md:299 [8+Suffix] | rein |
| 70 | `h27_review/setup_cache.py` | `verify/h27/setup_cache.py` | `fd944b2291bc13bfef122c6d8f2ef08dbc4c4c0cf001da176bd7a0a0cc47f238` | PIN herleitung_h27/REVIEW_H27.md:300 [8+Suffix] | rein |
| 71 | `h27_review/keyscan.py` | `verify/h27/keyscan.py` | `8113ae8dd00e302da1e010a6a14edd7f55c0c7b262cb6ca46b43f2c5e8f869fa` | PIN herleitung_h27/REVIEW_H27.md:300 [8+Suffix] | rein |
| 72 | `SPEC_H27_review.md` | `verify/h27/SPEC_H27_review.md` | `6ea1607fe97684bc4efc022e3e5e91becd169c00019901ad044711dd1770eb15` | - | Sandbox: tmp 4, home 1; FP: harvest_data-Import, S3-Variable-FP |

### `derivations/hfrv/` (10 Dateien)

| # | Quelle (scratchpad/) | Ziel (scinance3-impl/) | sha256 | Pin / Verweis in der Akte | Hygiene |
|---|---|---|---|---|---|
| 73 | `hfrv_herleitung/hfrv_common.py` | `derivations/hfrv/hfrv_common.py` | `490691590501e1b6cba9e8c46baf432411217a86bd5bb58e6b88328fa8545ba3` | PIN herleitung_hfrv/a2_census.json:24580 [64]; herleitung_hfrv/nuisance_hfrv.json:17611 [64] (+1) | Sandbox: home 3; FP: S3-Variable-FP |
| 74 | `hfrv_herleitung/hfrv_power.py` | `derivations/hfrv/hfrv_power.py` | `9f53ca4822ef58b1963671e1402eeba72ce2b5d950690e512345b95c5f8712f5` | PIN herleitung_hfrv/nuisance_hfrv.json:17612 [64] | Sandbox: tmp 1, home 1 |
| 75 | `hfrv_herleitung/nuisance_hfrv.py` | `derivations/hfrv/nuisance_hfrv.py` | `8381a1f0c4be4680d7d703d2bbe4c2e0479e1b32032bddd7fbe77fd77944d7b7` | PIN herleitung_hfrv/nuisance_hfrv.json:17615 [64] | Sandbox: tmp 1, home 1; FP: S3-Variable-FP |
| 76 | `hfrv_herleitung/a2_census.py` | `derivations/hfrv/a2_census.py` | `8fe9b22a0a4be60b4b3aba9f2bed819220c26882a00233d040493f857781e694` | PIN herleitung_hfrv/a2_census.json:24579 [64]; herleitung_hfrv/nuisance_hfrv.json:17608 [64] | rein |
| 77 | `hfrv_herleitung/make_tables.py` | `derivations/hfrv/make_tables.py` | `203dcc03ad77011e7756733bfc4bcaeddfeedb6ca4b77fc04a0d2b32e198cb91` | PIN herleitung_hfrv/nuisance_hfrv.json:17613 [64] | Sandbox: tmp 1, home 1; FP: S3-Variable-FP |
| 78 | `hfrv_herleitung/h27_common.py` | `derivations/hfrv/h27_common.py` | `4093396d3183f9b6e591e3faa0777ef32c234d8e32b943be3956a8c507e085ee` | PIN herleitung_h27/feasibility.json:9528 [64]; herleitung_h27/feasibility.json:9672 [64] (+4) | FP: harvest_data-Import |
| 79 | `hfrv_herleitung/h27_series.py` | `derivations/hfrv/h27_series.py` | `d3c9d339e655c059d739a900d61e6f439fe8378486c6b518973fffff641bc826` | PIN herleitung_h27/feasibility.json:9529 [64]; herleitung_hfrv/nuisance_hfrv.json:17610 [64] (+1) | FP: S3-Variable-FP |
| 80 | `hfrv_herleitung/nuisance.py` | `derivations/hfrv/nuisance.py` | `33e3f89a189463330e2762d8500bfa37b7ba69f1820dec964c8b6720f02a7009` | PIN herleitung_h27/feasibility.json:9530 [64]; herleitung_hfrv/nuisance_hfrv.json:17614 [64] (+1) | Sandbox: home 1; FP: S3-Variable-FP |
| 81 | `hfrv_herleitung/power_h27.py` | `derivations/hfrv/power_h27.py` | `d65c8579457aecb0cfa03ff3e4b82ec9af597c6f51199265e52864397162bb5b` | PIN herleitung_h27/feasibility.json:9533 [64]; herleitung_hfrv/nuisance_hfrv.json:17616 [64] (+1) | Sandbox: home 1; FP: S3-Variable-FP |
| 82 | `SPEC_HFRV_herleitung.md` | `derivations/hfrv/SPEC_HFRV_herleitung.md` | `b1dcc55d9e1ce8c8c14f38081250c387740ec3e58b814ff6f0d023247538e4da` | Name herleitung_hfrv/REVIEW_HFRV.md:6 | Sandbox: tmp 5, home 2; FP: S3-Variable-FP |

### `verify/hfrv/` (7 Dateien)

| # | Quelle (scratchpad/) | Ziel (scinance3-impl/) | sha256 | Pin / Verweis in der Akte | Hygiene |
|---|---|---|---|---|---|
| 83 | `hfrv_review/review_hfrv.py` | `verify/hfrv/review_hfrv.py` | `a749af2f2d3daff53e9f70a7082f6d3a6877d371031f97f2731c0f89165394a4` | PIN herleitung_hfrv/REVIEW_HFRV.md:306 [8+Suffix] | Sandbox: home 2 |
| 84 | `hfrv_review/compare.py` | `verify/hfrv/compare.py` | `3d91572e5dc94a2afa0f756b1ebe27ca5ce1ffd4130039108729041557b8cb58` | PIN herleitung_hfrv/REVIEW_HFRV.md:307 [8+Suffix] | Sandbox: home 1; FP: S3-Variable-FP |
| 85 | `hfrv_review/c_robust.py` | `verify/hfrv/c_robust.py` | `de3fd9d5add7f49bd1b963aa32ee157ab3cf1a43d2020f3be8bb06c917cd1ad0` | PIN herleitung_hfrv/REVIEW_HFRV.md:308 [8+Suffix] | rein |
| 86 | `hfrv_review/a2_review.py` | `verify/hfrv/a2_review.py` | `830c4dab662184d6952136fcb298ae81d80836f596550252145c9f41a5f789d2` | PIN herleitung_hfrv/REVIEW_HFRV.md:309 [8+Suffix] | rein |
| 87 | `hfrv_review/keyscan.py` | `verify/hfrv/keyscan.py` | `a643d013674cd56c71b352b2bbfd7863e9a87e4fbb842f64f055f1a0b0c27469` | PIN herleitung_hfrv/REVIEW_HFRV.md:310 [8+Suffix] | rein |
| 88 | `SPEC_HFRV_review.md` | `verify/hfrv/SPEC_HFRV_review.md` | `49728d86e435974c4a52143937ba6f56df832a3aaf289f5b66ba4c9b103397fb` | - | Sandbox: tmp 4, home 2; FP: S3-Variable-FP |
| 89 | `orch_check/hfrv_spot.py` | `verify/hfrv/hfrv_spot.py` | `429a6a70e10f4c8f941e95489a844446301fe69763f682ff2556b73878d0e6bd` | Name herleitung_hfrv/NACHRECHNUNG_ORCHESTRATOR.md:3 | Sandbox: tmp 1 |

### `derivations/h33/` (2 Dateien)

| # | Quelle (scratchpad/) | Ziel (scinance3-impl/) | sha256 | Pin / Verweis in der Akte | Hygiene |
|---|---|---|---|---|---|
| 90 | `h33_herleitung/h33_compute.py` | `derivations/h33/h33_compute.py` | `ef0788a0cca30cfa27b3afe53f106ffeea5411237f8f4c0d821c649a2ef346b0` | PIN herleitung_h33/nuisance_neg.json:24 [64]; herleitung_h33/power_h33.json:290 [64] (+1) | Sandbox: tmp 2 |
| 91 | `SPEC_H33_herleitung.md` | `derivations/h33/SPEC_H33_herleitung.md` | `7dbaa5c86853577ad0b7d916712aec7acb4102ba3ebdc9099c8b004c90832498` | Name (nur andere Themen) UEBERGABE_2026-10-12.md:223 | Sandbox: tmp 3, home 1 |

### `verify/h33/` (2 Dateien)

| # | Quelle (scratchpad/) | Ziel (scinance3-impl/) | sha256 | Pin / Verweis in der Akte | Hygiene |
|---|---|---|---|---|---|
| 92 | `h33_review/review_h33.py` | `verify/h33/review_h33.py` | `723fa4a417befd2e64fb8d4ae1d2d1df9236dac28e4eb2a8c7a09f40701cdee4` | PIN herleitung_h33/REVIEW_H33.md:16 [8] | rein |
| 93 | `SPEC_H33_review.md` | `verify/h33/SPEC_H33_review.md` | `326a6715f187af35af08f38a6197af2d9b6c43bd20de9b5e69806671186e9107` | - | Sandbox: tmp 3, home 1 |

### `derivations/bilanz/` (3 Dateien)

| # | Quelle (scratchpad/) | Ziel (scinance3-impl/) | sha256 | Pin / Verweis in der Akte | Hygiene |
|---|---|---|---|---|---|
| 94 | `bilanz/bilanz_census.py` | `derivations/bilanz/bilanz_census.py` | `4f90415f428e022cb9a8f32326eba2ad008e70fc3350b3507e54ad6612c34bfb` | PIN programm_bilanz.json:3110 [64]; REVIEW_PROGRAMM_BILANZ_2026-10-18.md:5 [8+Suffix] | Sandbox: tmp 2, home 3 |
| 95 | `bilanz/make_tables.py` | `derivations/bilanz/make_tables.py` | `632dfaf6e943008527cd89309d955c273245dc3a1dc1020a937119b184ee74a7` | Name PROGRAMM_BILANZ_2026-10-18.md:47 (+2) | Sandbox: home 1 |
| 96 | `SPEC_BILANZ_power_zensus.md` | `derivations/bilanz/SPEC_BILANZ_power_zensus.md` | `48a0d3981cd46a323f0e2596259d40532495c03a786a20728f61655f9247d13b` | Name REVIEW_PROGRAMM_BILANZ_2026-10-18.md:6 | Sandbox: tmp 1, home 2 |

### `verify/bilanz/` (2 Dateien)

| # | Quelle (scratchpad/) | Ziel (scinance3-impl/) | sha256 | Pin / Verweis in der Akte | Hygiene |
|---|---|---|---|---|---|
| 97 | `bilanz_review/review_check.py` | `verify/bilanz/review_check.py` | `b3bdc07434741a504154aeb21b2eca6709e47c6e4fe27f9c33cd51e7a1bb3fdf` | PIN REVIEW_PROGRAMM_BILANZ_2026-10-18.md:444 [8+Suffix] | Sandbox: home 2 |
| 98 | `SPEC_BILANZ_review.md` | `verify/bilanz/SPEC_BILANZ_review.md` | `c42ae37739c1e6ea8491312fb9685913461ff095dfb00f76da58aa08deae0b5d` | Name REVIEW_PROGRAMM_BILANZ_2026-10-18.md:6 | Sandbox: tmp 3, home 1 |

### `verify/bilanz/rerun/` (1 Dateien)

| # | Quelle (scratchpad/) | Ziel (scinance3-impl/) | sha256 | Pin / Verweis in der Akte | Hygiene |
|---|---|---|---|---|---|
| 99 | `bilanz_review/rerun/census_copy.py` | `verify/bilanz/rerun/census_copy.py` | `21ed2e7021d5b09ba0a85f7aeb2bc8408d14889835f46a471bb85e538797b1de` | PIN REVIEW_PROGRAMM_BILANZ_2026-10-18.md:446 [8+Suffix] | Sandbox: tmp 3, home 3 |

### `derivations/h32/` (4 Dateien)

| # | Quelle (scratchpad/) | Ziel (scinance3-impl/) | sha256 | Pin / Verweis in der Akte | Hygiene |
|---|---|---|---|---|---|
| 100 | `h32_herleitung/assemble.py` | `derivations/h32/assemble.py` | `6dc8195a507e2851f5523d786da0de7285dc2e004c2ee9bac86a9d1e89c06c74` | PIN herleitung_h32/power_h32.json:3537 [64] | Sandbox: home 1; FP: Name HARVEST/os.environ |
| 101 | `h32_herleitung/h32_power.py` | `derivations/h32/h32_power.py` | `7614599e00617eea771365a2a190f63abff17e5d111543d8738ceb3f546e2fd9` | PIN herleitung_h32/power_h32.json:3538 [64] | rein |
| 102 | `h32_herleitung/sector_check.py` | `derivations/h32/sector_check.py` | `5bebdc167d65aca57664a5d855a5795edf2940dc47fc6c0e27fcc606c96199b5` | PIN herleitung_h32/power_h32.json:3540 [64] | rein |
| 103 | `SPEC_H32_herleitung.md` | `derivations/h32/SPEC_H32_herleitung.md` | `80bf0b84a6a8115d3177c50b37bdb1a64b451bc5497a9252c357182ea1c67482` | - | Sandbox: tmp 1, home 1 |

### `derivations/h32/run/` (4 Dateien)

| # | Quelle (scratchpad/) | Ziel (scinance3-impl/) | sha256 | Pin / Verweis in der Akte | Hygiene |
|---|---|---|---|---|---|
| 104 | `run_h32_pilot.sh` | `derivations/h32/run/run_h32_pilot.sh` | `b8b4e36bb442060767ecaea1e61fc568cf8e5ebbfabc3c039c904f168f2bc542` | Name UEBERGABE_2026-10-12.md:204 | Sandbox: tmp 1, home 2 |
| 105 | `run_h32_v6.sh` | `derivations/h32/run/run_h32_v6.sh` | `5602953a63ea10cbcadc3269f8f39387d38030ced1f763de785918a6cd3045ae` | - | Sandbox: tmp 3, home 2 |
| 106 | `run_h32_v6b.sh` | `derivations/h32/run/run_h32_v6b.sh` | `cbaaf1082cf900da1eaa7185dee13d9f137455fa8d0cd4a05bbf464b1309b302` | Name UEBERGABE_2026-10-12.md:184 | Sandbox: tmp 2, home 2 |
| 107 | `run_v5e.sh` | `derivations/h32/run/run_v5e.sh` | `d8e26997079f1c7f852a741e51aba450cf72b71985a00f316c68c1710be8f804` | - | Sandbox: tmp 3, home 1 |

### `verify/h32/` (20 Dateien)

| # | Quelle (scratchpad/) | Ziel (scinance3-impl/) | sha256 | Pin / Verweis in der Akte | Hygiene |
|---|---|---|---|---|---|
| 108 | `h32_review/rv_power.py` | `verify/h32/rv_power.py` | `62a344b3a9564b01183718f9e984a82d69001f353e43014c6d8b7768b97893a2` | Name herleitung_h32/REVIEW_H32.md:16 (+3) | Sandbox: home 2; FP: S3-Variable-FP |
| 109 | `h32_review/rv_oc.py` | `verify/h32/rv_oc.py` | `80ab9deb694087fdc1a53c340447a0a860d6eef87d344b7ae9c4bcb1975820ea` | Name herleitung_h32/REVIEW_H32.md:16 (+3) | Sandbox: home 1 |
| 110 | `h32_review/rv_ceiling.py` | `verify/h32/rv_ceiling.py` | `d2fe1998e33ab481d0b3db62f0234aadecbc98faa9a3c522ba923f331ebbe985` | Name herleitung_h32/REVIEW_H32.md:16 (+2) | Sandbox: home 1 |
| 111 | `h32_review/rv_inject.py` | `verify/h32/rv_inject.py` | `298827c0b132bc243b1ee9c11587cbf9d429ad130f22cabffbd677e0e2cc6542` | Name herleitung_h32/REVIEW_H32.md:16 (+2) | Sandbox: home 2 |
| 112 | `h32_review/rv_sector.py` | `verify/h32/rv_sector.py` | `483105a06ba0f3eb8e655425193841c433bb89ae7d25bca4cd8c246cc08383c3` | Name herleitung_h32/REVIEW_H32.md:16 (+2) | Sandbox: home 2 |
| 113 | `h32_review/rv_serule.py` | `verify/h32/rv_serule.py` | `8940fd98ddf37d9e7dd113c453fd2878e2fecea0a823b6db0c98174f4e164dad` | Name herleitung_h32/REVIEW_H32.md:16 (+2) | rein |
| 114 | `h32_review/rv_wc.py` | `verify/h32/rv_wc.py` | `3ecd96e3278ab956e256a7061d10c0575b5cc87525199165a0ce1ad00d698eaf` | Name herleitung_h32/REVIEW_H32.md:17 (+2) | Sandbox: home 1 |
| 115 | `h32_review/rv_attn.py` | `verify/h32/rv_attn.py` | `6588f85471814264c1797ad65d4957b3628a3d378125ec319745099a8f99b590` | Name herleitung_h32/REVIEW_H32.md:17 (+2) | rein |
| 116 | `h32_reg_review/rr_check.py` | `verify/h32/rr_check.py` | `806c1c9987705405d3d93a02413d9d12126ba37c2b3ab72ae38c5d8c51bb3123` | Name herleitung_h32/REVIEW_REGISTRIERUNG_H32.md:334 | Sandbox: home 1 |
| 117 | `h32_reg_review/rr_q95_mc.py` | `verify/h32/rr_q95_mc.py` | `f359ba7c0a67fba1a6b439afe2e16a13dcc6279e2df6a94731e0342319af7283` | Name herleitung_h32/REVIEW_REGISTRIERUNG_H32.md:337 | Sandbox: home 2 |
| 118 | `h32_reg_review/rr_size_twins.py` | `verify/h32/rr_size_twins.py` | `f7af73cd97a437a3408484151564b85df30b77e4e3028283b28e3e8e822781b5` | Name herleitung_h32/REVIEW_REGISTRIERUNG_H32.md:107 (+1) | Sandbox: home 1 |
| 119 | `h32_reg_review/rr_twins.py` | `verify/h32/rr_twins.py` | `d82777be14eda27b745874686b803fc09183b1035754848998937fa1f94215f1` | Name herleitung_h32/REVIEW_REGISTRIERUNG_H32.md:104 (+1) | rein |
| 120 | `h32_reg_review2/rr2_check.py` | `verify/h32/rr2_check.py` | `8d7a11db815cf8bcbab3b3ea6f77a72eb3bc39085d2372220d5b08c101ef9b27` | Name herleitung_h32/REVIEW_REGISTRIERUNG_H32_NACHPRUEFUNG.md:252 | Sandbox: home 1 |
| 121 | `h32_reg_review2/rr2_locks.py` | `verify/h32/rr2_locks.py` | `0e7f1edf525364e780acdbf0fd92e0265b36a56bf3e66eff363ada01d0c41ff3` | Name herleitung_h32/REVIEW_REGISTRIERUNG_H32_NACHPRUEFUNG.md:253 | Sandbox: tmp 1, home 2 |
| 122 | `h32_reg_review2/rr2_pk.py` | `verify/h32/rr2_pk.py` | `2d014af0ed22e9daaaa52c999d6f3abfddc50098712953a4522305cb7baf3533` | Name herleitung_h32/REVIEW_REGISTRIERUNG_H32_NACHPRUEFUNG.md:98 (+1) | Sandbox: home 2 |
| 123 | `h32_reg_review2/rr2_pk_f.py` | `verify/h32/rr2_pk_f.py` | `40208c84d557007b879d189c95f8fd23d533b17d1695612d2d8502b1821371bc` | Name herleitung_h32/REVIEW_REGISTRIERUNG_H32_NACHPRUEFUNG.md:114 (+1) | Sandbox: home 2 |
| 124 | `h32_reg_review2/rr2_u3k.py` | `verify/h32/rr2_u3k.py` | `e5fb981f664411ba615ceddde7b758f41e58436b889da605e6cac9cdb49462ca` | Name herleitung_h32/REVIEW_REGISTRIERUNG_H32_NACHPRUEFUNG.md:123 (+1) | Sandbox: home 1 |
| 125 | `SPEC_H32_review.md` | `verify/h32/SPEC_H32_review.md` | `8c3b1e33797fd9ed8a57124085fe29dcec5513c679c8f62df05d3df171deaa97` | - | Sandbox: tmp 3, home 1 |
| 126 | `SPEC_H32_registrierung_review.md` | `verify/h32/SPEC_H32_registrierung_review.md` | `c248652b5aef3aafd387a1b40517914aa0ccb0ba7f992424f4fb2bd943eb1acc` | - | Sandbox: tmp 2, home 2 |
| 127 | `orch_check/h32_v6_power.py` | `verify/h32/h32_v6_power.py` | `800123e66d33db8048c97dfb1ff2440ae197373a8113d9f058b1034b4df7467f` | Name herleitung_h32/REVIEW_REGISTRIERUNG_H32.md:7 | Sandbox: tmp 1 |

### `verify/h32/smoke/` (6 Dateien)

| # | Quelle (scratchpad/) | Ziel (scinance3-impl/) | sha256 | Pin / Verweis in der Akte | Hygiene |
|---|---|---|---|---|---|
| 128 | `h32_smoke/smoke1.py` | `verify/h32/smoke/smoke1.py` | `0520a0746581e1185e21470bf6722d4161640cba75028d6008999d6b02e7438c` | - | Sandbox: home 2, wt 2 |
| 129 | `h32_smoke/smoke2.py` | `verify/h32/smoke/smoke2.py` | `5e528ed9123c886d28dad6c0dc7e8dc32b4a5cf25e452f07d40f90f7cd4c7ad1` | - | Sandbox: tmp 1, home 2, wt 2 |
| 130 | `h32_smoke/smoke3.py` | `verify/h32/smoke/smoke3.py` | `7a7d95a3107898fcadd8ff86c6a55f908c3ab75b2fcd9d800961a938481a429c` | - | Sandbox: tmp 1, home 2, wt 2 |
| 131 | `h32_smoke/adv.py` | `verify/h32/smoke/adv.py` | `da001dd67f2a49306704c07c225c072773286462772ded30a632229f6ffa943f` | - | Sandbox: home 2, wt 2 |
| 132 | `h32_smoke/check_equal.py` | `verify/h32/smoke/check_equal.py` | `108bdd2999a7c9da922c2fc90ef6eb99f04d9dea3d6fe60b2996d8944af5a8e0` | - | Sandbox: home 2, wt 2 |
| 133 | `h32_smoke/perm_experiment.py` | `verify/h32/smoke/perm_experiment.py` | `42d4844160b85d2e4686b34ce66f26d163b70c1715a36465a5f1cba1192c142e` | - | Sandbox: home 2, wt 2 |

## 3. `stage_optional/` und nicht gestagte Kandidaten

Vom Orchestrator zu entscheiden. Alle hygiene-rein (ASCII, keine Treffer ausser Sandbox-Pfaden und den Falsch-Positiven aus Abschnitt 5.2). Spalte Pin/Verweis: `-` = weder gepinnt noch in der Akte genannt; `Name` = nur per Dateiname genannt, aber ausserhalb der Themenliste dieses Auftrags.

| # | Quelle (scratchpad/) | Ziel (scinance3-impl/) | sha256 | Pin / Verweis in der Akte | Hygiene |
|---|---|---|---|---|---|
| 1 | `a1_herleitung/a1_explore2.py` | `derivations/a1/a1_explore2.py` | `210e31e8788662e457a362f7a96c5c8f64ab8d7cfb3b0ec021965e873cf9b71e` | - | Sandbox: tmp 1 |
| 2 | `orch_check/a1_indep.py` | `verify/a1/a1_indep.py` | `78c0f93f45a14d67cc07f2fc04618961656b4b3f0d9e0d4145d57a9494710572` | - | rein |
| 3 | `h33_herleitung/surv_probe.py` | `derivations/h33/surv_probe.py` | `c9df3ee0677462473969a0e462f06b4a3d1e58fa2372fe52ab5fa0fa01a22345` | - | rein |
| 4 | `h32_herleitung/kseries.py` | `derivations/h32/kseries.py` | `0b61992210611415a37d7dc67f80e73e6f89717ed1dd2f67335f9648d2581cde` | - | rein |
| 5 | `h32_herleitung/extract_v5e.py` | `derivations/h32/extract_v5e.py` | `90d5b0ae7912a920af8cda1b69daad75dbc57ff69fb9c89ad6d68b3a6cd72002` | - | rein |
| 6 | `h32_herleitung/keys.py` | `derivations/h32/keys.py` | `30c992772458ec97dece797a5c4ddbed00d699c226a9e373251e50e956420963` | - | rein |
| 7 | `SPEC_H32_builder.md` | `derivations/h32/SPEC_H32_builder.md` | `00ab200247c1887a8220ef2633bed1fb88d82bc0557de4f76e6c3e6d32f99d77` | - | rein |
| 8 | `h32_review/guard.py` | `verify/h32/guard.py` | `2fc4902570028c0d9ce2aa7ada30dd190f1463c53a995cab74e0dff63b260990` | - | rein |
| 9 | `h32_review/keytree.py` | `verify/h32/keytree.py` | `7682dec9a0135df70b4fc235dce7eed01c3dd09eac126cb6d608a59e717eb1ca` | - | rein |
| 10 | `scripts/recompute.py` | `verify/gate_audit/recompute.py` | `03250081c1bcee2131f10968470814d489ba91ebcec747dc077caacb93c96229` | Name REVIEW_GATE_AUDIT_v5c_2026-10-12.md:308 | rein |
| 11 | `scripts/variants.py` | `verify/gate_audit/variants.py` | `56d5a794685515cc11f0c70e4f4376825f721839497e3643776abd9d961adb4c` | Name REVIEW_GATE_AUDIT_v5c_2026-10-12.md:309 | rein |
| 12 | `scripts/sens_sigma_e.py` | `verify/gate_audit/sens_sigma_e.py` | `0063ec7990dc816c7cc0ee7f67f1b45465b275d3a875a9e37027d9a80ef0d3d3` | Name REVIEW_GATE_AUDIT_v5c_2026-10-12.md:310 (+1) | Sandbox: home 1 |
| 13 | `scripts/sens_clean_btc.py` | `verify/gate_audit/sens_clean_btc.py` | `799c5a19de198f418b78dc42b5429628e7a40f7719307cb29572036d23e53979` | Name REVIEW_GATE_AUDIT_v5c_2026-10-12.md:313 | Sandbox: home 1 |
| 14 | `scripts/full_rule_clean.py` | `verify/gate_audit/full_rule_clean.py` | `c7ff9454f3ae27997abe510da230f6220348e53c2ee4b9bd763986a89e8d5e0c` | Name REVIEW_GATE_AUDIT_v5c_2026-10-12.md:315 | Sandbox: home 1 |
| 15 | `mc_ci.py` | `verify/gate_audit/mc_ci.py` | `3c61c58502767a4b1fab7aa52e18bf135558692ca0bde04705becfd866c2348f` | Name REVIEW_GATE_AUDIT_PC_v3_2026-10-12.md:122 | rein |
| 16 | `power_v5e.py` | `verify/gate_audit/power_v5e.py` | `c0ea77cd97299660306973c0916f7a48514bb4eb1a64d3f566a1f8617a4b5587` | Name REVIEW_GATE_AUDIT_PC_v3_2026-10-12.md:59 | rein |
| 17 | `SPEC_DEC101_builder.md` | `derivations/h32/SPEC_DEC101_builder.md` | `b60ff274441ca8bdc85333d13d5c03af4b944ef0406a0a16174def7a6ec7bae4` | Name UEBERGABE_2026-10-12.md:179 | rein |
| 18 | `SPEC_PDF_belege.md` | `derivations/pdf_belege/SPEC_PDF_belege.md` | `13ae852979a7fba7bedb29528bbd740a666a7a1d0fb5d1106647f3e354a89263` | - | Sandbox: tmp 2 |
| 19 | `pdf_belege/extract.py` | `derivations/pdf_belege/extract.py` | `b16d09632edda8b13c89e971b2d24bd81128b4a18bae952a41b40a468dcede6b` | Name BELEGE_AUS_PDF_2026-10-20.md:296 | rein |
| 20 | `pdf_belege/calc.py` | `derivations/pdf_belege/calc.py` | `898bbc1e90cea1f17067346ba100b2e41e1e0a87555031e7c596a2139e7a22e9` | Name BELEGE_AUS_PDF_2026-10-20.md:296 | rein |
| 21 | `pdf_belege/header.py` | `derivations/pdf_belege/header.py` | `cc1d1ae7d20b15e2bb8240981e5ee7fc148230b2ae5cd89a09ccf987a9675c40` | Name BELEGE_AUS_PDF_2026-10-20.md:296 | rein |

Einordnung: (a) ungepinnte, unreferenzierte Hilfsdateien der Themenordner: `a1_explore2.py`, `kseries.py`, `extract_v5e.py`, `keys.py`, `surv_probe.py`, `guard.py`, `keytree.py`, `a1_indep.py` (Orchestrator-Nachrechnung A1, in der Akte nicht genannt); (b) ausserhalb der Themenliste, aber in der Akte genannt: Gate-Audit-Skripte (`scripts/*.py`, `mc_ci.py`, `power_v5e.py`), `SPEC_DEC101_builder.md`, `SPEC_H32_builder.md`, die BELEGE_AUS_PDF-Skripte und `SPEC_PDF_belege.md`.

**Nicht gestaged wegen Hygiene-Regel:**

| Quelle | sha256 | Zeile | Art | Folge |
|---|---|---|---|---|
| `pdf_belege/period.py` | `8e573ccad8db10a365d427545f31b4b89ddcd75d35f4e3751f55d27dc0e7f977` | 12, 13 | Nicht-ASCII | nicht gestaged; kein Pin in der Akte (Name nur im Fliesstext von BELEGE_AUS_PDF); Pin-Konflikt entfaellt |

## 4. Pin-Inventar und verlorene Pins

### 4.1 Pins je Akten-Quelle

| Akten-Quelle (Feld bzw. Tabelle) | Pins | im Scratchpad mit passender sha256 | gestaged | Hinweis |
|---|---|---|---|---|
| a1/feasibility.json skripte | 14 | 14 | 14 |  |
| a2_vorarbeit.json skripte_sha256 | 8 | 8 | 8 |  |
| a2_vorarbeit.json wiederverwendet_sha256 | 3 | 2 | 2 | `power_p1.py` liegt im Repo (`src/bybit_edge/research/power_p1.py`), sha256 = Pin |
| h27/feasibility.json skripte_sha256 | 11 | 11 | 11 |  |
| h27/feasibility.json stand_2026_10_13_ueberholt | 4 | 4 | 4 |  |
| hfrv/nuisance_hfrv.json skripte_sha256 | 9 | 9 | 9 |  |
| hfrv/a2_census.json skript_sha256 | 3 | 3 | 3 |  |
| h32/power_h32.json skripte | 3 | 3 | 3 |  |
| h33/power_h33.json meta/skript | 1 | 1 | 1 |  |
| h33/nuisance_neg.json skript_sha256 | 1 | 1 | 1 |  |
| programm_bilanz.json skript | 1 | 1 | 1 |  |
| REVIEW_H27.md Abschn. 6 | 8 | 8 | 8 |  |
| REVIEW_HFRV.md Abschn. 7 | 5 | 5 | 5 |  |
| REVIEW_PROGRAMM_BILANZ.md | 3 | 3 | 3 |  |
| REVIEW_H33.md Z. 5/16 | 2 | 2 | 2 |  |

Nicht erneut geprueft (bereits in F0, Commit 093509b): `a2_teilC.json skripte_sha256` (8) und `REVIEW_A2_TEILC.md` Abschnitt 6 (5). `REVIEW_P1.md`: `rechnung_p1.py` liegt im Repo (`state/herleitung_programmregel_p1/`).

### 4.2 Pins ohne auffindbare Datei (verloren)

**Skripte: keine.** Alle 59 im Scratchpad zu erwartenden Skript-Pins sind aufgeloest und gestaged; 1 Pin (`power_p1.py`) liegt im Repo.

Gegenprobe: alle Zeilen der Akte (ohne `state/runs/`), die einen Skriptnamen (`*.py`, `*.sh`) und ein Hex-Token >= 8 enthalten, gegen Scratchpad- und Repo-Hashes gehalten: 27 Tokens ohne Treffer, ausnahmslos Daten-/Lauf-/Commit-Hashes oder Datumszahlen (z.B. `result_sha256` der Vorlaeufe, Parquet-Extrakte, Fassung-1-`a2_teilC.json` 5741d90c... (nie committet), `code_sha256`), keine Skript-Pins.

Akten-Verweise auf Scratch-Dateien, die weiterhin fehlen (aus F0 Abschnitt 4.2, ausserhalb dieses Auftrags): `prd/PRD_SCINANCE3_DRAFT.md`, `prd/PRD_SCINANCE3_v2.md`, `prd/REVIEW_PRD3.md` (PRD-Entwuerfe; Repo-Namensvettern in `scinance3-impl/prd/`).

## 4.3 Nicht gestagte Dateien in den Themenordnern

### 4.3.1 Per sha256 gepinnte Ergebnis-, Zwischen- und Fassungs-Dateien (keine Skripte; Ausgaben mit Nuisance-Zahlen werden nach DEC-103 N1 (2c) nicht gestaged)

Falls der Orchestrator sie sichern will, gehoeren sie in ein privates Archiv, nicht ins oeffentliche Repo. Sie sind per sha256 in der Akte nachweisbar; ohne sie ist nur der Hash-Vergleich einer Neurechnung moeglich.

| Scratch-Datei(en) | sha256 | erste Akten-Fundstelle | im Repo |
|---|---|---|---|
| `a2_review/replay/a2v_oi.json`, `a2_vorarbeit/f1_snapshot/a2v_oi.json`, `a2_vorarbeit/work/a2v_oi.json` | `f3559cc83522a9a0536ef75d94385f00a440ec13986700e339fc1e9e924c7006` | herleitung_a2/NUISANCE_SIGMA30.md:419 | nein |
| `a2_review/replay/a2v_power.json`, `a2_vorarbeit/f1_snapshot/a2v_power.json`, `a2_vorarbeit/work/a2v_power.json` | `552bf0d19d88289c5996ee719f72c089e21769120cb7eea9dbd3552a8d157394` | herleitung_a2/NUISANCE_SIGMA30.md:419 | nein |
| `a2_review/replay/a2v_sigma30.json`, `a2_vorarbeit/f1_snapshot/a2v_sigma30.json` | `7e98d0229d4dc286be9e792ee408cabb4e8c8d459ca152a6dd2a58c6d4a749b5` | herleitung_a2/NUISANCE_SIGMA30.md:419 | nein |
| `a2_review/replay/out/a2_vorarbeit.json`, `a2_vorarbeit/f1_snapshot/a2_vorarbeit.json` | `2bd1ad7e7118cc4018a3fab077f999673db6785222dbedbf77b173447367d30a` | decisions.md:573 | nein |
| `a2_review/rv_oi.json` | `8e2e6b80cbb5def73e43b62dc0b1050b1d38305d412b0ee072cf9a0df9ec47ca` | herleitung_a2/REVIEW_A2_VORARBEIT.md:134 | nein |
| `a2_review/rv_power.json` | `ea03414516a3b276bc44d0bda51970e67ba60f75c90a1f98ccf105d2b7ccc43c` | herleitung_a2/REVIEW_A2_VORARBEIT.md:134 | nein |
| `a2_review/rv_sigma.json` | `e7b85dd0bbbf55ba0db42d0deb8ba0706ee325d9fbd121b7113e9d11a6af37b3` | herleitung_a2/REVIEW_A2_VORARBEIT.md:134 | nein |
| `a2_vorarbeit/f1_snapshot/ENTSCHEIDUNGSVORLAGEN.md` | `e4118e314b20f31041fa96c48d4ec2e363c6754adfdc584bbf8be9b22fdc81f2` | herleitung_a2/REVIEW_A2_VORARBEIT.md:9 | nein |
| `a2_vorarbeit/f1_snapshot/NUISANCE_SIGMA30.md` | `ca31718fef57d3d6e7593d0161681fffc3b18026af5fa47eb14158f83bb4427a` | herleitung_a2/REVIEW_A2_VORARBEIT.md:8 | nein |
| `a2_vorarbeit/f1_snapshot/PLACEBO_DESIGN_A2.md` | `332fc3fef50337cfef8e01fc7718ce1bdcd87773eb034b8dfe4c380f28e452b7` | herleitung_a2/REVIEW_A2_VORARBEIT.md:8 | nein |
| `a2_vorarbeit/f2_json_before_rerun.json` | `9a2f5ac91a1ce7f8c71953afd2ef83a6b5ceeda150ff9c28a681905c9de26052` | derivations/a2/c_common.py:122 | ja: `state/herleitung_a2/a2_vorarbeit.json` |
| `a2_vorarbeit/work/a2v_corr2.json` | `048022fb82400dc1b272bb15b219b9d710f071618ddd014df02bce34d8077d73` | herleitung_a2/NUISANCE_SIGMA30.md:424 | nein |
| `a2_vorarbeit/work/a2v_fut.json` | `6590ba5a2c8775546b0053b2e985e63a6b262c37f7fa54e3acaa0413818e1bf9` | herleitung_a2/NUISANCE_SIGMA30.md:423 | nein |
| `a2_vorarbeit/work/a2v_konj.json` | `02f23c9d42606450e142a80dfc950c398c37ba36cb2a4ed02e630fff483e1e12` | herleitung_a2/NUISANCE_SIGMA30.md:424 | nein |
| `a2_vorarbeit/work/a2v_sigma30.json` | `37700ae3863fe7d890c1d58a75cbef16d92b7e87d0acef5d662ad02d8b674bb3` | herleitung_a2/NUISANCE_SIGMA30.md:422 | nein |
| `bilanz_review/review_check.json` | `92e8c17ac37fcd4d0ff45be0b980c575a04669936300a508301c3c08b3a39f9c` | REVIEW_PROGRAMM_BILANZ_2026-10-18.md:445 | nein |
| `drittfassung/registered_proposal.yaml` | `df36f45eb4e52880a74c9cdda0d14a8e42284595ce18841be1f47f22a590801c` | herleitung_h28_h30_v3/ABGLEICH.md:116 | nein |
| `drittfassung/registered_template.yaml` | `c2c7dff2b592647610b1a9a01a87eca7ad745afe2a074a2840224a44026b6a94` | herleitung_h28_h30_v3/DRITTFASSUNG_H28_H30_entwurf.md:685 | nein |
| `gegen_out1.txt`, `gegen_out1c.txt`, `gegen_out2.txt` | `703bb81d936650786f8265850cb2c74f0bf8acda2e48831c14424fffb04e5045` | herleitung_programmregel_p1/REVIEW_P1.md:18 | nein |
| `h32_reg_review/h32_v1_reemit.yaml` | `bddfb9cb8213fefee20a19cf4eb091be1058359732552732a061bea0b2a28d90` | herleitung_h32/REVIEW_REGISTRIERUNG_H32.md:225 | nein |
| `h32_reg_review2/h32_v1_reemit.yaml`, `h32_v1_TEMPLATE_u3.yaml` | `a3079cf93657c58eed0737972f15ee864ea649442eac33e84557fab4f2cebbe9` | UEBERGABE_2026-10-12.md:195 | nein |
| `h32_review/rerun_out_power.json` | `bcb0d91c3ab323480aedf451384acc6b6d5a018aa8484c040e5e7008058faa89` | herleitung_h32/REVIEW_H32.md:47 | nein |
| `h32_review/rerun_power_h32.json` | `df17cafa337bc548c01f08bb85bf2845cc87e203e39541d45804049b94d51bf3` | herleitung_h32/ENTSCHEIDUNGSVORLAGEN.md:28 | nein |
| `h32_v6b_run1/h32_prelaunch.json`, `h32_v6b_run2/h32_prelaunch.json` | `f872a3af25753e84db2ac99d412ccfecc349b8bbedab2fc23868d83ffed3f98c` | herleitung_h32/REGISTRIERUNG_H32_entwurf.md:171 | ja: `state/runs/h32_20261021_v6b/h32_prelaunch.json` |
| `h32_v6b_run1/h32_prelaunch_p_replicates.json`, `h32_v6b_run2/h32_prelaunch_p_replicates.json` | `3c498e0751f9b35aefa37dd380ad66e783ac6dc6b0c3d10f918fc95ec8f656ef` | herleitung_h32/REGISTRIERUNG_H32_entwurf.md:158 | ja: `state/runs/h32_20261021_v6b/h32_prelaunch_p_replicates.json` |
| `h33_herleitung/run1/nuisance_neg.json`, `h33_herleitung/run2/nuisance_neg.json` | `05e6f2a0a396d0be008579e6d160147c2002d7229a176a01c0f2c1b2076f0835` | gate_log.md:75 | ja: `state/herleitung_h33/nuisance_neg.json` |
| `h33_herleitung/run1/power_h33.json`, `h33_herleitung/run2/power_h33.json` | `026494b6681fb3d5b97d0e2cf77c9845b953bde7e31e97f976bbf3207b5b5bc9` | gate_log.md:75 | ja: `state/herleitung_h33/power_h33.json` |
| `h33_review/out1.json`, `h33_review/out2.json` | `97f76824d241bd48f0541b83b478d140a6601a39eab876e4e77ca3214bcf6fbe` | herleitung_h33/REVIEW_H33.md:17 | nein |
| `reg/h28_h30_v3.yaml` | `bd948f34516bb444f152287863e6096da6faf82712b579c6dfa211599015c299` | REVIEW_GATE_AUDIT_PC_v3_2026-10-12.md:17 | ja: `state/registered/h28_h30_v3.yaml` |

### 4.3.2 Uebrige Dateien der Themenordner (nicht gestaged; gezaehlt, nicht geoeffnet)

| Scratch-Ordner | nicht gestaged (Anzahl nach Endung) | Einordnung |
|---|---|---|
| `a1_herleitung/` | .json 12, .log 1, .pkl 1, .txt 8 | Zwischen-JSON, Logs (Nuisance-Ausgaben), `cache/` (Panel-Pickle = Marktdaten) |
| `a1_review/` | .json 2, .pkl 1 | `rv_*.json` (Review-Ausgaben), `cache/` |
| `a2_vorarbeit/` | .json 11, .md 3, .py 6, .txt 13 | `work/*.json` und `f1_snapshot/*.json` (Ergebnis-JSON), `f1_snapshot/*.md` (fruehe Fassungen der Akte-Dokumente), `docedit/*.py` (Editierhilfen fuer die Akte-Dokumente, kein Herleitungs-Code), Laufprotokolle `run*.txt`, `sha*.txt` |
| `a2_review/` | .json 7 | `rv_*.json`, `replay/` (Neurechnung der Fassung 1, Ergebnis-JSON), `__pycache__` |
| `h27_herleitung/` | .bak 1, .json 8, .log 4, .md 1, .parquet 2403 | Ergebnis-JSON/Logs, `hcache/` (Marktdaten), Entwurfs-md `FEASIBILITY_*.md(.bak)` |
| `h27_review/` | .json 4, .log 3, .parquet 2283 | Ergebnis-JSON/Logs, `hcache/` (Marktdaten) |
| `hfrv_herleitung/` | .md 1 | `tables.md` (Nuisance-Tabelle), `hcache` |
| `hfrv_review/` | .json 3, .py 9 | Ergebnis-JSON; `rerun/hfrv_herleitung/` = Kopien der Herleitung mit umgeleiteter Ausgabe (neun .py; acht byte-gleich zu `hfrv_herleitung/`, `hfrv_common.py` mit eigener sha256 268dc8b5..., nicht gepinnt) |
| `h33_herleitung/` | .json 4 | `run1/`, `run2/` (Ergebnis-JSON, bitgleich zu den Repo-Dateien) |
| `h33_review/` | .json 2, .txt 1 | `out1.json`, `out2.json`, `err1.txt` |
| `bilanz/` | .md 1 | `tables.md` |
| `bilanz_review/` | .json 2 | `review_check.json`, `rerun/programm_bilanz_rerun.json` |
| `h32_herleitung/` | .json 2 | `out_power.json`, `out_sector.json` |
| `h32_review/` | .json 4 | Ergebnis-JSON |
| `h32_reg_review/` | .json 4, .log 1, .yaml 1 | Ergebnis-JSON, `h32_v1_reemit.yaml`, Testlog |
| `h32_reg_review2/` | .json 5, .log 1, .yaml 1 | Ergebnis-JSON, `h32_v1_reemit.yaml`, Testlog |
| `h32_smoke/` | .csv 12, .json 4, .md 2, .pkl 1, .sha256 1 | `state.pkl` (Pickle, nicht geoeffnet), `out_pilot/`, `out_run/` (Smoke-Ausgaben, synthetisch) |
| `orch_check/` | .json 1 | `h32_v6_power.json` (Ergebnis-JSON) |

Ausserhalb der Themenliste nicht angefasst: `hscripts/` (13 Dateien; `fetch_client.py` und `fetch_panel.py` enthalten laut F0-Vorpruefung URL-/Zugangsmuster und werden nie gestaged; die uebrigen wurden hier nicht geoeffnet), `harvest_client/` (fremder Client), `hcache/`, `hf_data/raw/` (Marktdaten), `panel*/`, Top-Level-Hilfsdateien des Scratchpads (`e1.py`..`e19.py`, `chk*.py`, `review_p1_check*.py`, `*_builder.md` ausser den zwei oben genannten, `draft_*.md`, `*.patch`, `*.log`) und `builder*/`. `review_p1_check*.py` und die uebrigen `SPEC_*_builder.md` sind in der Akte nicht per Namen genannt.

## 5. Hygiene-Befunde (Datei, Zeile, Art; ohne Werte)

### 5.1 Echte Treffer

**Keine** in den gestagten Dateien (Pflichtumfang und optional). Kein Hostname, keine URL, keine IP-Adresse, kein Endpunkt/Bucket-Name, keine Zugangsdaten, kein Token, keine E-Mail-Adresse, kein Produktname eines Sprachmodells, keine Nicht-ASCII-Zeichen. Werte der `HARVEST_S3_*`-Variablen (inkl. Hostanteil): 0 Treffer in 343 Dateien.

### 5.2 Muster-Treffer, von Hand als Falsch-Positive geklaert

| Art | Dateien (Zeilen) | Klaerung |
|---|---|---|
| Modellname `claude` (98 Zeilen in den gestagten Dateien) | alle Dateien mit Sandbox-Pfad `/tmp/claude-0/...`, `.claude/worktrees/...` oder dem Dateinamen `CLAUDE.md` | ausnahmslos Pfad- bzw. Dateiname, kein Modellname (Test: nach Entfernen dieser Teilstrings 0 Treffer); sonstige Produktnamen (opus, sonnet, haiku, anthropic, gpt, gemini, llama, copilot, co-authored-by): 0 |
| Umgebungsvariablen-Zugriff | `derivations/a1/a1_common.py` Z. 60 (`os.environ.get` fuer den Schalter `A1_EXCL1H`), `derivations/h32/assemble.py` Z. 39 (`os.environ.get` fuer `H32_REPO`, Default = Sandbox-Pfad); `derivations/h27/SPEC_H27_herleitung.md` Z. 14, 24 (nur die erlaubten Namen `HARVEST_S3_*`) | keine Werte, keine Zugangsdaten |
| Client-Anbindung (`harvest_data`) | `derivations/h27/h27_common.py` Z. 29-30, `catalog_check.py` Z. 16-17, `catalog_check2.py` Z. 13-14, `derivations/hfrv/h27_common.py` Z. 29-30; Specs `SPEC_H27_herleitung.md` Z. 22-23, `verify/h27/SPEC_H27_review.md` Z. 14 | `sys.path`-Einbindung des fremden Clients im Geschwisterordner `harvest_client/` und Modulimport; weder Host noch Schluessel im Skript; der Client selbst und seine Zugangs-Doku bleiben ausserhalb des Repos |
| Hostname-Muster | `derivations/a2/teilAB/a2v_sigma30.py` Z. 133 und `fassung1/a2v_sigma30.py` Z. 128 (`np.add.at(...)`, `.at` als TLD erkannt); `derivations/h27/catalog_check.py` Z. 26, `catalog_check2.py` Z. 20 (`hd.info()`, `.info` als TLD erkannt) | Methodenaufrufe |
| S3-/Bucket-/Endpunkt-Woerter | Variablen `S1/S2/S3` und `s3` (Statistik- bzw. Fenster-Namen) in h27/hfrv/h32/bilanz-Skripten; Text `Harvest-Bucket nie listen` in `SPEC_H27_*`; Kommentare `No endpoint/host is printed or stored` (`catalog_check.py` Z. 7) und `shared endpoint` (`verify/h27/rv_common.py` Z. 64) | keine Endpunkte, keine Bucket-Namen |
| E-Mail-Muster | nur in nicht gestagtem `review_p1_check.py` Z. 162, 185 (`exact@2.5287`, Format-Text) | nicht gestaged (ausserhalb der Themenliste, unreferenziert), Falsch-Positiv |

### 5.3 Bekannte Sandbox-Pfade (dokumentiert, kein Treffer)

| Zielordner | Dateien | davon mit `/tmp/claude-0/.../scratchpad/...` | mit `/home/user/...` | mit `.claude/worktrees/...` |
|---|---|---|---|---|
| `derivations/a1/` | 16 | 15 | 2 | 0 |
| `derivations/a2/teilAB/` | 15 | 2 | 5 | 0 |
| `derivations/bilanz/` | 3 | 2 | 3 | 0 |
| `derivations/h27/` | 12 | 1 | 3 | 0 |
| `derivations/h32/` | 13 | 5 | 6 | 0 |
| `derivations/h33/` | 3 | 2 | 1 | 0 |
| `derivations/hfrv/` | 10 | 4 | 7 | 0 |
| `derivations/pdf_belege/` | 4 | 1 | 0 | 0 |
| `verify/a1/` | 7 | 6 | 4 | 0 |
| `verify/a2/teilAB/` | 15 | 9 | 4 | 0 |
| `verify/bilanz/` | 3 | 2 | 3 | 0 |
| `verify/gate_audit/` | 7 | 0 | 3 | 0 |
| `verify/h27/` | 9 | 1 | 3 | 0 |
| `verify/h32/` | 28 | 6 | 22 | 6 |
| `verify/h33/` | 2 | 1 | 1 | 0 |
| `verify/hfrv/` | 7 | 2 | 3 | 0 |

`/home/user/scinance/...` (Repo-Wurzel, `src/`, `state/`) ist der Sandbox-Standard; `/tmp/claude-0/.../scratchpad/...` ist der Ordner des damaligen Sitzungs-Scratchpads (enthaelt eine Sitzungs-UUID, keinen Personennamen); `.claude/worktrees/agent-<id>` sind Agenten-Worktrees der Smoke-Skripte. Keine Pfade mit anderen Nutzernamen, kein `/root`, kein `~`. Decision des Orchestrators (Option a): stehen lassen, in den README dokumentieren.

## 6. README-Vorschlaege je Zielordner

Als Dateien: `scratchpad/prd_review/f0b/readme_vorschlaege/<Zielordner>/README.md`. Vorgeschlagen werden 14 README fuer die Pflicht-Zielordner plus zwei fuer die optionalen Ordner. Eingabe-sha256 und Ergebnis-sha256 sind aus den committeten Akten-JSON bzw. den Repo-Dateien uebernommen (nicht abgetippt).

### 6.1 `scinance3-impl/derivations/a1/README.md`

```
# derivations/a1 - Herleitung A1 (H-31), Stufe 1: Feasibility vor jedem Design (outcome-blind)

Zweck: Fensterzensus, Nuisance (SD, Autokorrelation, Varianzfaktor c), Formations-Sensitivitaet, Power/MDE80 und
Kill-4-CI des Funding-Sortier-Kandidaten A1 auf der Vorperiode. Outcome-Groessen nur fuer Haltewochen, die vor 2024-07-01
enden (Waechter assert_nuisance_holding_week in a1_common.py); keine Woche nach 2026-06-28 wird beruehrt.

Dateien: a1_common.py (Lader, Konstanten, Waechter), a1_explore.py (Union-Panel einmal laden, Cache), a1_window_census.py,
a1_nuisance.py, a1_formation_sensitivity.py, a1_psi_by_class.py, a1_power.py, a1_kill4_ci.py, a1_check_factor.py,
a1_selfcheck.py, a1_bookkeeping.py, a1_model.py, a1_consolidate.py (Montage feasibility.json), run_all.sh,
SPEC_A1_herleitung.md (Auftrag an die Herleitung). Die 14 Skripte sind byte-identisch zu den Pins in
state/herleitung_a1/feasibility.json (Feld skripte). Nicht gepinnt, daher nicht hier: a1_explore2.py (Exploration).

Reproduktion (nur mit dem Panel ausserhalb des Repos; Marktdaten sind nicht im Repo):
  Eingabe: Union-Panel (panel_1d + panel_1d_delisted), geladen ueber den Repo-Lader wp7_universe.panel_load.
    Fingerabdruck laut feasibility.json: union_range_sha256 a7e4dec7cb7475426f477c6d17359007b75026b2f8562b29e66457fed027793a
                                          delisting_dates_sha256 852bf75332fd1990b13b9a059fd871a75d7f71757b48e2bf102bc1f25c412933
  Aufruf: sh run_all.sh (beide Konfigurationen A1_EXCL1H=0/1, danach Kill-4, Selbstcheck, Buchhaltung, Montage).
  Ergebnis in der Akte: state/herleitung_a1/feasibility.json (sha256 b4680f7c0b7e58ce9a6fa256f6913656cb8b432b55b40bc915aa0f930ca72d9e; Feld skripte = Pins),
  FEASIBILITY.md, REVIEW_A1.md (Review: ../../verify/a1/).

Warnungen:
- a1_consolidate.py schreibt state/herleitung_a1/feasibility.json (a1_common.OUT): nur in einer Wegwerfkopie des Repos laufen lassen.
- a1_explore.py schreibt cache/a1_data.pkl (Panel-Cache = Marktdaten) neben das Skript: nie committen (.gitignore).
- Warnung Sandbox-Pfade (bekannt, unschaedlich; Entscheid Orchestrator 2026-11-02, Option a): Die Dateien sind
  BYTE-IDENTISCH zu den per sha256 gepinnten Fassungen und tragen deshalb Pfade der Entstehungs-Sandbox
  (/home/user/scinance/... und, in einem Teil der Skripte/Specs, /tmp/claude-0/.../scratchpad/... des damaligen Sitzungs-
  Scratchpads). Es sind keine Zugangsdaten und keine Hosts. Ohne Anpassung laufen die Skripte nur in einem Layout, das diese
  Pfade nachbildet; jede Aenderung (auch Kommentar, Pfad, Umlaut) bricht den Pin und braucht eine neue Fassung mit neuer sha256.
```

### 6.2 `scinance3-impl/derivations/a2/teilAB/README.md`

```
# derivations/a2/teilAB - Herleitungsskripte A2-Vorarbeit Teil A und B (EXP-CLOCK, DEC-98 Nachtrag 7)

Zweck: Teil A: Verfalls-OI, Kalender, Zeitlage der Slots; Teil B: sigma30-Nuisance der Vorperiode 2021-03-24..2024-05-31
(Streuung, Korrelation, Varianzfaktor), Power/MDE80 und Konjunktions-Power (Fassung 2, Auflagen A-1..A-6). Nur Streuung,
Zaehlungen, Korrelationen; kein Mittel, kein Median, kein Vorzeichen einer Verfallstag-Rendite (Waechter a2v_common.guard_keys).

Dateien: a2v_common.py (Regeln, Waechter, Lader), a2v_oi.py, a2v_sigma30.py, a2v_power.py, a2v_fut.py, a2v_corr2.py,
a2v_konj.py, a2v_build.py (Montage a2_vorarbeit.json), run_all.sh; SPEC_A2_vorarbeit.md (Auftrag Fassung 1),
SPEC_A2_auflagen.md (Auftrag Fassung 2). Die 8 a2v_*.py sind byte-identisch zu den Pins in state/herleitung_a2/a2_vorarbeit.json
(Feld skripte_sha256, Fassung 2). run_all.sh ist nicht gepinnt (nur per Namen in NUISANCE_SIGMA30.md Abschnitt 9 genannt).
fassung1/: Skripte, die die Ergebnisse der Fassung 1 erzeugten (a2v_common, a2v_sigma30, a2v_build, run_all.sh);
  a2v_oi.py und a2v_power.py waren in Fassung 1 und 2 identisch. Fassung-1-JSON sha256 2bd1ad7e7118...d30a (nicht im Repo;
  in NUISANCE_SIGMA30.md Abschnitt 9 und decisions.md DEC-98 N7 genannt); die Skript-sha256 der Fassung 1 stehen nur in jener
  nicht committeten JSON (Abgleich in F0b: alle fuenf stimmen).

Reproduktion (nur mit den Extrakten ausserhalb des Repos; Marktdaten sind nicht im Repo):
  Eingaben (sha256 laut a2_vorarbeit.json, inputs_sha256):
    bybit_rest_kline1m_BTCUSDT_2021-03-24_2024-05-31.parquet  94b9602f941716f4d3db9d1521323bc1d6e605088eabc273ee3b25013bdc98b8
    bybit_rest_kline1m_ETHUSDT_2021-03-24_2024-05-31.parquet  e5ba03b5b79f14bfd27bc16306ea2a8851c2307bc1b7600b37f9c58447e90785
    deribit_rest_settlements_CALENDAR_2017-05-25_2026-10-20.parquet  7ae48dcd6f99ef48d3166fbcc0b8188238e14cc48e3509d70f452be85b77f46f
    Settlement-Rohpartitionen <= 2026-06-30: 4578 Dateien, sha256 der sortierten Liste bd758d37ea5f6a421cc6c46db935c6aa9c0c11ade498e5a4baca6b4d230793b9
  Wiederverwendet (ungeaendert): hfrv_common.py (load_kline; ../../hfrv/, sha256 490691590501...5ba3), h27_common.py (../../h27/,
    4093396d3183...e085ee), src/bybit_edge/research/power_p1.py (74a8dedec983...d111).
  Layout: a2v_common.py erwartet Geschwisterordner <root>/hfrv_herleitung/ (mit hfrv_common.py, h27_common.py, h27_series.py,
    nuisance.py, power_h27.py), <root>/hf_data/raw/ (Parquet-Extrakte), <root>/hcache/raw/deribit/rest.settlements/ (Rohpartitionen)
    und <root> = Elternordner des Skriptordners. Aufruf: sh run_all.sh (Skriptordner = <root>/a2_vorarbeit/).
  Ergebnis in der Akte: state/herleitung_a2/a2_vorarbeit.json (Fassung 2, sha256 9a2f5ac91a1ce7f8c71953afd2ef83a6b5ceeda150ff9c28a681905c9de26052), NUISANCE_SIGMA30.md,
  PLACEBO_DESIGN_A2.md, ENTSCHEIDUNGSVORLAGEN.md. Review: ../../../verify/a2/teilAB/. Teil C: ../ (derivations/a2/).

Warnungen:
- a2v_build.py schreibt per Voreinstellung (a2v_common.OUT_DIR) nach state/herleitung_a2/a2_vorarbeit.json und ueberschreibt
  die committete Akte: nur in einer Wegwerfkopie laufen lassen. work/ (Zwischenausgaben a2v_*.json) NICHT committen (DEC-103 N1 (2c)).
- Die Zwischenausgaben (work/a2v_oi.json u.a.) tragen Nuisance-Zahlen und die in A-2 (DEC-103 N1 Nachtrag 1) genannte
  Schachtelungs-Struktur: Ausgaberegel (c) beachten; Struktur-Scan mit ../../../tools/channel_scan.py.
- Warnung Sandbox-Pfade (bekannt, unschaedlich; Entscheid Orchestrator 2026-11-02, Option a): Die Dateien sind
  BYTE-IDENTISCH zu den per sha256 gepinnten Fassungen und tragen deshalb Pfade der Entstehungs-Sandbox
  (/home/user/scinance/... und, in einem Teil der Skripte/Specs, /tmp/claude-0/.../scratchpad/... des damaligen Sitzungs-
  Scratchpads). Es sind keine Zugangsdaten und keine Hosts. Ohne Anpassung laufen die Skripte nur in einem Layout, das diese
  Pfade nachbildet; jede Aenderung (auch Kommentar, Pfad, Umlaut) bricht den Pin und braucht eine neue Fassung mit neuer sha256.
```

### 6.3 `scinance3-impl/derivations/h27/README.md`

```
# derivations/h27 - Herleitung H-27 (VRP auf DVOL-Backfill), Stufe 1: Feasibility (C.12), Nuisance, Nullwelt, Power

Zweck: Praemien-Reihe (IV minus RV, drei Einheiten S1/S2/S3), Nuisance (SD, ACF, Varianzfaktor c nach Regel P-3), Nullwelt-
SE, Power/MDE80 und Datenproben (Katalog, Schema, DVOL, Panel-Konvention). Nur Nuisance der Vorperiode; kein Praemien-Mittel.

Dateien: h27_common.py (Lader, Waechter, Client-Anbindung), h27_series.py, nuisance.py, nullworld.py, power_h27.py,
panel_coverage.py, catalog_check.py, catalog_check2.py, conv_check.py, dvol_probe.py, schema_probe_stream.py,
SPEC_H27_herleitung.md (Auftrag). Alle 11 Skripte sind byte-identisch zu den Pins in state/herleitung_h27/feasibility.json
(skripte_sha256; Stand 2026-10-13 ueberholt: 4 davon, gleiche sha256).

Reproduktion (nur in einer Sitzung mit Archivzugang; Marktdaten sind nicht im Repo):
  Eingabe: Data-Harvest-Archiv ueber den fremden Client (Geschwisterordner harvest_client/ mit harvest_data.py; bleibt ausserhalb
    des Repos, enthaelt Zugangs-Doku). Zugang ausschliesslich ueber die Umgebungs-Secrets HARVEST_S3_ENDPOINT / HARVEST_S3_ACCESS_KEY /
    HARVEST_S3_SECRET_KEY; die Skripte enthalten weder Host noch Schluessel. Katalog-Fingerabdruck: partitions_sha256 031bc30871cd06d893bcce1f9a01bacbb7e1512f242ad8ec544dfa041e14c7d7.
  Aufruf: je Skript python3 -I <skript>.py im Skriptordner (Cache hcache/ entsteht daneben; Marktdaten, nie committen).
  Ergebnis in der Akte: state/herleitung_h27/feasibility.json (sha256 097a7966cfbf83c297d4dc934fc8fbd01d4e612efb45c67b8ba591337d389319), FEASIBILITY.md, DATENPROBE.md,
  KONTAMINATION.md; Review: ../../verify/h27/. Die HF-RV-Fortsetzung steht in ../hfrv/ (nutzt dieselben Module).

Warnungen:
- Ausgaben (nuisance.json, power.json, *.log) entstehen im Skriptordner: nie committen (DEC-103 N1 (2c)).
- Warnung Sandbox-Pfade (bekannt, unschaedlich; Entscheid Orchestrator 2026-11-02, Option a): Die Dateien sind
  BYTE-IDENTISCH zu den per sha256 gepinnten Fassungen und tragen deshalb Pfade der Entstehungs-Sandbox
  (/home/user/scinance/... und, in einem Teil der Skripte/Specs, /tmp/claude-0/.../scratchpad/... des damaligen Sitzungs-
  Scratchpads). Es sind keine Zugangsdaten und keine Hosts. Ohne Anpassung laufen die Skripte nur in einem Layout, das diese
  Pfade nachbildet; jede Aenderung (auch Kommentar, Pfad, Umlaut) bricht den Pin und braucht eine neue Fassung mit neuer sha256.
```

### 6.4 `scinance3-impl/derivations/hfrv/README.md`

```
# derivations/hfrv - Herleitung HF-RV-Nuisance (Option 3, DEC-98) und A2-Ereigniszensus

Zweck: Nuisance der Praemie mit Hochfrequenz-RV (1-min-Kerzen) und DVOL der Vorperiode 2021-03-24..2024-05-31 (nur Streuung,
Verhaeltnisse, RV-Niveau; kein Praemien-Mittel), Power/Rauschboden und Tabellen; a2_census.py: Zensus der Verfallsereignisse
(Deribit-Kalender, deliveryPrices) fuer A2.

Dateien: hfrv_common.py (Regeln R-1.., Lader load_kline, Waechter), hfrv_power.py, nuisance_hfrv.py, a2_census.py,
make_tables.py (liest nuisance_hfrv.json, schreibt tables.md); SPEC_HFRV_herleitung.md (Auftrag). Dubletten aus ../h27/ (byte-gleich,
weil hfrv_common.py sie per sys.path aus demselben Ordner laedt): h27_common.py, h27_series.py, nuisance.py, power_h27.py.
Alle 9 Skripte sind byte-identisch zu den Pins in state/herleitung_hfrv/nuisance_hfrv.json (skripte_sha256) bzw. a2_census.json (skript_sha256).

Reproduktion (nur mit den Extrakten ausserhalb des Repos; Marktdaten sind nicht im Repo):
  Eingaben (sha256 laut nuisance_hfrv.json / a2_census.json, inputs_sha256):
    bybit_rest_kline1m_BTCUSDT_2021-03-24_2024-05-31.parquet  94b9602f941716f4d3db9d1521323bc1d6e605088eabc273ee3b25013bdc98b8
    bybit_rest_kline1m_ETHUSDT_2021-03-24_2024-05-31.parquet  e5ba03b5b79f14bfd27bc16306ea2a8851c2307bc1b7600b37f9c58447e90785
    deribit_dvol_raw_2021-03-24_2024-05-31.parquet  9a30c31269bd1be112707eea429aa8ecba07981c00630064724705727baf2e15
    deribit_rest_settlements_CALENDAR_2017-05-25_2026-10-20.parquet  7ae48dcd6f99ef48d3166fbcc0b8188238e14cc48e3509d70f452be85b77f46f
    deribit_rest_deliveryPrices_DATES_2016-03-18_2026-10-20.parquet  efb5bc355ef74ff049b91b9756336f0983f762196f48f72a55b978f1e0535dca
  Layout: hfrv_common.py erwartet <root>/hfrv_herleitung/ (dieser Ordner) und liest <root>/hf_data/raw/ sowie das Tages-Panel <root>/panel/panel_1d/ (BTC/ETH-Preisreihe); H27_FJ zeigt auf die
    committete state/herleitung_h27/feasibility.json. Aufruf: python3 -I nuisance_hfrv.py, python3 -I a2_census.py, python3 -I make_tables.py.
  Ergebnis in der Akte: state/herleitung_hfrv/nuisance_hfrv.json (sha256 3c03e5bfd3fb3e289c8d690696baababe7ddc2457710373afef8fb8cddd74fed),
  a2_census.json (sha256 99ba72f7353f93ff45c67b58ecc3fa0b012a12ecf7d0e8a26c39e8f09fdadf6d),
  NUISANCE_HFRV.md, A2_EREIGNISZENSUS.md; Review: ../../verify/hfrv/.

Warnungen:
- hfrv_common.OUT_DIR = state/herleitung_hfrv: nuisance_hfrv.py und a2_census.py ueberschreiben die committeten JSON (nur in
  Wegwerfkopie laufen lassen). tables.md (make_tables.py) enthaelt Nuisance-Zahlen: nicht committen (DEC-103 N1 (2c)).
- Warnung Sandbox-Pfade (bekannt, unschaedlich; Entscheid Orchestrator 2026-11-02, Option a): Die Dateien sind
  BYTE-IDENTISCH zu den per sha256 gepinnten Fassungen und tragen deshalb Pfade der Entstehungs-Sandbox
  (/home/user/scinance/... und, in einem Teil der Skripte/Specs, /tmp/claude-0/.../scratchpad/... des damaligen Sitzungs-
  Scratchpads). Es sind keine Zugangsdaten und keine Hosts. Ohne Anpassung laufen die Skripte nur in einem Layout, das diese
  Pfade nachbildet; jede Aenderung (auch Kommentar, Pfad, Umlaut) bricht den Pin und braucht eine neue Fassung mit neuer sha256.
```

### 6.5 `scinance3-impl/derivations/h33/README.md`

```
# derivations/h33 - Herleitung H-33 (beta-neutrales Kurzfrist-Reversal), outcome-frei, aus der H-32-Nuisance

Zweck: Umrechnung der v6b-Nuisance von H-32 auf die NEGATIVE Richtung, Literatur-Prior-Band, Power-Linien und Prior-Gitter (DEC-102
Option (a)). Kein Panel, kein Outcome, kein Harvest-Client.

Dateien: h33_compute.py (Skript sha256 ef0788a0cca30cfa27b3afe53f106ffeea5411237f8f4c0d821c649a2ef346b0, gepinnt in power_h33.json meta.skript und nuisance_neg.json skript_sha256),
SPEC_H33_herleitung.md (Auftrag).

Reproduktion (vollstaendig aus Repo-Dateien moeglich, keine Marktdaten):
  Eingaben (sha256 laut power_h33.json meta.eingaben_sha256):
    h32_v1_yaml     0fadda785f37a9ab24b31f650611a468f5c6bfef8be8fb65a7dc54261c1bbd60
    spread_census   fa1546be8216564005b21827190549b44edf8f5353602e5173b5d4f6497e7083
    v6b_json        f872a3af25753e84db2ac99d412ccfecc349b8bbedab2fc23868d83ffed3f98c
    v6b_replicates  3c498e0751f9b35aefa37dd380ad66e783ac6dc6b0c3d10f918fc95ec8f656ef
  Aufruf: python3 -I h33_compute.py <repo_root> <out_dir>   (zweimal, Ergebnis bitgleich; out_dir ausserhalb von state/).
  Ergebnis in der Akte: state/herleitung_h33/power_h33.json (sha256 026494b6681fb3d5b97d0e2cf77c9845b953bde7e31e97f976bbf3207b5b5bc9),
  nuisance_neg.json (sha256 05e6f2a0a396d0be008579e6d160147c2002d7229a176a01c0f2c1b2076f0835),
  ENTSCHEIDUNGSVORLAGEN.md; Review: ../../verify/h33/.

Warnungen:
- Ausgabe in ein eigenes out_dir leiten, nicht auf die committeten JSON (Nuisance-Dateien, DEC-103 N1 (2c)).
- Warnung Sandbox-Pfade (bekannt, unschaedlich; Entscheid Orchestrator 2026-11-02, Option a): Die Dateien sind
  BYTE-IDENTISCH zu den per sha256 gepinnten Fassungen und tragen deshalb Pfade der Entstehungs-Sandbox
  (/home/user/scinance/... und, in einem Teil der Skripte/Specs, /tmp/claude-0/.../scratchpad/... des damaligen Sitzungs-
  Scratchpads). Es sind keine Zugangsdaten und keine Hosts. Ohne Anpassung laufen die Skripte nur in einem Layout, das diese
  Pfade nachbildet; jede Aenderung (auch Kommentar, Pfad, Umlaut) bricht den Pin und braucht eine neue Fassung mit neuer sha256.
```

### 6.6 `scinance3-impl/derivations/bilanz/README.md`

```
# derivations/bilanz - Programm-Bilanz P-2: Power-Zensus ueber die verbleibenden Kandidaten

Zweck: Power/MDE/Zuordnung je Kandidat aus den Nuisance-Groessen der Akte (kein Outcome, kein Panel, keine DVOL-/Trade-Daten);
alle Power-Zahlen laufen ueber bybit_edge.research.power_p1 (DEC-94 (8)); Tabellen im Markdown.

Dateien: bilanz_census.py (sha256 4f90415f428e022cb9a8f32326eba2ad008e70fc3350b3507e54ad6612c34bfb, gepinnt in programm_bilanz.json Feld skript), make_tables.py (liest
programm_bilanz.json, schreibt tables.md; nur per Name in PROGRAMM_BILANZ_2026-10-18.md genannt), SPEC_BILANZ_power_zensus.md (Auftrag).

Reproduktion (aus Repo-Dateien, keine Marktdaten):
  Eingaben (programm_bilanz.json quellen_sha256):
    wp13a_20261012_v5e/wp13a_prelaunch.json  94d655599b90a0841fef3e3a77404e12f216e2c7281e337208042c0a475ae3b2
    herleitung_a1/feasibility.json           b4680f7c0b7e58ce9a6fa256f6913656cb8b432b55b40bc915aa0f930ca72d9e
    herleitung_h27/feasibility.json          097a7966cfbf83c297d4dc934fc8fbd01d4e612efb45c67b8ba591337d389319
    wp7_20260921/wp7_report.json             eb79a63b64c21651f97d6aabe2c0e2b3fba07ccabf8489201ba697cc05d27e6f
  Aufruf: PYTHONPATH=/home/user/scinance/src python3 -I bilanz_census.py, danach python3 -I make_tables.py.
  Ergebnis in der Akte: state/programm_bilanz.json (sha256 c4b2970251f8933920fff057b921056376e74c6521455bacf04eddfe8748cb4f), PROGRAMM_BILANZ_2026-10-18.md,
  REVIEW_PROGRAMM_BILANZ_2026-10-18.md; Review: ../../verify/bilanz/.

Warnungen:
- bilanz_census.py schreibt state/programm_bilanz.json direkt (OUT_JSON) und ueberschreibt die committete Datei: nur in Wegwerfkopie.
- Warnung Sandbox-Pfade (bekannt, unschaedlich; Entscheid Orchestrator 2026-11-02, Option a): Die Dateien sind
  BYTE-IDENTISCH zu den per sha256 gepinnten Fassungen und tragen deshalb Pfade der Entstehungs-Sandbox
  (/home/user/scinance/... und, in einem Teil der Skripte/Specs, /tmp/claude-0/.../scratchpad/... des damaligen Sitzungs-
  Scratchpads). Es sind keine Zugangsdaten und keine Hosts. Ohne Anpassung laufen die Skripte nur in einem Layout, das diese
  Pfade nachbildet; jede Aenderung (auch Kommentar, Pfad, Umlaut) bricht den Pin und braucht eine neue Fassung mit neuer sha256.
```

### 6.7 `scinance3-impl/derivations/h32/README.md`

```
# derivations/h32 - Herleitung H-32 (Zwei-Stufen-Design, fm8-Daempfung) und Laufskripte der Vorlaeufe

Zweck: h32_power.py: Power/MDE/Zuordnung/Uebergabeschwelle aus der Nuisance der Akte (v5e-Vorlauf-JSON, WP-7-Wochen-K, A1-Pilotbasis);
sector_check.py: synthetischer Sektor-/Power-Check (keine Marktdaten); assemble.py: Montage power_h32.json. run/: Laufskripte der
Vorlaeufe und des Pilots (rufen scripts/h32_fm8.py bzw. scripts/wp13_xsec.py des Repos).

Dateien: assemble.py, h32_power.py, sector_check.py (je byte-identisch zu den Pins in state/herleitung_h32/power_h32.json, Feld skripte),
SPEC_H32_herleitung.md; run/run_h32_pilot.sh (Pilot, DEC-101 Teil 2), run/run_h32_v6.sh, run/run_h32_v6b.sh (Vorlauf v6b zweimal),
run/run_v5e.sh (wp13a-v5e-Vorlauf, erzeugt state/runs/wp13a_20261012_v5e; das Ergebnis wp13a_prelaunch.json ist in der Akte mit
sha256 94d655599b90a0841fef3e3a77404e12f216e2c7281e337208042c0a475ae3b2 vielfach gepinnt). run_h32_v6.sh und run_v5e.sh sind per Namen nicht in der Akte genannt.

Reproduktion von power_h32.json (aus Repo-Dateien, keine Marktdaten):
  Eingaben: v5e-Vorlauf-JSON (sha256 94d655599b90a0841fef3e3a77404e12f216e2c7281e337208042c0a475ae3b2);
    WP-7-Wochen-K-Reihe decile_degeneration_weekly.csv (nur Spalten week, n_symbols; sha256 7c6119afe3bbaa862acd5f65bfcb3e53ffb8244e7056aba7f5a56df3a0fac9e5); A1-Pilotbasis-Metadaten.
  Aufruf: PYTHONPATH=<repo>/src python3 h32_power.py <repo> <out>; sector_check.py <repo> <power_json> <out>; assemble.py <scratch_dir> <out>.
  Ergebnis in der Akte: state/herleitung_h32/power_h32.json (sha256 f0d6e6d9c55e0a9326ab5b32988eb86bbd0c62ef283b0c3101a4889a402a56a3), ENTSCHEIDUNGSVORLAGEN.md; Review: ../../verify/h32/.

Warnungen:
- run/*.sh NICHT ausfuehren: sie schreiben nach state/runs/ bzw. benoetigen das Panel ausserhalb des Repos; der Pilot ist
  einmalig (DEC-99 (3), DEC-101 E10) und durch die registrierte YAML-sha256 gesperrt. Sie dienen nur als Nachweis, wie die Artefakte entstanden.
- Warnung Sandbox-Pfade (bekannt, unschaedlich; Entscheid Orchestrator 2026-11-02, Option a): Die Dateien sind
  BYTE-IDENTISCH zu den per sha256 gepinnten Fassungen und tragen deshalb Pfade der Entstehungs-Sandbox
  (/home/user/scinance/... und, in einem Teil der Skripte/Specs, /tmp/claude-0/.../scratchpad/... des damaligen Sitzungs-
  Scratchpads). Es sind keine Zugangsdaten und keine Hosts. Ohne Anpassung laufen die Skripte nur in einem Layout, das diese
  Pfade nachbildet; jede Aenderung (auch Kommentar, Pfad, Umlaut) bricht den Pin und braucht eine neue Fassung mit neuer sha256.
```

### 6.8 `scinance3-impl/verify/a1/README.md`

```
# verify/a1 - unabhaengige Nachpruefung A1 (H-31)

Review (REVIEW_A1.md Z. 5-6, 172-173): rv_load.py, rv_formation.py, rv_nuisance.py, rv_power.py, rv_wp7_zerofill.py (eigene Nachrechnung,
eigener Lader); SPEC_A1_review.md (Auftrag). Nicht per sha256 gepinnt, nur per Namen in der Akte.
Reproduktion: cd /tmp && PYTHONPATH=/home/user/scinance/src python -I rv_load.py, danach rv_formation.py, rv_nuisance.py, rv_power.py,
rv_wp7_zerofill.py (je Sekunden; Panel ausserhalb des Repos, siehe ../../derivations/a1/README.md). Ausgaben rv_formation.json,
rv_nuisance.json liegen nur im Scratchpad.
Unabhaengigkeitsregel: Herleitungs-Agenten lesen verify/ nicht, importieren und kopieren daraus nichts (SPEC_A2_auflagen.md; Review-
Unabhaengigkeit). Ergebnisdateien der Pruefskripte (rv_*.json, out*.json) sind NICHT hier: sie tragen Nuisance-Zahlen (DEC-103 N1 (2c)).
Warnung Sandbox-Pfade (bekannt, unschaedlich; Entscheid Orchestrator 2026-11-02, Option a): Die Dateien sind
BYTE-IDENTISCH zu den per sha256 gepinnten Fassungen und tragen deshalb Pfade der Entstehungs-Sandbox
(/home/user/scinance/... und, in einem Teil der Skripte/Specs, /tmp/claude-0/.../scratchpad/... des damaligen Sitzungs-
Scratchpads). Es sind keine Zugangsdaten und keine Hosts. Ohne Anpassung laufen die Skripte nur in einem Layout, das diese
Pfade nachbildet; jede Aenderung (auch Kommentar, Pfad, Umlaut) bricht den Pin und braucht eine neue Fassung mit neuer sha256.
```

### 6.9 `scinance3-impl/verify/a2/teilAB/README.md`

```
# verify/a2/teilAB - unabhaengige Nachpruefung A2-Vorarbeit Teil A/B (REVIEW_A2_VORARBEIT.md, NACHRECHNUNG_ORCHESTRATOR.md)

Review: rv_sigma.py (Streuung/rho/ACF/c, eigener Lader mit Assert vor jedem Preis, Seed 4711), rv_power.py (N, SE, MDE80, Konjunktions-
Power, MC-Seed 11), rv_oi.py (OI aus den Rohpartitionen), rv_fut.py (Futures-Kalender), rv_timing.py (Zeitlage), rv_did.py (DiD-Streuung),
rv_band.py (Blockwahl), cmp_sigma.py (Vergleich), keyscan.py / pathscan.py / guardtest.py (Siegel-Scans); SPEC_A2_review.md (Auftrag).
Orchestrator: a2_fut_check.py, a2_joint_check.py, a2_spot.py (NACHRECHNUNG_ORCHESTRATOR.md; eigener Code).
Pins: die Review-Skripte sind nicht per sha256 gepinnt (nur Namen, REVIEW_A2_VORARBEIT.md Z. 130-135); gepinnt sind nur Ausgaben
(rv_sigma.json e7b85dd0..., rv_power.json ea034145..., rv_oi.json 8e2e6b80...; Praefixe, Dateien nicht im Repo).
Reproduktion: Eingaben wie ../../../derivations/a2/teilAB/README.md; guardtest.py importiert a2v_common (Layout dort). Laufzeit < 1 min.
Unabhaengigkeitsregel: Herleitungs-Agenten lesen verify/ nicht, importieren und kopieren daraus nichts (SPEC_A2_auflagen.md; Review-
Unabhaengigkeit). Ergebnisdateien der Pruefskripte (rv_*.json, out*.json) sind NICHT hier: sie tragen Nuisance-Zahlen (DEC-103 N1 (2c)).
Warnung Sandbox-Pfade (bekannt, unschaedlich; Entscheid Orchestrator 2026-11-02, Option a): Die Dateien sind
BYTE-IDENTISCH zu den per sha256 gepinnten Fassungen und tragen deshalb Pfade der Entstehungs-Sandbox
(/home/user/scinance/... und, in einem Teil der Skripte/Specs, /tmp/claude-0/.../scratchpad/... des damaligen Sitzungs-
Scratchpads). Es sind keine Zugangsdaten und keine Hosts. Ohne Anpassung laufen die Skripte nur in einem Layout, das diese
Pfade nachbildet; jede Aenderung (auch Kommentar, Pfad, Umlaut) bricht den Pin und braucht eine neue Fassung mit neuer sha256.
```

### 6.10 `scinance3-impl/verify/h27/README.md`

```
# verify/h27 - unabhaengige Nachpruefung H-27 (REVIEW_H27.md Abschnitt 6)

Skripte mit gekuerzter sha256 (Praefix...Suffix, REVIEW_H27.md Z. 294-300, alle acht stimmen): rv_common.py bd8880ab...bb59b147,
nuisance_review.py ffd9469d...12faa63a, nullworld_review.py 82a80181...ab1ff267, noise_share.py a4f4f14e...b8b7627c, power_review.py
e45e4102...5b4c1cb2, conv_review.py 8ffd90a0...f9be7deb, setup_cache.py fd944b22...cc47f238, keyscan.py 8113ae8d...e8f869fa.
SPEC_H27_review.md (Auftrag). Eingaben und Zugang wie ../../derivations/h27/README.md (Archivzugang ueber Umgebungs-Secrets HARVEST_S3_*;
setup_cache.py kopiert den Cache der Vorperiode). Ausgaben nuisance_review.json, nullworld_review.json, noise_share.json, power_review.json
liegen nur im Scratchpad.
Unabhaengigkeitsregel: Herleitungs-Agenten lesen verify/ nicht, importieren und kopieren daraus nichts (SPEC_A2_auflagen.md; Review-
Unabhaengigkeit). Ergebnisdateien der Pruefskripte (rv_*.json, out*.json) sind NICHT hier: sie tragen Nuisance-Zahlen (DEC-103 N1 (2c)).
Warnung Sandbox-Pfade (bekannt, unschaedlich; Entscheid Orchestrator 2026-11-02, Option a): Die Dateien sind
BYTE-IDENTISCH zu den per sha256 gepinnten Fassungen und tragen deshalb Pfade der Entstehungs-Sandbox
(/home/user/scinance/... und, in einem Teil der Skripte/Specs, /tmp/claude-0/.../scratchpad/... des damaligen Sitzungs-
Scratchpads). Es sind keine Zugangsdaten und keine Hosts. Ohne Anpassung laufen die Skripte nur in einem Layout, das diese
Pfade nachbildet; jede Aenderung (auch Kommentar, Pfad, Umlaut) bricht den Pin und braucht eine neue Fassung mit neuer sha256.
```

### 6.11 `scinance3-impl/verify/hfrv/README.md`

```
# verify/hfrv - unabhaengige Nachpruefung HF-RV-Nuisance (REVIEW_HFRV.md Abschnitt 7, NACHRECHNUNG_ORCHESTRATOR.md)

Skripte mit gekuerzter sha256 (REVIEW_HFRV.md Z. 306-310, alle fuenf stimmen): review_hfrv.py a749af2f...165394a4, compare.py
3d91572e...57b8cb58, c_robust.py de3fd9d5...17cd1ad0, a2_review.py 830c4dab...a5f789d2, keyscan.py a643d013...b0c27469.
Orchestrator: hfrv_spot.py (NACHRECHNUNG_ORCHESTRATOR.md Z. 3). SPEC_HFRV_review.md (Auftrag).
Aufruf: python3 -I review_hfrv.py (~5 s), compare.py, c_robust.py, a2_review.py. Eingaben wie ../../derivations/hfrv/README.md.
Nicht uebernommen: der Rerun-Ordner des Reviewers (Kopien der Herleitung mit umgeleiteter Ausgabe; hfrv_common.py dort mit anderer
sha256 als der Pin) und die Ergebnis-JSON (review_hfrv.json u.a.).
Unabhaengigkeitsregel: Herleitungs-Agenten lesen verify/ nicht, importieren und kopieren daraus nichts (SPEC_A2_auflagen.md; Review-
Unabhaengigkeit). Ergebnisdateien der Pruefskripte (rv_*.json, out*.json) sind NICHT hier: sie tragen Nuisance-Zahlen (DEC-103 N1 (2c)).
Warnung Sandbox-Pfade (bekannt, unschaedlich; Entscheid Orchestrator 2026-11-02, Option a): Die Dateien sind
BYTE-IDENTISCH zu den per sha256 gepinnten Fassungen und tragen deshalb Pfade der Entstehungs-Sandbox
(/home/user/scinance/... und, in einem Teil der Skripte/Specs, /tmp/claude-0/.../scratchpad/... des damaligen Sitzungs-
Scratchpads). Es sind keine Zugangsdaten und keine Hosts. Ohne Anpassung laufen die Skripte nur in einem Layout, das diese
Pfade nachbildet; jede Aenderung (auch Kommentar, Pfad, Umlaut) bricht den Pin und braucht eine neue Fassung mit neuer sha256.
```

### 6.12 `scinance3-impl/verify/h33/README.md`

```
# verify/h33 - unabhaengige Nachpruefung H-33 (REVIEW_H33.md)

review_h33.py (sha256 723fa4a4...dee4, REVIEW_H33.md Z. 16; eigene Nachrechnung mit power_p1 und h32_fm8.estimators, zweimal gerechnet, Ausgabe out1 = out2);
SPEC_H33_review.md (Auftrag). Eingaben wie ../../derivations/h33/README.md; keine Marktdaten. Ausgaben out1.json / out2.json
(sha256 97f76824...6fbe, bitgleich) liegen nur im Scratchpad.
Unabhaengigkeitsregel: Herleitungs-Agenten lesen verify/ nicht, importieren und kopieren daraus nichts (SPEC_A2_auflagen.md; Review-
Unabhaengigkeit). Ergebnisdateien der Pruefskripte (rv_*.json, out*.json) sind NICHT hier: sie tragen Nuisance-Zahlen (DEC-103 N1 (2c)).
Warnung Sandbox-Pfade (bekannt, unschaedlich; Entscheid Orchestrator 2026-11-02, Option a): Die Dateien sind
BYTE-IDENTISCH zu den per sha256 gepinnten Fassungen und tragen deshalb Pfade der Entstehungs-Sandbox
(/home/user/scinance/... und, in einem Teil der Skripte/Specs, /tmp/claude-0/.../scratchpad/... des damaligen Sitzungs-
Scratchpads). Es sind keine Zugangsdaten und keine Hosts. Ohne Anpassung laufen die Skripte nur in einem Layout, das diese
Pfade nachbildet; jede Aenderung (auch Kommentar, Pfad, Umlaut) bricht den Pin und braucht eine neue Fassung mit neuer sha256.
```

### 6.13 `scinance3-impl/verify/bilanz/README.md`

```
# verify/bilanz - unabhaengige Nachpruefung Programm-Bilanz (REVIEW_PROGRAMM_BILANZ_2026-10-18.md Abschnitt "Skripte")

review_check.py (b3bdc074...a1bb3fdf: Nuisance-Lesung mit Waechter, ganzzahlige Dauern mit power_p1, fm8 auf W1/W2),
rerun/census_copy.py (21ed2e70...8797b1de: Kopie von ../../derivations/bilanz/bilanz_census.py mit nach Scratchpad umgeleiteter Ausgabe;
Ergebnis-JSON identisch bis auf das Feld skript); SPEC_BILANZ_review.md (Auftrag). Die Ausgabe review_check.json (92e8c17a...) liegt nur im Scratchpad.
Unabhaengigkeitsregel: Herleitungs-Agenten lesen verify/ nicht, importieren und kopieren daraus nichts (SPEC_A2_auflagen.md; Review-
Unabhaengigkeit). Ergebnisdateien der Pruefskripte (rv_*.json, out*.json) sind NICHT hier: sie tragen Nuisance-Zahlen (DEC-103 N1 (2c)).
Warnung Sandbox-Pfade (bekannt, unschaedlich; Entscheid Orchestrator 2026-11-02, Option a): Die Dateien sind
BYTE-IDENTISCH zu den per sha256 gepinnten Fassungen und tragen deshalb Pfade der Entstehungs-Sandbox
(/home/user/scinance/... und, in einem Teil der Skripte/Specs, /tmp/claude-0/.../scratchpad/... des damaligen Sitzungs-
Scratchpads). Es sind keine Zugangsdaten und keine Hosts. Ohne Anpassung laufen die Skripte nur in einem Layout, das diese
Pfade nachbildet; jede Aenderung (auch Kommentar, Pfad, Umlaut) bricht den Pin und braucht eine neue Fassung mit neuer sha256.
```

### 6.14 `scinance3-impl/verify/h32/README.md`

```
# verify/h32 - unabhaengige Nachpruefung H-32 (REVIEW_H32.md, REVIEW_REGISTRIERUNG_H32.md, ..._NACHPRUEFUNG.md)

Review der Herleitung: rv_power.py, rv_oc.py, rv_ceiling.py, rv_inject.py, rv_sector.py, rv_serule.py, rv_wc.py, rv_attn.py (REVIEW_H32.md Z. 16-17).
Registrierungs-Review: rr_check.py, rr_q95_mc.py, rr_size_twins.py, rr_twins.py (REVIEW_REGISTRIERUNG_H32.md); Nachpruefung: rr2_check.py,
rr2_locks.py, rr2_pk.py, rr2_pk_f.py, rr2_u3k.py (..._NACHPRUEFUNG.md). Orchestrator: h32_v6_power.py. smoke/: Builder-Smoke-Skripte auf synthetischem Panel
(REVIEW_REGISTRIERUNG_H32.md Z. 17 nennt nur das Verzeichnis; sie importieren tests.unit.h32_fixtures aus einem Worktree und lesen einen
Pickle-Zwischenstand, der nicht uebernommen ist). SPEC_H32_review.md, SPEC_H32_registrierung_review.md (Auftraege).
Pins: Skripte nicht per sha256 gepinnt (Namen); gepinnt sind Re-Emissionen/Ausgaben (h32_v1_reemit.yaml bddfb9cb... / a3079cf9...,
rerun_power_h32.json df17cafa..., rerun_out_power.json bcb0d91c...), nicht hier. Eingaben wie ../../derivations/h32/README.md.
Unabhaengigkeitsregel: Herleitungs-Agenten lesen verify/ nicht, importieren und kopieren daraus nichts (SPEC_A2_auflagen.md; Review-
Unabhaengigkeit). Ergebnisdateien der Pruefskripte (rv_*.json, out*.json) sind NICHT hier: sie tragen Nuisance-Zahlen (DEC-103 N1 (2c)).
Warnung Sandbox-Pfade (bekannt, unschaedlich; Entscheid Orchestrator 2026-11-02, Option a): Die Dateien sind
BYTE-IDENTISCH zu den per sha256 gepinnten Fassungen und tragen deshalb Pfade der Entstehungs-Sandbox
(/home/user/scinance/... und, in einem Teil der Skripte/Specs, /tmp/claude-0/.../scratchpad/... des damaligen Sitzungs-
Scratchpads). Es sind keine Zugangsdaten und keine Hosts. Ohne Anpassung laufen die Skripte nur in einem Layout, das diese
Pfade nachbildet; jede Aenderung (auch Kommentar, Pfad, Umlaut) bricht den Pin und braucht eine neue Fassung mit neuer sha256.
```

### 6.15 `scinance3-impl/derivations/pdf_belege/README.md` (optional)

```
# derivations/pdf_belege - Belege aus PDF (BELEGE_AUS_PDF_2026-10-20.md)

extract.py (Seitentext je PDF-Seite), calc.py, header.py, period.py (period.py ist NICHT ASCII und deshalb nicht gestaged), SPEC_PDF_belege.md.
Nur extract.py ist in der Akte genannt (BELEGE_AUS_PDF_2026-10-20.md Z. 296). Die PDFs selbst (Quellen) sind nicht im Repo.
Warnung Sandbox-Pfade (bekannt, unschaedlich; Entscheid Orchestrator 2026-11-02, Option a): Die Dateien sind
BYTE-IDENTISCH zu den per sha256 gepinnten Fassungen und tragen deshalb Pfade der Entstehungs-Sandbox
(/home/user/scinance/... und, in einem Teil der Skripte/Specs, /tmp/claude-0/.../scratchpad/... des damaligen Sitzungs-
Scratchpads). Es sind keine Zugangsdaten und keine Hosts. Ohne Anpassung laufen die Skripte nur in einem Layout, das diese
Pfade nachbildet; jede Aenderung (auch Kommentar, Pfad, Umlaut) bricht den Pin und braucht eine neue Fassung mit neuer sha256.
```

### 6.16 `scinance3-impl/verify/gate_audit/README.md` (optional)

```
# verify/gate_audit - Skripte der Gate-Audits v5c und PC v3 (2026-10-12)

scripts/{recompute, variants, sens_sigma_e, sens_clean_btc, full_rule_clean}.py (REVIEW_GATE_AUDIT_v5c_2026-10-12.md Z. 308-315), mc_ci.py,
power_v5e.py (REVIEW_GATE_AUDIT_PC_v3_2026-10-12.md Z. 59, 122). Nicht per sha256 gepinnt. Unabhaengigkeitsregel: Herleitungs-Agenten lesen verify/ nicht, importieren und kopieren daraus nichts (SPEC_A2_auflagen.md; Review-
Unabhaengigkeit). Ergebnisdateien der Pruefskripte (rv_*.json, out*.json) sind NICHT hier: sie tragen Nuisance-Zahlen (DEC-103 N1 (2c)).
Warnung Sandbox-Pfade (bekannt, unschaedlich; Entscheid Orchestrator 2026-11-02, Option a): Die Dateien sind
BYTE-IDENTISCH zu den per sha256 gepinnten Fassungen und tragen deshalb Pfade der Entstehungs-Sandbox
(/home/user/scinance/... und, in einem Teil der Skripte/Specs, /tmp/claude-0/.../scratchpad/... des damaligen Sitzungs-
Scratchpads). Es sind keine Zugangsdaten und keine Hosts. Ohne Anpassung laufen die Skripte nur in einem Layout, das diese
Pfade nachbildet; jede Aenderung (auch Kommentar, Pfad, Umlaut) bricht den Pin und braucht eine neue Fassung mit neuer sha256.
```

### 6.17 Aenderung an bestehenden README (Vorschlag)

```
derivations/a2/README.md, letzte Warnung:  - Teil A/B (a2v_*.py, Review rv_*.py) folgen mit F0b in teilAB/.
  ersetzen durch:                              - Teil A/B (a2v_*.py): teilAB/ (F0b); Review rv_*.py: ../../verify/a2/teilAB/.
verify/a2/README.md: Zeile ergaenzen:          Teil A/B (Review rv_*.py, Orchestrator a2_fut_check/a2_joint_check/a2_spot): teilAB/.
```

## 7. Offene Punkte fuer den Orchestrator

1. **Verschieben:** `cp -a scratchpad/prd_review/f0b/stage/scinance3-impl/. /home/user/scinance/scinance3-impl/` (kein Ueberschreiben bestehender Dateien: die Zielpfade `derivations/{a1,a2/teilAB,h27,hfrv,h33,bilanz,h32}/`, `verify/{a1,a2/teilAB,h27,hfrv,h33,bilanz,h32}/` sind neu). Danach README anlegen (Abschnitt 6) und sha256 der Zielpfade gegen diese Tabelle pruefen (`sha256sum -c` aus der Tabelle erzeugbar).
2. **Entscheid `stage_optional/`:** 21 Dateien (Abschnitt 3); Empfehlung: `a1_indep.py` (Orchestrator-Nachrechnung A1, wichtig fuer die Nachvollziehbarkeit von DEC-93), die Gate-Audit-Skripte und `SPEC_DEC101_builder.md`/`SPEC_H32_builder.md` mitnehmen; `a1_explore2.py`, `keys.py`, `kseries.py`, `extract_v5e.py`, `surv_probe.py`, `guard.py`, `keytree.py` nur bei Bedarf (Hilfs-/Explorationsskripte).
3. **`.gitignore` ergaenzen** (zusaetzlich zu `derivations/**/work/` und `verify/**/work/`): `scinance3-impl/derivations/**/cache/`, `scinance3-impl/derivations/**/hcache/`, `scinance3-impl/derivations/**/tables.md`, `*.pkl`, `scinance3-impl/derivations/**/nuisance.json` und `power.json` (H27-Ausgaben im Skriptordner) bzw. allgemein `scinance3-impl/derivations/**/*.json` mit Ausnahme `!scinance3-impl/derivations/a2/data_manifest/EXTRACT_LOG.json`, sowie `scinance3-impl/verify/**/*.json`. (`*.parquet` steht bereits drin.)
4. **Akten-Konkordanz (append-only):** Die Akte nennt Skripte weiter als `scratchpad/...`. Ein Erratum/Konkordanz-Vermerk 'jetzt unter `derivations/<thema>/` bzw. `verify/<thema>/`' (Zuordnung = Spalte Ziel in Abschnitt 2) genuegt; die Akten selbst nicht veraendern.
5. **Fassung-1-Ergebnisdateien und Review-Ausgaben** (Abschnitt 4.3.1: 23 Dateien bzw. Hash-Gruppen mit Akten-Pin, 6 weitere liegen bereits im Repo) bleiben nur im Scratchpad; bei Sitzungsende gehen sie verloren. Entscheid: privates Archiv oder Verzicht (Pins bleiben als Nachweis).
6. **Datenzugang fuer Reproduktion:** H27, HFRV, A2-Teil-A/B und A1 sind nur mit Archiv-/Panel-Zugang reproduzierbar; vollstaendig aus Repo-Dateien reproduzierbar sind H33, Bilanz und H32-Power (Eingabe-sha256 in den README).
7. **Doppelte Dateien:** `derivations/hfrv/{h27_common,h27_series,nuisance,power_h27}.py` sind byte-gleich zu `derivations/h27/` (gewollt, siehe Befund 4). Alternativ eine einzige Kopie plus Symlink; Symlinks im oeffentlichen Repo sind nicht empfohlen.
8. **Verify-Unabhaengigkeit:** Ablage der Review-Skripte im selben Repo hebt die Regel 'Herleitungs-Agenten lesen die Review-Skripte nicht' nicht auf; sie steht in den verify-README (V_NOTE). Fuer die automatische Architektur (F0-Fahrplan) ggf. Zugriffsregel in der Agenten-Konfiguration.
9. **`SPEC_A2_auflagen.md` und die `SPEC_*_review.md`:** in der Akte nicht per Namen genannt (Spalte `-`), aber im Auftrag benannt bzw. Themen-Specs; mitgenommen.

## 8. Kurzfassung

- gestaged: 133 Dateien in `stage/` (a1 21, a2/teilAB 30, h27 21, hfrv 17, h33 4, bilanz 6, h32 34) + 21 optional in `stage_optional/`; 1 Kandidat nicht gestaged (Nicht-ASCII, optional).
- Pins: 60 distinkte Skript-Pins in der Akte (ohne Teil C), 59 im Scratchpad gefunden und sha256-identisch (alle gestaged), 1 (`power_p1.py`) im Repo; verlorene Pins: 0. Review-/Orchestrator-Skripte sind meist nur per Namen genannt.
- Byte-identisch (sha256 Quelle = Kopie) 154/154; py_compile 128/128 OK, bash -n 7/7 OK; ASCII 100 %.
- Hygiene: 0 echte Treffer; Muster-Treffer (claude in Pfaden, os.environ-Schalter, harvest_data-Import, S3-Variablen, `.at`/`.info`) von Hand als Falsch-Positive geklaert; Werte der drei HARVEST_S3_-Variablen: 0 Treffer in 343 Dateien; keine JSON/CSV/Parquet/Pickle gestaged.
- Sandbox-Pfade bleiben stehen (Option a): 59 Dateien mit `/tmp/claude-0/...`, 70 mit `/home/user/...`; in den 16 README-Vorschlaegen dokumentiert.
- Wichtig: `a2v_common.py`/`hfrv_common.py` brauchen das Scratchpad-Layout (Geschwisterordner); Ausgabe-Skripte (`a2v_build.py`, `a1_consolidate.py`, `bilanz_census.py`, `nuisance_hfrv.py`, `a2_census.py`) ueberschreiben per Voreinstellung committete Akten-JSON; H-32-`run/*.sh` nie ausfuehren (Pilot einmalig).
- Fassung-1-Skripte der A2-Vorarbeit (andere sha256 als die Pins) sind unter `derivations/a2/teilAB/fassung1/` mitgesichert; gepinnte Ergebnis-/Fassungs-Dateien (23 Hash-Gruppen, Abschnitt 4.3.1) bleiben bewusst nur im Scratchpad.
- Dubletten gewollt: `h27_common.py`, `h27_series.py`, `nuisance.py`, `power_h27.py` in h27/ und hfrv/ (gleiche sha256).
- Offen: Entscheid zu stage_optional/ (21), `.gitignore`, Konkordanz-Vermerk, Archivierung der Ergebnis-JSON.
