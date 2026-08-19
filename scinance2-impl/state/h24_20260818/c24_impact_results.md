# H-24 — Fuehrt der Minuten-Nettofluss die folgende 30-Minuten-Bewegung? (KAPITALFREI)

- **Hypothese:** H-24 — `scinance2-impl/state/hypothesis_registry.md`
- **Erzeugt:** 2026-08-18T14:40:11+00:00 (UTC) · Status: RUN
- **Datenbindung:** WP-0-Bar-Cache · `gate_valid=true`
- **Urteilsgroesse:** daily Spearman(F_m, forward log move to m+30min), forward window starts at the NEXT minute close (bounce excluded); tests CONTINUATION (DEC-39), not persistence
- **Positivkontrolle (bindend):** daily Spearman(F_m, r_m); pooled mean must >= 0.1 per judgment window, else METHODICALLY INVALID (no verdict)
- **Rezenz-Klausel:** DEC-38: only the two most recent half-years are judgment-bearing; older windows are a descriptive era profile
- **Gate:** BEIDE Rezenz-Fenster mean(IC30) >= 0.02 UND p <= 0.05 nach BH-FDR alpha=0.1 ueber F-IMP. Hartes Ein-Fenster-DROP.
- **Abgrenzung:** H-05/GL-007/GL-010 cluster: tick-OFI signs on tick scale — different object; no rehabilitation implied

## Urteilstragende Zellen (Rezenz-Fenster)

| Fenster | Symbol-Tage | Tage | Floor | **mean IC30** | Lesart | median | >= 0,02 | Kontrolle IC_gleichzeitig | Kontrolle ok | boot-p | FDR | Zelle |
|---|---:|---:|:---:|---:|---|---:|:---:|---:|:---:|---:|:---:|:---:|
| W-R1 | 920 | 184 | ok | **-0.01790** | permanent | -0.01861 | nein | +0.53763 | ok | 1.0000 | nein | nein |
| W-R2 | 905 | 181 | ok | **-0.01691** | permanent | -0.01647 | nein | +0.52650 | ok | 1.0000 | nein | nein |

**Beide Fenster PASS:** nein · **Positivkontrolle:** bestanden · **Verdikt auswertbar:** ja

## Aera-Profil (deskriptiv, NICHT urteilstragend — Rezenz-Klausel)

| Fenster | Symbol-Tage | mean IC30 | Lesart | mean IC gleichzeitig | mean IC5 | mean IC120 |
|---|---:|---:|---|---:|---:|---:|
| E-2021H2 | 920 | -0.01201 | permanent | +0.53085 | +0.00413 | -0.00780 |
| E-2022H1 | 905 | -0.01130 | permanent | +0.58407 | -0.00657 | -0.01288 |
| E-2022H2 | 920 | -0.01676 | permanent | +0.59120 | -0.01826 | -0.01518 |
| E-2023H1 | 905 | -0.01932 | permanent | +0.57586 | -0.02013 | -0.01802 |
| E-2023H2 | 920 | -0.02236 | reversal | +0.60640 | -0.01624 | -0.01748 |
| E-2024H1 | 910 | -0.02234 | reversal | +0.58926 | -0.02607 | -0.01869 |
| E-2024H2 | 920 | -0.01854 | permanent | +0.56986 | -0.01753 | -0.01979 |
| E-2025H1 | 1060 | -0.01777 | permanent | +0.56012 | -0.01725 | -0.01614 |

*Lesart (DEC-39, NICHT urteilstragend): `reversal` = transienter Impact (Liquiditaets-Reversion), `permanent` = Impact bleibt im Preis (Forward-IC ~ 0), `continuation` = Fluss fuehrt weitere Bewegung. Das GATE prueft ausschliesslich `continuation`.*

*Erzeugt von `c24_impact/driver.py` — liest AUSSCHLIESSLICH den WP-0-Bar-Cache. capital_free=true. Gate-Urteil: gate-auditor gegen H-24.*