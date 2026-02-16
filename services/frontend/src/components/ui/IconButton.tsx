import { motion } from 'framer-motion';
import type { ReactNode } from 'react';

interface IconButtonProps {
  children: ReactNode;
  className?: string;
  disabled?: boolean;
  onClick?: () => void;
}

export function IconButton({ children, className = '', disabled, onClick }: IconButtonProps) {
  return (
    <motion.button
      whileTap={disabled ? undefined : { scale: 0.93 }}
      className={`w-9 h-9 rounded-xl flex items-center justify-center text-steel hover:text-chalk hover:bg-surface-2 transition-colors ${className}`}
      disabled={disabled}
      onClick={onClick}
    >
      {children}
    </motion.button>
  );
}
