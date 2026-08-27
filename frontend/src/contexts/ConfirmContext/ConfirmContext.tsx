import { createContext, useCallback, useContext, useMemo, useRef, useState } from 'react';
import type { PropsWithChildren } from 'react';
import { Dialog, DialogActions, DialogContent, DialogTitle } from '@mui/material';
import { Button } from '@/components/Button/Button';
import { he } from '@/locales/he';
import { useStyles } from './ConfirmContextStyles';

export interface ConfirmOptions {
  title: string;
  body: string;
  confirmLabel?: string;
  destructive?: boolean;
}

type ConfirmFn = (options: ConfirmOptions) => Promise<boolean>;

const ConfirmContext = createContext<ConfirmFn | null>(null);

/**
 * Imperative confirmation dialog.
 *
 * This is Context rather than a Jotai atom on purpose: the caller needs a
 * promise it can await inline —
 *
 *   if (!(await confirm({...}))) return;
 *
 * An atom would only expose state, forcing every caller to reimplement the
 * "wait for the answer, then continue" plumbing. One dialog instance is
 * mounted for the whole tree.
 */
export function ConfirmProvider({ children }: PropsWithChildren) {
  const { classes } = useStyles();
  const [options, setOptions] = useState<ConfirmOptions | null>(null);
  const resolverRef = useRef<((result: boolean) => void) | null>(null);

  const confirm = useCallback<ConfirmFn>((next) => {
    setOptions(next);
    return new Promise<boolean>((resolve) => {
      resolverRef.current = resolve;
    });
  }, []);

  const settle = useCallback((result: boolean) => {
    resolverRef.current?.(result);
    resolverRef.current = null;
    setOptions(null);
  }, []);

  // `confirm` is stable, so consumers never re-render because of this provider.
  const value = useMemo(() => confirm, [confirm]);

  return (
    <ConfirmContext.Provider value={value}>
      {children}

      <Dialog
        open={options !== null}
        onClose={() => settle(false)}
        classes={{ paper: classes.paper }}
        data-testid="confirm-dialog"
      >
        <DialogTitle className={classes.title}>{options?.title}</DialogTitle>
        <DialogContent className={classes.body}>{options?.body}</DialogContent>
        <DialogActions className={classes.actions}>
          <Button variant="ghost" onClick={() => settle(false)} data-testid="confirm-cancel">
            {he.actions.cancel}
          </Button>
          <Button
            variant={options?.destructive ? 'danger' : 'primary'}
            onClick={() => settle(true)}
            data-testid="confirm-accept"
          >
            {options?.confirmLabel ?? he.actions.confirm}
          </Button>
        </DialogActions>
      </Dialog>
    </ConfirmContext.Provider>
  );
}

export function useConfirm(): ConfirmFn {
  const context = useContext(ConfirmContext);
  if (!context) {
    throw new Error('useConfirm must be used inside a ConfirmProvider');
  }
  return context;
}
