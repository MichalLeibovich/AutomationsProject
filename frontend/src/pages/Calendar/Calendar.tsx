import { useMemo, useState } from 'react';
import { useAtomValue, useSetAtom } from 'jotai';
import { ButtonBase, Popover } from '@mui/material';
import ChevronPrevIcon from '@mui/icons-material/ChevronRightRounded';
import ChevronNextIcon from '@mui/icons-material/ChevronLeftRounded';
import { format } from 'date-fns';
import { he as hebrewLocale } from 'date-fns/locale';
import { Button } from '@/components/Button/Button';
import { applicationsAtom } from '@/atoms/appAtom';
import { openDayPanelAtom } from '@/atoms/panelAtom';
import { useCalendarMonth } from '@/hooks/useRuns';
import { he } from '@/locales/he';
import { tokens } from '@/theme/tokens';
import { CALENDAR_CHIP_LIMIT, MIN_SELECTABLE_DATE } from '@/utils/constants';
import { formatLongDate, formatMonthYear } from '@/utils/format';
import { resolveScopeColor } from '@/utils/scope';
import { useStyles } from './CalendarStyles';

export const Calendar = () => {
  const { classes, cx } = useStyles();
  const applications = useAtomValue(applicationsAtom);
  const openDay = useSetAtom(openDayPanelAtom);

  const [cursor, setCursor] = useState(() => new Date());
  const [jumpMenu, setJumpMenu] = useState<'month' | 'year' | null>(null);
  const [jumpAnchor, setJumpAnchor] = useState<HTMLButtonElement | null>(null);
  const today = new Date();
  const year = cursor.getFullYear();
  const month = cursor.getMonth();

  const openJumpMenu = (event: React.MouseEvent<HTMLButtonElement>, next: 'month' | 'year') => {
    setJumpAnchor(event.currentTarget);
    setJumpMenu(next);
  };
  const closeJumpMenu = () => {
    setJumpMenu(null);
    setJumpAnchor(null);
  };

  const isEarliestYear = year === MIN_SELECTABLE_DATE.getFullYear();

  const jumpMonths = Array.from({ length: 12 }, (_, index) => ({
    month: index,
    label: format(new Date(year, index, 1), 'LLLL', { locale: hebrewLocale }),
    // There is no run history before this, so an unreachable month is inert
    // rather than clickable-then-showing an empty view.
    disabled: isEarliestYear && index < MIN_SELECTABLE_DATE.getMonth(),
  }));

  // Bounded at the earliest year with run history, so the list never offers
  // a year that can only ever be empty.
  const jumpYears = Array.from(
    { length: today.getFullYear() - MIN_SELECTABLE_DATE.getFullYear() + 1 },
    (_, index) => today.getFullYear() - index,
  );

  // The API takes a 1-based month.
  const { data: days } = useCalendarMonth(year, month + 1);
  const dayList = days ?? [];

  const byDate = useMemo(
    () => new Map(dayList.map((day) => [new Date(day.date).getDate(), day])),
    [dayList],
  );

  const monthTotals = useMemo(
    () =>
      dayList.reduce(
        (accumulator, day) => ({
          total: accumulator.total + day.total,
          failed: accumulator.failed + day.failed,
        }),
        { total: 0, failed: 0 },
      ),
    [dayList],
  );

  const leadingBlanks = new Date(year, month, 1).getDay();
  const daysInMonth = new Date(year, month + 1, 0).getDate();

  const cells: (number | null)[] = [
    ...Array<null>(leadingBlanks).fill(null),
    ...Array.from({ length: daysInMonth }, (_, index) => index + 1),
  ];
  while (cells.length % 7 !== 0) cells.push(null);

  return (
    <div className={classes.card}>
      <div className={classes.toolbar}>
        <div>
          <div className={classes.monthTitle}>{formatMonthYear(cursor)}</div>
          <div className={cx(classes.subtitle, 'num')}>
            {he.calendar.monthSummary(monthTotals.total, monthTotals.failed)}
          </div>
        </div>

        <div className={classes.spacer} />

        <Button variant="ghost" size="small" onClick={() => setCursor(new Date())}>
          {he.actions.today}
        </Button>

        <div className={classes.jumpGroup}>
          <button
            type="button"
            className={classes.jumpTrigger}
            aria-label={he.calendar.chooseMonth}
            data-testid="calendar-jump-month"
            onClick={(event) => openJumpMenu(event, 'month')}
          >
            {format(cursor, 'LLLL', { locale: hebrewLocale })}
          </button>
          <button
            type="button"
            className={classes.jumpTrigger}
            aria-label={he.calendar.chooseYear}
            data-testid="calendar-jump-year"
            onClick={(event) => openJumpMenu(event, 'year')}
          >
            {format(cursor, 'yyyy', { locale: hebrewLocale })}
          </button>

          <Popover
            open={Boolean(jumpMenu)}
            anchorEl={jumpAnchor}
            onClose={closeJumpMenu}
            disableScrollLock
            anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
            transformOrigin={{ vertical: 'top', horizontal: 'center' }}
            slotProps={{ paper: { className: classes.jumpMenu } }}
          >
            {jumpMenu === 'month' ? (
              <div className="calendar-jump-month-grid">
                {jumpMonths.map(({ month: menuMonth, label, disabled }) => (
                  <button
                    key={menuMonth}
                    type="button"
                    disabled={disabled}
                    className={menuMonth === month ? 'is-selected' : undefined}
                    data-today={
                      year === today.getFullYear() && menuMonth === today.getMonth()
                        ? true
                        : undefined
                    }
                    onClick={() => {
                      setCursor(new Date(year, menuMonth, 1));
                      closeJumpMenu();
                    }}
                  >
                    {label}
                  </button>
                ))}
              </div>
            ) : (
              <div className="calendar-jump-year-list">
                {jumpYears.map((menuYear) => (
                  <button
                    key={menuYear}
                    type="button"
                    className={menuYear === year ? 'is-selected' : undefined}
                    data-today={menuYear === today.getFullYear() ? true : undefined}
                    onClick={() => {
                      // The current month may predate the cutoff in the
                      // earliest year, so it is clamped forward rather than
                      // landing on a month with no run history.
                      const clampedMonth =
                        menuYear === MIN_SELECTABLE_DATE.getFullYear()
                          ? Math.max(month, MIN_SELECTABLE_DATE.getMonth())
                          : month;
                      setCursor(new Date(menuYear, clampedMonth, 1));
                      closeJumpMenu();
                    }}
                  >
                    {menuYear}
                  </button>
                ))}
              </div>
            )}
          </Popover>
        </div>

        {/* Under RTL, "previous" sits on the right and points right. */}
        <div className={classes.navGroup}>
          <Button
            variant="tint"
            size="icon"
            aria-label={he.calendar.prevMonth}
            onClick={() => setCursor(new Date(year, month - 1, 1))}
          >
            <ChevronPrevIcon sx={{ fontSize: 18 }} />
          </Button>
          <Button
            variant="tint"
            size="icon"
            aria-label={he.calendar.nextMonth}
            onClick={() => setCursor(new Date(year, month + 1, 1))}
          >
            <ChevronNextIcon sx={{ fontSize: 18 }} />
          </Button>
        </div>
      </div>

      <div className={cx(classes.grid, classes.gridBorder)}>
        {he.calendar.weekdays.map((weekday) => (
          <div key={weekday} className={classes.headerCell}>
            {weekday}
          </div>
        ))}
      </div>

      <div className={classes.grid} role="grid">
        {cells.map((dayNumber, index) => {
          if (dayNumber === null) {
            return <div key={`pad-${index}`} className={classes.padCell} aria-hidden="true" />;
          }

          const date = new Date(year, month, dayNumber);
          const summary = byDate.get(dayNumber);
          const isToday = date.toDateString() === today.toDateString();
          const isFuture = date > today && !isToday;
          const hasRuns = (summary?.total ?? 0) > 0;

          return (
            <ButtonBase
              key={dayNumber}
              className={classes.day}
              // Future days cannot have runs, so they are not clickable.
              disabled={isFuture || !hasRuns}
              onClick={() => openDay(date.toISOString())}
              aria-label={`${formatLongDate(date)}, ${summary?.total ?? 0}`}
              data-testid={`calendar-day-${dayNumber}`}
            >
              <div className={classes.dayHead}>
                <span
                  className={cx(
                    classes.dayNumber,
                    isToday && classes.dayNumberToday,
                    isFuture && classes.dayNumberFuture,
                    'num',
                  )}
                >
                  {dayNumber}
                </span>

                {(summary?.failed ?? 0) > 0 && (
                  <span className={cx(classes.failedCount, 'num')}>
                    {he.calendar.failedCount(summary?.failed ?? 0)}
                  </span>
                )}
              </div>

              {summary?.preview.slice(0, CALENDAR_CHIP_LIMIT).map((run) => (
                <span key={run.id} className={classes.chip}>
                  <span
                    className={classes.chipBar}
                    style={{ background: resolveScopeColor(applications, run.scopeLabel) }}
                  />
                  <span className={classes.chipLabel}>{run.scopeLabel}</span>
                  <span
                    className={classes.chipStatus}
                    style={{
                      background:
                        run.status === 'passed' ? tokens.color.pass : tokens.color.fail,
                    }}
                  />
                </span>
              ))}

              {(summary?.total ?? 0) > CALENDAR_CHIP_LIMIT && (
                <span className={cx(classes.more, 'num')}>
                  {he.calendar.more((summary?.total ?? 0) - CALENDAR_CHIP_LIMIT)}
                </span>
              )}
            </ButtonBase>
          );
        })}
      </div>
    </div>
  );
};