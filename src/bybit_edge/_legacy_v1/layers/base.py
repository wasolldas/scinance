"""
BaseModule — Abstract base class for all Edge pipeline modules.

Every module (M1–M26) inherits from this class and implements at minimum
the ``compute`` method, returning a dict with keys:
    signal (int):      1 = Long, -1 = Short, 0 = Wait/Neutral
    confidence (float): 0.0–1.0
    method_id (str):   e.g. "M22"
    ts (float):        time.time() at computation
"""

from abc import ABC, abstractmethod
from typing import Any


class BaseModule(ABC):
    """Basis-Interface für alle Pipeline-Module."""

    @abstractmethod
    def compute(self, *args, **kwargs) -> dict[str, Any]:
        """Berechne Signal + Metadaten. Muss von jeder Sub-Klasse implementiert werden."""
        ...

    def validate(self) -> bool:
        """Prüft Konfiguration — gibt False zurück wenn nicht einsatzbereit."""
        return True

    def reset(self) -> None:
        """Setzt internen State zurück (für Backtester)."""
        ...
