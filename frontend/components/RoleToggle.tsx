"use client";

import { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { getRole, setRole, type Role } from "@/lib/roleStore";

const OPTIONS: { value: Role; label: string }[] = [
  { value: "buyer", label: "Buyer" },
  { value: "organiser", label: "Organiser" },
];

/**
 * One toggle, two sides. It writes the role and, when you are not already on the demo,
 * takes you there, because a toggle that changes nothing on screen is a lie about state.
 */
export function RoleToggle() {
  const pathname = usePathname();
  const router = useRouter();
  const [role, setLocalRole] = useState<Role>("buyer");

  useEffect(() => {
    setLocalRole(getRole());
  }, []);

  function choose(value: Role) {
    setLocalRole(value);
    setRole(value);
    if (pathname !== "/demo") router.push("/demo");
  }

  return (
    <div
      role="group"
      aria-label="View as"
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
            className={`u-transition rounded-pill px-3 py-1 t-meta ${
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
