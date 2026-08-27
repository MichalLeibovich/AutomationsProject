import { makeStyles } from 'tss-react/mui';

export const useStyles = makeStyles()(() => ({
  root: {
    display: 'grid',
    placeItems: 'center',
    minHeight: '60vh',
  },
}));
