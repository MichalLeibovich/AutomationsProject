import { keyframes } from 'tss-react';
import { makeStyles } from 'tss-react/mui';

const ring = keyframes`
  0%   { opacity: .55; transform: scale(.6); }
  70%  { opacity: 0;   transform: scale(1.35); }
  100% { opacity: 0; }
`;

interface StyleParams {
  color: string;
  size: number;
  live: boolean;
}

export const useStyles = makeStyles<StyleParams>()((_theme, { color, size, live }) => ({
  root: {
    position: 'relative',
    display: 'inline-block',
    flexShrink: 0,
    width: size,
    height: size,
    borderRadius: '50%',
    background: color,
    // `currentColor` lets the pulse ring inherit the identity colour.
    color,

    '&::after': {
      content: '""',
      position: 'absolute',
      inset: -5,
      borderRadius: '50%',
      border: '2px solid currentColor',
      opacity: 0,
      animation: live ? `${ring} 1.9s cubic-bezier(.32,.72,0,1) infinite` : 'none',
    },
  },
}));
