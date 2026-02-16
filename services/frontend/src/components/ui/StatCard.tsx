import { motion } from 'framer-motion';
import type { ReactNode } from 'react';
import { itemSlideUp } from '../../lib/motion';

interface StatCardProps {
  label: string;
  value: string | number;
  icon: ReactNode;
}

export function StatCard({ label, value, icon }: StatCardProps) {
  return (
    <motion.div
      variants={itemSlideUp}
      className="card flex flex-col items-center text-center gap-1 p-3 sm:flex-row sm:text-left sm:gap-3 sm:p-4"
    >
      <div className="w-8 h-8 sm:w-10 sm:h-10 rounded-xl bg-ember/10 flex items-center justify-center text-ember shrink-0 hidden sm:flex">
        {icon}
      </div>
      <div className="min-w-0">
        <p className="text-lg sm:text-xl font-bold font-mono text-chalk truncate">{value}</p>
        <p className="text-[10px] sm:text-xs text-steel truncate">{label}</p>
      </div>
    </motion.div>
  );
}
