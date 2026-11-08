/**
 * The transport, kept apart from the fixture-backed API module.
 *
 * Nothing here imports JSON and nothing here knows whether the app is reading
 * fixtures or a server, so `node --test` can load this file directly and check
 * the wire behaviour — query strings, error mapping, paging, the timeout —
 * through plain Node, with no bundler and no backend.
 */

import type { Page } from "./types.ts";

/** Long enough for a cold stdlib server, short enough that a dead one is visible. */
const DEFAULT_TIMEOUT_MS = 8000;

/**
 * A failed request, carrying the three things a screen needs: what the backend
 * said, the HTTP status so 404 can become the not-found page, and the machine
 * code so a caller can branch on `nonce_unknown` without matching prose.
 */
export class ApiError extends Error {
  readonly status: number;
  readonly code: string;
  /** The path that failed, without the origin. */
  readonly path: string;

  constructor(message: string, status: number, code: string, path: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.path = path;
  }
}

function asText(value: unknown): string | null {
  return typeof value === "string" && value.trim() !== "" ? value : null;
}

function field(body: unknown, key: string): unknown {
  if (typeof body !== "object" || body === null || !(key in body)) return undefined;
  // The one cast in this file: `in` proved the key is there, and JSON gives us
  // no shape to narrow to.
  return (body as Record<string, unknown>)[key];
}

/**
 * Turn whatever the server sent into an ApiError. The backend answers
 * `{message, status, code}`; a proxy or a panic may answer `{error}`, and a
 * body that is not JSON at all gets the status line and nothing invented.
 */
export function mapErrorBody(body: unknown, status: number, path: string): ApiError {
  const message =
    asText(field(body, "message")) ?? asText(field(body, "error")) ?? `HTTP ${status}`;
  const code = asText(field(body, "code")) ?? "http_error";
  return new ApiError(message, status, code, path);
}

/**
 * Query string from the parameters given, in the order given. Undefined, null
 * and empty mean "do not send this": a `?status=` reads as a filter for the
 * empty string on the server side, which is not what an unset filter means.
 */
export function buildQuery(
  params: Record<string, string | number | undefined | null>,
): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === null || value === "") continue;
    search.set(key, String(value));
  }
  const encoded = search.toString();
  return encoded ? `?${encoded}` : "";
}

/** A decimal offset, or 0 for anything that is not one. */
function cursorOffset(cursor: string | undefined): number {
  if (cursor === undefined || cursor === "") return 0;
  const value = Number(cursor);
  return Number.isInteger(value) && value >= 0 ? value : 0;
}

/**
 * Offset paging over an already-filtered, already-sorted array. The cursor is
 * the decimal offset itself so the fixtures and the server agree without a
 * mapping table; `nextCursor` is null only when nothing is left.
 */
export function paginate<T>(items: T[], cursor: string | undefined, limit: number): Page<T> {
  const start = cursorOffset(cursor);
  const size = Number.isFinite(limit) && limit > 0 ? Math.floor(limit) : 0;
  const end = start + size;
  const page: Page<T> = {
    items: items.slice(start, end),
    nextCursor: size > 0 && end < items.length ? String(end) : null,
  };
  return page;
}

function isAbort(error: unknown): boolean {
  // Node rejects a timed-out fetch with a DOMException named TimeoutError, and
  // an abandoned one with AbortError; neither is an Error instance everywhere.
  const name = field(error, "name");
  return name === "TimeoutError" || name === "AbortError";
}

/**
 * One request, one typed body. `cache: "no-store"` because every payload here is
 * a live figure, and a timeout because a hung socket must surface as a message
 * on the page rather than a spinner that never resolves.
 */
export async function requestJson<T>(
  baseUrl: string,
  path: string,
  init: RequestInit = {},
  timeoutMs: number = DEFAULT_TIMEOUT_MS,
): Promise<T> {
  const timeout = AbortSignal.timeout(timeoutMs);
  const signal = init.signal ? AbortSignal.any([init.signal, timeout]) : timeout;

  const headers = new Headers(init.headers);
  if (!headers.has("content-type")) headers.set("content-type", "application/json");

  let response: Response;
  try {
    response = await fetch(`${baseUrl}${path}`, {
      ...init,
      headers,
      cache: "no-store",
      signal,
    });
  } catch (error) {
    if (isAbort(error)) {
      const seconds = Math.round(timeoutMs / 1000);
      throw new ApiError(
        `The backend did not answer within ${seconds} seconds`,
        504,
        "timeout",
        path,
      );
    }
    throw error;
  }

  // Read the body before deciding: every error the backend sends carries a
  // message, and a success with no body is not one of our endpoints.
  const text = await response.text();
  let body: unknown = null;
  if (text !== "") {
    try {
      body = JSON.parse(text) as unknown;
    } catch {
      body = null;
    }
  }

  if (!response.ok) throw mapErrorBody(body, response.status, path);
  return body as T;
}
