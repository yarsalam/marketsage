export interface DecodedToken {
  exp?: number;
  iat?: number;
  sub?: string | number;
  temporary?: boolean;
  [claim: string]: unknown;
}

/**
 * Decode JWT claims for client-side UI decisions only.
 * This does not verify the token signature; the backend remains authoritative.
 */
export function decodeToken(token: string): DecodedToken | null {
  try {
    const parts = token.split(".");
    if (parts.length !== 3 || !parts[1]) return null;

    const base64 = parts[1].replace(/-/g, "+").replace(/_/g, "/");
    const padded = base64.padEnd(Math.ceil(base64.length / 4) * 4, "=");
    const binary = atob(padded);
    const bytes = Uint8Array.from(binary, (character) => character.charCodeAt(0));
    const parsed: unknown = JSON.parse(new TextDecoder().decode(bytes));

    if (typeof parsed !== "object" || parsed === null || Array.isArray(parsed)) {
      return null;
    }
    return parsed as DecodedToken;
  } catch {
    return null;
  }
}
