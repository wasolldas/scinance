# WP-10(B) - Maker-Fill-Schattenmessung (kapitalfrei, KEIN Alpha-Gate)

Quotes gesamt: 432348 | Horizonte (Design-Parameter): [10.0, 60.0] s | adv_sel-Horizont: 60.0 s | Etikett-Schwelle: 1.75 bp

## Fill-Rate-Kurve p_fill(t) (FIFO-conservative / pro-rata-cancel)
### fifo
- BTCUSDT buy (n=108085): p_fill(10s)=0.045, p_fill(60s)=0.065
- BTCUSDT sell (n=108085): p_fill(10s)=0.044, p_fill(60s)=0.065
- ETHUSDT buy (n=108085): p_fill(10s)=0.045, p_fill(60s)=0.056
- ETHUSDT sell (n=108085): p_fill(10s)=0.049, p_fill(60s)=0.060
### prorata
- BTCUSDT buy (n=108085): p_fill(10s)=0.290, p_fill(60s)=0.372
- BTCUSDT sell (n=108085): p_fill(10s)=0.295, p_fill(60s)=0.377
- ETHUSDT buy (n=108085): p_fill(10s)=0.275, p_fill(60s)=0.315
- ETHUSDT sell (n=108085): p_fill(10s)=0.285, p_fill(60s)=0.324

## Adverse Selektion (mittlere Mid-Bewegung gegen die Quote, bp) + Etikett
### fifo
- BTCUSDT buy (n_filled=6987): mean=0.627 bp, median=0.559 bp -> Maker-Vorteil traegt
- BTCUSDT sell (n_filled=6973): mean=0.678 bp, median=0.542 bp -> Maker-Vorteil traegt
- ETHUSDT buy (n_filled=6050): mean=0.713 bp, median=0.579 bp -> Maker-Vorteil traegt
- ETHUSDT sell (n_filled=6501): mean=0.773 bp, median=0.598 bp -> Maker-Vorteil traegt
### prorata
- BTCUSDT buy (n_filled=40206): mean=0.290 bp, median=0.122 bp -> Maker-Vorteil traegt
- BTCUSDT sell (n_filled=40792): mean=0.368 bp, median=0.131 bp -> Maker-Vorteil traegt
- ETHUSDT buy (n_filled=34005): mean=0.350 bp, median=0.182 bp -> Maker-Vorteil traegt
- ETHUSDT sell (n_filled=34993): mean=0.431 bp, median=0.265 bp -> Maker-Vorteil traegt

## Bootstrap-CI (95%, Kalendertag-Cluster, FIFO)
- p_fill(60s) BTCUSDT buy (n_days=78): 0.064 [0.060, 0.068] (seed=53, n_bootstrap=1000)
- p_fill(60s) BTCUSDT sell (n_days=78): 0.064 [0.059, 0.068] (seed=53, n_bootstrap=1000)
- p_fill(60s) ETHUSDT buy (n_days=78): 0.055 [0.051, 0.059] (seed=53, n_bootstrap=1000)
- p_fill(60s) ETHUSDT sell (n_days=78): 0.060 [0.055, 0.064] (seed=53, n_bootstrap=1000)
- adv_sel BTCUSDT buy (n_days=78): 0.284 bp [-0.321, 0.760] (seed=53, n_bootstrap=1000)
- adv_sel BTCUSDT sell (n_days=78): 0.640 bp [0.462, 0.822] (seed=53, n_bootstrap=1000)
- adv_sel ETHUSDT buy (n_days=78): 0.893 bp [0.560, 1.315] (seed=53, n_bootstrap=1000)
- adv_sel ETHUSDT sell (n_days=78): 0.902 bp [0.390, 1.517] (seed=53, n_bootstrap=1000)

## DEC-53-Artefakte
- Quote-Outcomes: E:\Claude\Projects\scinance\scinance3-impl\state\wp10b_20260924\wp10b_quote_outcomes.csv (n=432348, sha256=5d986d1887ae68dc...)
- Bootstrap-Fingerprint: E:\Claude\Projects\scinance\scinance3-impl\state\wp10b_20260924\wp10b_bootstrap_fingerprint.json (8 Eintraege, sha256=a8deec4c072d27de...)

(Kein PASS/FAIL. p_fill traegt keine Schwelle; adv_sel <= 1.75 bp ist ein ETIKETT "Maker-Vorteil traegt"/"traegt nicht", je Gruppe und Konvention getrennt berichtet -- FIFO ist die untere, pro-rata die obere Schranke.)

## Tages-Status je Symbol (aus dem fillshadow_1min-Store)

- BTCUSDT: no_raw=17, ok=78
    - 17x (kein Grund)
- ETHUSDT: no_raw=17, ok=78
    - 17x (kein Grund)

(Ein Tag ohne 'ok' liefert keine Quotes: no_raw = keine Rohdaten im Harvest, not_manifest_done = Harvest-Manifest ohne DONE fuer orderbook oder publicTrade, discarded = Sequenzbruch-Budget ueberschritten.)
