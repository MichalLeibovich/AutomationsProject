import { useState } from 'react';
import { useAtomValue } from 'jotai';
import CalendarIcon from '@mui/icons-material/CalendarMonthOutlined';
import CheckIcon from '@mui/icons-material/CheckCircleOutline';
import ChevronLeftIcon from '@mui/icons-material/ChevronLeft';
import ChevronRightIcon from '@mui/icons-material/ChevronRight';
import IconButton from '@mui/material/IconButton';
import Popover from '@mui/material/Popover';
import { DatePicker, LocalizationProvider } from '@mui/x-date-pickers';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFnsV3';
import type { PickersCalendarHeaderProps } from '@mui/x-date-pickers/PickersCalendarHeader';
import { he as hebrewLocale } from 'date-fns/locale';
import { addMonths, format, parseISO, setMonth, setYear, startOfMonth } from 'date-fns';
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { Button } from '@/components/Button/Button';
import { ChartCard } from '@/components/ChartCard/ChartCard';
import { EmptyState } from '@/components/EmptyState/EmptyState';
import { SegmentedControl } from '@/components/SegmentedControl/SegmentedControl';
import { StatCard } from '@/components/StatCard/StatCard';
import { applicationsAtom, isGeneralScopeAtom, selectedScopeAtom } from '@/atoms/appAtom';
import { useDashboard } from '@/hooks/useRuns';
import { he } from '@/locales/he';
import { toIsoDate } from '@/utils/format';
import { tokens } from '@/theme/tokens';
import type { RangePreset } from '@/types/api.types';
import { PASS_RATE_TARGET } from '@/utils/constants';
import { formatDuration } from '@/utils/format';
import { useStyles } from './DashboardStyles';

const AXIS = {
  tick: { fontSize: 11, fill: tokens.color.ink40 },
  axisLine: false,
  tickLine: false,
};

/**
 * Width reserved for the category axis, sized to the longest label.
 *
 * @param names - The category labels about to be rendered.
 * @returns A pixel width for the axis.
 */
const FEATURE_AXIS_MIN = 110;
const FEATURE_AXIS_MAX = 210;
/** Approximate advance width of one Hebrew character at the axis font size. */
const FEATURE_CHAR_WIDTH = 6.4;
/**
 * Longest label drawn in full.
 *
 * Chosen so the widest label still fits inside {@link FEATURE_AXIS_MAX}. Beyond
 * this the name is trimmed with an ellipsis rather than allowed to push the
 * axis wider, which would squeeze the bars into nothing on a narrow card. The
 * full name stays available on hover.
 */
const FEATURE_MAX_CHARS = 30;

const featureAxisWidth = (names: string[]): number => {
  const longest = names.reduce(
    (max, name) => Math.max(max, Math.min(name.length, FEATURE_MAX_CHARS)),
    0,
  );
  return Math.min(FEATURE_AXIS_MAX, Math.max(FEATURE_AXIS_MIN, longest * FEATURE_CHAR_WIDTH + 20));
};

/**
 * Category label for the failures chart, drawn beside the bar it belongs to.
 *
 * Recharts' own tick renders through its `Text` component, which measures the
 * string to decide where to break lines. That measurement misreads Hebrew badly
 * enough to wrap after a single character, which is what produced a column of
 * stray letters instead of a name. Drawing the label directly skips the
 * measuring entirely, so the text is never broken.
 *
 * `direction: ltr` on the element is deliberate and does not reverse anything:
 * the label is one Hebrew run, so its glyphs still order right-to-left, but the
 * text box now grows rightward from `x`. Under the inherited RTL direction it
 * would grow leftward instead and sit on top of the bar.
 */
const FeatureTick = ({
  x = 0,
  y = 0,
  payload,
}: {
  x?: number;
  y?: number;
  payload?: { value?: string | number };
}) => {
  const full = String(payload?.value ?? '');
  const shown = full.length > FEATURE_MAX_CHARS ? `${full.slice(0, FEATURE_MAX_CHARS - 1)}…` : full;

  return (
    <text
      x={x + 8}
      y={y}
      textAnchor="start"
      dominantBaseline="central"
      fontSize={11}
      fill={tokens.color.ink40}
      style={{ direction: 'ltr' }}
    >
      {/* Native SVG tooltip, so a trimmed name is still readable in full. */}
      {shown !== full && <title>{full}</title>}
      {shown}
    </text>
  );
};

const TOOLTIP = {
  contentStyle: {
    borderRadius: 12,
    border: `1px solid ${tokens.color.line}`,
    boxShadow: tokens.shadow.md,
    fontSize: 12.5,
    padding: '8px 11px',
    direction: 'rtl' as const,
    textAlign: 'right' as const,
  },
  labelStyle: { fontWeight: 600, color: tokens.color.ink, marginBottom: 4 },
};

/**
 * How many axis labels to skip so they stay legible.
 *
 * The series is now gap-free, so a 24-hour range returns 25 hourly points and a
 * one-hour range 13 five-minute ones. Printing every label overlaps them into an
 * unreadable smear at typical widths. Recharts takes the number of ticks to skip
 * between those it draws, so this targets roughly a dozen visible labels.
 *
 * Only labels are thinned — every data point is still plotted, so the curve, the
 * hover line and the tooltip all keep full resolution.
 *
 * @param pointCount - Number of points in the series.
 * @returns The `interval` value for Recharts' XAxis.
 */
// Thirteen lands each range on a round spacing: every 5 minutes over an
// hour, every 2 hours over a day, every day over a week.
const MAX_VISIBLE_LABELS = 13;

const labelInterval = (pointCount: number): number =>
  Math.max(0, Math.ceil(pointCount / MAX_VISIBLE_LABELS) - 1);

const toDateValue = (value: string): Date | null => (value ? parseISO(value) : null);

const toDraftValue = (value: Date | null): string => (value ? format(value, 'yyyy-MM-dd') : '');

/**
 * Earliest date a custom range may start at.
 *
 * There is no run history before this, so offering earlier dates would only ever
 * produce an empty chart. Bounding the picker means the limit is visible as
 * greyed-out cells rather than discovered through a validation error.
 */
const MIN_SELECTABLE_DATE = new Date(2023, 9, 7);

const CalendarHeader = ({
  currentMonth,
  onMonthChange,
  disabled,
}: PickersCalendarHeaderProps<Date>) => {
  const { classes } = useStyles();
  const [menu, setMenu] = useState<'month' | 'year' | null>(null);
  const [anchor, setAnchor] = useState<HTMLButtonElement | null>(null);

  const today = new Date();
  const viewedYear = currentMonth.getFullYear();
  const isCurrentYear = viewedYear === today.getFullYear();
  const isFutureYear = viewedYear > today.getFullYear();
  const isEarliestYear = viewedYear === MIN_SELECTABLE_DATE.getFullYear();

  const months = Array.from({ length: 12 }, (_, month) => ({
    month,
    label: format(setMonth(startOfMonth(currentMonth), month), 'LLLL', { locale: hebrewLocale }),
    // Bounded at both ends: a custom range can reach neither the future nor
    // further back than the earliest history, so an unreachable month is inert
    // rather than clickable-then-rejected.
    disabled:
      isFutureYear ||
      (isCurrentYear && month > today.getMonth()) ||
      (isEarliestYear && month < MIN_SELECTABLE_DATE.getMonth()),
  }));

  // The whole selectable span is four years, so every year fits in one panel.
  // Paging through decades was machinery for a range that does not exist.
  const years = Array.from(
    { length: today.getFullYear() - MIN_SELECTABLE_DATE.getFullYear() + 1 },
    (_, index) => ({ year: today.getFullYear() - index }),
  );

  const openMenu = (
    event: React.MouseEvent<HTMLButtonElement>,
    nextMenu: 'month' | 'year',
  ) => {
    setAnchor(event.currentTarget);
    setMenu(nextMenu);
  };
  const closeMenu = () => {
    setMenu(null);
    setAnchor(null);
  };

  return (
    <div className="dashboard-date-picker-header">
      <IconButton
        size="small"
        aria-label="החודש הקודם"
        disabled={disabled}
        onClick={() => onMonthChange(addMonths(currentMonth, -1), 'right')}
      >
        <ChevronRightIcon fontSize="small" />
      </IconButton>

      <div className="dashboard-date-picker-heading">
        <button type="button" onClick={(event) => openMenu(event, 'month')}>
          {format(currentMonth, 'LLLL', { locale: hebrewLocale })}
        </button>
        <button type="button" onClick={(event) => openMenu(event, 'year')}>
          {format(currentMonth, 'yyyy', { locale: hebrewLocale })}
        </button>
      </div>

      <IconButton
        size="small"
        aria-label="החודש הבא"
        disabled={disabled}
        onClick={() => onMonthChange(addMonths(currentMonth, 1), 'left')}
      >
        <ChevronLeftIcon fontSize="small" />
      </IconButton>

      <Popover
        open={Boolean(menu)}
        anchorEl={anchor}
        onClose={closeMenu}
        disableScrollLock
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
        transformOrigin={{ vertical: 'top', horizontal: 'center' }}
        slotProps={{ paper: { className: classes.datePickerMenu } }}
      >
        {menu === 'month' ? (
          <div className="dashboard-date-picker-month-grid">
            {months.map(({ month, label, disabled: monthDisabled }) => (
              <button
                key={month}
                type="button"
                disabled={monthDisabled}
                className={month === currentMonth.getMonth() ? 'is-selected' : undefined}
                data-today={isCurrentYear && month === today.getMonth() ? true : undefined}
                onClick={() => {
                  onMonthChange(setMonth(startOfMonth(currentMonth), month), 'left');
                  closeMenu();
                }}
              >
                {label}
              </button>
            ))}
          </div>
        ) : (
          <div className="dashboard-date-picker-year-list">
            {years.map(({ year }) => (
              <button
                key={year}
                type="button"
                className={year === currentMonth.getFullYear() ? 'is-selected' : undefined}
                data-today={year === today.getFullYear() ? true : undefined}
                onClick={() => {
                  onMonthChange(setYear(currentMonth, year), 'left');
                  closeMenu();
                }}
              >
                {year}
              </button>
            ))}
          </div>
        )}
      </Popover>
    </div>
  );
};

export const Dashboard = () => {
  const { classes, cx } = useStyles();
  const scope = useAtomValue(selectedScopeAtom);
  const isGeneral = useAtomValue(isGeneralScopeAtom);
  const applications = useAtomValue(applicationsAtom);

  const [range, setRange] = useState<RangePreset>('week');
  const [draft, setDraft] = useState({ from: '', to: '' });

  // Local date, not toISOString: that converts to UTC and would offer tomorrow
  // as a valid "today" for anyone in a positive offset during the evening.
  const today = toIsoDate(new Date());

  /**
   * Why the current draft cannot be applied, or null when it can.
   *
   * The inputs' min/max already stop the date picker offering an impossible
   * value, but a typed date bypasses them entirely, so the rules are enforced
   * here too and stated in words rather than silently refusing.
   */
  const rangeError = ((): string | null => {
    if (!draft.from || !draft.to) return null;
    if (draft.from > draft.to) return he.dashboard.rangeOrderError;
    if (draft.to > today || draft.from > today) return he.dashboard.rangeFutureError;
    return null;
  })();
  const [applied, setApplied] = useState<{ from: string; to: string } | null>(null);

  // A custom range must not query until both bounds are chosen and applied.
  const isReady = range !== 'custom' || applied !== null;
  const { data, isLoading } = useDashboard(
    { scope, range, from: applied?.from, to: applied?.to },
    isReady,
  );

  const scopeLabel = isGeneral
    ? he.dashboard.generalAutomation
    : (scope ?? he.dashboard.allAppsScope(applications.length));

  const stats = data?.stats;
  const hasData = !!stats && stats.totalRuns > 0;

  return (
    <div className={classes.root}>
      <div className={classes.toolbar}>
        <div>
          <div className={classes.title}>{he.dashboard.timeRange}</div>
          <div className={classes.subtitle}>{scopeLabel}</div>
        </div>

        <div className={classes.spacer} />

        {range === 'custom' && (
          <LocalizationProvider dateAdapter={AdapterDateFns} adapterLocale={hebrewLocale}>
            <div className={classes.customRange}>
              <div className={classes.field}>
                <label className={classes.fieldLabel} htmlFor="range-from-input">
                  {he.dashboard.from}
                </label>
                <DatePicker
                  value={toDateValue(draft.from)}
                  onChange={(value) => setDraft({ ...draft, from: toDraftValue(value) })}
                  format="dd/MM/yyyy"
                  views={['year', 'month', 'day']}
                  openTo="day"
                  minDate={MIN_SELECTABLE_DATE}
                  maxDate={toDateValue(draft.to) ?? toDateValue(today) ?? undefined}
                  slots={{ calendarHeader: CalendarHeader }}
                  slotProps={{
                    textField: {
                      id: 'range-from-input',
                      className: classes.dateInput,
                      size: 'small',
                      error: Boolean(rangeError),
                      inputProps: { 'data-testid': 'range-from' },
                    },
                    desktopPaper: { className: classes.datePickerPaper },
                    mobilePaper: { className: classes.datePickerPaper },
                  }}
                />
              </div>

              <span className={classes.rangeDash} aria-hidden="true">
                —
              </span>

              <div className={classes.field}>
                <label className={classes.fieldLabel} htmlFor="range-to-input">
                  {he.dashboard.to}
                </label>
                <DatePicker
                  value={toDateValue(draft.to)}
                  onChange={(value) => setDraft({ ...draft, to: toDraftValue(value) })}
                  format="dd/MM/yyyy"
                  views={['year', 'month', 'day']}
                  openTo="day"
                  minDate={toDateValue(draft.from) ?? MIN_SELECTABLE_DATE}
                  maxDate={toDateValue(today) ?? undefined}
                  slots={{ calendarHeader: CalendarHeader }}
                  slotProps={{
                    textField: {
                      id: 'range-to-input',
                      className: classes.dateInput,
                      size: 'small',
                      error: Boolean(rangeError),
                      inputProps: { 'data-testid': 'range-to' },
                    },
                    desktopPaper: { className: classes.datePickerPaper },
                    mobilePaper: { className: classes.datePickerPaper },
                  }}
                />
              </div>

              <Button
                variant="primary"
                size="small"
                disabled={!draft.from || !draft.to || Boolean(rangeError)}
                onClick={() => setApplied(draft)}
                data-testid="range-apply"
              >
                {he.actions.apply}
              </Button>

              {rangeError && (
                <span className={classes.rangeError} role="alert">
                  {rangeError}
                </span>
              )}
            </div>
          </LocalizationProvider>
        )}

        <SegmentedControl<RangePreset>
          small
          value={range}
          onChange={setRange}
          testId="range-control"
          options={[
            { value: 'hour', label: he.dashboard.ranges.hour },
            { value: 'day', label: he.dashboard.ranges.day },
            { value: 'week', label: he.dashboard.ranges.week },
            { value: 'custom', label: he.dashboard.ranges.custom },
          ]}
        />
      </div>

      {!hasData || !data ? (
        <div className={classes.emptyCard}>
          <EmptyState
            icon={<CalendarIcon fontSize="inherit" />}
            title={
              isLoading
                ? he.errors.loading
                : !isReady
                  ? he.dashboard.pickRange
                  : he.dashboard.noRuns
            }
            body={!isReady ? he.dashboard.pickRangeBody : he.dashboard.noRunsBody}
          />
        </div>
      ) : (
        <>
          <div className={classes.stats}>
            <StatCard
              testId="stat-total-runs"
              label={he.dashboard.totalRuns}
              value={stats.totalRuns}
              hint={he.dashboard.completedCleanly(stats.totalRuns - stats.failedRuns)}
            />
            <StatCard
              testId="stat-pass-rate"
              label={he.dashboard.passRate}
              value={`${stats.passRate}%`}
              tone={stats.passRate >= PASS_RATE_TARGET ? tokens.color.pass : tokens.color.fail}
              hint={
                stats.passRate >= PASS_RATE_TARGET
                  ? he.dashboard.withinTarget
                  : he.dashboard.belowTarget
              }
            />
            <StatCard
              testId="stat-failures"
              label={he.dashboard.failures}
              value={stats.failedRuns}
              tone={stats.failedRuns > 0 ? tokens.color.fail : undefined}
              hint={he.dashboard.acrossFeatures(data.failuresByFeature.length)}
            />
            <StatCard
              testId="stat-avg-duration"
              label={he.dashboard.avgDuration}
              value={formatDuration(stats.averageDurationSeconds)}
              hint={he.dashboard.perRun}
            />
          </div>

          {/*
            Time flows left-to-right even under RTL — that is the convention in
            Hebrew dashboards. Only the value axis moves to the right.
          */}
          <ChartCard
            title={he.dashboard.volumeTitle}
            subtitle={he.dashboard.volumeSub}
            height={230}
            testId="chart-volume"
          >
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={data.volume} // The first and last labels are centred on their points, so half of each
                  // sits outside the plot area. Without side margins the earliest
                  // time is clipped at the edge.
                  margin={{ top: 4, right: -14, left: 22, bottom: 0 }}>
                <defs>
                  <linearGradient id="gradPassed" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor={tokens.color.pass} stopOpacity={0.28} />
                    <stop offset="100%" stopColor={tokens.color.pass} stopOpacity={0.02} />
                  </linearGradient>
                  <linearGradient id="gradFailed" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor={tokens.color.fail} stopOpacity={0.3} />
                    <stop offset="100%" stopColor={tokens.color.fail} stopOpacity={0.02} />
                  </linearGradient>
                </defs>
                <CartesianGrid vertical={false} stroke="rgba(10,36,78,.07)" />
                <XAxis dataKey="label" {...AXIS} interval={labelInterval(data.volume.length)} />
                <YAxis {...AXIS} orientation="right" allowDecimals={false} />
                <Tooltip {...TOOLTIP} />
                <Area
                  type="monotone"
                  dataKey="passed"
                  name={he.status.passed}
                  stroke={tokens.color.pass}
                  strokeWidth={2}
                  fill="url(#gradPassed)"
                />
                <Area
                  type="monotone"
                  dataKey="failed"
                  name={he.status.failed}
                  stroke={tokens.color.fail}
                  strokeWidth={2}
                  fill="url(#gradFailed)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </ChartCard>

          <div className={classes.chartPair}>
            {/* Categorical comparison: fully mirrored for RTL. */}
            <ChartCard
              title={he.dashboard.byFeatureTitle}
              subtitle={he.dashboard.byFeatureSub}
              testId="chart-by-feature"
            >
              {data.failuresByFeature.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    data={data.failuresByFeature}
                    layout="vertical"
                    margin={{ top: 0, right: 8, left: 4, bottom: 0 }}
                  >
                    <CartesianGrid horizontal={false} stroke="rgba(10,36,78,.07)" />
                    <XAxis type="number" {...AXIS} allowDecimals={false} reversed />
                    <YAxis
                      type="category"
                      dataKey="name"
                      width={featureAxisWidth(data.failuresByFeature.map((f) => f.name))}
                      orientation="right"
                      axisLine={false}
                      tickLine={false}
                      tick={<FeatureTick />}
                    />
                    <Tooltip {...TOOLTIP} cursor={{ fill: 'rgba(10,36,78,.045)' }} />
                    <Bar dataKey="count" name={he.dashboard.failuresUnit} radius={[7, 0, 0, 7]} barSize={18}>
                      {data.failuresByFeature.map((entry, index) => (
                        <Cell
                          key={entry.name}
                          fill={entry.color ?? tokens.chartPalette[index % tokens.chartPalette.length]}
                        />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <EmptyState
                  icon={<CheckIcon fontSize="inherit" />}
                  title={he.dashboard.noFailures}
                  body={he.dashboard.noFailuresBody}
                />
              )}
            </ChartCard>

            <ChartCard
              title={he.dashboard.byErrorTitle}
              subtitle={he.dashboard.byErrorSub}
              testId="chart-by-error"
            >
              {data.failuresByErrorType.length > 0 ? (
                <div className={classes.donutWrap}>
                  <div className={classes.donut}>
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie
                          data={data.failuresByErrorType}
                          dataKey="count"
                          nameKey="name"
                          innerRadius="63%"
                          outerRadius="92%"
                          paddingAngle={3}
                          stroke="none"
                        >
                          {data.failuresByErrorType.map((entry, index) => (
                            <Cell
                              key={entry.name}
                              fill={
                                entry.color ??
                                tokens.chartPalette[index % tokens.chartPalette.length]
                              }
                            />
                          ))}
                        </Pie>
                        <Tooltip {...TOOLTIP} />
                      </PieChart>
                    </ResponsiveContainer>

                    <div className={classes.donutCentre}>
                      <div>
                        <div className={cx(classes.donutTotal, 'num')}>{stats.failedRuns}</div>
                        <div className={classes.subtitle}>{he.dashboard.failuresUnit}</div>
                      </div>
                    </div>
                  </div>

                  <div className={classes.legend}>
                    {data.failuresByErrorType.map((entry, index) => (
                      <div key={entry.name} className={classes.legendRow}>
                        <span
                          className={classes.legendDot}
                          style={{
                            background:
                              entry.color ??
                              tokens.chartPalette[index % tokens.chartPalette.length],
                          }}
                        />
                        <span className={classes.legendName}>{entry.name}</span>
                        <span className={cx(classes.legendCount, 'num')}>{entry.count}</span>
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <EmptyState
                  icon={<CheckIcon fontSize="inherit" />}
                  title={he.dashboard.noFailures}
                  body={he.dashboard.noFailuresBody}
                />
              )}
            </ChartCard>
          </div>
        </>
      )}
    </div>
  );
};