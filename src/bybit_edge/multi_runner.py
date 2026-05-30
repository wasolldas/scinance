"""
MultiSymbolRunner — orchestriert mehrere parallele :class:`LiveRunner`,
einen pro Symbol, mit *einer* geteilten :class:`PersistenceLayer`.

Designprinzipien:
    - Jede WS-Connection bleibt sauber isoliert (1 Collector pro Symbol).
    - DuckDB ist Multi-Symbol-fähig (``symbol``-Spalte je Tabelle) — die
      gemeinsame ``PersistenceLayer`` reicht aus (single-writer in-process).
    - Order-Execution bleibt bewusst auf *ein* Symbol beschränkt
      (Position-Sizing-/Hedging-Fragen sind nicht Teil dieser Aufgabe).
    - Die einzelnen ``LiveRunner`` und der bestehende single-symbol Pfad
      bleiben unverändert in ihrem Default-Verhalten.

Verwendung::

    runner = MultiSymbolRunner(["BTCUSDT", "ETHUSDT"], execution_symbol="BTCUSDT")
    await runner.run()
"""
from __future__ import annotations

import asyncio
import logging
from typing import Optional

from bybit_edge.config import PERSIST_ENABLED, PRIMARY_SYMBOL
from bybit_edge.live_runner import LiveRunner
from bybit_edge.persistence.db import PersistenceLayer

logger = logging.getLogger(__name__)


class MultiSymbolRunner:
    """Startet pro Symbol einen :class:`LiveRunner` parallel.

    Parameters
    ----------
    symbols:
        Liste der zu sammelnden Symbole (z.B. ``["BTCUSDT", "ETHUSDT"]``).
        Muss nicht leer sein, Strings müssen nicht leer sein und alle Symbole
        müssen eindeutig sein.
    execution_symbol:
        Symbol, für das Order-Execution erlaubt ist. Wenn ``None``, wird
        :data:`PRIMARY_SYMBOL` verwendet, sofern dieses in ``symbols``
        enthalten ist (sonst läuft alles read-only). Wenn das angegebene
        Symbol nicht in ``symbols`` enthalten ist, wird eine Warnung
        geloggt und kein Runner führt Orders aus.
    """

    def __init__(
        self,
        symbols: list[str],
        execution_symbol: Optional[str] = None,
    ) -> None:
        if not isinstance(symbols, list) or len(symbols) == 0:
            raise ValueError("symbols must be a non-empty list")
        for sym in symbols:
            if not isinstance(sym, str) or not sym.strip():
                raise ValueError(f"invalid symbol entry: {sym!r}")
        if len(set(symbols)) != len(symbols):
            raise ValueError(f"symbols must be unique, got: {symbols}")

        self.symbols: list[str] = list(symbols)

        # Execution-Symbol-Auflösung
        if execution_symbol is None:
            chosen: Optional[str] = (
                PRIMARY_SYMBOL if PRIMARY_SYMBOL in self.symbols else None
            )
        else:
            if execution_symbol not in self.symbols:
                logger.warning(
                    "execution_symbol=%s nicht in symbols=%s — laufe komplett read-only.",
                    execution_symbol, self.symbols,
                )
                chosen = None
            else:
                chosen = execution_symbol
        self.execution_symbol: Optional[str] = chosen

        # Geteilte Persistenz: EINE Instanz für alle LiveRunner.
        self.persist: Optional[PersistenceLayer] = None
        if PERSIST_ENABLED:
            try:
                self.persist = PersistenceLayer()
                logger.info(
                    "MultiSymbolRunner: geteilte PersistenceLayer initialisiert"
                )
            except Exception:
                logger.exception(
                    "MultiSymbolRunner: PersistenceLayer-Init fehlgeschlagen — "
                    "laufe ohne Persistenz weiter."
                )
                self.persist = None

        # Pro Symbol ein LiveRunner (Execution-Override pro Symbol).
        self.runners: list[LiveRunner] = [
            LiveRunner(
                symbol=sym,
                shared_persist=self.persist,
                execution_override=(sym == self.execution_symbol),
            )
            for sym in self.symbols
        ]

        self._running: bool = False

    async def run(self) -> None:
        """Startet alle LiveRunner parallel; läuft, bis ``stop()`` aufgerufen wird."""
        exec_info = (
            f"execution for {self.execution_symbol}"
            if self.execution_symbol
            else "no execution"
        )
        logger.info(
            "Starting MultiSymbolRunner — %d symbols (%s), %s",
            len(self.symbols), ",".join(self.symbols), exec_info,
        )
        self._running = True
        try:
            await asyncio.gather(*[r.run() for r in self.runners])
        except asyncio.CancelledError:
            logger.info("MultiSymbolRunner cancelled — fahre herunter.")
        finally:
            await self.stop()

    async def stop(self) -> None:
        """Stoppt alle Runner parallel; schließt die geteilte PersistenceLayer einmalig."""
        if not self._running and self.persist is None:
            # idempotenter no-op
            return
        self._running = False

        # Alle Runner parallel stoppen (jeder respektiert _owns_persist=False).
        results = await asyncio.gather(
            *[r.stop() for r in self.runners], return_exceptions=True
        )
        for sym, res in zip(self.symbols, results):
            if isinstance(res, Exception):
                logger.warning("Runner %s stop() error: %s", sym, res)

        # Genau hier — und nur einmal — schließen wir die geteilte Persistenz.
        if self.persist is not None:
            try:
                counts = self.persist.row_counts()
                logger.info("MultiSymbolRunner Persistenz-Stand: %s", counts)
            except Exception:
                logger.exception("row_counts() bei Shutdown fehlgeschlagen")
            try:
                self.persist.close()
            except Exception:
                logger.exception("PersistenceLayer.close() fehlgeschlagen")
            self.persist = None

        logger.info("MultiSymbolRunner gestoppt.")
