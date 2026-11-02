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
