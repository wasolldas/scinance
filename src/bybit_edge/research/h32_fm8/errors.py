"""Loud-fail exceptions of the H-32 driver (C.14).  ``H32Abort`` always means: no hand-over / no verdict / no result."""
from __future__ import annotations


class H32Abort(RuntimeError):
    """Base of every loud abort of the driver."""


class SchemaError(H32Abort, ValueError):
    """The registered YAML (or a template) does not follow the H-32 schema (PP1/P1)."""


class PinError(H32Abort):
    """T5: a registered constant differs from the code constant / the value derived from the loaded panel (PP3/P4)."""


class PanelCutError(H32Abort):
    """DEC-96 E3 / DEC-99 (3): the panel is not cut, or a date beyond the cut was reached."""


class SealError(H32Abort):
    """An outcome week outside the allowed range would be set against a characteristic (PP4/P7), or a sealed file was named."""


class KMinError(H32Abort):
    """PRD 5.3 Kill (2): K_t below the minimum in a judged week."""


class DataFingerprintError(H32Abort):
    """The loaded panel does not match the data fingerprints of the registration (PP2/P3)."""


class PilotLockError(H32Abort):
    """Pilot lock (P0') or exactly-one-pilot lock (PP0'): the pilot result is missing, differs, or an earlier one exists."""


class ArtifactError(H32Abort):
    """DEC-53: a mandatory artifact is missing or does not reproduce the estimators -- NO HAND-OVER / NO VERDICT."""


class NullCalibrationError(H32Abort):
    """The re-computed null constants deviate more than +-10 % from the frozen ones (P6)."""


class PositiveControlAbort(H32Abort):
    """The positive control cannot be run (no handed variant, world cannot reach the target, ...)."""
