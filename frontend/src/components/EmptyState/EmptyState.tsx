import type { ReactNode } from 'react';
import { useStyles } from './EmptyStateStyles';

export interface EmptyStateProps {
  icon: ReactNode;
  title: string;
  body?: string;
  action?: ReactNode;
}

/**
 * Every list and chart renders this rather than nothing, so an empty result
 * is always distinguishable from a failed load.
 */
export const EmptyState = ({ icon, title, body, action }: EmptyStateProps) => {
  const { classes } = useStyles();

  return (
    <div className={classes.root} data-testid="empty-state">
      <div className={classes.icon}>{icon}</div>
      <div className={classes.title}>{title}</div>
      {body && <div className={classes.body}>{body}</div>}
      {action}
    </div>
  );
};
