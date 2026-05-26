"""
Bybit Edge System — Entry Point.

Windows-kompatibles asyncio-Setup + Hauptschleife.
Verwendung: python -m bybit_edge
"""
import sys
import asyncio
import logging
import signal
from typing import NoReturn

from bybit_edge.config import LOG_LEVEL, RANDOM_SEED


def _configure_windows_asyncio() -> None:
    """Setzt die korrekte EventLoop-Policy unter Windows.

    Windows Python 3.11+ verwendet standardmaessig ProactorEventLoop,
    aber websockets benoetigt SelectorEventLoop fuer einige Operationen.
    Wir setzen WindowsSelectorEventLoopPolicy explizit, da ProactorEventLoop
    Probleme mit einigen asyncio-basierten Libraries verursacht.
    """
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


def _configure_logging() -> None:
    """Konfiguriert das Root-Logging mit dem PRD-konformen Level."""
    log_format = (
        "%(asctime)s.%(msecs)03d | %(levelname)-8s | "
        "%(name)-30s | %(message)s"
    )
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
        format=log_format,
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def _set_random_seeds() -> None:
    """Fixiert Random-Seeds fuer Reproduzierbarkeit (PRD Abschnitt 9.1)."""
    import random

    random.seed(RANDOM_SEED)

    try:
        import numpy as np
        np.random.seed(RANDOM_SEED)
    except ImportError:
        pass

    try:
        import torch
        torch.manual_seed(RANDOM_SEED)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(RANDOM_SEED)
    except ImportError:
        pass


async def _shutdown(loop: asyncio.AbstractEventLoop, sig: signal.Signals) -> None:
    """Graceful Shutdown bei SIGINT/SIGTERM."""
    logger = logging.getLogger("bybit_edge.shutdown")
    logger.info("Signal %s empfangen — fahre herunter...", sig.name)

    tasks = [
        t for t in asyncio.all_tasks(loop)
        if t is not asyncio.current_task()
    ]
    for task in tasks:
        task.cancel()

    results = await asyncio.gather(*tasks, return_exceptions=True)
    for i, result in enumerate(results):
        if isinstance(result, Exception) and not isinstance(result, asyncio.CancelledError):
            logger.error("Task %d warf Fehler beim Shutdown: %s", i, result)

    loop.stop()
    logger.info("Shutdown abgeschlossen. %d Tasks beendet.", len(tasks))


async def main() -> None:
    """Hauptschleife des Bybit Edge Systems.

    Startet den WebSocket-Collector und alle aktiven Layer.
    Wird durch signal handler beendet.
    """
    logger = logging.getLogger("bybit_edge.main")
    logger.info("Bybit Edge System startet...")
    logger.info("Random Seed: %d", RANDOM_SEED)
    logger.info("Log Level: %s", LOG_LEVEL)

    # Placeholder fuer den vollstaendigen Pipeline-Start.
    # Wird durch den Infra-Builder (Agent 02) mit dem echten
    # Collector + State + Layer-Stack ersetzt.
    logger.info("System bereit. Warte auf Pipeline-Komponenten...")

    # Endlos-Loop bis Signal
    try:
        while True:
            await asyncio.sleep(1.0)
    except asyncio.CancelledError:
        logger.info("Main-Loop cancelled — beende.")


def run() -> NoReturn:
    """Synchroner Entry-Point: konfiguriert alles und startet die Event-Loop."""
    _configure_windows_asyncio()
    _configure_logging()
    _set_random_seeds()

    logger = logging.getLogger("bybit_edge")
    logger.info("Python %s auf %s", sys.version, sys.platform)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # Signal-Handler registrieren (nicht auf Windows moeglich fuer SIGTERM)
    if sys.platform != "win32":
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(
                sig,
                lambda s=sig: asyncio.ensure_future(_shutdown(loop, s)),
            )

    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt — beende.")
    finally:
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()
        logger.info("Event-Loop geschlossen.")

    sys.exit(0)


if __name__ == "__main__":
    run()
