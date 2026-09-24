import { colorSchemeFor } from "./preference";

describe("colorSchemeFor", () => {
  it("forces the chosen scheme", () => {
    expect(colorSchemeFor("light")).toBe("light");
    expect(colorSchemeFor("dark")).toBe("dark");
  });

  it("follows the phone for system or no choice yet", () => {
    expect(colorSchemeFor("system")).toBe("unspecified");
    expect(colorSchemeFor(null)).toBe("unspecified");
  });
});
