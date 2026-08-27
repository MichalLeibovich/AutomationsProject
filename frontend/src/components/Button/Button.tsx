import { ButtonBase } from '@mui/material';
import type { ButtonBaseProps } from '@mui/material';
import type { ReactNode } from 'react';
import { useStyles } from './ButtonStyles';

export type ButtonVariant = 'primary' | 'tint' | 'ghost' | 'danger';
export type ButtonSize = 'medium' | 'small' | 'icon';

export interface ButtonProps extends ButtonBaseProps {
  variant?: ButtonVariant;
  size?: ButtonSize;
  children?: ReactNode;
}

export const Button = ({
  variant = 'tint',
  size = 'medium',
  className,
  children,
  ...rest
}: ButtonProps) => {
  const { classes, cx } = useStyles();

  // `className` is for layout only — margin, grid placement. Appearance is
  // owned by ButtonStyles via the variant and size classes.
  return (
    <ButtonBase
      className={cx(classes.root, classes[variant], classes[size], className)}
      {...rest}
    >
      {children}
    </ButtonBase>
  );
};
