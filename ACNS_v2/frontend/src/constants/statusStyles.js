// Centralized visual styles for issue statuses and priorities.
//
// Keeping these here means every dashboard, card, and detail view renders the
// same colors — change a class once and every surface picks it up.
//
// NOTE: several views intentionally treat unhandled statuses differently
// (e.g. fall back to Open styling, or a neutral gray). See the comment next to
// STATUS_BADGE_STYLES_WITHOUT_CLOSED before reusing these maps.

// Border pill styles for the four canonical issue statuses.
export const STATUS_BADGE_STYLES = {
  Open: "bg-red-100 text-red-800 border-red-200",
  "In Progress": "bg-yellow-100 text-yellow-800 border-yellow-200",
  Resolved: "bg-green-100 text-green-800 border-green-200",
  Closed: "bg-gray-100 text-gray-700 border-gray-200",
};

// Compact styles without a border (small pills in lists / activity feeds).
export const STATUS_PILL_STYLES = {
  Open: "bg-red-100 text-red-800",
  "In Progress": "bg-yellow-100 text-yellow-800",
  Resolved: "bg-green-100 text-green-800",
  Closed: "bg-gray-100 text-gray-600",
};

// Expanded per-status style tokens used by table views (e.g. AdminIssues).
export const STATUS_CONFIG = {
  Open:         { bg: 'bg-red-100',    text: 'text-red-700',    border: 'border-red-200',    dot: 'bg-red-500'    },
  'In Progress':{ bg: 'bg-yellow-100', text: 'text-yellow-700', border: 'border-yellow-200', dot: 'bg-yellow-500' },
  Resolved:     { bg: 'bg-green-100',  text: 'text-green-700',  border: 'border-green-200',  dot: 'bg-green-500'  },
  Closed:       { bg: 'bg-gray-100',   text: 'text-gray-600',   border: 'border-gray-200',   dot: 'bg-gray-400'   },
};

// Issue priority badge styles.
export const PRIORITY_BADGE_STYLES = {
  Critical: "bg-red-100 text-red-700",
  High: "bg-orange-100 text-orange-700",
  Normal: "bg-blue-100 text-blue-700",
};

// Neutral gray badge (with border) used as a fallback in the user issue popup.
export const GRAY_STATUS_BADGE = "bg-gray-100 text-gray-600 border-gray-200";

// Badge styles WITHOUT a Closed entry.
//
// Some views (IssueCard, the user issue popup) intentionally have no Closed
// mapping and currently render any unhandled status — including Closed — with
// their fallback style. Keep using this export for those views so their exact
// rendering is preserved.
export const STATUS_BADGE_STYLES_WITHOUT_CLOSED = Object.fromEntries(
  Object.entries(STATUS_BADGE_STYLES).filter(([status]) => status !== "Closed")
);
