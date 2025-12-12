"use client";

import { motion } from "framer-motion";
import { ReactNode } from "react";

interface GlowButtonProps {
  children: ReactNode;
  onClick?: () => void;
  variant?: "primary" | "secondary" | "danger" | "success";
  size?: "sm" | "md" | "lg";
  className?: string;
  disabled?: boolean;
  loading?: boolean;
  icon?: ReactNode;
}

const variantStyles = {
  primary: {
    bg: "from-violet-600 to-cyan-500",
    glow: "rgba(139, 92, 246, 0.4)",
    hover: "rgba(6, 182, 212, 0.4)",
  },
  secondary: {
    bg: "from-gray-600 to-gray-500",
    glow: "rgba(107, 114, 128, 0.3)",
    hover: "rgba(156, 163, 175, 0.4)",
  },
  danger: {
    bg: "from-rose-600 to-red-500",
    glow: "rgba(244, 63, 94, 0.4)",
    hover: "rgba(239, 68, 68, 0.4)",
  },
  success: {
    bg: "from-emerald-600 to-green-500",
    glow: "rgba(16, 185, 129, 0.4)",
    hover: "rgba(34, 197, 94, 0.4)",
  },
};

const sizeStyles = {
  sm: "px-4 py-2 text-sm",
  md: "px-6 py-3 text-base",
  lg: "px-8 py-4 text-lg",
};

export function GlowButton({
  children,
  onClick,
  variant = "primary",
  size = "md",
  className = "",
  disabled = false,
  loading = false,
  icon,
}: GlowButtonProps) {
  const style = variantStyles[variant];

  return (
    <motion.button
      onClick={onClick}
      disabled={disabled || loading}
      whileHover={{ scale: disabled ? 1 : 1.02, y: disabled ? 0 : -2 }}
      whileTap={{ scale: disabled ? 1 : 0.98 }}
      className={`
        relative overflow-hidden rounded-xl font-semibold
        bg-gradient-to-r ${style.bg}
        ${sizeStyles[size]}
        ${disabled ? "opacity-50 cursor-not-allowed" : "cursor-pointer"}
        ${className}
        text-white shadow-lg
        transition-shadow duration-300
      `}
      style={{
        boxShadow: `0 4px 20px ${style.glow}`,
      }}
    >
      {/* Animated shine effect */}
      <motion.div
        className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent"
        initial={{ x: "-100%" }}
        whileHover={{ x: "100%" }}
        transition={{ duration: 0.6, ease: "easeInOut" }}
      />

      {/* Content */}
      <span className="relative flex items-center justify-center gap-2">
        {loading ? (
          <motion.div
            className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full"
            animate={{ rotate: 360 }}
            transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
          />
        ) : (
          <>
            {icon}
            {children}
          </>
        )}
      </span>
    </motion.button>
  );
}

// Icon button variant
interface IconButtonProps {
  icon: ReactNode;
  onClick?: () => void;
  color?: "cyan" | "violet" | "rose" | "emerald" | "default";
  size?: "sm" | "md" | "lg";
  className?: string;
  tooltip?: string;
}

const iconColorStyles = {
  cyan: "text-cyan-400 hover:bg-cyan-500/20 hover:text-cyan-300",
  violet: "text-violet-400 hover:bg-violet-500/20 hover:text-violet-300",
  rose: "text-rose-400 hover:bg-rose-500/20 hover:text-rose-300",
  emerald: "text-emerald-400 hover:bg-emerald-500/20 hover:text-emerald-300",
  default: "text-white/60 hover:bg-white/10 hover:text-white",
};

const iconSizeStyles = {
  sm: "p-2",
  md: "p-3",
  lg: "p-4",
};

export function IconButton({
  icon,
  onClick,
  color = "default",
  size = "md",
  className = "",
  tooltip,
}: IconButtonProps) {
  return (
    <motion.button
      onClick={onClick}
      whileHover={{ scale: 1.1 }}
      whileTap={{ scale: 0.95 }}
      title={tooltip}
      className={`
        rounded-xl transition-colors duration-200
        ${iconColorStyles[color]}
        ${iconSizeStyles[size]}
        ${className}
      `}
    >
      {icon}
    </motion.button>
  );
}

