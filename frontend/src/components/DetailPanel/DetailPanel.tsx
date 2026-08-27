import { useCallback, useEffect, useRef } from 'react';
import type { ReactNode } from 'react';
import { ButtonBase, Drawer, IconButton, useMediaQuery, useTheme } from '@mui/material';
import ChevronEndIcon from '@mui/icons-material/ChevronLeftRounded';
import CloseIcon from '@mui/icons-material/CloseRounded';
import { useEscapeKey } from '@/hooks/useEscapeKey';
import { he } from '@/locales/he';
import { useStyles } from './DetailPanelStyles';

export interface DetailPanelProps {
  open: boolean;
  header: ReactNode;
  children: ReactNode;
  footer?: ReactNode;
  /** Depth in the navigation stack. Changing it replays the slide transition. */
  level: number;
  onClose: () => void;
  onBack?: () => void;
}

/**
 * One panel serves both the day summary and the run debrief. Pushing a run
 * does not stack a second overlay — the content slides and a back crumb
 * appears, so there is never a modal on top of a modal.
 *
 * MUI's Drawer supplies the scrim, focus trap, scroll lock and RTL-aware
 * slide direction, all of which had to be hand-rolled previously.
 */
export const DetailPanel = ({
  open,
  header,
  children,
  footer,
  level,
  onClose,
  onBack,
}: DetailPanelProps) => {
  const { classes } = useStyles();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const bodyRef = useRef<HTMLDivElement>(null);

  // Escape steps back one level when there is somewhere to return to.
  const handleEscape = useCallback(() => (onBack ? onBack() : onClose()), [onBack, onClose]);
  useEscapeKey(handleEscape, open);

  useEffect(() => {
    if (bodyRef.current) bodyRef.current.scrollTop = 0;
  }, [level]);

  return (
    <Drawer
      open={open}
      onClose={onClose}
      anchor={isMobile ? 'bottom' : 'right'}
      classes={{ paper: classes.paper }}
      // Escape is handled above so it can step back rather than always close.
      disableEscapeKeyDown
      ModalProps={{ keepMounted: false }}
      data-testid="detail-panel"
    >
      <span className={classes.handle} aria-hidden="true" />

      <div className={classes.header}>
        <div className={classes.headerContent}>
          {onBack && (
            <ButtonBase className={classes.crumb} onClick={onBack} data-testid="panel-back">
              <span className={classes.crumbIcon}>
                <ChevronEndIcon fontSize="inherit" />
              </span>
              {he.actions.backToDay}
            </ButtonBase>
          )}
          {header}
        </div>

        <IconButton size="small" onClick={onClose} aria-label={he.panel.close}>
          <CloseIcon sx={{ fontSize: 19 }} />
        </IconButton>
      </div>

      <div className={classes.body} ref={bodyRef}>
        {/* Keying on level restarts the enter animation for each push. */}
        <div key={level} className={classes.step}>
          {children}
        </div>
      </div>

      {footer && <div className={classes.footer}>{footer}</div>}
    </Drawer>
  );
};
