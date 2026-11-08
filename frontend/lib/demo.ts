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

/**
 * Resales a cap would have blocked. Deleted: the landing proof band used to
 * print `3` from here while `records/devnet-artefacts.json` holds exactly one
 * refused transfer (`6010 E_CAP_EXCEEDED` at priceLamports 1250000001). The
 * band now counts the artefact's own refusal row, so this value has no reader
 * and no source. A demo constant that contradicts the one record on disk is
 * not a caveat, it is a false figure in display type.
 */

/** Fees a checkout would have added. There is no checkout and no fee field. */
export const HIDDEN_FEES = 0;

/** Lets a surface say "Demo figures" without sniffing which values it used. */
export const HAS_DEMO_FIGURES = true;
