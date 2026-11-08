/**
 * DEMO VALUES, NO BACKEND SOURCE
 *
 * The only numbers in the product that are not read from the backend. The
 * brief allows exactly one module for them, one named export per value, and
 * requires the proof band to carry a "Demo figures" note whenever any of them
 * is on screen.
 *
 * Nothing may import these except the landing proof band. If an endpoint ever
 * answers one of them, delete the export rather than keep the demo value alive
 * beside the real one.
 */

/** Resales a cap would have blocked. Nothing blocks anything yet: zero listings. */
export const RESALES_BLOCKED_AT_CAP = 3;

/** Fees a checkout would have added. There is no checkout and no fee field. */
export const HIDDEN_FEES = 0;

/** Lets a surface say "Demo figures" without sniffing which values it used. */
export const HAS_DEMO_FIGURES = true;
