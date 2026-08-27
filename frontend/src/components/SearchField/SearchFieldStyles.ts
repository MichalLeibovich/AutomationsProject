import { makeStyles } from 'tss-react/mui';
import { tokens } from '@/theme/tokens';

export const useStyles = makeStyles()(() => ({
  root: {
    width: '100%',

    '& .MuiOutlinedInput-root': {
      borderRadius: tokens.radius.control,
      background: tokens.color.tintSoft,
      fontSize: tokens.font.size.base,
      transition: 'background .2s, box-shadow .2s',

      '& fieldset': { border: 0 },
      '&:hover': { background: tokens.color.tintSoft },
    },

    '& .MuiOutlinedInput-input': {
      padding: '8px 0',
      '&::placeholder': { color: tokens.color.ink25, opacity: 1 },
    },
  },

  icon: {
    color: tokens.color.ink25,
    fontSize: 17,
  },
}));
