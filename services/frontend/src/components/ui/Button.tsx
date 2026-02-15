import { motion } from 'framer-motion';
import { clsx } from 'clsx';
import type { ReactNode } from 'react';

type Variant = 'primary' | 'secondary' | 'ghost' | 'danger' | 'energy' | 'warning';

const variantClass: Record<Variant, string> = {
  primary: 'btn btn-primary',
  secondary: 'btn btn-secondary',
  ghost: 'btn btn-ghost',
  danger: 'btn btn-danger',
  energy: 'btn btn-energy',
  warning: 'btn btn-warning',
};

interface ButtonProps {
  variant?: Variant;
  small?: boolean;
  className?: string;
  children: ReactNode;
  disabled?: boolean;
  type?: 'button' | 'submit' | 'reset';
  onClick?: () => void;
}

export function Button({ variant = 'primary', small, className, children, disabled, type = 'button', onClick }: ButtonProps) {
  return (
    <motion.button
      whileTap={disabled ? undefined : { scale: 0.97 }}
      className={clsx(variantClass[variant], small && 'btn-sm', className)}
      disabled={disabled}
      type={type}
      onClick={onClick}
    >
      {children}
    </motion.button>
  );
}
