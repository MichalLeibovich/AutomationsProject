import { useAtomValue } from 'jotai';
import { Tooltip } from '@mui/material';
import ListIcon from '@mui/icons-material/ChecklistOutlined';
import DashboardIcon from '@mui/icons-material/SpaceDashboardOutlined';
import HistoryIcon from '@mui/icons-material/TimelineOutlined';
import CalendarIcon from '@mui/icons-material/CalendarMonthOutlined';
import ScheduleIcon from '@mui/icons-material/UpdateOutlined';
import PlayIcon from '@mui/icons-material/PlayArrowRounded';
import { Button } from '@/components/Button/Button';
import { NotificationPermission } from '@/components/NotificationPermission/NotificationPermission';
import { ScopeFilter } from '@/components/ScopeFilter/ScopeFilter';
import { SegmentedControl } from '@/components/SegmentedControl/SegmentedControl';
import { applicationsAtom, isGeneralScopeAtom, scopeFilterVisibleAtom } from '@/atoms/appAtom';
import type { ViewId } from '@/atoms/appAtom';
import { he } from '@/locales/he';
import { useStyles } from './NavbarStyles';

export interface NavbarProps {
  activeView: ViewId;
  onViewChange: (view: ViewId) => void;
  onRunAllMain: () => void;
  failureCounts?: Record<string, number>;
}

export const Navbar = ({
  activeView,
  onViewChange,
  onRunAllMain,
  failureCounts,
}: NavbarProps) => {
  const { classes } = useStyles();
  const applications = useAtomValue(applicationsAtom);
  const scopeVisible = useAtomValue(scopeFilterVisibleAtom);
  const isGeneral = useAtomValue(isGeneralScopeAtom);

  return (
    <header className={classes.root} data-testid="app-header">
      <div className={classes.inner}>
        <div className={classes.row}>
          <div className={classes.brand}>
            <div className={classes.mark}>NOC</div>
            <div>
              <div className={classes.wordmark} dir="ltr">
                {he.brand.name}
              </div>
              <div className={classes.tagline}>{he.brand.tagline(applications.length)}</div>
            </div>
          </div>

          <div className={classes.spacer} />

          <SegmentedControl<ViewId>
            value={activeView}
            onChange={onViewChange}
            testId="view-tabs"
            options={[
              {
                value: 'tests',
                label: he.nav.tests,
                icon: <ListIcon fontSize="inherit" />
              },
              {
                value: 'scheduled',
                label: he.nav.scheduled,
                icon: <ScheduleIcon fontSize="inherit" />,
              },
              {
                value: 'timeline',
                label: he.nav.timeline,
                icon: <HistoryIcon fontSize="inherit" />
              },
              {
                value: 'dashboard',
                label: he.nav.dashboard,
                icon: <DashboardIcon fontSize="inherit" />,
              },
              {
                value: 'calendar',
                label: he.nav.calendar,
                icon: <CalendarIcon fontSize="inherit" />,
              },
            ]}
          />

          {/*
            Application-scoped action. Hidden in the General scope: there is no
            "main" automation there, and bulk-firing permission changes would
            be dangerous. The API refuses it independently.
          */}
          {!isGeneral && (
            <Tooltip title="">
              <span>
                <Button
                  variant="primary"
                  onClick={onRunAllMain}
                  data-testid="run-all-main"
                >
                  <PlayIcon sx={{ fontSize: 16 }} />
                  {he.actions.runAllMain}
                </Button>
              </span>
            </Tooltip>
          )}

          <div className={classes.user}>
            <NotificationPermission />
          </div>
        </div>

        {scopeVisible ? (
          <ScopeFilter failureCounts={failureCounts} />
        ) : (
          <div className={classes.spacerRow} />
        )}
      </div>
    </header>
  );
};
