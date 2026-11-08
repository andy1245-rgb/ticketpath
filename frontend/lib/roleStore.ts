/**
 * Which side of the product you are looking at. One value, two readers: the header
 * toggle writes it and the demo page renders from it. A static export has no server
 * session, so it is a `localStorage` key plus a DOM event, and nothing else.
 */

export type Role = "buyer" | "organiser";

export const ROLE_KEY = "seatpass.role.v1";
export const ROLE_EVENT = "seatpass:role";

export function getRole(): Role {
  if (typeof window === "undefined") return "buyer";
  return window.localStorage.getItem(ROLE_KEY) === "organiser" ? "organiser" : "buyer";
}

export function setRole(role: Role): void {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(ROLE_KEY, role);
  window.dispatchEvent(new CustomEvent<Role>(ROLE_EVENT, { detail: role }));
}

export function subscribeRole(handler: (role: Role) => void): () => void {
  const listener = (event: Event) => handler((event as CustomEvent<Role>).detail);
  window.addEventListener(ROLE_EVENT, listener);
  return () => window.removeEventListener(ROLE_EVENT, listener);
}
