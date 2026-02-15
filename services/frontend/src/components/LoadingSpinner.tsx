import { Dumbbell } from 'lucide-react';

export function LoadingSpinner({ message = 'Loading...' }: { message?: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-20 gap-4">
      <div className="relative">
        <div className="w-12 h-12 rounded-full border-2 border-primary/20 border-t-primary animate-spin" />
        <Dumbbell size={20} className="absolute inset-0 m-auto text-primary animate-pulse-glow" />
      </div>
      <p className="text-text-secondary text-sm">{message}</p>
    </div>
  );
}
