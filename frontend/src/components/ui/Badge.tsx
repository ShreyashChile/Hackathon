"use client";

import { motion } from "framer-motion";
import { ReactNode } from "react";

type BadgeVariant = "critical" | "warning" | "success" | "info" | "default";
type BadgeSize = "sm" | "md" | "lg";

interface BadgeProps {
  children: ReactNode;
  variant?: BadgeVariant;
  size?: BadgeSize;
  pulse?: boolean;
  icon?: ReactNode;
  className?: string;
}

const variantStyles: Record<BadgeVariant, string> = {
  critical: "bg-rose-500/20 text-rose-400 border-rose-500/30",
  warning: "bg-amber-500/20 text-amber-400 border-amber-500/30",
  success: "bg-emerald-500/20 text-emerald-400 border-emerald-500/30",
  info: "bg-cyan-500/20 text-cyan-400 border-cyan-500/30",
  default: "bg-white/10 text-white/70 border-white/20",
};

const sizeStyles: Record<BadgeSize, string> = {
  sm: "px-2 py-0.5 text-xs",
  md: "px-3 py-1 text-xs",
  lg: "px-4 py-1.5 text-sm",
};

export function Badge({
  children,
  variant = "default",
  size = "md",
  pulse = false,
  icon,
  className = "",
}: BadgeProps) {
  return (
    <motion.span
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      className={`
        inline-flex items-center gap-1.5 rounded-full border font-semibold
        ${variantStyles[variant]}
        ${sizeStyles[size]}
        ${className}
      `}
    >
      {pulse && (
        <span className="relative flex h-2 w-2">
          <span
            className={`
              animate-ping absolute inline-flex h-full w-full rounded-full opacity-75
              ${variant === "critical" ? "bg-rose-400" : ""}
              ${variant === "warning" ? "bg-amber-400" : ""}
              ${variant === "success" ? "bg-emerald-400" : ""}
              ${variant === "info" ? "bg-cyan-400" : ""}
              ${variant === "default" ? "bg-white/50" : ""}
            `}
          />
          <span
            className={`
              relative inline-flex rounded-full h-2 w-2
              ${variant === "critical" ? "bg-rose-500" : ""}
              ${variant === "warning" ? "bg-amber-500" : ""}
              ${variant === "success" ? "bg-emerald-500" : ""}
              ${variant === "info" ? "bg-cyan-500" : ""}
              ${variant === "default" ? "bg-white/70" : ""}
            `}
          />
        </span>
      )}
      {icon}
      {children}
    </motion.span>
  );
}

// Priority badge specific for alerts
interface PriorityBadgeProps {
  priority: "P1_CRITICAL" | "P2_HIGH" | "P3_MEDIUM" | "P4_LOW" | "P5_INFO";
}

const priorityConfig: Record<
  PriorityBadgeProps["priority"],
  { label: string; variant: BadgeVariant }
> = {
  P1_CRITICAL: { label: "Critical", variant: "critical" },
  P2_HIGH: { label: "High", variant: "warning" },
  P3_MEDIUM: { label: "Medium", variant: "info" },
  P4_LOW: { label: "Low", variant: "default" },
  P5_INFO: { label: "Info", variant: "success" },
};

export function PriorityBadge({ priority }: PriorityBadgeProps) {
  const config = priorityConfig[priority];
  return (
    <Badge variant={config.variant} pulse={priority === "P1_CRITICAL"}>
      {config.label}
    </Badge>
  );
}

// Movement status badge
interface MovementBadgeProps {
  status: "ACTIVE" | "SLOW_MOVING" | "NON_MOVING" | "DEAD_STOCK";
}

const movementConfig: Record<
  MovementBadgeProps["status"],
  { label: string; variant: BadgeVariant }
> = {
  ACTIVE: { label: "Active", variant: "success" },
  SLOW_MOVING: { label: "Slow Moving", variant: "warning" },
  NON_MOVING: { label: "Non-Moving", variant: "critical" },
  DEAD_STOCK: { label: "Dead Stock", variant: "critical" },
};

export function MovementBadge({ status }: MovementBadgeProps) {
  const config = movementConfig[status];
  return (
    <Badge
      variant={config.variant}
      pulse={status === "DEAD_STOCK" || status === "NON_MOVING"}
    >
      {config.label}
    </Badge>
  );
}

