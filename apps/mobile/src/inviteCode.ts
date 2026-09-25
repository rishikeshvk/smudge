export const CODE_LENGTH = 8;

// Shows the code the way it was handed out, ABCD-EFGH, whatever was typed or pasted.
export function formatCode(raw: string): string {
  const code = raw
    .toUpperCase()
    .replace(/[^A-Z0-9]/g, "")
    .slice(0, CODE_LENGTH);
  return code.length > 4 ? `${code.slice(0, 4)}-${code.slice(4)}` : code;
}

export function isComplete(formatted: string): boolean {
  return formatted.replace("-", "").length === CODE_LENGTH;
}
