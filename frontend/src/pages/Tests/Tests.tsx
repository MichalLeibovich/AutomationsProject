import { useCallback } from 'react';
import { useAtomValue, useSetAtom } from 'jotai';
import ListIcon from '@mui/icons-material/ChecklistOutlined';
import { AppCard } from '@/components/AppCard/AppCard';
import { Button } from '@/components/Button/Button';
import { EmptyState } from '@/components/EmptyState/EmptyState';
import { applicationsAtom, isGeneralScopeAtom, selectedScopeAtom } from '@/atoms/appAtom';
import { markRunStartedAtom, runtimeByDefinitionAtom } from '@/atoms/runtimeAtom';
import { pushToastAtom } from '@/atoms/toastAtom';
import { useConfirm } from '@/contexts/ConfirmContext/ConfirmContext';
import { useTestDefinitions } from '@/hooks/useRuns';
import { he } from '@/locales/he';
import { runService } from '@/services/runService';
import { GENERAL_COLOR } from '@/utils/constants';
import { visibleApplications } from '@/utils/scope';
import { useStyles } from './TestsStyles';

export const Tests = () => {
  const scope = useAtomValue(selectedScopeAtom);
  const isGeneral = useAtomValue(isGeneralScopeAtom);
  const applications = useAtomValue(applicationsAtom);
  const runtime = useAtomValue(runtimeByDefinitionAtom);

  const markStarted = useSetAtom(markRunStartedAtom);
  const pushToast = useSetAtom(pushToastAtom);
  const confirm = useConfirm();

  const { data: definitions, isLoading, error, reload } = useTestDefinitions(scope);
  const allDefinitions = definitions ?? [];

  const visible = visibleApplications(applications, scope);
  const solo = isGeneral || visible.length === 1;
  const { classes } = useStyles({ solo });

  const handleRun = useCallback(
    async (definitionId: string) => {
      const definition = allDefinitions.find((entry) => entry.id === definitionId);
      if (!definition) return;

      // General automations change production state, so the intent is
      // confirmed before anything is enqueued. With no roles left, this
      // confirmation is the remaining guard in the interface; the API refuses
      // to bulk-run the general scope independently.
      if (definition.scope === 'general') {
        const accepted = await confirm({
          title: he.tests.confirmPrivilegedTitle,
          body: he.tests.confirmPrivilegedBody(definition.name),
          confirmLabel: he.actions.run,
          destructive: true,
        });
        if (!accepted) return;
      }

      try {
        const run = await runService.start(definitionId);
        markStarted({ definitionId, runId: run.id });
      } catch {
        pushToast({ message: he.errors.generic, severity: 'error' });
      }
    },
    [allDefinitions, pushToast, confirm, markStarted],
  );

  const handleStop = useCallback(
    async (definitionId: string) => {
      const runId = runtime[definitionId]?.runId;
      if (!runId) return;

      try {
        await runService.cancel(runId);
      } catch {
        pushToast({ message: he.errors.generic, severity: 'error' });
      }
    },
    [runtime, pushToast],
  );


  if (isGeneral) {
    return (
      <div className={classes.grid}>
        <AppCard
          title={he.scope.general}
          color={GENERAL_COLOR}
          definitions={allDefinitions.filter((entry) => entry.scope === 'general')}
          runtime={runtime}
          canRun={() => true}
          wide
          onRun={(id) => void handleRun(id)}
          onStop={(id) => void handleStop(id)}
        />
      </div>
    );
  }

  // Three different situations that used to render identically as "loading",
  // which made a failed request indistinguishable from an empty catalog.
  if (isLoading) {
    return <EmptyState icon={<ListIcon fontSize="inherit" />} title={he.errors.loading} />;
  }

  if (error) {
    return (
      <EmptyState
        icon={<ListIcon fontSize="inherit" />}
        title={he.errors.loadFailed}
        body={error.isNetworkError ? he.errors.serverUnreachable : error.message}
        action={
          <Button variant="tint" onClick={reload}>
            {he.actions.retry}
          </Button>
        }
      />
    );
  }

  if (visible.length === 0) {
    return (
      <EmptyState
        icon={<ListIcon fontSize="inherit" />}
        title={he.errors.noAutomations}
        body={he.errors.noAutomationsHint}
      />
    );
  }

  return (
    <div className={classes.grid}>
      {visible.map((application) => (
        <AppCard
          key={application.id}
          title={application.name}
          color={application.color}
          definitions={allDefinitions.filter(
            (entry) => entry.applicationId === application.id,
          )}
          runtime={runtime}
          canRun={() => true}
          wide={solo}
          onRun={(id) => void handleRun(id)}
          onStop={(id) => void handleStop(id)}
        />
      ))}
    </div>
  );
};
