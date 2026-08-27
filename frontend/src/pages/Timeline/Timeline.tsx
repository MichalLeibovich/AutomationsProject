import { useMemo, useState } from 'react';
import { useAtomValue, useSetAtom } from 'jotai';
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TableSortLabel,
} from '@mui/material';
import DownloadIcon from '@mui/icons-material/FileDownloadOutlined';
import CommentIcon from '@mui/icons-material/ChatBubbleOutlineRounded';
import SearchIcon from '@mui/icons-material/SearchOutlined';
import { Button } from '@/components/Button/Button';
import { EmptyState } from '@/components/EmptyState/EmptyState';
import { IdentityDot } from '@/components/IdentityDot/IdentityDot';
import { SearchField } from '@/components/SearchField/SearchField';
import { SegmentedControl } from '@/components/SegmentedControl/SegmentedControl';
import { StatusBadge } from '@/components/StatusBadge/StatusBadge';
import { applicationsAtom, selectedScopeAtom } from '@/atoms/appAtom';
import { openRunPanelAtom } from '@/atoms/panelAtom';
import { pushToastAtom } from '@/atoms/toastAtom';
import { useDebounce } from '@/hooks/useDebounce';
import { useRunList } from '@/hooks/useRuns';
import { he } from '@/locales/he';
import { runService } from '@/services/runService';
import type { RunSortField, SortDirection } from '@/types/api.types';
import { SEARCH_DEBOUNCE_MS, TIMELINE_PAGE_SIZE } from '@/utils/constants';
import { dayKey, formatDuration, formatLongDate, formatTime } from '@/utils/format';
import { resolveScopeColor } from '@/utils/scope';
import { useStyles } from './TimelineStyles';

type StatusFilter = 'all' | 'passed' | 'failed';

export const Timeline = () => {
  const { classes, cx } = useStyles();
  const scope = useAtomValue(selectedScopeAtom);
  const applications = useAtomValue(applicationsAtom);
  const openRun = useSetAtom(openRunPanelAtom);
  const pushToast = useSetAtom(pushToastAtom);

  const [sort, setSort] = useState<{ field: RunSortField; direction: SortDirection }>({
    field: 'started_at',
    direction: 'desc',
  });
  const [status, setStatus] = useState<StatusFilter>('all');
  const [search, setSearch] = useState('');
  const [limit, setLimit] = useState(TIMELINE_PAGE_SIZE);

  // Debounced so typing does not fire a request per keystroke.
  const debouncedSearch = useDebounce(search, SEARCH_DEBOUNCE_MS);

  const { data, isLoading, error } = useRunList({
    scope,
    status,
    search: debouncedSearch,
    sort: sort.field,
    direction: sort.direction,
    limit,
    offset: 0,
  });

  const rows = data?.items ?? [];
  const total = data?.total ?? 0;

  const toggleSort = (field: RunSortField) =>
    setSort((current) => ({
      field,
      direction: current.field === field && current.direction === 'desc' ? 'asc' : 'desc',
    }));

  // The API streams the CSV rather than queueing a job, so the browser can
  // download it by navigating. No polling, and no blob held in memory.
  const handleExport = () => {
    const url = runService.buildExportUrl({
      scope,
      status,
      search: debouncedSearch,
      sort: sort.field,
      direction: sort.direction,
    });
    window.open(url, '_blank', 'noopener');
    pushToast({ message: he.timeline.exportStarted, severity: 'success' });
  };

  const grouped = useMemo(() => {
    if (sort.field !== 'started_at') {
      return rows.map((run) => ({ run, dayHeader: null as string | null }));
    }

    let previous: string | null = null;
    return rows.map((run) => {
      const key = dayKey(run.startedAt);
      const dayHeader = key !== previous ? formatLongDate(run.startedAt) : null;
      previous = key;
      return { run, dayHeader };
    });
  }, [rows, sort.field]);

  const sortableHeader = (field: RunSortField, label: string) => (
    <TableCell>
      <TableSortLabel
        active={sort.field === field}
        direction={sort.field === field ? sort.direction : 'desc'}
        onClick={() => toggleSort(field)}
      >
        {label}
      </TableSortLabel>
    </TableCell>
  );

  const renderBody = () => {
    if (error) {
      return <EmptyState icon={<SearchIcon fontSize="inherit" />} title={he.errors.network} />;
    }
    if (isLoading && rows.length === 0) {
      return <EmptyState icon={<SearchIcon fontSize="inherit" />} title={he.errors.loading} />;
    }
    if (rows.length === 0) {
      return (
        <EmptyState
          icon={<SearchIcon fontSize="inherit" />}
          title={he.timeline.empty}
          body={
            debouncedSearch ? he.timeline.emptySearch(debouncedSearch) : he.timeline.emptyFilter
          }
        />
      );
    }

    return (
      <>
        <TableContainer>
          <Table className={classes.table} size="small">
            <TableHead>
              <TableRow>
                <TableCell>{he.timeline.columns.scope}</TableCell>
                <TableCell>{he.timeline.columns.test}</TableCell>
                {sortableHeader('started_at', he.timeline.columns.startedAt)}
                {sortableHeader('duration_seconds', he.timeline.columns.duration)}
                <TableCell>{he.timeline.columns.runBy}</TableCell>
                {sortableHeader('status', he.timeline.columns.status)}
                <TableCell />
              </TableRow>
            </TableHead>

            <TableBody>
              {grouped.map(({ run, dayHeader }) => [
                dayHeader ? (
                  <TableRow key={`${run.id}-day`} className={classes.dayRow}>
                    <TableCell colSpan={7}>{dayHeader}</TableCell>
                  </TableRow>
                ) : null,

                <TableRow key={run.id} data-testid="timeline-row">
                  <TableCell>
                    <span className={classes.scopeCell}>
                      <IdentityDot color={resolveScopeColor(applications, run.applicationId)} />
                      {run.scopeLabel}
                    </span>
                  </TableCell>
                  <TableCell className={classes.muted}>{run.testName}</TableCell>
                  <TableCell className="num">{formatTime(run.startedAt)}</TableCell>
                  <TableCell className="num">{formatDuration(run.durationSeconds)}</TableCell>
                  <TableCell className={classes.muted}>{run.triggeredBy}</TableCell>
                  <TableCell>
                    <StatusBadge status={run.status} />
                  </TableCell>
                  <TableCell className={classes.actionCell}>
                    <Button
                      variant="ghost"
                      size="small"
                      onClick={() => openRun(run)}
                      data-testid="debrief-button"
                    >
                      <CommentIcon sx={{ fontSize: 14 }} />
                      {he.actions.debrief}
                    </Button>
                  </TableCell>
                </TableRow>,
              ])}
            </TableBody>
          </Table>
        </TableContainer>

        {total > rows.length && (
          <div className={classes.footer}>
            <Button
              variant="ghost"
              size="small"
              onClick={() => setLimit((value) => value + TIMELINE_PAGE_SIZE)}
            >
              {he.actions.showMore}{' '}
              <span className="num">{he.timeline.remaining(total - rows.length)}</span>
            </Button>
          </div>
        )}
      </>
    );
  };

  return (
    <div className={classes.card}>
      <div className={classes.toolbar}>
        <div>
          <div className={classes.title}>{he.timeline.title}</div>
          <div className={cx(classes.subtitle, 'num')}>
            {he.timeline.count(rows.length, total, scope ?? he.scope.allApps)}
          </div>
        </div>

        <div className={classes.spacer} />

        <div className={classes.search}>
          <SearchField
            value={search}
            onChange={setSearch}
            placeholder={he.timeline.searchPlaceholder}
            testId="timeline-search"
          />
        </div>

        <SegmentedControl<StatusFilter>
          small
          value={status}
          onChange={setStatus}
          testId="status-filter"
          options={[
            { value: 'all', label: he.timeline.all },
            { value: 'passed', label: he.status.passed },
            { value: 'failed', label: he.status.failed },
          ]}
        />

        <Button variant="tint" size="small" onClick={() => handleExport()} data-testid="export-button">
          <DownloadIcon sx={{ fontSize: 15 }} />
          {he.actions.export}
        </Button>
      </div>

      {renderBody()}
    </div>
  );
};
