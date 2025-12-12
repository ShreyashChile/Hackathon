"use client";

import { motion } from "framer-motion";

interface SkeletonProps {
  className?: string;
  variant?: "text" | "circular" | "rectangular";
  width?: string | number;
  height?: string | number;
}

export function Skeleton({
  className = "",
  variant = "rectangular",
  width,
  height,
}: SkeletonProps) {
  const baseStyles = "skeleton";
  const variantStyles = {
    text: "rounded",
    circular: "rounded-full",
    rectangular: "rounded-xl",
  };

  return (
    <div
      className={`${baseStyles} ${variantStyles[variant]} ${className}`}
      style={{
        width: width,
        height: height || (variant === "text" ? "1em" : undefined),
      }}
    />
  );
}

// Card skeleton
export function CardSkeleton() {
  return (
    <div className="glass-card p-6 space-y-4">
      <div className="flex items-center justify-between">
        <Skeleton width={120} height={16} variant="text" />
        <Skeleton width={40} height={40} variant="circular" />
      </div>
      <Skeleton width={80} height={32} variant="text" />
      <Skeleton width="100%" height={8} variant="text" />
    </div>
  );
}

// Chart skeleton
export function ChartSkeleton({ height = 300 }: { height?: number }) {
  return (
    <div className="glass-card p-6">
      <Skeleton width={150} height={20} variant="text" className="mb-4" />
      <div
        className="flex items-end gap-2 justify-around"
        style={{ height: height - 60 }}
      >
        {[40, 65, 45, 80, 55, 70, 50].map((h, i) => (
          <motion.div
            key={i}
            initial={{ height: 0 }}
            animate={{ height: `${h}%` }}
            transition={{ duration: 0.5, delay: i * 0.1 }}
          >
            <Skeleton width={40} height="100%" />
          </motion.div>
        ))}
      </div>
    </div>
  );
}

// Table skeleton
export function TableSkeleton({ rows = 5 }: { rows?: number }) {
  return (
    <div className="glass-card overflow-hidden">
      {/* Header */}
      <div className="flex gap-4 p-4 border-b border-white/10">
        {[100, 150, 120, 80, 100].map((w, i) => (
          <Skeleton key={i} width={w} height={12} variant="text" />
        ))}
      </div>
      {/* Rows */}
      {Array.from({ length: rows }).map((_, rowIndex) => (
        <div
          key={rowIndex}
          className="flex gap-4 p-4 border-b border-white/5 last:border-b-0"
        >
          {[100, 150, 120, 80, 100].map((w, i) => (
            <Skeleton key={i} width={w} height={16} variant="text" />
          ))}
        </div>
      ))}
    </div>
  );
}

// Full page loading
export function PageLoader() {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-50 flex items-center justify-center bg-[#0f0f23]/80 backdrop-blur-sm"
    >
      <div className="text-center">
        <motion.div
          className="w-16 h-16 border-4 border-violet-500/30 border-t-violet-500 rounded-full mx-auto"
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
        />
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3 }}
          className="mt-4 text-white/60 font-medium"
        >
          Loading...
        </motion.p>
      </div>
    </motion.div>
  );
}

// Inline spinner
export function Spinner({ size = 24 }: { size?: number }) {
  return (
    <motion.div
      className="border-2 border-white/20 border-t-white rounded-full"
      style={{ width: size, height: size }}
      animate={{ rotate: 360 }}
      transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
    />
  );
}

