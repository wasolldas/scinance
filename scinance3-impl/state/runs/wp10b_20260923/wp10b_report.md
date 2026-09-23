# WP-10(B) - Maker-Fill-Schattenmessung (kapitalfrei, KEIN Alpha-Gate)

Quotes gesamt: 380508 | Horizonte (Design-Parameter): [10.0, 60.0] s | adv_sel-Horizont: 60.0 s | Etikett-Schwelle: 1.75 bp

## Fill-Rate-Kurve p_fill(t) (FIFO-conservative / pro-rata-cancel)
### fifo
- BTCUSDT buy (n=95125): p_fill(10s)=0.044, p_fill(60s)=0.064
- BTCUSDT sell (n=95125): p_fill(10s)=0.044, p_fill(60s)=0.064
- ETHUSDT buy (n=95125): p_fill(10s)=0.045, p_fill(60s)=0.056
- ETHUSDT sell (n=95125): p_fill(10s)=0.048, p_fill(60s)=0.060
### prorata
- BTCUSDT buy (n=95125): p_fill(10s)=0.286, p_fill(60s)=0.370
- BTCUSDT sell (n=95125): p_fill(10s)=0.291, p_fill(60s)=0.375
- ETHUSDT buy (n=95125): p_fill(10s)=0.274, p_fill(60s)=0.316
- ETHUSDT sell (n=95125): p_fill(10s)=0.284, p_fill(60s)=0.325

## Adverse Selektion (mittlere Mid-Bewegung gegen die Quote, bp) + Etikett
### fifo
- BTCUSDT buy (n_filled=6093): mean=0.610 bp, median=0.531 bp -> Maker-Vorteil traegt
- BTCUSDT sell (n_filled=6122): mean=0.693 bp, median=0.547 bp -> Maker-Vorteil traegt
- ETHUSDT buy (n_filled=5349): mean=0.737 bp, median=0.600 bp -> Maker-Vorteil traegt
- ETHUSDT sell (n_filled=5718): mean=0.754 bp, median=0.587 bp -> Maker-Vorteil traegt
### prorata
- BTCUSDT buy (n_filled=35238): mean=0.289 bp, median=0.092 bp -> Maker-Vorteil traegt
- BTCUSDT sell (n_filled=35682): mean=0.363 bp, median=0.121 bp -> Maker-Vorteil traegt
- ETHUSDT buy (n_filled=30079): mean=0.358 bp, median=0.144 bp -> Maker-Vorteil traegt
- ETHUSDT sell (n_filled=30911): mean=0.420 bp, median=0.240 bp -> Maker-Vorteil traegt

## Bootstrap-CI (95%, Kalendertag-Cluster, FIFO)
- p_fill(60s) BTCUSDT buy (n_days=69): 0.063 [0.058, 0.068] (seed=53, n_bootstrap=1000)
- p_fill(60s) BTCUSDT sell (n_days=69): 0.063 [0.058, 0.069] (seed=53, n_bootstrap=1000)
- p_fill(60s) ETHUSDT buy (n_days=69): 0.056 [0.051, 0.060] (seed=53, n_bootstrap=1000)
- p_fill(60s) ETHUSDT sell (n_days=69): 0.060 [0.054, 0.065] (seed=53, n_bootstrap=1000)
- adv_sel BTCUSDT buy (n_days=69): 0.217 bp [-0.509, 0.751] (seed=53, n_bootstrap=1000)
- adv_sel BTCUSDT sell (n_days=69): 0.658 bp [0.433, 0.865] (seed=53, n_bootstrap=1000)
- adv_sel ETHUSDT buy (n_days=69): 0.925 bp [0.577, 1.439] (seed=53, n_bootstrap=1000)
- adv_sel ETHUSDT sell (n_days=69): 0.914 bp [0.321, 1.625] (seed=53, n_bootstrap=1000)

## DEC-53-Artefakte
- Quote-Outcomes: E:\Claude\Projects\scinance\scinance3-impl\state\wp10b_20260923\wp10b_quote_outcomes.csv (n=380508, sha256=b6f700e7742a5996...)
- Bootstrap-Fingerprint: E:\Claude\Projects\scinance\scinance3-impl\state\wp10b_20260923\wp10b_bootstrap_fingerprint.json (8 Eintraege, sha256=15b709e949e86db4...)

(Kein PASS/FAIL. p_fill traegt keine Schwelle; adv_sel <= 1.75 bp ist ein ETIKETT "Maker-Vorteil traegt"/"traegt nicht", je Gruppe und Konvention getrennt berichtet -- FIFO ist die untere, pro-rata die obere Schranke.)

## Tages-Status je Symbol (aus dem fillshadow_1min-Store)

- BTCUSDT: no_raw=25, ok=69
    - 25x (kein Grund)
- ETHUSDT: no_raw=25, ok=69
    - 25x (kein Grund)

(Ein Tag ohne 'ok' liefert keine Quotes: no_raw = keine Rohdaten im Harvest, not_manifest_done = Harvest-Manifest ohne DONE fuer orderbook oder publicTrade, discarded = Sequenzbruch-Budget ueberschritten.)
