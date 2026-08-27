import { useStyles } from './StatCardStyles';

export interface StatCardProps {
  label: string;
  value: string | number;
  hint?: string;
  /** Overrides the value colour — used to flag a KPI outside target. */
  tone?: string;
  testId?: string;
}

export const StatCard = ({ label, value, hint, tone, testId }: StatCardProps) => {
  const { classes, cx } = useStyles();

  return (
    <div className={classes.root} data-testid={testId}>
      <div className={classes.label}>{label}</div>
      <div className={cx(classes.value, 'num')} style={tone ? { color: tone } : undefined}>
        {value}
      </div>
      {hint && <div className={classes.hint}>{hint}</div>}
    </div>
  );
};
