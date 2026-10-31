# Anfrage an das Data-Harvest-Projekt: 1-Minuten-Kerzen fuer das A2-Negativ-Panel (2026-10-31)

> Zweck: Das A2-Design (EXP-CLOCK, DEC-103) verlangt als Gate-Bedingung (4) ein Negativ-Panel aus Realdaten:
> Perpetuals ohne liquide Optionskette (XRP, BNB, SOL vor 2025), auf denen die 30-Minuten-Rendite 07:30-08:00 UTC
> an Freitagen gegen Mo-Do keinen Verfallseffekt zeigen darf. Dafuer fehlen im Archiv die 1-Minuten-Kerzen.
> Kein Hostname, keine Zugangsdaten in dieser Datei.

## Was fehlt

- `bybit/rest.kline1m` fuehrt im Katalog (Stand 2026-10-31) nur BTCUSDT (ab 2020-03-25) und ETHUSDT (ab 2021-03-15).
- Gebraucht werden dieselben 1-Minuten-Kerzen (REST, lineare USDT-Perps, Kestrel-Schema wie BTCUSDT) fuer
  **XRPUSDT, BNBUSDT, SOLUSDT**, Zeitraum **2021-03-24 bis 2026-06-28** (Vorperiode fuer die Nuisance und die beiden
  Urteilsfenster W1/W2; danach bitte wie BTC/ETH taeglich weiterfuehren). Fehlende Tage bitte im Katalog als
  Luecke fuehren, nicht fuellen.
- Groesse: ~1.440 Zeilen je Symbol und Tag, ~62 KB je Tag (wie BTCUSDT) -> rund 120 MB je Symbol fuer 5,3 Jahre.

## Was nicht gebraucht wird

- Keine Orderbuecher, keine Trades, keine Optionsdaten fuer diese Symbole.
- Keine Daten fuer BTCUSDT/ETHUSDT (vorhanden).

## Lesart in Scinance

- Nur Zaehlungen und Streuungsmasse auf der Vorperiode (<= 2024-05-31) bis zu einer Registrierung; die Fenster
  2024-07-01..2026-06-28 bleiben bis dahin unberuehrt; das Blind-Siegel DEC-96 E3 (BTC/ETH ab 2026-07-01) ist von
  dieser Anfrage nicht betroffen.
- Die Cloud liest nur ueber `hd.catalog()` / `hd.load()` (kein Listing des Buckets).

Rueckmeldung bitte als kurze Notiz (Zeitraum geliefert, Luecken), die Scinance in `state/decisions.md` (DEC-103
Nachtrag) fuehrt.
