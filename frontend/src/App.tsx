import { useCallback, useEffect, useRef } from 'react';
import { Outlet, useLocation, useNavigate } from 'react-router-dom';
import { useAtomValue, useSetAtom } from 'jotai';
import DownloadIcon from '@mui/icons-material/FileDownloadOutlined';
import { Button } from '@/components/Button/Button';
import { DetailPanel } from '@/components/DetailPanel/DetailPanel';
import { DayDetail, DayDetailHeader } from '@/components/DayDetail/DayDetail';
import { Navbar } from '@/components/Navbar/Navbar';
import { RunDebrief, RunDebriefHeader } from '@/components/RunDebrief/RunDebrief';
import type { RunDebriefHandle } from '@/components/RunDebrief/RunDebrief';
import {
  activeViewAtom,
  applicationsAtom,
  selectedScopeAtom,
  VIEWS,
} from '@/atoms/appAtom';
import type { ViewId } from '@/atoms/appAtom';
import {
  closePanelAtom,
  panelBackAtom,
  panelCanGoBackAtom,
  panelDepthAtom,
  panelTopAtom,
} from '@/atoms/panelAtom';
import { pushToastAtom } from '@/atoms/toastAtom';
import { useApplications } from '@/hooks/useRuns';
import { useDayRuns } from '@/hooks/useRuns';
import { useLiveRuns } from '@/hooks/useLiveRuns';
import { useScheduleFailureNotifications } from '@/hooks/useScheduleFailureNotifications';
import { he } from '@/locales/he';
import { paths } from '@/routes/paths';
import { runService } from '@/services/runService';
import { useStyles } from './AppStyles';

const isViewId = (value: string): value is ViewId => (VIEWS as readonly string[]).includes(value);

/**
 * Authenticated shell: navbar, routed page outlet, and the shared detail
 * panel. Mounted once by AppRoutes so navigating between views does not
 * remount the chrome or drop the live status connection.
 */
export const AppLayout = () => {
  const { classes } = useStyles();
  const navigate = useNavigate();
  const location = useLocation();

  const setActiveView = useSetAtom(activeViewAtom);
  const setApplications = useSetAtom(applicationsAtom);
  const pushToast = useSetAtom(pushToastAtom);

  const scope = useAtomValue(selectedScopeAtom);
  const panelTop = useAtomValue(panelTopAtom);
  const panelDepth = useAtomValue(panelDepthAtom);
  const canGoBack = useAtomValue(panelCanGoBackAtom);
  const goBack = useSetAtom(panelBackAtom);
  const closePanel = useSetAtom(closePanelAtom);

  const { data: applications } = useApplications();

  useLiveRuns();
  useScheduleFailureNotifications();

  useEffect(() => {
    if (applications) setApplications(applications);
  }, [applications, setApplications]);

  // The URL is the source of truth; the atom is the read model the navbar and
  // scope filter subscribe to.
  useEffect(() => {
    const segment = location.pathname.split('/')[1] ?? '';
    if (isViewId(segment)) setActiveView(segment);
  }, [location.pathname, setActiveView]);

  const handleViewChange = useCallback(
    (view: ViewId) => navigate(`/${view}`),
    [navigate],
  );

  const handleRunAllMain = useCallback(async () => {
    try {
      const started = await runService.startBulkMain(scope);
      navigate(paths.tests);
      pushToast({
        message:
          started.length > 0 ? he.tests.runningOn(started.length) : he.tests.alreadyRunning,
        severity: 'success',
      });
    } catch {
      pushToast({ message: he.errors.generic, severity: 'error' });
    }
  }, [scope, navigate, pushToast]);


  const activeView = (location.pathname.split('/')[1] ?? '') as ViewId;

  return (
    <div className={classes.root}>
      <Navbar
        activeView={isViewId(activeView) ? activeView : 'tests'}
        onViewChange={handleViewChange}
        onRunAllMain={() => void handleRunAllMain()}
      />

      <main className={classes.main}>
        <Outlet />
      </main>

      {panelTop?.kind === 'day' && (
        <DayPanel date={panelTop.date} level={panelDepth} onClose={closePanel} />
      )}

      {panelTop?.kind === 'run' && (
        <RunPanel
          runId={panelTop.run.id}
          level={panelDepth}
          onClose={closePanel}
          onBack={canGoBack ? goBack : undefined}
        />
      )}
    </div>
  );
};

/** Split out so `useDayRuns` only mounts while a day is actually open. */
const DayPanel = ({
  date,
  level,
  onClose,
}: {
  date: string;
  level: number;
  onClose: () => void;
}) => {
  const { data } = useDayRuns(date);
  const runs = data?.items ?? [];

  return (
    <DetailPanel
      open
      level={level}
      onClose={onClose}
      header={<DayDetailHeader date={date} runs={runs} />}
    >
      <DayDetail runs={runs} />
    </DetailPanel>
  );
};

const RunPanel = ({
  runId,
  level,
  onClose,
  onBack,
}: {
  runId: string;
  level: number;
  onClose: () => void;
  onBack?: () => void;
}) => {
  const panelTop = useAtomValue(panelTopAtom);
  // Lets the footer trigger the download without duplicating the
  // comments/artifacts fetch that RunDebrief already owns.
  const debriefRef = useRef<RunDebriefHandle>(null);

  if (panelTop?.kind !== 'run' || panelTop.run.id !== runId) return null;
  const { run } = panelTop;

  const handleDownloadReport = () => {
    debriefRef.current?.downloadReport();
  };

  return (
    <DetailPanel
      open
      level={level}
      onClose={onClose}
      onBack={onBack}
      header={<RunDebriefHeader run={run} />}
      footer={
        <>
          <Button
            variant="tint"
            onClick={handleDownloadReport}
            data-testid="download-report-button"
          >
            <DownloadIcon sx={{ fontSize: 15 }} />
            {he.actions.downloadReport}
          </Button>
          <Button variant="ghost" onClick={onClose}>
            {he.actions.close}
          </Button>
        </>
      }
    >
      <RunDebrief ref={debriefRef} run={run} />
    </DetailPanel>
  );
};
