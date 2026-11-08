import assert from "node:assert/strict";
import { createServer } from "node:http";
import type { AddressInfo } from "node:net";
import { test } from "node:test";

import { ApiError, buildQuery, mapErrorBody, paginate, requestJson } from "./http.ts";

test("buildQuery keeps the given order and drops unset values", () => {
  assert.equal(buildQuery({}), "");
  assert.equal(
    buildQuery({ status: undefined, city: null, q: "" }),
    "",
    "undefined, null and empty must not become a filter for the empty string",
  );
  assert.equal(
    buildQuery({ status: "on_sale", city: "St. Louis, MO", limit: 25 }),
    "?status=on_sale&city=St.+Louis%2C+MO&limit=25",
  );
  // Order is the caller's, not alphabetical, so the same call is the same URL.
  assert.equal(buildQuery({ b: 2, a: 1 }), "?b=2&a=1");
  assert.equal(buildQuery({ cursor: "0" }), "?cursor=0", "a string zero is a cursor, not unset");
});

test("mapErrorBody reads message, then error, then the status line", () => {
  const full = mapErrorBody(
    { message: "event nope not found", status: 404, code: "not_found" },
    404,
    "/api/events/nope",
  );
  assert.ok(full instanceof ApiError);
  assert.ok(full instanceof Error);
  assert.equal(full.name, "ApiError");
  assert.equal(full.message, "event nope not found");
  assert.equal(full.status, 404);
  assert.equal(full.code, "not_found");
  assert.equal(full.path, "/api/events/nope");

  const fallback = mapErrorBody({ error: "bad gateway" }, 502, "/health");
  assert.equal(fallback.message, "bad gateway");
  assert.equal(fallback.code, "http_error", "no code in the body means the generic one");

  const bare = mapErrorBody("<html>oops</html>", 500, "/api/events");
  assert.equal(bare.message, "HTTP 500");
  assert.equal(bare.code, "http_error");

  const emptyish = mapErrorBody({ message: "", code: "" }, 400, "/api/tickets");
  assert.equal(emptyish.message, "HTTP 400", "an empty message is no message");
  assert.equal(emptyish.code, "http_error");
});

test("paginate walks the cursor and stops", () => {
  const items = ["a", "b", "c", "d", "e"];

  const first = paginate(items, undefined, 2);
  assert.deepEqual(first.items, ["a", "b"]);
  assert.equal(first.nextCursor, "2");

  const second = paginate(items, "2", 2);
  assert.deepEqual(second.items, ["c", "d"]);
  assert.equal(second.nextCursor, "4");

  const last = paginate(items, "4", 2);
  assert.deepEqual(last.items, ["e"]);
  assert.equal(last.nextCursor, null);

  const exact = paginate(items, "3", 2);
  assert.deepEqual(exact.items, ["d", "e"]);
  assert.equal(exact.nextCursor, null, "a page that ends on the last item has no next cursor");

  const invalid = paginate(items, "not-a-cursor", 2);
  assert.deepEqual(invalid.items, ["a", "b"], "an unreadable cursor starts at the top");
  assert.equal(paginate(items, "-4", 2).nextCursor, "2", "a negative offset is not a cursor");
  assert.deepEqual(paginate(items, "9", 2).items, []);
  assert.equal(paginate([], undefined, 10).nextCursor, null);
});

test("requestJson returns the body and maps a failed response", async () => {
  const server = createServer((req, res) => {
    if (req.url === "/ok") {
      res.writeHead(200, { "content-type": "application/json" });
      res.end(JSON.stringify({ hello: "world" }));
      return;
    }
    if (req.url === "/slow") return; // never answers, so the timeout has to fire
    res.writeHead(404, { "content-type": "application/json" });
    res.end(JSON.stringify({ message: "event nope not found", status: 404, code: "not_found" }));
  });

  await new Promise<void>((resolve) => server.listen(0, "127.0.0.1", resolve));
  const { port } = server.address() as AddressInfo;
  const base = `http://127.0.0.1:${port}`;

  try {
    assert.deepEqual(await requestJson<{ hello: string }>(base, "/ok"), { hello: "world" });

    const failure = await requestJson(base, "/api/events/nope").then(
      () => null,
      (error: unknown) => error,
    );
    assert.ok(failure instanceof ApiError);
    assert.equal(failure.status, 404);
    assert.equal(failure.code, "not_found");
    assert.equal(failure.message, "event nope not found");
    assert.equal(failure.path, "/api/events/nope");

    const timeout = await requestJson(base, "/slow", {}, 50).then(
      () => null,
      (error: unknown) => error,
    );
    assert.ok(timeout instanceof ApiError);
    assert.equal(timeout.status, 504);
    assert.equal(timeout.code, "timeout");
    assert.equal(timeout.path, "/slow");
  } finally {
    server.closeAllConnections();
    await new Promise<void>((resolve) => server.close(() => resolve()));
  }
});
