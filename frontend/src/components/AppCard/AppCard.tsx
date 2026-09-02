import { useEffect, useMemo, useState } from 'react';
import { ButtonBase, Collapse } from '@mui/material';
import ChevronDownIcon from '@mui/icons-material/ExpandMoreRounded';
import { IdentityDot } from '@/components/IdentityDot/IdentityDot';
import { SearchField } from '@/components/SearchField/SearchField';
import { TestRow } from '@/components/TestRow/TestRow';
import type { TestRuntimeState } from '@/atoms/runtimeAtom';
import { he } from '@/locales/he';
import type { TestDefinition } from '@/types/application.types';
import type { TestDisplayStatus } from '@/types/run.types';
import { useStyles } from './AppCardStyles';

export interface AppCardProps {
  title: string;
  color: string;
  definitions: TestDefinition[];
  runtime: Record<string, TestRuntimeState>;
  canRun: (definition: TestDefinition) => boolean;
  /** Rendered full width when it is the only card on screen. */
  wide?: boolean;
  onRun: (definitionId: string) => void;
  onStop: (definitionId: string) => void;
}

/** Above this count the secondary list gets its own filter field. */
const SEARCH_THRESHOLD = 1;

export const AppCard = ({
  title,
  color,
  definitions,
  runtime,
  canRun,
  wide = false,
  onRun,
  onStop,
}: AppCardProps) => {
  const { classes, cx } = useStyles({ color, wide });
  const [isOpen, setIsOpen] = useState(false);
  const [query, setQuery] = useState('');

  // Drilling into a single application implies wanting the detail.
  useEffect(() => {
    if (wide) setIsOpen(true);
  }, [wide]);

  const mainTest = definitions.find((definition) => definition.kind === 'main');
  /** General automation has no primary task, so the hierarchy does not apply. */
  const isFlat = !mainTest;
  const secondary = definitions.filter((definition) => definition.kind !== 'main');

  const visible = useMemo(
    () =>
      secondary.filter((definition) =>
        definition.name.toLowerCase().includes(query.trim().toLowerCase()),
      ),
    [secondary, query],
  );

  const statusOf = (id: string): TestDisplayStatus => runtime[id]?.status ?? 'idle';
  const passed = definitions.filter((d) => statusOf(d.id) === 'passed').length;
  const failed = definitions.filter((d) => statusOf(d.id) === 'failed').length;
  const isLive = definitions.some((d) => ['running', 'queued'].includes(statusOf(d.id)));

  const summary = (() => {
    if (isLive) return he.status.running;
    if (failed > 0) return he.tests.summaryFailing(failed, passed);
    if (passed > 0) return he.tests.summaryPassing(passed, definitions.length);
    return isFlat ? he.tests.sharedAutomation : he.tests.waiting;
  })();

  const renderRow = (definition: TestDefinition) => {
    const state = runtime[definition.id];

    return (
      <TestRow
        key={definition.id}
        definition={definition}
        color={color}
        status={state?.status ?? 'idle'}
        elapsedSeconds={state?.elapsedSeconds ?? 0}
        durationSeconds={state?.durationSeconds ?? null}
        endedAt={state?.endedAt ?? null}
        failureReason={state?.failureReason ?? null}
        canRun={canRun(definition)}
        onRun={() => onRun(definition.id)}
        onStop={() => onStop(definition.id)}
      />
    );
  };

  const secondaryBody = (
    <div className={classes.secondaryList}>
      {secondary.length > SEARCH_THRESHOLD && (
        <div className={cx(classes.searchField, wide && classes.fullSpan)}>
          <SearchField
            value={query}
            onChange={setQuery}
            placeholder={isFlat ? he.tests.filterAutomations : he.tests.filterSecondary}
          />
        </div>
      )}

      {visible.length > 0 ? (
        visible.map(renderRow)
      ) : (
        <div className={classes.emptyNote}>{he.tests.noMatch(query, secondary.length)}</div>
      )}
    </div>
  );

  return (
    <section className={classes.root} data-testid={`app-card-${title}`}>
      <header className={classes.header}>
        <IdentityDot color={color} live={isLive} />
        <div className={classes.headerText}>
          <h2 className={classes.title}>{title}</h2>
          <div className={cx(classes.subtitle, 'num')}>{summary}</div>
        </div>
      </header>

      {mainTest && renderRow(mainTest)}

      <div style={{ marginTop: isFlat ? 0 : 8 }}>
        {isFlat ? (
          secondaryBody
        ) : (
          <>
            <ButtonBase
              className={classes.disclosure}
              aria-expanded={isOpen}
              onClick={() => setIsOpen((open) => !open)}
              data-testid="secondary-disclosure"
            >
              <span>
                {he.tests.secondary}{' '}
                <span className={cx(classes.count, 'num')}>({secondary.length})</span>
              </span>
              <span className={cx(classes.chevron, isOpen && classes.chevronOpen)}>
                <ChevronDownIcon fontSize="inherit" />
              </span>
            </ButtonBase>

            <Collapse in={isOpen} unmountOnExit>
              {secondaryBody}
            </Collapse>
          </>
        )}
      </div>
    </section>
  );
};
