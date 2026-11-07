"""The seam a pricing model plugs into. The core never imports a model directly.

This module registers nothing on its own. `ticketpath.server.build_orchestrator` registers
the console's engine, which is a rule-based bounded estimator over the recorded resale
trail, not a fitted model, and `/health` carries that in `pricingModel.kind` and
`pricingModel.fitted`. With nothing registered, `estimate` returns `available: false` with
a reason and no number, which is the only honest reply: there is no calibrated model and
no data to calibrate one against.

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
        self._description: dict = {}

    def register(
        self,
        model: Model,
        version: str,
        *,
        kind: str | None = None,
        fitted: bool | None = None,
        note: str | None = None,
    ) -> None:
        """Install a model implementation, and what it honestly is.

        `kind`, `fitted` and `note` are for `/health`. Whatever is registered here is
        described there in these words, so the status block cannot claim more than the
        registered thing is: a rule-based estimator is not a fitted model, and saying
        "registered" alone lets a reader assume otherwise.
        """
        self._model = model
        self._model_version = version
        self._description = {"kind": kind, "fitted": fitted, "note": note}

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
        # Forced after the model returns, whatever it said. The price-specific sale
        # probability is not identified from a transaction ledger, so no model is allowed
        # to hand one up, and a model that tries is not trusted to remove it itself.
        estimate["saleProbability"] = None
        estimate["saleProbabilityReason"] = "not_identified"
        return estimate

    def status(self) -> dict:
        """Status block for /health.

        Available means the seam has something behind it. It never means a model was
        fitted: `kind` and `fitted` say what the registered thing is, and `note` says it
        in one sentence a reader can quote.
        """
        if not self.available:
            return {
                "available": False,
                "modelVersion": None,
                "reason": "no_model_registered",
                "kind": None,
                "fitted": None,
                "note": (
                    "No pricing model is registered. Returning a number here would be an "
                    "invented number."
                ),
            }
        return {
            "available": True,
            "modelVersion": self._model_version,
            "reason": "registered",
            "kind": self._description.get("kind"),
            "fitted": self._description.get("fitted"),
            "note": self._description.get("note"),
        }
