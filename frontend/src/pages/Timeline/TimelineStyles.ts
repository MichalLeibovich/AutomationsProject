import { makeStyles } from 'tss-react/mui';
import { tokens } from '@/theme/tokens';

export const useStyles = makeStyles()(() => ({
  card: {
    overflow: 'hidden',
    borderRadius: tokens.radius.card,
    background: tokens.color.surface,
    border: '1px solid rgba(10,36,78,.05)',
    boxShadow: tokens.shadow.sm,
  },
  toolbar: {
    display: 'flex',
    alignItems: 'center',
    gap: 12,
    flexWrap: 'wrap',
    padding: '14px 18px',
  },
  title: {
    fontSize: tokens.font.size.md,
    fontWeight: tokens.font.weight.semibold,
  },
  subtitle: {
    fontSize: tokens.font.size.sm,
    color: tokens.color.ink40,
  },
  spacer: { flex: 1 },
  search: { width: 300 },

  table: {
    '& .MuiTableCell-root': {
      borderColor: tokens.color.line,
      fontSize: tokens.font.size.base,
      padding: '11px 14px',
    },
    '& .MuiTableCell-head': {
      fontSize: tokens.font.size.xs,
      fontWeight: 640,
      color: tokens.color.ink40,
      background: tokens.color.surface,
      whiteSpace: 'nowrap',
      padding: '9px 14px',
    },
    '& .MuiTableSortLabel-root': {
      '&:hover': { color: tokens.color.ink },
      '&.Mui-active': { color: tokens.color.ink },
    },
    '& .MuiTableBody-root .MuiTableRow-root:hover': {
      background: tokens.color.tintSoft,
    },
  },

  /** Day dividers only make sense while sorted chronologically. */
  dayRow: {
    '& .MuiTableCell-root': {
      background: tokens.color.canvas,
      padding: '7px 14px',
      fontSize: tokens.font.size.xs,
      fontWeight: 640,
      color: tokens.color.ink40,
    },
    '&:hover .MuiTableCell-root': { background: tokens.color.canvas },
  },

  scopeCell: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: 8,
    fontWeight: tokens.font.weight.medium,
  },
  muted: { color: tokens.color.ink60 },
  actionCell: { textAlign: 'end' },
  footer: {
    padding: 14,
    textAlign: 'center',
    borderTop: `1px solid ${tokens.color.line}`,
  },
}));
