/** Sentinel for the General scope. Never an Application id. */
export const GENERAL_SCOPE = 'general';

/** `null` selection means "all applications", which excludes General. */
export const ALL_APPS_SCOPE = null;

export const GENERAL_COLOR = '#6B7A94';

export const TIMELINE_PAGE_SIZE = 60;

export const CALENDAR_CHIP_LIMIT = 3;

/** Pass-rate threshold that flips the dashboard KPI from red to green. */
export const PASS_RATE_TARGET = 75;

export const SEARCH_DEBOUNCE_MS = 300;

export const LOCALE = 'he-IL';

/**
 * Earliest date with run history; nothing before this is selectable.
 *
 * There is no run history before this, so offering earlier dates would only
 * ever produce an empty view. Bounding pickers to it means the limit is
 * visible as greyed-out cells rather than discovered through an empty state.
 */
export const MIN_SELECTABLE_DATE = new Date(2023, 9, 7);
