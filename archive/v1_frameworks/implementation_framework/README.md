# Bybit Edge — Implementierungs-Framework
## Claude Code · Phase 0–4 · PRD → Production Code

---

## Was dieses Framework tut

Dieses Framework implementiert das `FINAL_PRD.md` vollständig:

```
PRD → Analyse → Infrastruktur → 21 Module → Tests → Pipeline → GitHub
```

**6 Agenten, 4 Phasen, 24 Wochen:**

| Agent | Aufgabe | Einmalig/Wiederholt |
|-------|---------|---------------------|
| Analyst | PRD parsen, Dependency-Graph, Windows-Kompatibilität | Einmalig (Session 1) |
| Infra Builder | WebSocket-Collector, State-Engine, Persistence, Backtester | Einmalig (Session 1) |
| Module Builder | Alle 21 Module M1–M26 implementieren | Wiederholt (Sessions 2–N) |
| Test Engineer | Unit-Tests + Walk-Forward-Backtests | Nach jedem Modul |
| Integrator | 5-Layer-Pipeline + Decision Aggregator + 5 Strategien | Session N |
| DevOps | GitHub, Windows-Scripts, Docker-VPS | Laufend |

---

## Hardware-Profil

| Komponente | Spec | Verwendung |
|-----------|------|-----------|
| GPU | RTX 5060 Ti (16 GB VRAM) | M1 (SNN), M18 (PatchTST), M19 (TimesNet), M20 (MOMENT) |
| RAM | 82 GB | OrderbookState in-memory, Multi-Symbol-Panel |
| VPS | Docker/Ubuntu | 24/7 Collector, Live-Bot |
| Plattform | Windows (Entwicklung) + Linux (Production) | conda + Docker |

---

## Schnellstart

```bash
# 1. Repo klonen / Ordner öffnen in Claude Code
cd bybit-edge-impl
claude  # Claude Code liest CLAUDE.md automatisch

# Claude Code führt dann autonom aus:
# Session 1: Analyst → Infra Builder → Tests → GitHub Push
# Session 2: M22, M23, M2 (Quick Wins) → Tests → Backtest → Push
# Session 3+: Weitere Module nach Priorität
```

---

## Prioritäts-Reihenfolge (aus PRD)

```
Phase 0:  Infra (WebSocket, DB, Backtester)        → v0.1.0
Phase 1:  M22, M23, M24, M2, M7, M8, M15          → v0.2.0 (Strategie 3 live-paper!)
Phase 2:  M26, M14a, M25, M6, M4, M9, M5          → v0.3.0
Phase 3:  M14b, M16, M18, M19, M20, M17, M13, M21 → v0.4.0
Phase 4:  M1, M11, M12, M10, M3                    → v1.0.0
```

**Erste live-paper-testbare Version: Ende Phase 1 (Woche 5)**

---

## Windows-kritische Punkte

1. `tick` Library (Hawkes) → NUR im Docker-Container; `hawkeslib` auf Windows
2. asyncio → `WindowsProactorEventLoopPolicy` in `__main__.py`
3. PyTorch + CUDA → conda (nicht pip) für CUDA-Support
4. pyrqa + IDTxl → OpenJDK erforderlich
5. Alle Pfade → `pathlib.Path`, kein `os.path`

---

*Framework Version 1.0 | Bybit Edge Implementation | Powered by Claude Code*
