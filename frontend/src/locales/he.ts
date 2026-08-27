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
    tests: 'בדיקות',
    dashboard: 'לוח בקרה',
    timeline: 'היסטוריה',
    calendar: 'יומן',
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
    noFailuresBody: 'כל הריצות בטווח הזה עברו בהצלחה.',
    pickRange: 'בחרו טווח תאריכים',
    pickRangeBody: 'בחרו תאריך התחלה וסיום ולחצו על החל כדי לראות תוצאות.',
    noRuns: 'אין ריצות בטווח הזה',
    noRunsBody: 'הרחיבו את הטווח או בטלו את סינון האפליקציה כדי לראות פעילות נוספת.',
  },

  timeline: {
    title: 'היסטוריית ריצות',
    count: (shown: number, total: number, scope: string) =>
      `${shown} מתוך ${total} ריצות · ${scope}`,
    searchPlaceholder: 'חיפוש לפי אפליקציה, בדיקה, מפעיל או שגיאה',
    all: 'הכל',
    columns: {
      scope: 'תחום',
      test: 'בדיקה',
      startedAt: 'התחילה',
      duration: 'משך',
      runBy: 'הורץ על ידי',
      status: 'סטטוס',
    },
    remaining: (count: number) => `(נותרו ${count})`,
    empty: 'אין ריצות שתואמות לסינון',
    emptySearch: (query: string) =>
      `לא נמצאה התאמה ל"${query}". נסו מונח אחר או אפסו את סינון הסטטוס.`,
    emptyFilter: 'שנו את סינון הסטטוס או בטלו את בחירת האפליקציה.',
    exportStarted: 'הייצוא החל. הקובץ יורד בסיום העיבוד.',
    exportReady: 'הייצוא מוכן להורדה.',
  },

  calendar: {
    monthSummary: (total: number, failed: number) => `${total} ריצות · ${failed} נכשלו`,
    prevMonth: 'החודש הקודם',
    nextMonth: 'החודש הבא',
    failedCount: (count: number) => `${count} נכשלו`,
    more: (count: number) => `עוד ${count}`,
    weekdays: ['א׳', 'ב׳', 'ג׳', 'ד׳', 'ה׳', 'ו׳', 'ש׳'],
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
    whatWentWrong: 'מה השתבש',
    screenshots: 'צילומי מסך',
    comments: 'הערות',
    noComments: 'אין עדיין הערות. הוסיפו הערה ראשונה כדי שהמשמרת הבאה תדע במה מדובר.',
    commentPlaceholder: 'הוסיפו הערה לצוות',
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
