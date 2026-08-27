import { keyframes } from 'tss-react';
import { makeStyles } from 'tss-react/mui';
import { tokens } from '@/theme/tokens';
import type { TestDisplayStatus } from '@/types/run.types';

const spin = keyframes`to { transform: rotate(360deg); }`;

/** Four semantic states, so a failure is identifiable by colour alone. */
const PALETTE: Record<TestDisplayStatus, { fg: string; bg: string }> = {
  passed: { fg: tokens.color.pass, bg: tokens.color.passBg },
  failed: { fg: tokens.color.fail, bg: tokens.color.failBg },
  timed_out: { fg: tokens.color.fail, bg: tokens.color.failBg },
  cancelled: { fg: tokens.color.idle, bg: tokens.color.idleBg },
  running: { fg: tokens.color.running, bg: tokens.color.runningBg },
  queued: { fg: tokens.color.running, bg: tokens.color.runningBg },
  idle: { fg: tokens.color.idle, bg: tokens.color.idleBg },
};

export const useStyles = makeStyles<{ status: TestDisplayStatus }>()((_theme, { status }) => {
  const tone = PALETTE[status];

  return {
    root: {
      display: 'inline-flex',
      alignItems: 'center',
      gap: 5,
      paddingBlock: 3,
      paddingInlineStart: 7,
      paddingInlineEnd: 9,
      borderRadius: tokens.radius.pill,
      fontSize: tokens.font.size.xs,
      fontWeight: tokens.font.weight.semibold,
      background: tone.bg,
      color: tone.fg,
      whiteSpace: 'nowrap',
    },
    spinner: {
      animation: `${spin} 1s linear infinite`,
      display: 'flex',
    },
  };
});
