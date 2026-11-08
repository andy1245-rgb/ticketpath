"""Hard budgets for a run: per agent and for the total, lamports and actions.

Money is an integer number of lamports. There is no float in this module and there must
never be one: a float would make "spent" and "remaining" disagree at the lamport, and a
budget that disagrees with itself is not a budget.

The three rules this module keeps:

- A check never mutates. `check` either passes or raises, leaving the tracker exactly as
  it was, so an intent that is refused leaves no trace in the budget.
- A charge that would exceed leaves the tracker untouched. `charge` checks first, then
  mutates, then returns an immutable snapshot. An over-charge therefore changes nothing
  and the caller can go on to record the refusal with a truthful before/after balance.
- A frozen agent cannot be charged. `freeze` is the kill switch at agent scope and it is
  idempotent: the first reason is the recorded reason, later calls do not rewrite it.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from .config import AgentSpec


class BudgetExceeded(RuntimeError):
    """A spend that a budget refuses, naming which budget and the numbers.

    `kind` is one of "agent_lamports", "agent_actions", "total_lamports",
    "total_actions", "agent_frozen", so a caller can branch on the refusal without
    parsing the message.
    """

    def __init__(self, kind: str, agent_id: str, requested: int, spent: int, limit: int) -> None:
        self.kind = kind
        self.agent_id = agent_id
        self.requested = requested
        self.spent = spent
        self.limit = limit
        super().__init__(
            f"{kind}: agent {agent_id} requested {requested}, spent {spent}, limit {limit}"
        )


@dataclass(frozen=True)
class AgentBudgetState:
    """One agent's immutable budget position."""

    agent_id: str
    spent_lamports: int
    limit_lamports: int
    actions: int
    limit_actions: int
    frozen: bool
    freeze_reason: str | None

    @property
    def remaining_lamports(self) -> int:
        return self.limit_lamports - self.spent_lamports

    @property
    def remaining_actions(self) -> int:
        return self.limit_actions - self.actions


@dataclass(frozen=True)
class BudgetState:
    """An immutable snapshot of every agent plus the run totals."""

    agents: tuple[AgentBudgetState, ...]
    total_spent_lamports: int
    total_limit_lamports: int
    total_actions: int
    total_limit_actions: int

    @property
    def total_remaining_lamports(self) -> int:
        return self.total_limit_lamports - self.total_spent_lamports

    @property
    def total_remaining_actions(self) -> int:
        return self.total_limit_actions - self.total_actions


class BudgetTracker:
    """Tracks what each agent and the run as a whole have spent.

    Every `charge` is one action and some lamports. `check` asks whether one more charge
    of that size would be admitted, so it tests the lamport headroom and the action
    headroom together. A charge of zero lamports is still an action and is counted.
    """

    def __init__(self, agents: Sequence[AgentSpec], total_lamports: int, total_actions: int) -> None:
        if isinstance(total_lamports, bool) or not isinstance(total_lamports, int):
            raise TypeError("total_lamports: expected an integer number of lamports")
        if isinstance(total_actions, bool) or not isinstance(total_actions, int):
            raise TypeError("total_actions: expected an integer")
        if total_lamports < 0:
            raise ValueError(f"total_lamports: must not be negative, got {total_lamports}")
        if total_actions < 0:
            raise ValueError(f"total_actions: must not be negative, got {total_actions}")

        self._agents: dict[str, dict] = {}
        for spec in agents:
            if spec.agent_id in self._agents:
                raise ValueError(f"agents: duplicate agent_id {spec.agent_id!r}")
            self._agents[spec.agent_id] = {
                "spent_lamports": 0,
                "limit_lamports": spec.budget_lamports,
                "actions": 0,
                "limit_actions": spec.budget_actions,
                "frozen": False,
                "freeze_reason": None,
            }
        self._total_lamports = total_lamports
        self._total_actions = total_actions
        self._total_spent_lamports = 0
        self._total_actions_used = 0

    def _entry(self, agent_id: str) -> dict:
        try:
            return self._agents[agent_id]
        except KeyError:
            raise KeyError(f"unknown agent_id {agent_id!r}") from None

    def check(self, agent_id: str, lamports: int) -> None:
        """Raise `BudgetExceeded` if one more charge of `lamports` is not allowed.

        Never mutates: the tracker is identical before and after a passing or a failing
        check. The four budgets are tested in a fixed order (frozen, agent lamports,
        agent actions, total lamports, total actions) so the first refusal is the one
        the operator sees and the message is reproducible.
        """
        entry = self._entry(agent_id)
        if isinstance(lamports, bool) or not isinstance(lamports, int):
            raise TypeError(f"lamports: expected an integer, got {type(lamports).__name__}")
        if lamports < 0:
            raise ValueError(f"lamports: must not be negative, got {lamports}")

        if entry["frozen"]:
            raise BudgetExceeded(
                "agent_frozen", agent_id, lamports, entry["spent_lamports"],
                entry["limit_lamports"],
            )
        if entry["spent_lamports"] + lamports > entry["limit_lamports"]:
            raise BudgetExceeded(
                "agent_lamports", agent_id, lamports, entry["spent_lamports"],
                entry["limit_lamports"],
            )
        if entry["actions"] + 1 > entry["limit_actions"]:
            raise BudgetExceeded(
                "agent_actions", agent_id, lamports, entry["actions"],
                entry["limit_actions"],
            )
        if self._total_spent_lamports + lamports > self._total_lamports:
            raise BudgetExceeded(
                "total_lamports", agent_id, lamports, self._total_spent_lamports,
                self._total_lamports,
            )
        if self._total_actions_used + 1 > self._total_actions:
            raise BudgetExceeded(
                "total_actions", agent_id, lamports, self._total_actions_used,
                self._total_actions,
            )

    def charge(self, agent_id: str, lamports: int) -> BudgetState:
        """Check, then charge one action for `lamports`, then return a snapshot.

        If the check raises, nothing has been mutated: the charge is all-or-nothing.
        """
        self.check(agent_id, lamports)
        entry = self._entry(agent_id)
        entry["spent_lamports"] += lamports
        entry["actions"] += 1
        self._total_spent_lamports += lamports
        self._total_actions_used += 1
        return self.state()

    def freeze(self, agent_id: str, reason: str) -> None:
        """Freeze an agent so no further charge is admitted. Idempotent.

        The first reason is kept; a later freeze does not rewrite the history of why the
        agent stopped. An unknown agent raises `KeyError`.
        """
        entry = self._entry(agent_id)
        if not isinstance(reason, str) or not reason.strip():
            raise ValueError("reason: a non-empty string is required")
        if entry["frozen"]:
            return
        entry["frozen"] = True
        entry["freeze_reason"] = reason

    def is_frozen(self, agent_id: str) -> bool:
        """Whether the agent is frozen. An unknown agent raises `KeyError`."""
        return bool(self._entry(agent_id)["frozen"])

    def state(self) -> BudgetState:
        """The immutable snapshot `charge` returns, in agent-id input order."""
        agents = tuple(
            AgentBudgetState(
                agent_id=agent_id,
                spent_lamports=entry["spent_lamports"],
                limit_lamports=entry["limit_lamports"],
                actions=entry["actions"],
                limit_actions=entry["limit_actions"],
                frozen=entry["frozen"],
                freeze_reason=entry["freeze_reason"],
            )
            for agent_id, entry in self._agents.items()
        )
        return BudgetState(
            agents=agents,
            total_spent_lamports=self._total_spent_lamports,
            total_limit_lamports=self._total_lamports,
            total_actions=self._total_actions_used,
            total_limit_actions=self._total_actions,
        )

    def snapshot(self) -> dict:
        """A plain dict of plain values, JSON-serialisable, in agent-id input order."""
        agents = [
            {
                "agent_id": agent_id,
                "spent_lamports": entry["spent_lamports"],
                "limit_lamports": entry["limit_lamports"],
                "remaining_lamports": entry["limit_lamports"] - entry["spent_lamports"],
                "actions": entry["actions"],
                "limit_actions": entry["limit_actions"],
                "remaining_actions": entry["limit_actions"] - entry["actions"],
                "frozen": entry["frozen"],
                "freeze_reason": entry["freeze_reason"],
            }
            for agent_id, entry in self._agents.items()
        ]
        return {
            "agents": agents,
            "total": {
                "spent_lamports": self._total_spent_lamports,
                "limit_lamports": self._total_lamports,
                "remaining_lamports": self._total_lamports - self._total_spent_lamports,
                "actions": self._total_actions_used,
                "limit_actions": self._total_actions,
                "remaining_actions": self._total_actions - self._total_actions_used,
            },
        }
