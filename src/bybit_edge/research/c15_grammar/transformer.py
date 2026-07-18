"""Decoder-only causal transformer for the H-15 trade-tape grammar gate.

Registry H-15 (pre-fixed): "Decoder-only Causal-Transformer (~2-4M Parameter,
Kontext 1024 Token), Next-Token-Cross-Entropy, je Symbol trainiert."

Pre-fixed default architecture (documented here, NOT tuned on test folds —
registry Selbstkill: hyper-parameters fixed BEFORE the run):
    d_model=256, n_heads=4, n_layers=4, ffn=4*d_model, dropout=0.1,
    learned positional embedding over 1024 positions, separate LM head.
    => ~3.5M trainable parameters (inside the registered 2-4M band).
Training (pre-fixed defaults): AdamW lr=3e-4, cosine schedule, grad-clip 1.0,
batch 32 non-overlapping (context+1)-chunks, epochs=3, per-seed shuffling.

Torch-optional IMPORT GUARD (structurally identical to ``m18_patchtst.py``:
``try: import torch ... except: _TORCH_AVAILABLE = False``, module stays
importable without torch). The FALLBACK BEHAVIOUR beyond the import guard
differs deliberately: ``m18_patchtst.fit()`` without torch returns a
degraded-but-defined result (a documented no-op); every train/eval entry
point here instead raises ``ComputeUnavailableError`` with an honest
message. For a verdict-bearing gate this is the stricter of the two choices
(fail-loud, never fabricates numbers) — appropriate here, not a weaker
imitation of the m18 pattern. ``torch_cuda_status()`` reports availability
without side effects (used by the CLI ``--check-gpu-only`` compute gate).

COMPUTE GATE (binding): a verdict-bearing H-15 run REQUIRES a real CUDA
device (registry "Rechenaufwand: GPU, zwingend"). This module trains on
whatever device it is given; the DRIVER enforces that gate (``gate_valid`` /
``ran_on_gpu`` flags, CPU only in the explicitly marked mechanics mode).

Cross-entropy convention: identical to ``markov_baseline`` — mean negative
NATURAL log-likelihood per token (nats) over positions ``t >= CE_WARMUP`` of
the standalone stream. Causality: within each evaluation chunk position t is
predicted from chunk positions < t only (causal mask); chunks are
non-overlapping and never cross fold boundaries.

KAPITALFREI: pure sequence modelling. No capital metric anywhere.
"""
from __future__ import annotations

import logging
import math
from dataclasses import dataclass
from typing import Any

import numpy as np

from .markov_baseline import CE_WARMUP

_LOG = logging.getLogger(__name__)

try:  # PyTorch optional (m18_patchtst.py pattern)
    import torch
    import torch.nn as nn

    _TORCH_AVAILABLE = True
except Exception:  # pragma: no cover - sandbox has no torch
    torch = None  # type: ignore[assignment]
    nn = None  # type: ignore[assignment]
    _TORCH_AVAILABLE = False


class ComputeUnavailableError(RuntimeError):
    """Raised when torch (or a required CUDA device) is not available."""


@dataclass(frozen=True)
class GrammarTransformerConfig:
    """Pre-fixed architecture/training config (registry H-15 band 2-4M params)."""

    vocab_size: int = 128
    context_len: int = 1024
    d_model: int = 256
    n_heads: int = 4
    n_layers: int = 4
    dropout: float = 0.1
    lr: float = 3e-4
    batch_size: int = 32
    epochs: int = 3
    grad_clip: float = 1.0


def torch_cuda_status() -> dict[str, Any]:
    """Honest torch/CUDA availability report (no run, no side effects)."""
    status: dict[str, Any] = {
        "torch_available": bool(_TORCH_AVAILABLE),
        "torch_version": None,
        "cuda_available": False,
        "cuda_device_count": 0,
        "cuda_device_name": None,
    }
    if _TORCH_AVAILABLE:
        status["torch_version"] = str(torch.__version__)
        try:
            status["cuda_available"] = bool(torch.cuda.is_available())
            if status["cuda_available"]:
                status["cuda_device_count"] = int(torch.cuda.device_count())
                status["cuda_device_name"] = str(torch.cuda.get_device_name(0))
        except Exception as exc:  # pragma: no cover - defensive
            status["cuda_probe_error"] = str(exc)
    return status


def _require_torch() -> None:
    if not _TORCH_AVAILABLE:
        raise ComputeUnavailableError(
            "torch is not installed — the H-15 transformer arm cannot run. "
            "This sandbox/degraded environment can only exercise pipeline "
            "mechanics (tokenizer, folds, Markov baseline, surrogates)."
        )


if _TORCH_AVAILABLE:

    class GrammarTransformer(nn.Module):
        """Decoder-only causal LM: token emb + learned pos emb + causal encoder."""

        def __init__(self, cfg: GrammarTransformerConfig) -> None:
            super().__init__()
            self.cfg = cfg
            self.tok_emb = nn.Embedding(cfg.vocab_size, cfg.d_model)
            self.pos_emb = nn.Parameter(torch.zeros(1, cfg.context_len, cfg.d_model))
            nn.init.trunc_normal_(self.pos_emb, std=0.02)
            layer = nn.TransformerEncoderLayer(
                d_model=cfg.d_model,
                nhead=cfg.n_heads,
                dim_feedforward=cfg.d_model * 4,
                dropout=cfg.dropout,
                batch_first=True,
                activation="gelu",
                norm_first=True,
            )
            self.encoder = nn.TransformerEncoder(layer, num_layers=cfg.n_layers)
            self.ln_f = nn.LayerNorm(cfg.d_model)
            self.head = nn.Linear(cfg.d_model, cfg.vocab_size)

        def forward(self, x: "torch.Tensor") -> "torch.Tensor":
            # x: (B, L) int64, L <= context_len -> logits (B, L, V)
            b, length = x.shape
            h = self.tok_emb(x) + self.pos_emb[:, :length, :]
            mask = torch.triu(
                torch.full((length, length), float("-inf"), device=x.device),
                diagonal=1,
            )
            h = self.encoder(h, mask=mask, is_causal=True)
            return self.head(self.ln_f(h))


def release_device_memory(device: str) -> None:
    """Best-effort release of torch's cached CUDA allocator memory.

    Called by the driver after a fold's seed models have been dropped so
    the ~200-surrogate evaluation of the NEXT fold does not sit on top of
    stale cached GPU blocks (and their host-side bookkeeping). Safe no-op
    without torch, without CUDA, or on CPU devices — never raises.
    """
    if not _TORCH_AVAILABLE:
        return
    try:
        if str(device).startswith("cuda") and torch.cuda.is_available():
            torch.cuda.empty_cache()
    except Exception:  # pragma: no cover - defensive
        pass


def num_parameters(model: Any) -> int:
    """Trainable parameter count (0 without torch)."""
    if not _TORCH_AVAILABLE or model is None:
        return 0
    return int(sum(p.numel() for p in model.parameters() if p.requires_grad))


def _chunk_stream(tokens: np.ndarray, chunk_len: int) -> np.ndarray:
    """Non-overlapping (chunk_len)-windows over a token stream (2-D int).

    Chunks of length ``chunk_len`` with stride ``chunk_len - 1`` so every
    position (except the very first of each chunk) is a prediction target
    exactly once; the trailing remainder shorter than 2 is dropped.

    Dtype: keeps a SIGNED integer input dtype (int16 storage for vocab
    <= 256 — the -1 padding needs a signed type); anything else is held as
    int64 as before. Token VALUES are unchanged either way; the torch side
    casts to ``torch.long`` per batch.
    """
    dtype = tokens.dtype if tokens.dtype.kind == "i" else np.int64
    n = tokens.size
    stride = chunk_len - 1
    if n < 2:
        return np.zeros((0, chunk_len), dtype=dtype)
    starts = list(range(0, max(1, n - 1), stride))
    rows = []
    for s in starts:
        chunk = tokens[s: s + chunk_len]
        if chunk.size < 2:
            continue
        rows.append(chunk)
    if not rows:
        return np.zeros((0, chunk_len), dtype=dtype)
    width = max(r.size for r in rows)
    out = np.full((len(rows), width), -1, dtype=dtype)
    for i, r in enumerate(rows):
        out[i, : r.size] = r
    return out


def train_transformer(
    train_tokens: np.ndarray,
    cfg: GrammarTransformerConfig,
    *,
    seed: int,
    device: str,
    verbose: bool = False,
) -> Any:
    """Train one grammar transformer on ONE train fold; returns the model.

    Next-token cross-entropy over non-overlapping (context_len+1)-chunks,
    AdamW + cosine schedule, per-epoch shuffling seeded by ``seed`` (the
    registered 3-seeds-per-fold discipline is driven by the caller).
    Raises ``ComputeUnavailableError`` without torch.
    """
    _require_torch()
    tokens = np.asarray(train_tokens)
    if tokens.dtype.kind != "i":
        tokens = tokens.astype(np.int64)
    if tokens.size < cfg.context_len + 1:
        # short streams still trainable (single shorter chunk) — honest
        # degradation, flagged by the caller through n_train_tokens.
        _LOG.warning("train stream (%d) shorter than context+1 (%d)",
                     tokens.size, cfg.context_len + 1)
    chunks = _chunk_stream(tokens, cfg.context_len + 1)
    if chunks.shape[0] == 0:
        raise ComputeUnavailableError("train stream too short to form one chunk")

    torch.manual_seed(seed)
    model = GrammarTransformer(cfg).to(device)
    optim = torch.optim.AdamW(model.parameters(), lr=cfg.lr)
    n_batches = max(1, math.ceil(chunks.shape[0] / cfg.batch_size))
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(
        optim, T_max=max(1, cfg.epochs * n_batches),
    )
    loss_fn = nn.CrossEntropyLoss(ignore_index=-1)
    rng = np.random.default_rng(seed)

    model.train()
    for ep in range(cfg.epochs):
        order = rng.permutation(chunks.shape[0])
        ep_losses: list[float] = []
        for b0 in range(0, chunks.shape[0], cfg.batch_size):
            idx = order[b0: b0 + cfg.batch_size]
            # explicit long cast: chunks may be stored int16 (values exact)
            batch = torch.from_numpy(chunks[idx]).to(device=device, dtype=torch.long)
            inp = batch[:, :-1].clamp_min(0)  # -1 padding -> token 0 input
            tgt = batch[:, 1:]                # -1 padding ignored by loss
            optim.zero_grad()
            logits = model(inp)
            loss = loss_fn(logits.reshape(-1, cfg.vocab_size), tgt.reshape(-1))
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), cfg.grad_clip)
            optim.step()
            sched.step()
            ep_losses.append(float(loss.item()))
        if verbose:
            _LOG.info("c15 transformer seed=%d ep=%d ce=%.4f",
                      seed, ep, float(np.mean(ep_losses)))
    return model


def evaluate_ce(
    model: Any,
    tokens: np.ndarray,
    cfg: GrammarTransformerConfig,
    *,
    device: str,
    eval_batch_size: int = 64,
) -> float:
    """Mean next-token CE (nats) over positions ``>= CE_WARMUP`` of ``tokens``.

    Same evaluation support as the Markov baselines (``CE_WARMUP``), so the
    CE gap compares like with like. Chunks never cross the stream boundary;
    within a chunk the causal mask guarantees position t sees only < t.
    """
    _require_torch()
    tokens = np.asarray(tokens)
    if tokens.dtype.kind != "i":
        tokens = tokens.astype(np.int64)
    n = tokens.size
    if n <= CE_WARMUP:
        return float("nan")
    chunks = _chunk_stream(tokens, cfg.context_len + 1)
    if chunks.shape[0] == 0:
        return float("nan")
    stride = cfg.context_len  # chunk s starts at global position s*stride

    model.eval()
    total_nll = 0.0
    total_cnt = 0
    with torch.no_grad():
        for b0 in range(0, chunks.shape[0], eval_batch_size):
            batch_np = chunks[b0: b0 + eval_batch_size]
            # explicit long cast: chunks may be stored int16 (values exact)
            batch = torch.from_numpy(batch_np).to(device=device, dtype=torch.long)
            inp = batch[:, :-1].clamp_min(0)
            tgt = batch[:, 1:]
            logits = model(inp)
            logp = torch.log_softmax(logits, dim=-1)
            safe_tgt = tgt.clamp_min(0)
            nll = -logp.gather(-1, safe_tgt.unsqueeze(-1)).squeeze(-1)  # (B, L)
            valid = tgt >= 0
            # global position of target column j in chunk i: i*stride + j + 1
            rows = torch.arange(b0, b0 + batch.shape[0], device=device)
            gpos = rows.unsqueeze(1) * stride + torch.arange(
                1, batch.shape[1], device=device
            ).unsqueeze(0)
            keep = valid & (gpos >= CE_WARMUP)
            total_nll += float(nll[keep].sum().item())
            total_cnt += int(keep.sum().item())
    if total_cnt == 0:
        return float("nan")
    return total_nll / total_cnt


__all__ = [
    "ComputeUnavailableError",
    "GrammarTransformerConfig",
    "evaluate_ce",
    "num_parameters",
    "release_device_memory",
    "torch_cuda_status",
    "train_transformer",
    "_TORCH_AVAILABLE",
]
