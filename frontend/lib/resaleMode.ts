/**
 * One spelling of the three resale modes, and one order to list them in.
 *
 * The same field used to render as `banned` on the buyer side, "BANNED" on the
 * organiser side and "Monitored" in a note, so a reader had three spellings of
 * one state on one screen. Any view that prints a resale mode imports this map.
 */

import type { ResaleMode } from "./demoState";

export const RESALE_MODE_ORDER: readonly ResaleMode[] = ["open", "monitored", "banned"];

export const RESALE_MODE_LABEL: Readonly<Record<ResaleMode, string>> = {
  open: "Open",
  monitored: "Monitored",
  banned: "Banned",
};

/** The mode an event record carries, from the booleans the API does serve. */
export function resaleModeOf(resaleEnabled: boolean): ResaleMode {
  return resaleEnabled ? "open" : "banned";
}
