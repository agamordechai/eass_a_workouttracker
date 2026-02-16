import { motion } from 'framer-motion';
import type { ReactNode } from 'react';

interface GlowButtonProps {
  children: ReactNode;
  variant?: 'ember' | 'secondary' | 'ghost' | 'danger' | 'warning';
  size?: 'sm' | 'md';
  className?: string;
  disabled?: boolean;
  type?: 'button' | 'submit' | 'reset';
  onClick?: () => void;
}

const variantClass: Record<string, string> = {
  ember: 'btn btn-ember',
  secondary: 'btn btn-secondary',
  ghost: 'btn btn-ghost',
  danger: 'btn btn-danger',
  warning: 'btn btn-warning',
};

export function GlowButton({ children, variant = 'ember', size, className = '', disabled, type = 'button', onClick }: GlowButtonProps) {
  return (
    <motion.button
      whileTap={disabled ? undefined : { scale: 0.97 }}
      className={`${variantClass[variant]} ${size === 'sm' ? 'btn-sm' : ''} ${className}`}
      disabled={disabled}
      type={type}
      onClick={onClick}
    >
      {children}
    </motion.button>
  );
}
