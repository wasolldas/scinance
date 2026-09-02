# Windows-Kompatibilitätsbericht

Generiert: 2026-05-26 | PRD-Quelle: FINAL_PRD.md | 21 Methoden analysiert

---

## Kritische Probleme (5 identifiziert)

### 1. `tick` Library (M14 Hawkes MLE)

- **Status:** NICHT nativ unter Windows kompilierbar (C++/OpenMP-Abhängigkeiten ohne Windows-Build-Support)
- **Betroffene Methoden:** M14 (Hawkes Spektralradius 6-D)
- **Lösung A:** WSL2 + Ubuntu-Environment (für VPS-Build ohnehin Standard)
- **Lösung B:** `hawkeslib` (pip install hawkeslib) — reine Python/NumPy-Implementierung, Windows-kompatibel, ähnliche API für exponentiellen Kernel
- **Lösung C:** Eigene scipy.optimize-basierte MLE als Fallback (immer implementieren, ~100 LOC)
- **Empfehlung:** Implementiere BEIDE Fallbacks (hawkeslib + eigene MLE). `tick` nur im Docker-Container (Linux VPS). Code-Struktur:
  ```python
  try:
      from tick.hawkes import HawkesExpKern
  except ImportError:
      from bybit_edge.layers.l4_pattern.hawkes_fallback import HawkesExpKernFallback as HawkesExpKern
  ```

### 2. asyncio ProactorEventLoop (alle Module)

- **Status:** Windows Python 3.11+ verwendet standardmäßig ProactorEventLoop. Einige asyncio-basierte Libraries (websockets, aiohttp) haben Kompatibilitätsprobleme.
- **Betroffene Module:** Alle (WebSocket-Collector, gesamte Pipeline)
- **Fix:** In `src/bybit_edge/__main__.py` (bereits implementiert):
  ```python
  import sys, asyncio
  if sys.platform == "win32":
      asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
  ```
- **Status:** GELÖST in `__main__.py`

### 3. PyTorch + CUDA (M1, M18, M19, M20)

- **Status:** PyTorch CUDA-Support unter Windows erfordert Installation via conda (nicht pip)
- **Betroffene Methoden:** M1 (SpikeWavformer), M18 (PatchTST), M19 (TimesNet), M20 (MOMENT)
- **Hardware:** RTX 5060 Ti mit CUDA 12.x
- **Fix:** Installation ausschließlich via conda:
  ```bash
  conda install pytorch torchvision torchaudio pytorch-cuda=12.4 -c pytorch -c nvidia
  ```
- **NICHT via pip** (CUDA-Packages oft inkompatibel auf Windows via pip)
- **Verifikation:**
  ```python
  python -c "import torch; print(torch.cuda.is_available()); print(torch.cuda.get_device_name(0))"
  ```
- **Empfehlung:** `environment.yml` mit conda-Channels für PyTorch+CUDA; pip nur für reine Python-Packages

### 4. `pyrqa` (M12 RQA) — Java-Abhängigkeit

- **Status:** pyrqa benötigt Java Runtime (OpenJDK) für die interne Berechnung
- **Betroffene Methoden:** M12 (Recurrence Quantification Analysis)
- **Fix Windows:**
  ```bash
  choco install openjdk
  # oder manuell: https://adoptium.net/
  set JAVA_HOME=C:\Program Files\Eclipse Adoptium\jdk-21.0.x
  pip install pyrqa
  ```
- **Fix Linux/Docker:**
  ```bash
  apt-get install -y default-jre
  pip install pyrqa
  ```
- **Alternative:** Eigene RQA-Implementierung in reinem NumPy (~200 LOC für DET/LAM-Berechnung) als Fallback

### 5. `IDTxl` (M17 Renyi-Transfer-Entropy) — Java-Abhängigkeit

- **Status:** IDTxl nutzt intern JIDT (Java Information Dynamics Toolkit) — erfordert JVM
- **Betroffene Methoden:** M17 (Renyi-TE Lead-Lag-Graph)
- **Fix:** Gleiche Java-Installation wie pyrqa (OpenJDK)
- **Alternative:** `pyinform` als leichterer Ersatz (pip install pyinform, kein Java nötig)
- **Empfehlung:** pyinform als primäre Library verwenden; IDTxl nur für erweiterte Renyi-TE mit q-Parameter, dann im Docker-Container

---

## Querschnitts-Regel: Pfad-Handling

- **ALLE Pfade** in der gesamten Codebase via `pathlib.Path` — niemals `os.path.join` mit hardcodierten Slashes
- Windows: `\` vs. Linux: `/` — pathlib abstrahiert automatisch
- Config-Pfade (DATA_DIR, DB_PATH, PARQUET_DIR) sind bereits als `pathlib.Path` definiert
- **Keine String-Pfade:** `open("data/foo.parquet")` ist verboten; korrekt: `open(PARQUET_DIR / "foo.parquet")`

---

## Unkritische Kompatibilitätsprobleme (Warnings, kein Blocker)

| Library | Windows-Status | Betroffene Methoden | Hinweise |
|---------|---------------|---------------------|----------|
| `hmmlearn` | Vollständig kompatibel | M9 | pip install |
| `PyWavelets` (pywt) | Vollständig kompatibel | M1, M4 | pip install |
| `ripser` | Installierbar via pip | M11 | C++-Compilation, aber Wheels vorhanden |
| `gudhi` | Installierbar via pip/conda | M11 | conda empfohlen |
| `persim` | Vollständig kompatibel | M11 | pip install |
| `giotto-tda` | Installierbar via pip | M11 | Wheels für Windows vorhanden |
| `snnTorch` | PyTorch-basiert | M1 | Nach PyTorch-Install problemlos |
| `Norse` | PyTorch-basiert | M1 | Nach PyTorch-Install problemlos |
| `ordpy` | Vollständig kompatibel | M7 | Reines Python |
| `antropy` | Vollständig kompatibel | M7 | pip install |
| `MFDFA` | Vollständig kompatibel | M10 | pip install |
| `bayesian-changepoint-detection` | Vollständig kompatibel | M8 | pip install |
| `pykalman` | Vollständig kompatibel | M24 | pip install |
| `filterpy` | Vollständig kompatibel | M24 | pip install |
| `numba` | Vollständig kompatibel | M2 | conda empfohlen |
| `polars` | Vollständig kompatibel | M2, M6, M13 | pip install |
| `duckdb` | Vollständig kompatibel | Persistence | pip install |
| `pyarrow` | Vollständig kompatibel | Persistence | pip install |
| `tslearn` | Vollständig kompatibel | M16 | pip install |
| `saxpy` | Vollständig kompatibel | M16 | pip install |
| `Biopython` | Vollständig kompatibel | M16 | pip install |
| `parasail` | Wheels vorhanden | M16 | pip install |
| `httpx` | Vollständig kompatibel | M21 | pip install |
| `sortedcontainers` | Vollständig kompatibel | M3 | Reines Python |
| `scipy` | Vollständig kompatibel | M8, M14, M15, M26 | pip/conda install |
| `statsmodels` | Vollständig kompatibel | M5, M25 | pip install |
| `transformers` | Vollständig kompatibel | M20 | pip install |
| `momentfm` | Vollständig kompatibel | M20 | pip install |

---

## Methoden-Kompatibilitäts-Matrix

| Methode | Windows nativ | Mit Workaround | Nur Docker/WSL2 | Workaround |
|---------|:------------:|:--------------:|:---------------:|------------|
| M1 SpikeWavformer | - | X | - | conda PyTorch+CUDA |
| M2 OFI | X | - | - | - |
| M3 Iceberg | X | - | - | - |
| M4 Wavelet | X | - | - | - |
| M5 FFD | X | - | - | - |
| M6 Shannon | X | - | - | - |
| M7 PE | X | - | - | - |
| M8 BOCPD | X | - | - | - |
| M9 HMM | X | - | - | - |
| M10 MF-DFA | X | - | - | - |
| M11 TDA | X | - | - | - |
| M12 RQA | - | X | - | OpenJDK installieren |
| M13 CSZ | X | - | - | - |
| M14 Hawkes | - | - | X | tick nur Linux; hawkeslib als Fallback |
| M15 GR/Omori | X | - | - | - |
| M16 TFSAX+SW | X | - | - | - |
| M17 Renyi-TE | - | X | - | pyinform statt IDTxl; oder OpenJDK |
| M18 PatchTST | - | X | - | conda PyTorch+CUDA |
| M19 TimesNet | - | X | - | conda PyTorch+CUDA |
| M20 MOMENT | - | X | - | conda PyTorch+CUDA |
| M21 L/S-Ratio | X | - | - | - |
| M22 Funding | X | - | - | - |
| M23 Basis | X | - | - | - |
| M24 Kalman | X | - | - | - |
| M25 Kyle Lambda | X | - | - | - |
| M26 SIR | X | - | - | - |

**Zusammenfassung:** 16/21 Methoden laufen nativ unter Windows. 4 Methoden benötigen conda-PyTorch oder OpenJDK. 1 Methode (M14 Hawkes mit `tick`) erfordert Linux/WSL2/Docker, hat aber hawkeslib-Fallback.

---

## Setup-Reihenfolge für Windows

1. **Anaconda/Miniconda installieren** (https://docs.conda.io/en/latest/miniconda.html)
2. **CUDA 12.4 Toolkit installieren** (https://developer.nvidia.com/cuda-12-4-0-download-archive)
3. **Conda-Environment erstellen:**
   ```bash
   conda env create -f environment.yml
   conda activate bybit-edge
   ```
4. **CUDA-Verifikation:**
   ```bash
   python -c "import torch; print(torch.cuda.is_available()); print(torch.cuda.get_device_name(0))"
   ```
5. **OpenJDK installieren** (für pyrqa + IDTxl, falls benötigt):
   ```bash
   choco install openjdk
   ```
6. **Editable Install:**
   ```bash
   pip install -e ".[dev]"
   ```
7. **Verifikation:**
   ```bash
   python -m bybit_edge
   pytest tests/ -v
   ```

---

## Setup-Reihenfolge für Linux VPS (Docker)

1. **Docker + Docker Compose installieren**
2. **NVIDIA Container Toolkit installieren** (für GPU-Support)
3. **Build + Start:**
   ```bash
   cd docker/
   docker compose up --build -d
   ```
4. **Alle Libraries inklusive `tick` sind im Container verfügbar**
