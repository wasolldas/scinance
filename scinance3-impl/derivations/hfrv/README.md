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
