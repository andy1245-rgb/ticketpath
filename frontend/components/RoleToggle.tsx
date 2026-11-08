"use client";

import { useEffect, useState } from "react";
import { getRole, setRole, type Role } from "@/lib/roleStore";

// The stored value stays `organiser` because it is the key in an existing
// localStorage entry; only the label a reader sees is spelled one way with
// `/organizer`, the header and the footer.
const OPTIONS: { value: Role; label: string }[] = [
  { value: "buyer", label: "Buyer" },
  { value: "organiser", label: "Organizer" },
];

/**
 * One toggle, two sides, and it lives on `/demo` only, which is the one place
 * that reads the stored role.
 *
 * It used to sit in the header on every route and push `/demo` when clicked: on
 * `/rules` or `/events` it navigated away and changed nothing else, and a
 * `role="group"` moving a screen-reader user to a new page is a state change
 * with no announcement. The navigation is now the navigation, and this control
 * only writes what the page underneath re-renders against.
 */
export function RoleToggle() {
  const [role, setLocalRole] = useState<Role>("buyer");

  useEffect(() => {
    setLocalRole(getRole());
  }, []);

  function choose(value: Role) {
    setLocalRole(value);
    setRole(value);
  }

  return (
    <div
      role="group"
      aria-label="Demo view as"
      className="inline-flex items-center rounded-pill border border-line bg-surface-2 p-1"
    >
      {OPTIONS.map((option) => {
        const active = role === option.value;
        return (
          <button
            key={option.value}
            type="button"
            onClick={() => choose(option.value)}
            aria-pressed={active}
            className={`u-transition inline-flex min-h-9 items-center rounded-pill px-3 py-2 t-meta ${
              active ? "bg-ink text-on-accent" : "text-muted hover:text-ink"
            }`}
          >
            {option.label}
          </button>
        );
      })}
    </div>
  );
}
