# H-12 · Cross-Exchange-Fragmentierungsmatrix Mess-Gate (RMT/MP-IPR, F-FRAG, KAPITALFREI)

- **Hypothese:** H-12 — `scinance2-impl/state/hypothesis_registry.md` (Welle 4)
- **Erzeugt:** 2026-08-10T09:58:59+00:00 (UTC)
- **Quelle:** `E:\Claude\Projects\scinance\data\harvest/raw/{bybit,binance,deribit}/publicTrade (windows 2026-03-27..2026-05-15 + 2026-05-16..2026-07-04)`
- **Fenster (vorregistriert):** W1, W2
- **Panel:** 6 Serien = 2 Symbole x 3 Boersen, Minuten-Last-Price, Forward-Fill <= 1 min, Tag gueltig >= 1380/1440 min je Serie
- **Spektrum:** Log-Returns je Serie je Tag z-standardisiert, Korrelationsmatrix C (6x6), Eigenzerlegung, IPR(v) = Summe(v_i^4)
- **Null (zweistufig):** (a) MC-Gaussian-Wishart-Referenz (NICHT urteilstragend) · (b) Ein-Faktor-Gauss-Null je Tag aus (lambda1, v1), Tages-p = P(lambda2_sim >= lambda2_obs), Add-one-Konvention · MC-Ziehungen/Reps: 1000 · Seed: 42
- **FDR-Familie:** F-FRAG (EINE Familie ueber BEIDE Fenster, 85 Tages-Tests) · BH-FDR alpha 0.1 · p_crit 0.0410 · FDR-signifikant: 67
- **KAPITALFREI:** ja — reine Mess-/Explorationsfrage. Cross-Exchange-Arbitragesignal waere NEUE H-12b, NICHT impliziert.
- **Validitaets-Vorbedingung:** Validitaets-Vorbedingung (VOR dem Gate, KEIN Gate-Bestandteil): IPR(v1) <= 0,25 an >= 90% der gueltigen Tage UND >= 35 gueltige Tage je Fenster. Verfehlt -> Lauf UNGUELTIG: eigener Status, KEIN Verdikt, explizit NICHT DROP (Registry H-12).
- **Validitaets-Status dieses Laufs:** **GUELTIG**

> Gate-Urteil faellt der gate-auditor gegen H-12. WEITER verlangt in BEIDEN Fenstern: (a) Anteil gueltiger Tage mit lambda2 nach BH-FDR alpha=0,10 ueber F-FRAG signifikant ueber der Ein-Faktor-Null >= 20% UND (b) Median-IPR(v2) ueber den FDR-signifikanten Tagen >= 0,40 UND (c) an >= 70% der FDR-signifikanten Tage groesste v2^2-Boersenlast auf derselben Boerse. DROP: (a), (b) ODER (c) in einem Fenster verfehlt (hartes Ein-Fenster-Kriterium), kein Graubereich. Validitaets-Vorbedingung verfehlt -> Lauf UNGUELTIG (kein Verdikt, NICHT DROP). A-priori: DROP.

**WEITER-Indikation (nur bei gueltigem Lauf):** nein · **alle Fenster gueltig:** ja · **alle Kriterien in allen Fenstern:** nein

## Kriterien je Fenster (Gate-Kern)

| Fenster | gueltige Tage | FDR-sig Tage | (a) Anteil >= 0,20 | (b) Median-IPR(v2) >= 0,40 | (c) dominante Boerse (Anteil >= 0,70) | a | b | c | alle |
|---|---:|---:|---:|---:|---|:---:|:---:|:---:|:---:|
| W1 | 47 | 42 | 0.8936 | 0.1695 | deribit (0.9524) | ja | nein | ja | nein |
| W2 | 38 | 25 | 0.6579 | 0.1687 | deribit (0.9600) | ja | nein | ja | nein |

## Validitaets-Vorbedingung je Fenster (kein Gate-Bestandteil)

| Fenster | gueltige Tage (>= 35) | IPR(v1)<=0,25-Anteil (>= 0,90) | Fenster gueltig |
|---|---:|---:|:---:|
| W1 | 47 (ja) | 1.0000 (ja) | ja |
| W2 | 38 (ja) | 1.0000 (ja) | ja |

## MC-Wishart-Referenz je Fenster (Stufe a — NICHT urteilstragend)

| Fenster | T_eff (Median) | Q | MP lambda+ | lambda1 q95 | lambda2 q95 | lambda2 q99 |
|---|---:|---:|---:|---:|---:|---:|
| W1 | 1440 | 240.0 | 1.1333 | 1.1230 | 1.0699 | 1.0823 |
| W2 | 1440 | 240.0 | 1.1333 | 1.1210 | 1.0679 | 1.0798 |

## Tagesuebersicht W1

| Datum | gueltig | T_eff | lambda1 | lambda2 | IPR(v1) | IPR(v2) | p(lambda2) | FDR-sig | dominante Boerse (v2^2) |
|---|:---:|---:|---:|---:|---:|---:|---:|:---:|---|
| 2026-03-27 | ja | 1439 | 5.5303 | 0.3458 | 0.1667 | 0.1670 | 0.0010 | ja | binance |
| 2026-03-28 | ja | 1419 | 5.3115 | 0.4925 | 0.1668 | 0.1721 | 0.0010 | ja | deribit |
| 2026-03-29 | ja | 1422 | 5.5688 | 0.2820 | 0.1668 | 0.1728 | 0.2677 | nein | deribit |
| 2026-03-30 | ja | 1436 | 5.4971 | 0.3340 | 0.1668 | 0.1752 | 0.0060 | ja | deribit |
| 2026-03-31 | ja | 1407 | 5.5654 | 0.3218 | 0.1667 | 0.1675 | 0.0010 | ja | deribit |
| 2026-04-01 | ja | 1439 | 5.5113 | 0.3402 | 0.1668 | 0.1694 | 0.0010 | ja | deribit |
| 2026-04-02 | ja | 1438 | 5.5195 | 0.3705 | 0.1667 | 0.1684 | 0.0010 | ja | deribit |
| 2026-04-03 | ja | 1435 | 5.3050 | 0.3930 | 0.1672 | 0.1878 | 0.0090 | ja | deribit |
| 2026-04-04 | nein (Panel-Luecke) | — | — | — | — | — | — | — | — |
| 2026-04-05 | ja | 1398 | 5.3854 | 0.4432 | 0.1668 | 0.1673 | 0.0010 | ja | deribit |
| 2026-04-06 | ja | 1437 | 5.4661 | 0.4082 | 0.1667 | 0.1672 | 0.0010 | ja | deribit |
| 2026-04-07 | ja | 1438 | 5.5491 | 0.3599 | 0.1667 | 0.1676 | 0.0010 | ja | deribit |
| 2026-04-08 | ja | 1437 | 5.4478 | 0.4047 | 0.1668 | 0.1704 | 0.0010 | ja | deribit |
| 2026-04-09 | ja | 1434 | 5.5981 | 0.2785 | 0.1668 | 0.1802 | 0.2498 | nein | deribit |
| 2026-04-10 | ja | 1436 | 5.4790 | 0.3412 | 0.1668 | 0.1713 | 0.0020 | ja | deribit |
| 2026-04-11 | ja | 1423 | 5.3253 | 0.4907 | 0.1667 | 0.1669 | 0.0010 | ja | deribit |
| 2026-04-12 | ja | 1429 | 5.5525 | 0.3110 | 0.1667 | 0.1677 | 0.0010 | ja | deribit |
| 2026-04-13 | ja | 1438 | 5.4970 | 0.4166 | 0.1667 | 0.1668 | 0.0010 | ja | binance |
| 2026-04-14 | ja | 1439 | 5.4455 | 0.4301 | 0.1667 | 0.1670 | 0.0010 | ja | deribit |
| 2026-04-15 | ja | 1438 | 5.5432 | 0.2849 | 0.1668 | 0.1738 | 0.3337 | nein | deribit |
| 2026-04-16 | ja | 1438 | 5.6146 | 0.2610 | 0.1667 | 0.1681 | 0.3946 | nein | deribit |
| 2026-04-17 | ja | 1437 | 5.5013 | 0.3956 | 0.1667 | 0.1679 | 0.0010 | ja | deribit |
| 2026-04-18 | ja | 1437 | 5.2994 | 0.4998 | 0.1668 | 0.1684 | 0.0010 | ja | deribit |
| 2026-04-19 | ja | 1437 | 5.5467 | 0.2989 | 0.1668 | 0.1701 | 0.0270 | ja | deribit |
| 2026-04-20 | ja | 1439 | 5.5682 | 0.3141 | 0.1667 | 0.1686 | 0.0020 | ja | deribit |
| 2026-04-21 | ja | 1439 | 5.5735 | 0.2966 | 0.1667 | 0.1683 | 0.0150 | ja | deribit |
| 2026-04-22 | ja | 1438 | 5.3139 | 0.5501 | 0.1667 | 0.1671 | 0.0010 | ja | deribit |
| 2026-04-23 | ja | 1437 | 5.4777 | 0.3738 | 0.1668 | 0.1708 | 0.0010 | ja | deribit |
| 2026-04-24 | ja | 1432 | 5.3918 | 0.3968 | 0.1669 | 0.1726 | 0.0010 | ja | deribit |
| 2026-04-25 | nein (Panel-Luecke) | — | — | — | — | — | — | — | — |
| 2026-04-26 | ja | 1398 | 5.1060 | 0.7075 | 0.1669 | 0.1674 | 0.0010 | ja | deribit |
| 2026-04-27 | ja | 1431 | 5.4796 | 0.3562 | 0.1668 | 0.1696 | 0.0010 | ja | deribit |
| 2026-04-28 | ja | 1424 | 5.3089 | 0.3936 | 0.1672 | 0.1851 | 0.0030 | ja | deribit |
| 2026-04-29 | ja | 1433 | 5.4115 | 0.4212 | 0.1668 | 0.1684 | 0.0010 | ja | deribit |
| 2026-04-30 | ja | 1428 | 5.4704 | 0.2996 | 0.1670 | 0.2090 | 0.8851 | nein | deribit |
| 2026-05-01 | ja | 1428 | 5.4098 | 0.3795 | 0.1670 | 0.1851 | 0.0010 | ja | deribit |
| 2026-05-02 | nein (Panel-Luecke) | — | — | — | — | — | — | — | — |
| 2026-05-03 | ja | 1387 | 5.3067 | 0.4088 | 0.1670 | 0.1707 | 0.0010 | ja | deribit |
| 2026-05-04 | ja | 1435 | 5.5973 | 0.2952 | 0.1667 | 0.1696 | 0.0100 | ja | deribit |
| 2026-05-05 | ja | 1438 | 5.4347 | 0.3704 | 0.1669 | 0.1760 | 0.0010 | ja | deribit |
| 2026-05-06 | ja | 1413 | 5.2447 | 0.4641 | 0.1672 | 0.1764 | 0.0010 | ja | deribit |
| 2026-05-07 | ja | 1437 | 5.4010 | 0.3696 | 0.1670 | 0.1750 | 0.0020 | ja | deribit |
| 2026-05-08 | ja | 1430 | 5.3775 | 0.3774 | 0.1670 | 0.1748 | 0.0010 | ja | deribit |
| 2026-05-09 | ja | 1346 | 4.9686 | 0.5655 | 0.1674 | 0.1687 | 0.0010 | ja | deribit |
| 2026-05-10 | ja | 1379 | 5.2846 | 0.5066 | 0.1668 | 0.1672 | 0.0010 | ja | deribit |
| 2026-05-11 | ja | 1432 | 5.4453 | 0.3592 | 0.1669 | 0.1775 | 0.0010 | ja | deribit |
| 2026-05-12 | ja | 1431 | 5.3436 | 0.3992 | 0.1669 | 0.1681 | 0.0010 | ja | deribit |
| 2026-05-13 | ja | 1422 | 5.3483 | 0.3990 | 0.1669 | 0.1751 | 0.0010 | ja | deribit |
| 2026-05-14 | ja | 1434 | 5.4318 | 0.3689 | 0.1669 | 0.1706 | 0.0010 | ja | deribit |
| 2026-05-15 | ja | 1426 | 5.3965 | 0.3868 | 0.1669 | 0.1713 | 0.0010 | ja | deribit |

## Tagesuebersicht W2

| Datum | gueltig | T_eff | lambda1 | lambda2 | IPR(v1) | IPR(v2) | p(lambda2) | FDR-sig | dominante Boerse (v2^2) |
|---|:---:|---:|---:|---:|---:|---:|---:|:---:|---|
| 2026-05-16 | ja | 1370 | 5.1691 | 0.4904 | 0.1672 | 0.1759 | 0.0010 | ja | deribit |
| 2026-05-17 | ja | 1394 | 5.3908 | 0.4598 | 0.1668 | 0.1709 | 0.0010 | ja | bybit |
| 2026-05-18 | ja | 1435 | 5.5770 | 0.2899 | 0.1667 | 0.1693 | 0.0410 | ja | deribit |
| 2026-05-19 | ja | 1386 | 5.4493 | 0.3120 | 0.1669 | 0.1748 | 0.3946 | nein | deribit |
| 2026-05-20 | ja | 1433 | 5.5414 | 0.2549 | 0.1669 | 0.2362 | 1.0000 | nein | deribit |
| 2026-05-21 | ja | 1432 | 5.5564 | 0.2597 | 0.1669 | 0.1863 | 0.9890 | nein | deribit |
| 2026-05-22 | ja | 1433 | 5.6431 | 0.2027 | 0.1667 | 0.1789 | 1.0000 | nein | deribit |
| 2026-05-23 | ja | 1421 | 5.4654 | 0.4006 | 0.1667 | 0.1671 | 0.0010 | ja | deribit |
| 2026-05-24 | ja | 1423 | 5.4653 | 0.3225 | 0.1669 | 0.1765 | 0.1179 | nein | deribit |
| 2026-05-25 | ja | 1423 | 5.2953 | 0.3709 | 0.1673 | 0.2508 | 0.3047 | nein | deribit |
| 2026-05-26 | ja | 1436 | 5.4581 | 0.3716 | 0.1668 | 0.1764 | 0.0010 | ja | deribit |
| 2026-05-27 | ja | 1437 | 5.4905 | 0.3302 | 0.1668 | 0.1813 | 0.0090 | ja | deribit |
| 2026-05-28 | ja | 1438 | 5.5072 | 0.3559 | 0.1667 | 0.1682 | 0.0010 | ja | deribit |
| 2026-05-29 | ja | 1432 | 5.4978 | 0.3465 | 0.1668 | 0.1702 | 0.0010 | ja | deribit |
| 2026-05-30 | ja | 1372 | 5.0911 | 0.4848 | 0.1678 | 0.2477 | 0.0010 | ja | deribit |
| 2026-05-31 | ja | 1410 | 5.2612 | 0.4288 | 0.1671 | 0.1797 | 0.0010 | ja | deribit |
| 2026-06-01 | ja | 1439 | 5.5089 | 0.3373 | 0.1668 | 0.1720 | 0.0010 | ja | deribit |
| 2026-06-02 | ja | 1439 | 5.5119 | 0.4027 | 0.1667 | 0.1693 | 0.0010 | ja | deribit |
| 2026-06-03 | ja | 1439 | 5.4834 | 0.4274 | 0.1667 | 0.1678 | 0.0010 | ja | deribit |
| 2026-06-04 | ja | 1439 | 5.6935 | 0.2462 | 0.1667 | 0.1685 | 0.3287 | nein | deribit |
| 2026-06-05 | ja | 1439 | 5.6584 | 0.2977 | 0.1667 | 0.1670 | 0.0010 | ja | deribit |
| 2026-06-06 | ja | 1439 | 5.6640 | 0.2496 | 0.1667 | 0.1678 | 0.4535 | nein | deribit |
| 2026-06-07 | ja | 1439 | 5.6366 | 0.2861 | 0.1667 | 0.1682 | 0.0050 | ja | deribit |
| 2026-06-08 | ja | 1439 | 5.6032 | 0.2893 | 0.1667 | 0.1682 | 0.0140 | ja | deribit |
| 2026-06-09 | ja | 1438 | 5.6182 | 0.2751 | 0.1667 | 0.1708 | 0.1299 | nein | deribit |
| 2026-06-10 | ja | 1439 | 5.6784 | 0.2075 | 0.1667 | 0.1776 | 1.0000 | nein | deribit |
| 2026-06-11 | ja | 1438 | 5.5189 | 0.3778 | 0.1667 | 0.1722 | 0.0010 | ja | deribit |
| 2026-06-12 | ja | 1407 | 5.5543 | 0.2594 | 0.1669 | 0.1859 | 0.9920 | nein | deribit |
| 2026-06-13 | ja | 1404 | 5.1093 | 0.5030 | 0.1680 | 0.2435 | 0.0010 | ja | deribit |
| 2026-06-14 | nein (Panel-Luecke) | — | — | — | — | — | — | — | — |
| 2026-06-15 | ja | 1439 | 5.2872 | 0.5493 | 0.1668 | 0.1674 | 0.0010 | ja | deribit |
| 2026-06-16 | nein (Panel-Luecke) | — | — | — | — | — | — | — | — |
| 2026-06-17 | nein (Panel-Luecke) | — | — | — | — | — | — | — | — |
| 2026-06-18 | nein (Panel-Luecke) | — | — | — | — | — | — | — | — |
| 2026-06-19 | nein (Panel-Luecke) | — | — | — | — | — | — | — | — |
| 2026-06-20 | nein (Panel-Luecke) | — | — | — | — | — | — | — | — |
| 2026-06-21 | nein (Panel-Luecke) | — | — | — | — | — | — | — | — |
| 2026-06-22 | nein (Panel-Luecke) | — | — | — | — | — | — | — | — |
| 2026-06-23 | nein (Panel-Luecke) | — | — | — | — | — | — | — | — |
| 2026-06-24 | nein (Panel-Luecke) | — | — | — | — | — | — | — | — |
| 2026-06-25 | nein (Panel-Luecke) | — | — | — | — | — | — | — | — |
| 2026-06-26 | ja | 1439 | 5.6441 | 0.2821 | 0.1667 | 0.1682 | 0.0020 | ja | deribit |
| 2026-06-27 | nein (Panel-Luecke) | — | — | — | — | — | — | — | — |
| 2026-06-28 | ja | 1419 | 5.4629 | 0.3056 | 0.1670 | 0.2147 | 0.7642 | nein | deribit |
| 2026-06-29 | ja | 1436 | 5.5369 | 0.3362 | 0.1667 | 0.1687 | 0.0010 | ja | deribit |
| 2026-06-30 | ja | 1377 | 5.2345 | 0.3611 | 0.1672 | 0.2404 | 0.4595 | nein | deribit |
| 2026-07-01 | ja | 1438 | 5.4903 | 0.3667 | 0.1667 | 0.1675 | 0.0010 | ja | deribit |
| 2026-07-02 | ja | 1433 | 5.3742 | 0.5159 | 0.1667 | 0.1669 | 0.0010 | ja | deribit |
| 2026-07-03 | ja | 1435 | 5.3196 | 0.4805 | 0.1668 | 0.1685 | 0.0010 | ja | deribit |
| 2026-07-04 | ja | 1415 | 5.0708 | 0.6672 | 0.1670 | 0.1680 | 0.0010 | ja | deribit |

*Erzeugt von `scripts/c12_frag.py` (Welle 4, read-only Harvester-Backfill). capital_free=true. Endgueltiges Gate-Urteil: gate-auditor gegen H-12.*
