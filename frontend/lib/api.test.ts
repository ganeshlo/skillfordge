import { afterEach, describe, expect, it, vi } from "vitest";

import { api, saveAccessToken } from "./api";

afterEach(() => {
  saveAccessToken(null);
  vi.unstubAllGlobals();
});

describe("api authentication headers", () => {
  it("does not attach a stale bearer token to public authentication requests", async () => {
    saveAccessToken("expired-token");
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify({ data: { access: "fresh-token" }, request_id: null }), { status: 200, headers: { "Content-Type": "application/json" } }));
    vi.stubGlobal("fetch", fetchMock);

    await api<{ access: string }>("/auth/token/", { method: "POST", body: "{}" });

    const headers = fetchMock.mock.calls[0][1].headers as Record<string, string>;
    expect(headers.Authorization).toBeUndefined();
  });

  it("continues attaching the token to protected API requests", async () => {
    saveAccessToken("valid-token");
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify({ data: {}, request_id: null }), { status: 200, headers: { "Content-Type": "application/json" } }));
    vi.stubGlobal("fetch", fetchMock);

    await api("/me/");

    const headers = fetchMock.mock.calls[0][1].headers as Record<string, string>;
    expect(headers.Authorization).toBe("Bearer valid-token");
  });
});
