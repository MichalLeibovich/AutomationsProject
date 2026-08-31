import { Navigate, Route, Routes } from 'react-router-dom';
import { AppLayout } from '@/App';
import { Calendar } from '@/pages/Calendar/Calendar';
import { Dashboard } from '@/pages/Dashboard/Dashboard';
import { NotFound } from '@/pages/NotFound/NotFound';
import { ScheduledAutomations } from '@/pages/ScheduledAutomations/ScheduledAutomations';
import { Tests } from '@/pages/Tests/Tests';
import { Timeline } from '@/pages/Timeline/Timeline';
import { paths } from './paths';

/**
 * Route table.
 *
 * Every view nests inside AppLayout, so the navbar and detail panel mount once
 * rather than per page — which also keeps the live status connection alive
 * across navigation. There is no authentication gate; the root opens straight
 * onto the test grid.
 */
export const AppRoutes = () => (
  <Routes>
    <Route element={<AppLayout />}>
      <Route path={paths.root} element={<Navigate to={paths.tests} replace />} />
      <Route path={paths.tests} element={<Tests />} />
      <Route path={paths.dashboard} element={<Dashboard />} />
      <Route path={paths.timeline} element={<Timeline />} />
      <Route path={paths.calendar} element={<Calendar />} />
      <Route path={paths.scheduled} element={<ScheduledAutomations />} />
      <Route path={paths.notFound} element={<NotFound />} />
    </Route>
  </Routes>
);
