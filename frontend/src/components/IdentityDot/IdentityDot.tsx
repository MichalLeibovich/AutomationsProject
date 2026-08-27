import { useStyles } from './IdentityDotStyles';

export interface IdentityDotProps {
  /** Resolved application colour, or the neutral slate used for General. */
  color: string;
  /** Renders the pulsing ring that signals an in-flight run. */
  live?: boolean;
  size?: number;
}

/**
 * The signature element of the interface. Colour identifies the application;
 * the ring identifies activity. Together they make the grid readable at a
 * glance from across a room.
 */
export const IdentityDot = ({ color, live = false, size = 10 }: IdentityDotProps) => {
  const { classes } = useStyles({ color, size, live });

  return <span className={classes.root} aria-hidden="true" />;
};
