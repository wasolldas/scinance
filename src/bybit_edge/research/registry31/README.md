# registry31 - schema and linter for registrations under Constitution 3.1

Programme step F1 (DEC-104 E9; PRD_ANALYSE section 7, building block 2).  Status: staged, not yet merged; nothing in the
repository imports this package.

## Purpose

* `schema.py`: the data model of a registration (YAML template 3.1, PRD v3 draft section 3.3) as a tree of `Spec` nodes:
  type, required or optional, allowed values, range, pattern, source.  All 30 mandatory lines PZ-01..PZ-30 are mapped to
  their fields in `PZ_FIELDS`.  There are NO defaults: a missing required field, an unknown field, a null where a value
  is required, or a wrong type is an issue (loud fail).  A field that may hold an explicit null (`decision_rule.screen`,
  `decision_rule.stability_test`, `sesoi_curve.persistenz_ref`) must still be present.  `json_schema()` exports the same
  tree as JSON Schema (draft 2020-12).
* `lint.py`: the rules as a table of data (`RULES`: id, title, dossier source, needed input paths, check).  A rule whose
  input is invalid is reported as HINWEIS "not checked"; the schema defect itself is the FEHLER (R01).

The package reads one YAML file.  It reads no market data, no sealed file, no network.  The only third-party module is
pyyaml.

## Usage

```
python -m bybit_edge.research.registry31.lint scinance3-impl/state/registered/<file>.yaml
python -m bybit_edge.research.registry31.lint <file>.yaml --json
python -m bybit_edge.research.registry31.lint --list-rules
python -m bybit_edge.research.registry31.lint --emit-schema
```

Output: one line per finding `[STATUS] RULE (source): message`, then `SUMMARY`.  Status is OK, FEHLER or HINWEIS.  The
output is deterministic (rule-table order, no time stamps).  Return code: 0 = no FEHLER (HINWEIS allowed), 1 = at least
one FEHLER, 2 = file unreadable, not YAML, or duplicate YAML key.  The linter prints the class and path of a suspicious
text (model name, host, credential), never the text.

`scinance3-impl/state/registered/TEMPLATE_3_1.yaml` is the commented pattern (header "TEMPLATE, nicht registriert").  It
is not a registration: every `<...>` is an unresolved placeholder (R02) and the schema rejects it (R01).

## Rules

HINWEIS findings never fail the run; they mark a user submission or a structural finding.

| Rule | Check | Source |
|---|---|---|
| R01-SCHEMA | required fields present, typed, allowed values; no defaults, no unknown fields | PRD v3 3.1 (a)/(b); 3.2 PZ-01..PZ-30; DEC-104 E9 |
| R02-PLATZHALTER | no unresolved template placeholders '<...>' | PRD v3 3.3; PRD 3.1 (b) |
| R03-ALPHA | alpha_test = 0.0025 and z_krit = 2.8070 (fixed per test) | DEC-104 E2; VR-b14; PZ-15 |
| R04-SCREEN | screen / stability_test variants a, a', c; only the decided variant | DEC-104 E2, E6, N2 (4); PZ-16 |
| R05-KOHORTE | cohort = first day of a quarter >= 2027-01-01 | DEC-104 E4 (f); PZ-14 |
| R06-FENSTER-ZONE | windows lie in their zone and are covered by a zone entry; one judging window | DEC-104 E4 (a), (d), (e); FENSTERREGISTER 1; PZ-13 |
| R07-ZONE-X | no zone-X data as confirmation | DEC-104 E4 (a), (c); KONTO_ZONE_X |
| R08-FAMILIE | zone V policy and pure zone-K start per data family | DEC-104 E4 (i); FENSTERREGISTER 2, 6; VR-d16; PZ-13, PZ-30 |
| R09-ZONENEINTRAG | zone entries: section inside the zone, rein_ab consistent | FENSTERREGISTER 1, 6; PZ-13 |
| R10-BLICKE | looks: zone V exactly one, zone K plan complete | DEC-104 E4 (d), (e), N2 (7); PZ-17; VR-d11, VR-d12 |
| R11-SESOI | sesoi_curve: frame, cost basis label, persistence, curve, SESOI value | DEC-104 E3 (a), N3 (1); DEC-105 (1), (8); PZ-18 |
| R12-TESTBARKEIT | MDE80 <= SESOI, else strukturell nicht testbar; flag and verdict consistent | DEC-104 E3 (a); VR-c01; PZ-01 |
| R13-PRIOR | prior_label set; UNBELEGT carries a two-sided sensitivity span; selection-adjusted | DEC-104 E3 (b), (c), (d); VR-c05, VR-c06; PZ-19 |
| R14-LITERATUR | literature is a label, never a block | DEC-104 E3 (b); VR-c05 |
| R15-SELEKTION-K | selection K >= 1 and cumulative K >= K | DEC-104 E9, N1 (9); VR-b17; PZ-04, PZ-20 |
| R16-OC-ZEILE | oc_line complete, >= 1000 seeds, plausible | DEC-104 E8 (a); VR-f04; PZ-21 |
| R17-STRENGE | strictness ratio >= 1.3 -> Nutzer-Vorlage | DEC-104 E8 (b); VR-f05; PZ-22 |
| R18-NEFF-C | n_eff > 0 and c_overlap >= 1 | DEC-51 (3), (5); DEC-104 N2 (7); VR-b03, VR-b05; PZ-23, PZ-24 |
| R19-C17 | c17_refs are unique rows of the account inventory | DEC-104 N1 (1); VR-d18; PZ-29 |
| R20-JAHRESBUCH | annual book consistent; > 0.10 -> Nutzer-Vorlage | DEC-104 E4 (g); VR-d14; PZ-28 |
| R21-BERICHTSZEILE | report_line carries the nine mandatory fields | DEC-105; VR-f02; PZ-11 |
| R22-ARTEFAKTE | result artifacts: cluster series + bootstrap (sha256 or seed + generator fingerprint) | DEC-53; VR-f03; PZ-11 |
| R23-KONSTANTEN | constants_hash pinned and equal to the cost-model hash | PRD 3.3.6; VR-g14; PZ-06 |
| R24-CODE-HASH | code_sha256: repository-relative, unique paths | PRD_ANALYSE 7 (versioned script) |
| R25-STEUER | tax treatment 'UNBELEGT - PRD 8.2' | PRD 3.3.9; PRD 8.2; PZ-09 |
| R26-TEXT-HYGIENE | no model names, host names, credentials in any text | project hard rules; public repository |
| R27-REFS | derivation references are repository-relative, not sealed, not below data/harvest | project hard rules; PRD 3.1 (b) |
| R28-LESESTATUS | reading status per file; sealed files recorded as read are flagged | DEC-104 N1 (6); VR-g07; PZ-25 |
| R29-DESIGN-MENUE | chosen design belongs to the registered menu | DEC-104 E5; VR-e01; PZ-26 |
| R30-ERREICHBARKEIT | every parameter reaches observations in the judging windows | DEC-104 E8 (d); VR-f07; PZ-27 |
| R31-FDR | cohort BY q and BH alpha fixed at 0.10 | DEC-104 E4 (f); VR-b16, VR-b17, VR-d13 |
| R32-VORWISSEN | vorwissens_klasse names the families of the zone entries | DEC-104 E4 (i); VR-d16; PZ-30 |
| R33-POSITIVKONTROLLE | positive control preceding, production configuration | PRD 3.3.8; VR-f12; PZ-08 |

## Data families and zones (FENSTERREGISTER section 2 and 6; `schema.FAMILIES`)

| Family | Pure zone K from (`zone_k_start`) | Zone V policy | Rule |
|---|---|---|---|
| F1 | 2026-10-01 | exception | zone K prospectively only; zone V only for the A2 r_pre exception (DEC-104 E4 (i)) |
| F2 | 2026-07-01 | blind | zone V (W1/W2) only while blind (C.17), zone K; sealed IC series stay unread |
| F3 | 2026-09-15 | non_outcome | zone V only for non-outcome statistics; funding level K from 2026-09-15 (OI/turnover 2026-07-01 -- the stricter date is used) |
| F4 | 2026-07-01 | no | zone K prospectively; snapshot dates from 2026-07 only as counts |
| F5 | 2026-07-01 | no | zone K entirely; before cohort 1 counts only |
| F6 | 2026-10-01 | no | zone K prospectively for daily aggregates; microstructure K from 2026-10-01 |

Zones (DEC-104 E4 (a), DEC-104 N1 (3)): X = up to 2024-06-30; V = 2024-07-01..2026-06-30 (daily statistics); K = from
2026-07-01 (pure per family from the date above).  V policy: `no` = not confirmable in V; `blind` = only while blind
(C.17); `exception` = only with `ausnahme: a2_r_pre`; `non_outcome` = only with `outcome_beruehrend: false`.

## Notes on the schema

* Field names follow the YAML template 3.1.  Extensions against the template text (to be adopted into PRD v3 3.3 or
  dropped): `code_sha256` (no number without a versioned script), `test_pflichten` (PZ-12, one `path#test_id` per T0..T7),
  `decision_rule.variante` (PZ-16: `a`, `a'`, `c`; only `a` is registrable until the user decision P-2, constant
  `schema.DECIDED_VARIANT`), and in `sesoi_curve`: `horizont_tage`, `punkte` (the curve), `gabelung_etikett`,
  `persistenz_herkunft`, `persistenz_ref`.  `looks.zone_v` / `looks.zone_k` and `prior_label.sensitivitaetsspanne` are
  optional in the schema and required by rules when the zones used or the label UNBELEGT demand them.
* Names of the brief: `data_family` is `zone[].datenfamilie`, `zone_k_start` is `zone[].rein_ab` checked against
  `schema.ZONE_K_START`, `selection_k` is `selection.K` (PZ-20), `alpha_test` is `decision_rule.alpha_test`, `c17_list`
  is accepted as an alias of `c17_refs` (both together is an issue).
* `n_eff` and `c_overlap` are numbers or `{wert, ref}`.  A derivation reference is `path#test_id` (strict) or a path.
* The key `null` in `fixtures` is read as the text "null" (YAML would turn an unquoted `null:` into a null key); duplicate
  YAML keys are rejected.
* Not checked (needs data or a ledger): the arithmetic of power, MDE80, OC line and strictness ratio (they are inputs
  with derivation references), hashes against files, append-only pins of old entries, the FDR book.

## Tests

```
cd <stage or repository root>
PYTHONPATH=src:/home/user/scinance/src python -m pytest tests/unit/test_registry31.py -q
```
