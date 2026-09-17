# WP-10(B) - Maker-Fill-Schattenmessung (kapitalfrei, KEIN Alpha-Gate)

Quotes gesamt: 357468 | Horizonte (Design-Parameter): [10.0, 60.0] s | adv_sel-Horizont: 60.0 s | Etikett-Schwelle: 1.75 bp

## Fill-Rate-Kurve p_fill(t) (FIFO-conservative / pro-rata-cancel)
### fifo
- BTCUSDT buy (n=90805): p_fill(10s)=0.043, p_fill(60s)=0.063
- BTCUSDT sell (n=90805): p_fill(10s)=0.043, p_fill(60s)=0.063
- ETHUSDT buy (n=87925): p_fill(10s)=0.043, p_fill(60s)=0.055
- ETHUSDT sell (n=87925): p_fill(10s)=0.047, p_fill(60s)=0.058
### prorata
- BTCUSDT buy (n=90805): p_fill(10s)=0.284, p_fill(60s)=0.367
- BTCUSDT sell (n=90805): p_fill(10s)=0.289, p_fill(60s)=0.372
- ETHUSDT buy (n=87925): p_fill(10s)=0.269, p_fill(60s)=0.313
- ETHUSDT sell (n=87925): p_fill(10s)=0.279, p_fill(60s)=0.321

## Adverse Selektion (mittlere Mid-Bewegung gegen die Quote, bp) + Etikett
### fifo
- BTCUSDT buy (n_filled=5728): mean=0.565 bp, median=0.503 bp -> Maker-Vorteil traegt
- BTCUSDT sell (n_filled=5708): mean=0.709 bp, median=0.555 bp -> Maker-Vorteil traegt
- ETHUSDT buy (n_filled=4832): mean=0.735 bp, median=0.599 bp -> Maker-Vorteil traegt
- ETHUSDT sell (n_filled=5138): mean=0.736 bp, median=0.540 bp -> Maker-Vorteil traegt
### prorata
- BTCUSDT buy (n_filled=33359): mean=0.281 bp, median=0.088 bp -> Maker-Vorteil traegt
- BTCUSDT sell (n_filled=33773): mean=0.361 bp, median=0.115 bp -> Maker-Vorteil traegt
- ETHUSDT buy (n_filled=27521): mean=0.361 bp, median=0.145 bp -> Maker-Vorteil traegt
- ETHUSDT sell (n_filled=28263): mean=0.409 bp, median=0.235 bp -> Maker-Vorteil traegt

## Bootstrap-CI (95%, Kalendertag-Cluster, FIFO)
- p_fill(60s) BTCUSDT buy (n_days=66): 0.062 [0.058, 0.067] (seed=53, n_bootstrap=1000)
- p_fill(60s) BTCUSDT sell (n_days=66): 0.062 [0.057, 0.067] (seed=53, n_bootstrap=1000)
- p_fill(60s) ETHUSDT buy (n_days=64): 0.054 [0.050, 0.059] (seed=53, n_bootstrap=1000)
- p_fill(60s) ETHUSDT sell (n_days=64): 0.058 [0.053, 0.063] (seed=53, n_bootstrap=1000)
- adv_sel BTCUSDT buy (n_days=66): 0.170 bp [-0.552, 0.711] (seed=53, n_bootstrap=1000)
- adv_sel BTCUSDT sell (n_days=66): 0.663 bp [0.452, 0.871] (seed=53, n_bootstrap=1000)
- adv_sel ETHUSDT buy (n_days=64): 0.944 bp [0.548, 1.474] (seed=53, n_bootstrap=1000)
- adv_sel ETHUSDT sell (n_days=64): 0.887 bp [0.229, 1.664] (seed=53, n_bootstrap=1000)

## DEC-53-Artefakte
- Quote-Outcomes: E:\Claude\Projects\scinance\scinance3-impl\state\wp10b_20260916\wp10b_quote_outcomes.csv (n=357468, sha256=0a0e0d226a1ea0e2...)
- Bootstrap-Fingerprint: E:\Claude\Projects\scinance\scinance3-impl\state\wp10b_20260916\wp10b_bootstrap_fingerprint.json (8 Eintraege, sha256=2706f32df18a4be6...)

(Kein PASS/FAIL. p_fill traegt keine Schwelle; adv_sel <= 1.75 bp ist ein ETIKETT "Maker-Vorteil traegt"/"traegt nicht", je Gruppe und Konvention getrennt berichtet -- FIFO ist die untere, pro-rata die obere Schranke.)

## Tages-Status je Symbol (aus dem fillshadow_1min-Store)

- BTCUSDT: discarded=3, no_raw=18, ok=66
    - 18x (kein Grund)
    - 1x 14 sequence breaks > 10
    - 1x 24 sequence breaks > 10
    - 1x 277792 sequence breaks > 10
- ETHUSDT: discarded=5, no_raw=18, ok=64
    - 18x (kein Grund)
    - 1x 11 sequence breaks > 10
    - 1x 16 sequence breaks > 10
    - 1x 28 sequence breaks > 10
    - 1x 27 sequence breaks > 10

(Ein Tag ohne 'ok' liefert keine Quotes: no_raw = keine Rohdaten im Harvest, not_manifest_done = Harvest-Manifest ohne DONE fuer orderbook oder publicTrade, discarded = Sequenzbruch-Budget ueberschritten.)
