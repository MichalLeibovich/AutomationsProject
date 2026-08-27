import { makeStyles } from 'tss-react/mui';

export const useStyles = makeStyles<{ solo: boolean }>()((theme, { solo }) => ({
  /**
   * `align-items: start` stops a tall card from stretching its row siblings.
   * Without it, expanding one card visually inflated the others — which read
   * as shared state but was purely a grid artefact.
   */
  grid: {
    display: 'grid',
    alignItems: 'start',
    gap: 16,
    gridTemplateColumns: solo ? '1fr' : 'repeat(auto-fill, minmax(480px, 1fr))',
    [theme.breakpoints.down('lg')]: { gridTemplateColumns: '1fr' },
  },
}));
