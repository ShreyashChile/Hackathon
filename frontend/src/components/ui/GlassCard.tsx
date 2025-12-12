"use client";

import { motion } from "framer-motion";
import { ReactNode } from "react";

interface GlassCardProps {
  children: ReactNode;
  className?: string;
  hover?: boolean;
  glow?: boolean;
  delay?: number;
  onClick?: () => void;
}

export function GlassCard({
  children,
  className = "",
  hover = true,
  glow = false,
  delay = 0,
  onClick,
}: GlassCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{
        duration: 0.5,
        delay,
        ease: [0.4, 0, 0.2, 1],
      }}
      whileHover={
        hover
          ? {
              y: -4,
              scale: 1.01,
              transition: { duration: 0.3 },
            }
          : undefined
      }
      onClick={onClick}
      className={`
        glass-card 
        ${glow ? "glass-card-glow" : ""} 
        ${onClick ? "cursor-pointer" : ""}
        ${className}
      `}
    >
      {children}
    </motion.div>
  );
}

// Variant for KPI/stat cards with icon
interface StatCardProps {
  title: string;
  value: string | number;
  icon: ReactNode;
  trend?: {
    value: number;
    isPositive: boolean;
  };
  color?: "cyan" | "violet" | "rose" | "emerald" | "amber";
  delay?: number;
}

const colorMap = {
  cyan: "from-cyan-500/20 to-cyan-500/5 border-cyan-500/30",
  violet: "from-violet-500/20 to-violet-500/5 border-violet-500/30",
  rose: "from-rose-500/20 to-rose-500/5 border-rose-500/30",
  emerald: "from-emerald-500/20 to-emerald-500/5 border-emerald-500/30",
  amber: "from-amber-500/20 to-amber-500/5 border-amber-500/30",
};

const iconColorMap = {
  cyan: "text-cyan-400 bg-cyan-500/20",
  violet: "text-violet-400 bg-violet-500/20",
  rose: "text-rose-400 bg-rose-500/20",
  emerald: "text-emerald-400 bg-emerald-500/20",
  amber: "text-amber-400 bg-amber-500/20",
};

export function StatCard({
  title,
  value,
  icon,
  trend,
  color = "cyan",
  delay = 0,
}: StatCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay, ease: [0.4, 0, 0.2, 1] }}
      whileHover={{ y: -4, transition: { duration: 0.3 } }}
      className={`
        relative overflow-hidden rounded-2xl p-6
        bg-gradient-to-br ${colorMap[color]}
        border backdrop-blur-xl
      `}
    >
      {/* Background glow */}
      <div
        className={`
          absolute -top-12 -right-12 w-32 h-32 rounded-full blur-3xl opacity-30
          ${color === "cyan" ? "bg-cyan-500" : ""}
          ${color === "violet" ? "bg-violet-500" : ""}
          ${color === "rose" ? "bg-rose-500" : ""}
          ${color === "emerald" ? "bg-emerald-500" : ""}
          ${color === "amber" ? "bg-amber-500" : ""}
        `}
      />

      <div className="relative flex items-start justify-between">
        <div>
          <p className="text-sm text-white/60 font-medium mb-1">{title}</p>
          <p className="text-3xl font-bold text-white">{value}</p>
          {trend && (
            <div className="flex items-center gap-1 mt-2">
              <span
                className={`text-sm font-medium ${
                  trend.isPositive ? "text-emerald-400" : "text-rose-400"
                }`}
              >
                {trend.isPositive ? "↑" : "↓"} {Math.abs(trend.value)}%
              </span>
              <span className="text-xs text-white/40">vs last week</span>
            </div>
          )}
        </div>
        <div className={`p-3 rounded-xl ${iconColorMap[color]}`}>{icon}</div>
      </div>
    </motion.div>
  );
}

