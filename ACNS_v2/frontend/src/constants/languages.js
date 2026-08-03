// SMS notification languages offered in the UI.
//
// Codes are ISO 639-1 and must match VALID_PREFERRED_LANGUAGES in
// backend/config.py. The default code must match DEFAULT_PREFERRED_LANGUAGE.
export const SMS_LANGUAGE_OPTIONS = [
  { code: "en", label: "English", hint: "English" },
  { code: "te", label: "తెలుగు", hint: "Telugu" },
  { code: "hi", label: "हिन्दी", hint: "Hindi" },
];

export const DEFAULT_SMS_LANGUAGE = "en";
