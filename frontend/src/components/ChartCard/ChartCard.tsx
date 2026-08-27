import type { ReactNode } from 'react';
import { useStyles } from './ChartCardStyles';

export interface ChartCardProps {
  title: string;
  subtitle?: string;
  height?: number;
  children: ReactNode;
  testId?: string;
}

export const ChartCard = ({
  title,
  subtitle,
  height = 262,
  children,
  testId,
}: ChartCardProps) => {
  const { classes } = useStyles({ height });

  return (
    <div className={classes.root} data-testid={testId}>
      <div className={classes.header}>
        <div className={classes.title}>{title}</div>
        {subtitle && <div className={classes.subtitle}>{subtitle}</div>}
      </div>
      <div className={classes.body}>{children}</div>
    </div>
  );
};
