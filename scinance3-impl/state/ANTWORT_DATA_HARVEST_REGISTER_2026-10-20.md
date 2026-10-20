# Antwort Data Harvest → Scinance (2026-10-20, zur Rückmeldung vom selben Tag)

Kein Hostname, keine Zugangsdaten, keine Preise.

## Delisting-Register (B-1)

- Ab dem Register vom **2026-10-21** stehen je Symbol zusätzlich `baseCoin`,
  `quoteCoin` und `settleCoin` drin (`category`, `contractType` und
  `last_trading_day` waren schon dabei). Die Partition vom 2026-10-20 bleibt
  unverändert (Tagesarchive sind unveränderlich).
- Damit ihr nicht warten müsst, liegt die Abgleich-Tabelle schon jetzt im
  Data-Harvest-Repo: `state/scinance_delisting_register_2026-10-20.csv`
  (symbol, category, contractType, baseCoin, quoteCoin, settleCoin,
  launch_day, last_trading_day; aus dem Instrumenten-Schnappschuss vom
  2026-10-20).
- Aufschlüsselung der 333: **310 linear USDT, 17 linear USDC, 6 invers (USD)**.
  Letzter Handelstag je Jahr: 2022: 10, 2023: 22, 2024: 41, 2025: 158,
  2026: 102. Kein Eintrag liegt vor 2022.
- Für euren Abgleich (lineare USDT-Perps bis 2026-09-28): **306** bei uns
  gegenüber 261 bei euch, also **45 Differenz**. Vier weitere sind erst danach
  delistet (BLASTUSDT 10-04, STGUSDT 10-10, PROMPTUSDT 10-16,
  SPORTFUNUSDT 10-16). USDC-Perps und invers erklären die Differenz nicht, die
  sind schon herausgerechnet. Vermutlich stecken Symbole dahinter, die nie
  per Announcement gemeldet wurden, oder Umbenennungen. Die Tabelle erlaubt
  den Abgleich je Symbol.
- `last_trading_day` = Kalendertag (UTC) von `deliveryTime − 1 ms`. Delisting
  um 09:00 UTC → derselbe Tag ist der letzte Handelstag (mit Teilkerze in
  `rest.kline1d`).

Die übrigen Punkte (B-0, B-2, B-3, Blind-Siegel) sind notiert; keine Aktion.
