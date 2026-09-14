# WP-10(B) - Maker-Fill-Schattenmessung (kapitalfrei, KEIN Alpha-Gate)

Quotes gesamt: 0 | Horizonte (Design-Parameter): [10.0, 60.0] s | adv_sel-Horizont: 60.0 s | Etikett-Schwelle: 1.75 bp

## Fill-Rate-Kurve p_fill(t) (FIFO-conservative / pro-rata-cancel)
### fifo
### prorata

## Adverse Selektion (mittlere Mid-Bewegung gegen die Quote, bp) + Etikett
### fifo
### prorata

## Bootstrap-CI (95%, Kalendertag-Cluster, FIFO)

## DEC-53-Artefakte
- Quote-Outcomes: E:\Claude\Projects\scinance\scinance3-impl\state\wp10b_20260910\wp10b_quote_outcomes.csv (n=0, sha256=93511727136d0fdf...)
- Bootstrap-Fingerprint: E:\Claude\Projects\scinance\scinance3-impl\state\wp10b_20260910\wp10b_bootstrap_fingerprint.json (0 Eintraege, sha256=96019ccaadccbee5...)

(Kein PASS/FAIL. p_fill traegt keine Schwelle; adv_sel <= 1.75 bp ist ein ETIKETT "Maker-Vorteil traegt"/"traegt nicht", je Gruppe und Konvention getrennt berichtet -- FIFO ist die untere, pro-rata die obere Schranke.)
