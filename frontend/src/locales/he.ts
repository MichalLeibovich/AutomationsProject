/** Feminine cardinal numbers, as "שעות" takes — 1 and 2 are irregular and
 * handled separately in {@link he.schedule.everyHours}. */
const HOUR_WORDS: Record<number, string> = {
  3: 'שלוש',
  4: 'ארבע',
  5: 'חמש',
  6: 'שש',
  7: 'שבע',
  8: 'שמונה',
  9: 'תשע',
  10: 'עשר',
  11: 'אחת עשרה',
  12: 'שתים עשרה',
};

/**
 * All user-facing copy. Centralised so the Hebrew strings are not scattered
 * across components — the prerequisite for adding a second locale later.
 */
export const he = {
  brand: {
    name: 'NOC Test',
    tagline: (apps: number) => `${apps} אפליקציות · אוטומציה כללית`,
  },
 
  nav: {
    tests: 'אוטומציות',
    dashboard: 'לוח בקרה',
    timeline: 'היסטוריה',
    calendar: 'יומן',
    scheduled: 'אוטומציות מתוזמנות',
    signOut: 'התנתקות',
  },
 
  scope: {
    allApps: 'כל האפליקציות',
    general: 'כללי',
    generalTooltip: 'אוטומציה משותפת שאינה משויכת לאפליקציה מסוימת',
    label: 'תחום',
  },
 
  actions: {
    runAllMain: 'הרצת כל הבדיקות הראשיות',
    run: 'הרץ',
    stop: 'עצור',
    apply: 'החל',
    export: 'ייצוא',
    debrief: 'תחקיר',
    close: 'סגירה',
    cancel: 'ביטול',
    confirm: 'אישור',
    downloadReport: 'הורדת דוח',
    send: 'שליחה',
    today: 'היום',
    backToDay: 'חזרה ליום',
    showMore: 'הצגת 60 נוספות',
    retry: 'נסו שוב',
    signIn: 'התחברות',
  },
 
  status: {
    passed: 'עברה',
    failed: 'נכשלה',
    running: 'בריצה',
    queued: 'בתור',
    cancelled: 'בוטלה',
    timed_out: 'פסק זמן',
    idle: 'טרם הורצה',
  },
 
  tests: {
    secondary: 'בדיקות משניות',
    filterSecondary: 'סינון בדיקות משניות',
    filterAutomations: 'סינון אוטומציות',
    notRunThisSession: 'טרם הורצה במפגש הנוכחי',
    sharedAutomation: 'אוטומציה משותפת, לא משויכת לאפליקציה',
    waiting: 'ממתינה',
    waitingForRunner: 'ממתינה לשרת ההרצה',
    noPermission: 'אין לך הרשאה להריץ בדיקות',
    noMatch: (query: string, total: number) =>
      `לא נמצאה התאמה ל"${query}". נקו את הסינון כדי לראות את כל ${total}.`,
    runningOn: (count: number) => `מריץ בדיקה ראשית ב-${count} אפליקציות`,
    alreadyRunning: 'כל הבדיקות הראשיות כבר רצות',
    summaryFailing: (failed: number, passed: number) => `${failed} נכשלות · ${passed} עוברות`,
    summaryPassing: (passed: number, total: number) => `${passed} מתוך ${total} עוברות`,
    confirmPrivilegedTitle: 'הרצת אוטומציה מורשית',
    confirmPrivilegedBody: (name: string) =>
      `"${name}" משנה הרשאות בסביבת הייצור. הפעולה תירשם ביומן הביקורת. להמשיך?`,
  },
 
  dashboard: {
    timeRange: 'טווח זמן',
    generalAutomation: 'אוטומציה כללית',
    allAppsScope: (count: number) => `כל האפליקציות · ${count} מוצרים`,
    rangeOrderError: 'תאריך ההתחלה חייב להיות לפני תאריך הסיום',
    rangeFutureError: 'לא ניתן לבחור תאריך עתידי',
    // Run history begins on this date; anything earlier is not a narrower
    // query, it's an empty one — so the picker refuses it and says why.
    rangeTooEarlyError: 'לא ניתן לבחור תאריך לפני 7 באוקטובר 2023',
    from: 'מתאריך',
    to: 'עד תאריך',
    ranges: { hour: 'שעה אחרונה', day: '24 שעות', week: '7 ימים', custom: 'מותאם' },
    totalRuns: 'סה״כ ריצות',
    passRate: 'אחוז הצלחה',
    failures: 'כשלים',
    avgDuration: 'משך ממוצע',
    completedCleanly: (count: number) => `${count} הסתיימו ללא כשל`,
    withinTarget: 'עומד ביעד',
    belowTarget: 'מתחת ליעד של 75%',
    acrossFeatures: (count: number) => `ב-${count} רכיבים`,
    perRun: 'לכל ריצה שהושלמה',
    volumeTitle: 'נפח ריצות',
    volumeSub: 'ריצות שעברו ונכשלו בטווח הנבחר',
    byFeatureTitle: 'כשלים לפי רכיב',
    byFeatureSub: 'היכן הריצות נכשלות בתדירות הגבוהה ביותר',
    byErrorTitle: 'סוגי שגיאות',
    byErrorSub: 'התפלגות סיבות הכשל',
    failuresUnit: 'כשלים',
    noFailures: 'אין כשלים',
    noFailuresBody: 'כל הריצות בטווח הזה עברו בהצלחה',
    pickRange: 'בחרו טווח תאריכים',
    pickRangeBody: 'בחרו תאריך התחלה וסיום ולחצו על החל כדי לראות תוצאות.',
    noRuns: 'אין ריצות בטווח הזה',
    noRunsBody: 'הרחיבו את הטווח או בטלו את סינון האפליקציה כדי לראות פעילות נוספת.',
  },
 
  timeline: {
    title: 'היסטוריית ריצות',
    count: (shown: number, total: number, scope: string) =>
      `${shown} מתוך ${total} ריצות · ${scope}`,
    searchPlaceholder: 'חיפוש לפי מערכת, בדיקה, מפעיל או שגיאה',
    all: 'הכל',
    columns: {
      scope: 'תחום',
      test: 'בדיקה',
      startedAt: 'התחילה',
      duration: 'משך',
      runBy: 'הורץ על ידי',
      trigger: 'סוג הרצה',
      status: 'סטטוס',
    },
    remaining: (count: number) => `(נותרו ${count})`,
    empty: 'אין ריצות שתואמות לסינון',
    emptySearch: (query: string) =>
      `לא נמצאה התאמה ל"${query}". נסו מונח אחר או אפסו את סינון הסטטוס.`,
    emptyFilter: 'שנו את סינון הסטטוס או בטלו את בחירת האפליקציה.',
    exportStarted: 'הייצוא החל. הקובץ יורד בסיום העיבוד.',
    exportReady: 'הייצוא מוכן להורדה.',
    triggerManual: 'ידני',
    triggerAutomatic: 'אוטומטי',
    groupScheduled: 'סנן וקבץ אוטומציות מתוזמנות',
  },
 
  calendar: {
    monthSummary: (total: number, failed: number) => `${total} ריצות · ${failed} נכשלו`,
    prevMonth: 'החודש הקודם',
    nextMonth: 'החודש הבא',
    failedCount: (count: number) => `${count} נכשלו`,
    more: (count: number) => `עוד ${count}`,
    weekdays: ['א׳', 'ב׳', 'ג׳', 'ד׳', 'ה׳', 'ו׳', 'ש׳'],
  },
 
  schedule: {
    upcomingTitle: 'אוטומציות הבאות שעתידות לרוץ',
    next24hTitle: 'תזמון 24 השעות הקרובות',
    noUpcoming: 'אין אוטומציות מתוזמנות בטווח הקרוב',
    skipped: 'בוטל',
    restore: 'שחזור',
    addRun: 'הוספת ריצה מתוזמנת',
    addRunTitle: 'הוספת ריצה מתוזמנת',
    addRunApplication: 'מערכת',
    addRunDate: 'תאריך',
    addRunTimeOfDay: 'שעה',
    addRunPastError: 'לא ניתן לתזמן ריצה בעבר',
    addRunSubmit: 'תזמון',
    addRunSuccess: 'הריצה תוזמנה',
    deleteSelected: 'מחיקת ריצות נבחרות',
    deleteConfirmTitle: 'ביטול ריצות מתוזמנות',
    deleteConfirmBody: (system: string, times: string) =>
      `למחוק את הריצות המתוזמנות של ${system} בשעות ${times}?`,
    deleteSuccess: 'הריצות בוטלו',
    restoreSuccess: 'הריצה שוחזרה',
    everyHours: (hours: number): string => {
      if (hours === 1) return 'כל שעה';
      if (hours === 2) return 'כל שעתיים';
      const word = HOUR_WORDS[hours];
      return word ? `כל ${word} שעות` : `כל ${hours} שעות`;
    },
    edit: 'עריכה',
    doneEditing: 'סיום עריכה',
    clearSelection: 'ניקוי בחירה',
    selectGroup: (time: string): string => `בחירת כל הריצות בשעה ${time}`,
    frequencyTitle: 'תדירות הרצת האוטומציות',
    frequencyTestName: 'בדיקת שפיות - טעינת האתר',
    noFrequency: 'לא הוגדרו אוטומציות מתוזמנות פעילות',
  },

  notifications: {
    permissionButtonLabel: 'התראות דפדפן',
    permissionDefault: 'לחצו כדי לאפשר התראות שולחן עבודה על כשל באוטומציה מתוזמנת',
    permissionGranted: 'התראות שולחן עבודה פעילות',
    permissionDenied: 'התראות דפדפן חסומות. ניתן לשנות זאת בהגדרות הדפדפן',
    failureTitle: (system: string) => `כשל באוטומציה מתוזמנת — ${system}`,
    failureBody: (test: string) => test,
  },

  panel: {
    anonymous: 'אנונימי',
    authorPlaceholder: 'שם (לא חובה)',
    close: 'סגירת הפאנל',
    dayDetail: 'פירוט יומי',
    daySummary: (total: number, passed: number, failed: number) =>
      `${total} ריצות · ${passed} עברו · ${failed} נכשלו`,
    runDebrief: 'תחקיר ריצה',
    at: 'בשעה',
    startedAt: 'התחילה',
    endedAt: 'הסתיימה',
    duration: 'משך',
    runBy: 'הורץ על ידי',
    runId: 'מזהה ריצה',
    whatWentWrong: 'מה השתבש',
    screenshots: 'צילומי מסך',
    comments: 'הערות',
    noComments: 'אין עדיין הערות. הוסיפו הערה ראשונה כדי שהמשמרת הבאה תדע במה מדובר.',
    commentPlaceholder: 'הוסיפו הערה לצוות',
  },
 
  /** Section labels for the downloadable plain-text run report. */
  report: {
    details: 'פרטי ריצה',
    status: 'סטטוס',
    noComments: 'אין הערות לריצה זו.',
  },
 
  login: {
    title: 'התחברות למערכת',
    subtitle: 'ניהול בדיקות ואוטומציה',
    email: 'דואר אלקטרוני',
    password: 'סיסמה',
    invalid: 'פרטי ההתחברות שגויים',
  },
 
  errors: {
    generic: 'משהו השתבש. נסו לרענן את הדף.',
    network: 'לא ניתן להתחבר לשרת. בדקו את החיבור ונסו שוב.',
    forbidden: 'אין לך הרשאה לבצע פעולה זו.',
    notFound: 'המשאב המבוקש לא נמצא.',
    loading: 'טוען…',
    loadFailed: 'לא ניתן לטעון את הנתונים',
    serverUnreachable: 'השרת אינו מגיב. ודאו שהשרת פועל ושכתובת ה-API נכונה.',
    noAutomations: 'לא הוגדרו אוטומציות',
    noAutomationsHint: 'הריצו את סקריפט האתחול כדי לרשום את האפליקציות והאוטומציות.',
    notFoundTitle: 'הדף לא נמצא',
    notFoundBody: 'הכתובת שהזנתם אינה קיימת במערכת.',
    backHome: 'חזרה לבדיקות',
  },
} as const;
 
export type Copy = typeof he;
 