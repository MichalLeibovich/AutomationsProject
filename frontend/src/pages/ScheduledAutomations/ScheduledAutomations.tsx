import { useEffect, useMemo, useState } from 'react';
import type { MouseEvent as ReactMouseEvent } from 'react';
import { useAtomValue, useSetAtom } from 'jotai';
import {
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  IconButton,
  MenuItem,
  Popover,
  TextField,
} from '@mui/material';
import AddRounded from '@mui/icons-material/AddRounded';
import ChevronLeftIcon from '@mui/icons-material/ChevronLeft';
import ChevronRightIcon from '@mui/icons-material/ChevronRight';
import CloseRounded from '@mui/icons-material/CloseRounded';
import DeleteOutlineRounded from '@mui/icons-material/DeleteOutlineRounded';
import EditRounded from '@mui/icons-material/EditRounded';
import RestoreRounded from '@mui/icons-material/RestoreRounded';
import UpdateOutlined from '@mui/icons-material/UpdateOutlined';
import { DatePicker, LocalizationProvider, TimePicker } from '@mui/x-date-pickers';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFnsV3';
import type { PickersCalendarHeaderProps } from '@mui/x-date-pickers/PickersCalendarHeader';
import { he as hebrewLocale } from 'date-fns/locale';
import { addMonths, format, isSameDay, setMonth, setYear, startOfMonth } from 'date-fns';
import { Button } from '@/components/Button/Button';
import { EmptyState } from '@/components/EmptyState/EmptyState';
import { IdentityDot } from '@/components/IdentityDot/IdentityDot';
import { SearchField } from '@/components/SearchField/SearchField';
import { applicationsAtom } from '@/atoms/appAtom';
import { pushToastAtom } from '@/atoms/toastAtom';
import { useConfirm } from '@/contexts/ConfirmContext/ConfirmContext';
import { useRunList, useTestDefinitions } from '@/hooks/useRuns';
import { useSchedules, useUpcomingOccurrences } from '@/hooks/useSchedules';
import { he } from '@/locales/he';
import { scheduleService } from '@/services/scheduleService';
import type { Schedule, ScheduledOccurrence } from '@/types/schedule.types';
import type { TestRun } from '@/types/run.types';
import { formatTime } from '@/utils/format';
import { resolveScopeColor } from '@/utils/scope';
import { useStyles } from './ScheduledAutomationsStyles';

const UPCOMING_WINDOW_HOURS = 24;
/** Recent runs fetched to find each system's last main-test run — comfortably
 * more than the number of active systems, so a run further back never hides
 * a more recent one that happens to sort after it in the page. */
const RECENT_RUNS_LIMIT = 200;

/** Whole-hour cadences the schedule table itself accepts — every positive
 * divisor of a day, matching the `schedules_every_hours_divides_day`
 * database constraint. */
const FREQUENCY_OPTIONS = [1, 2, 3, 4, 6, 8, 12, 24];

const minutesUntil = (occurrenceAt: string): number =>
  Math.round((new Date(occurrenceAt).getTime() - Date.now()) / 60_000);

const occurrenceKey = (occurrence: ScheduledOccurrence): string =>
  `${occurrence.kind}:${occurrence.scheduleId ?? occurrence.extraRunId}:${occurrence.occurrenceAt}`;

/**
 * Month/year quick-jump calendar header, matching the one on the dashboard's
 * custom date range picker so both pickers feel like the same control.
 */
const CalendarHeader = ({ currentMonth, onMonthChange, disabled }: PickersCalendarHeaderProps<Date>) => {
  const { classes } = useStyles();
  const [menu, setMenu] = useState<'month' | 'year' | null>(null);
  const [anchor, setAnchor] = useState<HTMLButtonElement | null>(null);

  const today = new Date();
  const viewedYear = currentMonth.getFullYear();
  const isCurrentYear = viewedYear === today.getFullYear();

  // An extra run is always in the future, so the only real bound is "not
  // before today" — there is no earliest-history floor to respect here.
  const months = Array.from({ length: 12 }, (_, month) => ({
    month,
    label: format(setMonth(startOfMonth(currentMonth), month), 'LLLL', { locale: hebrewLocale }),
    disabled: isCurrentYear && month < today.getMonth(),
  }));

  const years = Array.from({ length: 5 }, (_, index) => ({ year: today.getFullYear() + index }));

  const openMenu = (event: ReactMouseEvent<HTMLButtonElement>, nextMenu: 'month' | 'year') => {
    setAnchor(event.currentTarget);
    setMenu(nextMenu);
  };
  const closeMenu = () => {
    setMenu(null);
    setAnchor(null);
  };

  return (
    <div className="schedule-date-picker-header">
      <IconButton
        size="small"
        aria-label="החודש הקודם"
        disabled={disabled}
        onClick={() => onMonthChange(addMonths(currentMonth, -1), 'right')}
      >
        <ChevronRightIcon fontSize="small" />
      </IconButton>

      <div className="schedule-date-picker-heading">
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
          <div className="schedule-date-picker-month-grid">
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
          <div className="schedule-date-picker-year-list">
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

export const ScheduledAutomations = () => {
  const { classes, cx } = useStyles();
  const applications = useAtomValue(applicationsAtom);
  const pushToast = useSetAtom(pushToastAtom);
  const confirm = useConfirm();

  const {
    data: upcoming,
    isLoading: upcomingLoading,
    reload: reloadUpcoming,
  } = useUpcomingOccurrences(UPCOMING_WINDOW_HOURS);
  const {
    data: schedules,
    isLoading: schedulesLoading,
    reload: reloadSchedules,
  } = useSchedules();
  const { data: applicationDefinitions } = useTestDefinitions(null);
  const { data: recentRuns } = useRunList({
    sort: 'started_at',
    direction: 'desc',
    limit: RECENT_RUNS_LIMIT,
  });

  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [addOpen, setAddOpen] = useState(false);
  const [editMode, setEditMode] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [editingSchedule, setEditingSchedule] = useState<Schedule | null>(null);

  const occurrences = upcoming ?? [];

  // The 24h list filtered by system name or time-of-day, so a busy schedule
  // can be narrowed down without touching the "about to run" tiles above it.
  const searchedOccurrences = useMemo(() => {
    const query = searchQuery.trim().toLowerCase();
    if (!query) return occurrences;
    return occurrences.filter(
      (occurrence) =>
        occurrence.applicationName.toLowerCase().includes(query) ||
        formatTime(occurrence.occurrenceAt).includes(query),
    );
  }, [occurrences, searchQuery]);

  // Each application's main automation id, so a run can be matched back to
  // "the" system-sanity test rather than any test that happens to be its most
  // recent.
  const mainDefinitionByApplication = useMemo(() => {
    const map = new Map<string, string>();
    for (const definition of applicationDefinitions ?? []) {
      if (definition.kind === 'main' && definition.applicationId) {
        map.set(definition.applicationId, definition.id);
      }
    }
    return map;
  }, [applicationDefinitions]);

  // The most recent main-test run per application, manual or scheduled —
  // `recentRuns` is already newest-first, so the first match per application
  // is its last run.
  const lastMainRunByApplication = useMemo(() => {
    const map = new Map<string, TestRun>();
    for (const run of recentRuns?.items ?? []) {
      if (!run.applicationId || map.has(run.applicationId)) continue;
      if (mainDefinitionByApplication.get(run.applicationId) !== run.testDefinitionId) continue;
      map.set(run.applicationId, run);
    }
    return map;
  }, [recentRuns, mainDefinitionByApplication]);

  // One group per scheduled time slot, so an hour with several applications
  // shows its time once rather than once per application.
  const occurrenceGroups = useMemo(() => {
    const order: string[] = [];
    const buckets = new Map<string, ScheduledOccurrence[]>();

    for (const occurrence of searchedOccurrences) {
      if (!buckets.has(occurrence.occurrenceAt)) {
        buckets.set(occurrence.occurrenceAt, []);
        order.push(occurrence.occurrenceAt);
      }
      buckets.get(occurrence.occurrenceAt)!.push(occurrence);
    }

    return order.map((occurrenceAt) => ({ occurrenceAt, items: buckets.get(occurrenceAt)! }));
  }, [searchedOccurrences]);

  // The headline "about to run" tiles: the single next non-cancelled
  // occurrence per application, not the full 24h list.
  const nextPerApplication = useMemo(() => {
    const seen = new Map<string, ScheduledOccurrence>();
    for (const occurrence of occurrences) {
      if (occurrence.skipped) continue;
      if (!seen.has(occurrence.applicationId)) seen.set(occurrence.applicationId, occurrence);
    }
    return [...seen.values()].sort((a, b) => a.occurrenceAt.localeCompare(b.occurrenceAt));
  }, [occurrences]);

  // One row per actively-scheduled system, carrying everything the three
  // panels show for it — the single source the frequency/next-run/last-run
  // columns all read from, so their rows can never drift out of alignment.
  const systemRows = useMemo(() => {
    return (schedules ?? [])
      .filter((schedule) => schedule.isActive)
      .map((schedule) => ({
        schedule,
        nextOccurrence:
          nextPerApplication.find((occurrence) => occurrence.applicationId === schedule.applicationId) ??
          null,
        lastRun: lastMainRunByApplication.get(schedule.applicationId) ?? null,
      }))
      .sort((a, b) =>
        (a.schedule.applicationName ?? '').localeCompare(b.schedule.applicationName ?? '', 'he'),
      );
  }, [schedules, nextPerApplication, lastMainRunByApplication]);

  const selectedOccurrences = occurrences.filter((occurrence) =>
    selected.has(occurrenceKey(occurrence)),
  );

  const toggleSelected = (occurrence: ScheduledOccurrence) => {
    const key = occurrenceKey(occurrence);
    setSelected((current) => {
      const next = new Set(current);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  };

  const isGroupSelected = (group: { items: ScheduledOccurrence[] }) => {
    const selectable = group.items.filter((occurrence) => !occurrence.skipped);
    return selectable.length > 0 && selectable.every((occurrence) => selected.has(occurrenceKey(occurrence)));
  };

  const toggleGroupSelected = (group: { items: ScheduledOccurrence[] }) => {
    const selectable = group.items.filter((occurrence) => !occurrence.skipped);
    const allSelected = isGroupSelected(group);
    setSelected((current) => {
      const next = new Set(current);
      for (const occurrence of selectable) {
        const key = occurrenceKey(occurrence);
        if (allSelected) next.delete(key);
        else next.add(key);
      }
      return next;
    });
  };

  const handleDeleteSelected = async () => {
    if (selectedOccurrences.length === 0) return;

    const systems = [...new Set(selectedOccurrences.map((item) => item.applicationName))].join(
      ', ',
    );
    const times = selectedOccurrences
      .map((item) => formatTime(item.occurrenceAt))
      .join(', ');

    const accepted = await confirm({
      title: he.schedule.deleteConfirmTitle,
      body: he.schedule.deleteConfirmBody(systems, times),
      confirmLabel: he.schedule.deleteSelected,
      destructive: true,
    });
    if (!accepted) return;

    try {
      await Promise.all(
        selectedOccurrences.map((item) =>
          item.kind === 'schedule'
            ? scheduleService.skip(item.scheduleId as string, item.occurrenceAt)
            : scheduleService.removeExtra(item.extraRunId as string),
        ),
      );
      setSelected(new Set());
      reloadUpcoming();
      pushToast({ message: he.schedule.deleteSuccess, severity: 'success' });
    } catch {
      pushToast({ message: he.errors.generic, severity: 'error' });
    }
  };

  const handleRestore = async (occurrence: ScheduledOccurrence) => {
    if (!occurrence.scheduleId) return;
    try {
      await scheduleService.restore(occurrence.scheduleId, occurrence.occurrenceAt);
      reloadUpcoming();
      pushToast({ message: he.schedule.restoreSuccess, severity: 'success' });
    } catch {
      pushToast({ message: he.errors.generic, severity: 'error' });
    }
  };

  const handleAdded = () => {
    setAddOpen(false);
    reloadUpcoming();
    pushToast({ message: he.schedule.addRunSuccess, severity: 'success' });
  };

  const handleFrequencyUpdated = () => {
    setEditingSchedule(null);
    reloadSchedules();
    reloadUpcoming();
    pushToast({ message: he.schedule.editFrequencySuccess, severity: 'success' });
  };

  const handleExitEdit = () => {
    setEditMode(false);
    setSelected(new Set());
  };

  return (
    <div className={classes.root}>
      <section className={classes.overview}>
        {!schedulesLoading && systemRows.length === 0 ? (
          <EmptyState icon={<UpdateOutlined fontSize="inherit" />} title={he.schedule.noSystems} />
        ) : (
          <div className={classes.overviewRow}>
            <div className={classes.nameColumn}>
              <div className={classes.panelHeading} />
              {systemRows.map(({ schedule }) => (
                <div key={schedule.id} className={classes.nameRow}>
                  <IconButton
                    size="small"
                    className={classes.nameEditButton}
                    aria-label={he.schedule.editFrequency(schedule.applicationName ?? '')}
                    onClick={() => setEditingSchedule(schedule)}
                    data-testid="edit-frequency-button"
                  >
                    <EditRounded fontSize="inherit" />
                  </IconButton>
                  <IdentityDot color={resolveScopeColor(applications, schedule.applicationId)} />
                  <span className={classes.nameText}>{schedule.applicationName}</span>
                </div>
              ))}
            </div>

            <div className={classes.panel}>
              <div className={classes.panelHeading}>
                <div className={classes.panelHeadingBig}>{he.schedule.frequencyPanelTitle}</div>
                <div className={classes.panelHeadingSmall}>{he.schedule.frequencyPanelSubtitle}</div>
              </div>
              {systemRows.map(({ schedule }) => (
                <div key={schedule.id} className={classes.panelRow}>
                  <span className={classes.panelRowValue}>{he.schedule.everyHours(schedule.everyHours)}</span>
                </div>
              ))}
            </div>

            <div className={classes.panel}>
              <div className={classes.panelHeading}>
                <div className={classes.panelHeadingBig}>{he.schedule.nextRunPanelTitle}</div>
                <div className={classes.panelHeadingSmall}>{he.schedule.nextRunPanelSubtitle}</div>
              </div>
              {systemRows.map(({ schedule, nextOccurrence }) => (
                <div key={schedule.id} className={classes.panelRow}>
                  {nextOccurrence ? (
                    <>
                      <span className={cx(classes.panelRowValue, classes.panelRowValueTime, 'num')}>
                        {formatTime(nextOccurrence.occurrenceAt)}
                      </span>
                      <span className={classes.panelRowMuted}>
                        {he.schedule.timeUntil(minutesUntil(nextOccurrence.occurrenceAt))}
                      </span>
                    </>
                  ) : (
                    <span className={classes.panelRowMuted}>{he.schedule.noValue}</span>
                  )}
                </div>
              ))}
            </div>

            <div className={classes.panel}>
              <div className={classes.panelHeading}>
                <div className={classes.panelHeadingBig}>{he.schedule.lastRunPanelTitle}</div>
                <div className={classes.panelHeadingSmall}>{he.schedule.lastRunPanelSubtitle}</div>
              </div>
              {systemRows.map(({ schedule, lastRun }) => (
                <div key={schedule.id} className={classes.panelRow}>
                  {lastRun ? (
                    <>
                      <span className={cx(classes.panelRowValue, classes.panelRowValueTime, 'num')}>
                        {formatTime(lastRun.startedAt)}
                      </span>
                      <span className={classes.panelRowTag}>
                        {lastRun.triggerSource === 'manual'
                          ? he.schedule.lastRunManual
                          : he.schedule.lastRunAutomatic}
                      </span>
                    </>
                  ) : (
                    <span className={classes.panelRowMuted}>{he.schedule.noValue}</span>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </section>

      <section className={classes.card}>
        <div className={classes.cardHeader}>
          <div className={classes.title}>{he.schedule.next24hTitle}</div>
          <div className={classes.search}>
            <SearchField
              value={searchQuery}
              onChange={setSearchQuery}
              placeholder={he.schedule.searchPlaceholder}
              testId="occurrence-search"
            />
          </div>
          <div className={classes.spacer} />

          {editMode && selectedOccurrences.length > 0 && (
            <Button
              variant="ghost"
              size="small"
              onClick={() => setSelected(new Set())}
              data-testid="clear-selection-button"
            >
              <CloseRounded sx={{ fontSize: 15 }} />
              {he.schedule.clearSelection}
            </Button>
          )}

          {editMode && selectedOccurrences.length > 0 && (
            <Button
              variant="danger"
              size="small"
              onClick={() => void handleDeleteSelected()}
              data-testid="delete-selected-button"
            >
              <DeleteOutlineRounded sx={{ fontSize: 15 }} />
              {he.schedule.deleteSelected}
            </Button>
          )}

          <Button variant="tint" size="small" onClick={() => setAddOpen(true)} data-testid="add-run-button">
            <AddRounded sx={{ fontSize: 16 }} />
            {he.schedule.addRun}
          </Button>

          {editMode ? (
            <Button variant="ghost" size="small" onClick={handleExitEdit} data-testid="done-editing-button">
              {he.schedule.doneEditing}
            </Button>
          ) : (
            <Button variant="ghost" size="small" onClick={() => setEditMode(true)} data-testid="edit-button">
              <EditRounded sx={{ fontSize: 15 }} />
              {he.schedule.edit}
            </Button>
          )}
        </div>

        {!upcomingLoading && searchedOccurrences.length === 0 ? (
          <EmptyState icon={<UpdateOutlined fontSize="inherit" />} title={he.schedule.noUpcoming} />
        ) : (
          <div className={classes.groupList}>
            {occurrenceGroups.map((group) => (
              <div key={group.occurrenceAt} className={classes.group}>
                {editMode && group.items.some((occurrence) => !occurrence.skipped) && (
                  <input
                    type="checkbox"
                    checked={isGroupSelected(group)}
                    onChange={() => toggleGroupSelected(group)}
                    aria-label={he.schedule.selectGroup(formatTime(group.occurrenceAt))}
                    data-testid="select-group-checkbox"
                  />
                )}

                <span className={cx(classes.groupTime, 'num')}>
                  {formatTime(group.occurrenceAt)}
                </span>
                <div className={classes.groupEntries}>
                  {group.items.map((occurrence) => {
                    const key = occurrenceKey(occurrence);
                    return (
                      <div
                        key={key}
                        className={cx(classes.occurrenceChip, occurrence.skipped && classes.rowSkipped)}
                        data-testid="occurrence-row"
                      >
                        {editMode && !occurrence.skipped && (
                          <input
                            type="checkbox"
                            checked={selected.has(key)}
                            onChange={() => toggleSelected(occurrence)}
                            aria-label={occurrence.applicationName}
                          />
                        )}

                        <IdentityDot
                          color={resolveScopeColor(applications, occurrence.applicationId)}
                        />
                        {occurrence.applicationName}
                        {occurrence.skipped && (
                          <span className={classes.skippedLabel}>{he.schedule.skipped}</span>
                        )}

                        {editMode && occurrence.skipped && (
                          <Button
                            variant="ghost"
                            size="small"
                            onClick={() => void handleRestore(occurrence)}
                            data-testid="restore-button"
                          >
                            <RestoreRounded sx={{ fontSize: 15 }} />
                            {he.schedule.restore}
                          </Button>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      <AddScheduledRunDialog
        open={addOpen}
        onClose={() => setAddOpen(false)}
        onCreated={handleAdded}
      />

      <EditFrequencyDialog
        schedule={editingSchedule}
        onClose={() => setEditingSchedule(null)}
        onUpdated={handleFrequencyUpdated}
      />
    </div>
  );
};

const AddScheduledRunDialog = ({
  open,
  onClose,
  onCreated,
}: {
  open: boolean;
  onClose: () => void;
  onCreated: () => void;
}) => {
  const { classes } = useStyles();
  const applications = useAtomValue(applicationsAtom);
  const pushToast = useSetAtom(pushToastAtom);

  const [applicationId, setApplicationId] = useState('');
  const [dateValue, setDateValue] = useState<Date | null>(null);
  const [timeValue, setTimeValue] = useState<Date | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const runAt = useMemo(() => {
    if (!dateValue || !timeValue) return null;
    const merged = new Date(dateValue);
    merged.setHours(timeValue.getHours(), timeValue.getMinutes(), 0, 0);
    return merged;
  }, [dateValue, timeValue]);

  const pastError = runAt && runAt <= new Date() ? he.schedule.addRunPastError : null;

  const resetFields = () => {
    setApplicationId('');
    setDateValue(null);
    setTimeValue(null);
  };

  const handleClose = () => {
    if (submitting) return;
    resetFields();
    onClose();
  };

  const handleSubmit = async () => {
    if (!applicationId || !runAt || pastError) return;

    setSubmitting(true);
    try {
      await scheduleService.addExtra(applicationId, runAt.toISOString());
      resetFields();
      onCreated();
    } catch {
      pushToast({ message: he.errors.generic, severity: 'error' });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onClose={handleClose} data-testid="add-run-dialog">
      <DialogTitle>{he.schedule.addRunTitle}</DialogTitle>
      <DialogContent>
        <TextField
          select
          fullWidth
          className={classes.dialogField}
          label={he.schedule.addRunApplication}
          value={applicationId}
          onChange={(event) => setApplicationId(event.target.value)}
          data-testid="add-run-application"
        >
          {applications.map((application) => (
            <MenuItem key={application.id} value={application.id}>
              {application.name}
            </MenuItem>
          ))}
        </TextField>

        <LocalizationProvider dateAdapter={AdapterDateFns} adapterLocale={hebrewLocale}>
          <div className={classes.dateTimeRow}>
            <div className={classes.field}>
              <label className={classes.fieldLabel} htmlFor="add-run-date-input">
                {he.schedule.addRunDate}
              </label>
              <DatePicker
                value={dateValue}
                onChange={setDateValue}
                format="dd/MM/yyyy"
                views={['year', 'month', 'day']}
                openTo="day"
                minDate={new Date()}
                slots={{ calendarHeader: CalendarHeader }}
                slotProps={{
                  textField: {
                    id: 'add-run-date-input',
                    className: classes.dateInput,
                    size: 'small',
                    error: Boolean(pastError),
                    inputProps: { 'data-testid': 'add-run-date' },
                  },
                  desktopPaper: { className: classes.datePickerPaper },
                  mobilePaper: { className: classes.datePickerPaper },
                }}
              />
            </div>

            <div className={classes.field}>
              <label className={classes.fieldLabel} htmlFor="add-run-time-input">
                {he.schedule.addRunTimeOfDay}
              </label>
              <TimePicker
                value={timeValue}
                onChange={setTimeValue}
                ampm={false}
                minTime={dateValue && isSameDay(dateValue, new Date()) ? new Date() : undefined}
                slotProps={{
                  textField: {
                    id: 'add-run-time-input',
                    className: classes.dateInput,
                    size: 'small',
                    error: Boolean(pastError),
                    inputProps: { 'data-testid': 'add-run-time' },
                  },
                  desktopPaper: { className: classes.timePickerPaper },
                  mobilePaper: { className: classes.timePickerPaper },
                }}
              />
            </div>

            {pastError && (
              <span className={classes.rangeError} role="alert">
                {pastError}
              </span>
            )}
          </div>
        </LocalizationProvider>
      </DialogContent>
      <DialogActions>
        <Button variant="ghost" onClick={handleClose}>
          {he.actions.cancel}
        </Button>
        <Button
          variant="primary"
          disabled={!applicationId || !runAt || Boolean(pastError) || submitting}
          onClick={() => void handleSubmit()}
          data-testid="add-run-submit"
        >
          {he.schedule.addRunSubmit}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

const EditFrequencyDialog = ({
  schedule,
  onClose,
  onUpdated,
}: {
  schedule: Schedule | null;
  onClose: () => void;
  onUpdated: () => void;
}) => {
  const { classes } = useStyles();
  const pushToast = useSetAtom(pushToastAtom);

  const [everyHours, setEveryHours] = useState(schedule?.everyHours ?? 1);
  const [submitting, setSubmitting] = useState(false);

  // Reset to the schedule's current value each time a different (or no)
  // schedule is opened, rather than carrying over the previous edit's pick.
  useEffect(() => {
    if (schedule) setEveryHours(schedule.everyHours);
  }, [schedule]);

  const handleClose = () => {
    if (submitting) return;
    onClose();
  };

  const handleSubmit = async () => {
    if (!schedule) return;

    setSubmitting(true);
    try {
      await scheduleService.updateFrequency(schedule.id, everyHours);
      onUpdated();
    } catch {
      pushToast({ message: he.errors.generic, severity: 'error' });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Dialog open={schedule !== null} onClose={handleClose} data-testid="edit-frequency-dialog">
      <DialogTitle>{he.schedule.editFrequencyTitle}</DialogTitle>
      <DialogContent>
        <TextField
          select
          fullWidth
          className={classes.dialogField}
          label={he.schedule.editFrequencyField}
          value={everyHours}
          onChange={(event) => setEveryHours(Number(event.target.value))}
          data-testid="edit-frequency-select"
        >
          {FREQUENCY_OPTIONS.map((hours) => (
            <MenuItem key={hours} value={hours}>
              {he.schedule.everyHours(hours)}
            </MenuItem>
          ))}
        </TextField>
        <p className={classes.editFrequencyNote}>{he.schedule.editFrequencyNote}</p>
      </DialogContent>
      <DialogActions>
        <Button variant="ghost" onClick={handleClose}>
          {he.actions.cancel}
        </Button>
        <Button
          variant="primary"
          disabled={submitting || everyHours === schedule?.everyHours}
          onClick={() => void handleSubmit()}
          data-testid="edit-frequency-submit"
        >
          {he.schedule.editFrequencySubmit}
        </Button>
      </DialogActions>
    </Dialog>
  );
};
