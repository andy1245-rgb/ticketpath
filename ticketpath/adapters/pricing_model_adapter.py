"""The seam a pricing model plugs into. The core never imports a model directly.

Nothing is registered in this build. `estimate` therefore returns `available:
false` with a reason, and no number, which is the only honest reply: there is no
calibrated model and no data to calibrate one against.

The shapes below are the engine's own product, not the frontend contract's. The
contract carries the recorded price trail and aggregates over it; it has no
endpoint for "what is this worth", "how does that move", "what is the chance it
sells", or "what primary price maximises risk-adjusted value". That gap is
recorded in records/CONTRACT-MAP.md section 5.
"""

from __future__ import annotations

from typing import Callable, Mapping

# A model receives a request dict and returns an estimate dict. The request
# carries at least: ticketId, eventId, tierId, faceValueLamports, asOf (ISO-8601),
# and whatever resale record the caller has. The adapter does not invent features.
Model = Callable[[Mapping], Mapping]

REQUIRED_ESTIMATE_KEYS = (
    "modelVersion",
    "asOf",
    "expectedResaleLamports",
    "saleProbability",
    "recommendedPrimaryLamports",
    "horizonHours",
    "basis",
)


class PricingModelAdapter:
    """Registry of at most one active model, plus the refusal path."""

    def __init__(self) -> None:
        self._model: Model | None = None
        self._model_version: str | None = None

    def register(self, model: Model, version: str) -> None:
        """Install a model implementation. Not called by this build."""
        self._model = model
        self._model_version = version

    @property
    def available(self) -> bool:
        return self._model is not None

    def estimate(self, request: Mapping) -> dict:
        """Dispatch to the registered model, or say plainly that there is none."""
        if self._model is None:
            return {
                "available": False,
                "modelVersion": None,
                "asOf": request.get("asOf"),
                "expectedResaleLamports": None,
                "saleProbability": None,
                "recommendedPrimaryLamports": None,
                "horizonHours": None,
                "basis": "no_model_registered",
                "note": (
                    "No pricing model is registered. This is the seam it plugs into; "
                    "returning a number here would be an invented number."
                ),
            }
        estimate = dict(self._model(request))
        missing = [key for key in REQUIRED_ESTIMATE_KEYS if key not in estimate]
        if missing:
            raise ValueError(f"pricing model returned an estimate missing {missing}")
        estimate["available"] = True
        estimate["modelVersion"] = estimate.get("modelVersion") or self._model_version
        return estimate

    def status(self) -> dict:
        """Status block for /health."""
        return {
            "available": self.available,
            "modelVersion": self._model_version,
            "reason": "no_model_registered" if not self.available else "registered",
        }
