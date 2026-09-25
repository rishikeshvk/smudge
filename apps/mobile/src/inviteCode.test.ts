import { formatCode, isComplete } from "./inviteCode";

describe("formatCode", () => {
  it("groups a typed code in fours, in capitals", () => {
    expect(formatCode("kdrn7q4m")).toBe("KDRN-7Q4M");
  });

  it("ignores spaces, dashes and anything past eight characters", () => {
    expect(formatCode(" kd rn-7q4m-xyz ")).toBe("KDRN-7Q4M");
  });

  it("adds the dash only once a fifth character arrives", () => {
    expect(formatCode("kdrn")).toBe("KDRN");
    expect(formatCode("kdrn7")).toBe("KDRN-7");
  });
});

describe("isComplete", () => {
  it("needs all eight characters", () => {
    expect(isComplete("KDRN-7Q4")).toBe(false);
    expect(isComplete("KDRN-7Q4M")).toBe(true);
  });
});
