import { describe, expect, it } from "vitest";
import { compactPayload, normalizeTitle } from "@/shared/lib/format";

describe("format helpers", () => {
  it("normalizes titles for catalog payloads", () => {
    expect(normalizeTitle("  Null   Point #1  ")).toBe("null point #1");
  });

  it("removes empty values recursively", () => {
    expect(
      compactPayload({
        raw_title: "Null Point",
        source_url: "",
        wishlist: {
          target_price: "",
          currency: "RUB",
          comment: null,
        },
      }),
    ).toEqual({
      raw_title: "Null Point",
      wishlist: {
        currency: "RUB",
      },
    });
  });
});
