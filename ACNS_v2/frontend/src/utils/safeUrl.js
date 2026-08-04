/**
 * src/utils/safeUrl.js — render-side URL hardening (P2-01).
 *
 * The backend validates photo URLs at the schema boundary (http/https, or a
 * raster-image base64 data URL), but legacy documents may still contain
 * javascript:/file: URLs (or an attacker may slip one past a future code
 * path). Every image/link render should pass the URL through `safeUrl` so an
 * unsafe value is NEVER placed into an href/src attribute. Returns null for
 * anything unsafe, and a string otherwise.
 *
 * Allowed:
 *   * well-formed http/https URLs without credentials
 *   * raster-image base64 data URLs (data:image/{jpeg,png,gif,webp,bmp};...)
 *     — these mirror what the backend accepts. SVG/HTML data URLs are rejected
 *     (SVG can embed script).
 */

const ALLOWED_PROTOCOLS = new Set(["http:", "https:"]);
const ALLOWED_IMAGE_DATA_TYPES = new Set(["jpeg", "png", "gif", "webp", "bmp"]);

export default function safeUrl(value) {
  if (!value || typeof value !== "string") return null;
  const trimmed = value.trim();
  if (!trimmed) return null;
  if (trimmed.toLowerCase().startsWith("data:")) {
    const match = /^data:image\/([a-z0-9.+-]+);base64,/.exec(trimmed);
    if (!match || !ALLOWED_IMAGE_DATA_TYPES.has(match[1].toLowerCase())) return null;
    return trimmed;
  }
  try {
    const parsed = new URL(trimmed);
    if (!ALLOWED_PROTOCOLS.has(parsed.protocol)) return null;
    if (!parsed.hostname) return null;
    if (parsed.username || parsed.password) return null;
    return trimmed;
  } catch {
    return null;
  }
}
