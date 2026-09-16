# WP-10(B) - Maker-Fill-Schattenmessung (kapitalfrei, KEIN Alpha-Gate)

Quotes gesamt: 354000 | Horizonte (Design-Parameter): [10.0, 60.0] s | adv_sel-Horizont: 60.0 s | Etikett-Schwelle: 1.75 bp

## Fill-Rate-Kurve p_fill(t) (FIFO-conservative / pro-rata-cancel)
### fifo
- BTCUSDT buy (n=89938): p_fill(10s)=0.042, p_fill(60s)=0.061
- BTCUSDT sell (n=89938): p_fill(10s)=0.041, p_fill(60s)=0.060
- ETHUSDT buy (n=87058): p_fill(10s)=0.042, p_fill(60s)=0.053
- ETHUSDT sell (n=87058): p_fill(10s)=0.044, p_fill(60s)=0.056
### prorata
- BTCUSDT buy (n=89938): p_fill(10s)=0.275, p_fill(60s)=0.357
- BTCUSDT sell (n=89938): p_fill(10s)=0.280, p_fill(60s)=0.362
- ETHUSDT buy (n=87058): p_fill(10s)=0.261, p_fill(60s)=0.304
- ETHUSDT sell (n=87058): p_fill(10s)=0.269, p_fill(60s)=0.311

## Adverse Selektion (mittlere Mid-Bewegung gegen die Quote, bp) + Etikett
### fifo
- BTCUSDT buy (n_filled=85): mean=-9.480 bp, median=0.515 bp -> Maker-Vorteil traegt
- BTCUSDT sell (n_filled=77): mean=0.762 bp, median=1.048 bp -> Maker-Vorteil traegt
- ETHUSDT buy (n_filled=42): mean=14.685 bp, median=1.017 bp -> Maker-Vorteil traegt nicht
- ETHUSDT sell (n_filled=77): mean=11.611 bp, median=-0.814 bp -> Maker-Vorteil traegt nicht
### prorata
- BTCUSDT buy (n_filled=107): mean=-11.655 bp, median=0.777 bp -> Maker-Vorteil traegt
- BTCUSDT sell (n_filled=94): mean=1.227 bp, median=0.189 bp -> Maker-Vorteil traegt
- ETHUSDT buy (n_filled=56): mean=11.300 bp, median=0.775 bp -> Maker-Vorteil traegt nicht
- ETHUSDT sell (n_filled=91): mean=8.855 bp, median=-1.778 bp -> Maker-Vorteil traegt nicht

## Bootstrap-CI (95%, Kalendertag-Cluster, FIFO)
- p_fill(60s) BTCUSDT buy (n_days=63): 0.061 [0.055, 0.066] (seed=53, n_bootstrap=1000)
- p_fill(60s) BTCUSDT sell (n_days=63): 0.060 [0.054, 0.067] (seed=53, n_bootstrap=1000)
- p_fill(60s) ETHUSDT buy (n_days=61): 0.053 [0.048, 0.058] (seed=53, n_bootstrap=1000)
- p_fill(60s) ETHUSDT sell (n_days=61): 0.056 [0.051, 0.062] (seed=53, n_bootstrap=1000)
- adv_sel BTCUSDT buy (n_days=21): -8.622 bp [-19.135, 0.528] (seed=53, n_bootstrap=1000)
- adv_sel BTCUSDT sell (n_days=19): -4.428 bp [-18.964, 4.331] (seed=53, n_bootstrap=1000)
- adv_sel ETHUSDT buy (n_days=27): 17.499 bp [-12.226, 60.340] (seed=53, n_bootstrap=1000)
- adv_sel ETHUSDT sell (n_days=32): 18.300 bp [-1.691, 44.412] (seed=53, n_bootstrap=1000)

## DEC-53-Artefakte
- Quote-Outcomes: E:\Claude\Projects\scinance\scinance3-impl\state\wp10b_20260915\wp10b_quote_outcomes.csv (n=354000, sha256=283a63ae425fab14...)
- Bootstrap-Fingerprint: E:\Claude\Projects\scinance\scinance3-impl\state\wp10b_20260915\wp10b_bootstrap_fingerprint.json (8 Eintraege, sha256=64ed59c900193935...)

(Kein PASS/FAIL. p_fill traegt keine Schwelle; adv_sel <= 1.75 bp ist ein ETIKETT "Maker-Vorteil traegt"/"traegt nicht", je Gruppe und Konvention getrennt berichtet -- FIFO ist die untere, pro-rata die obere Schranke.)

## Tages-Status je Symbol (aus dem fillshadow_1min-Store)

- BTCUSDT: meta_missing=86
- ETHUSDT: meta_missing=86

(Ein Tag ohne 'ok' liefert keine Quotes: no_raw = keine Rohdaten im Harvest, not_manifest_done = Harvest-Manifest ohne DONE fuer orderbook oder publicTrade, discarded = Sequenzbruch-Budget ueberschritten.)
