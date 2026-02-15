import { clsx } from 'clsx';
import type { ReactNode, HTMLAttributes } from 'react';

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode;
}

export function Card({ className, children, ...props }: CardProps) {
  return (
    <div className={clsx('card', className)} {...props}>
      {children}
    </div>
  );
}
