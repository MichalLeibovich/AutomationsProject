import { useAtomValue, useSetAtom } from 'jotai';
import { ButtonBase, Tooltip } from '@mui/material';
import GridIcon from '@mui/icons-material/GridViewOutlined';
import SettingsIcon from '@mui/icons-material/TuneOutlined';
import { applicationsAtom, selectedScopeAtom, toggleScopeAtom } from '@/atoms/appAtom';
import { he } from '@/locales/he';
import { GENERAL_SCOPE } from '@/utils/constants';
import { useStyles } from './ScopeFilterStyles';

export interface ScopeFilterProps {
  /** Lifetime failure counts, keyed by scope identifier. */
  failureCounts?: Record<string, number>;
}

/**
 * Layout: [All apps] │ application pills │ [General]
 *
 * The bookends carry icons rather than colour dots, because neither is an
 * application. "All apps" aggregates the products and deliberately excludes
 * General, which holds shared automation not tied to any product.
 */
export const ScopeFilter = ({ failureCounts = {} }: ScopeFilterProps) => {
  const { classes, cx } = useStyles();
  const applications = useAtomValue(applicationsAtom);
  const selected = useAtomValue(selectedScopeAtom);
  const toggleScope = useSetAtom(toggleScopeAtom);
  const setScope = useSetAtom(selectedScopeAtom);

  const renderCount = (scope: string, isActive: boolean) => {
    const count = failureCounts[scope] ?? 0;
    if (count === 0) return null;

    return (
      <span className={cx(classes.count, isActive && classes.countActive, 'num')}>{count}</span>
    );
  };

  return (
    <div className={classes.root} role="group" aria-label={he.scope.label} data-testid="scope-filter">
      <ButtonBase
        className={cx(classes.pill, selected === null && classes.pillActive)}
        aria-pressed={selected === null}
        onClick={() => setScope(null)}
        data-testid="scope-pill-all"
      >
        <span className={classes.icon}>
          <GridIcon fontSize="inherit" />
        </span>
        {he.scope.allApps}
      </ButtonBase>

      <span className={classes.divider} aria-hidden="true" />

      {applications.map((application) => {
        const isActive = selected === application.name;

        return (
          <ButtonBase
            key={application.id}
            className={cx(classes.pill, isActive && classes.pillActive)}
            aria-pressed={isActive}
            onClick={() => toggleScope(application.name)}
            data-testid={`scope-pill-${application.name}`}
          >
            <span className={classes.dot} style={{ background: application.color }} />
            {application.name}
            {renderCount(application.name, isActive)}
          </ButtonBase>
        );
      })}

      <span className={classes.divider} aria-hidden="true" />

      <Tooltip title={he.scope.generalTooltip}>
        <ButtonBase
          className={cx(classes.pill, selected === GENERAL_SCOPE && classes.pillActive)}
          aria-pressed={selected === GENERAL_SCOPE}
          onClick={() => toggleScope(GENERAL_SCOPE)}
          data-testid="scope-pill-general"
        >
          <span className={classes.icon}>
            <SettingsIcon fontSize="inherit" />
          </span>
          {he.scope.general}
          {renderCount(GENERAL_SCOPE, selected === GENERAL_SCOPE)}
        </ButtonBase>
      </Tooltip>
    </div>
  );
};
