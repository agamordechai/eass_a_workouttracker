import type { Variants, Transition } from 'framer-motion';

export const pageVariants: Variants = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -10 },
};

export const pageTransition: Transition = {
  duration: 0.3,
  ease: [0.25, 0.1, 0.25, 1],
};

export const containerStagger: Variants = {
  animate: {
    transition: { staggerChildren: 0.04 },
  },
};

export const itemSlideUp: Variants = {
  initial: { opacity: 0, y: 16 },
  animate: { opacity: 1, y: 0, transition: { duration: 0.3 } },
};

export const tapScale = { scale: 0.97 };

export const expandCollapse: Variants = {
  collapsed: { height: 0, opacity: 0, overflow: 'hidden' },
  expanded: { height: 'auto', opacity: 1, overflow: 'hidden' },
};

export const navSpring: Transition = {
  type: 'spring',
  stiffness: 400,
  damping: 30,
};
