import { describe, it, expect } from "vitest";
import { formatCurrency, formatDate } from "./utils";

describe("formatCurrency", () => {
  it("formats a number", () => {
    expect(formatCurrency(1234.5)).toBe("$1,234.50");
  });

  it("formats a string amount", () => {
    expect(formatCurrency("42.99")).toBe("$42.99");
  });

  it("handles zero", () => {
    expect(formatCurrency(0)).toBe("$0.00");
  });

  it("handles null", () => {
    expect(formatCurrency(null)).toBe("$0.00");
  });

  it("handles undefined", () => {
    expect(formatCurrency(undefined)).toBe("$0.00");
  });

  it("handles empty string", () => {
    expect(formatCurrency("")).toBe("$0.00");
  });

  it("handles non-numeric string", () => {
    expect(formatCurrency("abc")).toBe("$0.00");
  });
});

describe("formatDate", () => {
  it("formats a date string", () => {
    const result = formatDate("2026-03-01");
    expect(result).toBeTruthy();
    expect(result).toContain("2026");
  });
});
