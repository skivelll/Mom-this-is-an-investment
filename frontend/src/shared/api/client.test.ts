import { afterEach, describe, expect, it, vi } from "vitest";
import { apiRequest, getToken, setToken } from "@/shared/api/client";

describe("apiRequest", () => {
  afterEach(() => {
    window.localStorage.clear();
    vi.restoreAllMocks();
  });

  it("clears stored JWT after an unauthorized response", async () => {
    setToken("expired-token");
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ detail: "Unauthorized" }), {
        status: 401,
        headers: { "content-type": "application/json" },
      }),
    );

    await expect(apiRequest("/auth/me")).rejects.toMatchObject({ status: 401 });

    expect(getToken()).toBeNull();
  });
});
