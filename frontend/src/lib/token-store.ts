// Access token lives in memory only — never localStorage, never a
// non-httpOnly cookie. The refresh token is a httpOnly cookie the browser
// handles automatically; this module is just the read/write point the axios
// interceptor and AuthContext both need without creating a circular import.

let accessToken: string | null = null;

export function getAccessToken(): string | null {
  return accessToken;
}

export function setAccessToken(token: string | null): void {
  accessToken = token;
}
