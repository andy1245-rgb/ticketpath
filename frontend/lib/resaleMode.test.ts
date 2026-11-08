import assert from "node:assert/strict";
import { test } from "node:test";

import { RESALE_MODE_LABEL, RESALE_MODE_ORDER, resaleModeOf } from "./resaleMode.ts";

test("every resale mode in the record has one label, in one spelling", () => {
  assert.deepEqual(RESALE_MODE_ORDER, ["open", "monitored", "banned"]);
  for (const mode of RESALE_MODE_ORDER) {
    const label = RESALE_MODE_LABEL[mode];
    assert.ok(label.length > 0);
    // Title case throughout: no shouting, no lowercase leak of the wire value.
    assert.equal(label, label[0].toUpperCase() + label.slice(1).toLowerCase());
    assert.notEqual(label.toLowerCase(), label);
  }
});

test("the label map covers the record's modes and nothing else", () => {
  assert.deepEqual(Object.keys(RESALE_MODE_LABEL).sort(), ["banned", "monitored", "open"]);
});

test("the API's two booleans map onto the three modes without inventing one", () => {
  assert.equal(resaleModeOf(true), "open");
  assert.equal(resaleModeOf(false), "banned");
});
