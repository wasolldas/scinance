"""Shared helpers and guards for the H-27 derivation (result blindness, KONTAMINATION.md 5).

Guards (loud fail, C.14):
  * ``RV_LAST_PRICE_DAY`` -- no realized volatility on days >= 2024-06-01: price series are
    truncated before any return is formed (``truncate_prices``).
  * ``DVOL_LEVEL_LAST_DAY`` -- no DVOL level statistic on days >= 2024-07-01 (``dvol_levels``
    refuses later days; coverage helpers never return values).
  * ``no_mean`` -- refuses output keys that would carry the mean of the premium (any unit) or a
    DVOL level mean of the pre-period.
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RV_LAST_PRICE_DAY = "2024-05-31"
DVOL_LEVEL_LAST_DAY = "2024-06-30"
NUISANCE_FIRST_IV_DAY = "2021-03-24"
NUISANCE_LAST_IV_DAY = "2024-05-01"     # t + 30 <= 2024-05-31
LABEL = ("Nuisance 2021-03-24..2024-05-31 (IV-Tage bis 2024-05-01, Preise bis 2024-05-31): nur "
         "Streuungs-, Autokorrelations- und Verhaeltnisgroessen; der Mittelwert der Praemie (jede "
         "Einheit) und das DVOL-Mittel der Vorperiode werden weder ausgegeben noch gespeichert.")


def harvest():
    """Configure the harvest client with the session cache and reuse the catalog downloaded
    ONCE by catalog_check.py (no second 280 MB download)."""
    sys.path.insert(0, str(HERE.parent / "harvest_client"))
    import harvest_data as hd
    import polars as pl
    hd.configure(cache_dir=HERE / "hcache")
    local = HERE / "hcache" / "catalog" / "partitions.parquet"
    if not local.exists():
        raise RuntimeError("catalog copy missing -- run catalog_check.py once")
    hd._catalog = pl.read_parquet(local)  # in-process reuse of the single download
    return hd


def truncate_prices(days: list[str], *arrays):
    """Drop every price day after RV_LAST_PRICE_DAY before any return is formed."""
    keep = [i for i, d in enumerate(days) if d <= RV_LAST_PRICE_DAY]
    if not keep:
        raise ValueError("no price day <= RV_LAST_PRICE_DAY")
    out = [[days[i] for i in keep]]
    for a in arrays:
        out.append([a[i] for i in keep])
    return out


def assert_rv_day(day: str) -> None:
    if day > RV_LAST_PRICE_DAY:
        raise RuntimeError(f"result blindness: RV on {day} > {RV_LAST_PRICE_DAY} refused")


def assert_dvol_level_day(day: str) -> None:
    if day > DVOL_LEVEL_LAST_DAY:
        raise RuntimeError(f"result blindness: DVOL level on {day} > {DVOL_LEVEL_LAST_DAY} refused")


_FORBIDDEN = ("mean_prem", "prem_mean", "mean_premium", "premium_mean", "mean_p", "dvol_mean",
              "mean_dvol", "mean_iv", "iv_mean")


def no_mean(d):
    """Recursively refuse keys that would carry a premium mean or a pre-period DVOL mean."""
    if isinstance(d, dict):
        for k, v in d.items():
            kl = str(k).lower()
            if any(f in kl for f in _FORBIDDEN):
                raise RuntimeError(f"result blindness: output key {k!r} refused")
            no_mean(v)
    elif isinstance(d, (list, tuple)):
        for v in d:
            no_mean(v)
    return d
