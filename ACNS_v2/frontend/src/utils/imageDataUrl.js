/**
 * src/utils/imageDataUrl.js — client-side image helper (Base64 uploads).
 *
 * Images are sent to the backend as base64 data URLs because Firebase Storage
 * is not available on the Spark (free) plan. The decoded-size cap mirrors
 * backend core/config.MAX_IMAGE_DATA_BYTES (512 KB) — keep both in sync. The
 * cap also keeps a stored issue document well under Firestore's 1 MB document
 * size limit.
 */

export const MAX_IMAGE_BYTES = 512 * 1024;

/**
 * Compute the decoded byte size of a base64 data URL. Returns Infinity when
 * the value is not a parseable data URL.
 */
export function dataUrlByteSize(dataUrl) {
  try {
    const comma = String(dataUrl).indexOf(",");
    if (comma === -1) return Infinity;
    const payload = String(dataUrl).slice(comma + 1);
    const padding = payload.endsWith("==") ? 2 : payload.endsWith("=") ? 1 : 0;
    return Math.floor((payload.length * 3) / 4) - padding;
  } catch {
    return Infinity;
  }
}

/**
 * Throw a friendly Error when a data URL's decoded size exceeds MAX_IMAGE_BYTES.
 */
export function assertDataUrlWithinLimit(dataUrl) {
  if (dataUrlByteSize(dataUrl) > MAX_IMAGE_BYTES) {
    throw new Error(`Image is too large. Maximum size is ${MAX_IMAGE_BYTES / 1024}KB.`);
  }
}
