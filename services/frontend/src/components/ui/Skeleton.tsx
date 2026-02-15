import { clsx } from 'clsx';

interface SkeletonProps {
  className?: string;
}

export function Skeleton({ className }: SkeletonProps) {
  return (
    <div
      className={clsx(
        'rounded-lg bg-gradient-to-r from-zinc-800 via-zinc-700 to-zinc-800 bg-[length:200%_100%] animate-shimmer',
        className
      )}
    />
  );
}
