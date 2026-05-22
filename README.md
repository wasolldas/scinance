# Edge Research Framework — Bybit Retail Trader Edge

Autonomes Multi-Agenten-Forschungssystem zur Entdeckung eines statistischen Edges für
Retail-Trader auf Bybit Perpetual Futures. Ziel ist ein mathematisch fundiertes PRD
(Product Requirements Document) mit priorisierten, implementierbaren Methoden.

## Struktur

```
edge_research_framework/
├── CLAUDE.md                     Master-Orchestrierung
├── agents/
│   ├── 01_orchestrator.md
│   ├── 02_scout.md
│   ├── 03_quant_researcher.md
│   ├── 04_critic.md
│   ├── 05_synthesizer.md
│   └── 06_prd_architect.md
└── results/
    ├── round_1_scout.md
    ├── round_1_quant.md
    ├── critic_report_1.md
    ├── synthesis.md
    └── FINAL_PRD.md              ← Zieldokument
```

## Pipeline (Zielarchitektur)

```
[Bybit WebSocket]
    │
[L1 SNN Ingestion] → [L2 Wavelet Denoising] → [L3 Entropy Greenlight]
                                                       │
                              [L4 TFSAX/DNABERT + Hawkes Matrix]
                                                       │
                                          [L5 Quantum Risk Module]
                                                       │
                                              [EXECUTION DECISION]
```
