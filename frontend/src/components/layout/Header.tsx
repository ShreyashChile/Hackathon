"use client";

import { motion } from "framer-motion";
import { Bell, Search, RefreshCw, User } from "lucide-react";
import { useState } from "react";
import { IconButton } from "../ui/GlowButton";

interface HeaderProps {
  title: string;
  subtitle?: string;
  onRefresh?: () => void;
  isRefreshing?: boolean;
}

export function Header({
  title,
  subtitle,
  onRefresh,
  isRefreshing = false,
}: HeaderProps) {
  const [searchOpen, setSearchOpen] = useState(false);

  return (
    <motion.header
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="glass sticky top-0 z-30 px-6 py-4 mb-6 flex items-center justify-between"
    >
      {/* Title */}
      <div>
        <motion.h1
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.1 }}
          className="text-2xl font-bold text-white"
        >
          {title}
        </motion.h1>
        {subtitle && (
          <motion.p
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.2 }}
            className="text-sm text-white/50 mt-0.5"
          >
            {subtitle}
          </motion.p>
        )}
      </div>

      {/* Actions */}
      <div className="flex items-center gap-2">
        {/* Search */}
        <motion.div
          animate={{ width: searchOpen ? 250 : 44 }}
          className="relative overflow-hidden"
        >
          {searchOpen && (
            <motion.input
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              type="text"
              placeholder="Search SKUs..."
              className="w-full px-4 py-2.5 pr-10 bg-white/5 border border-white/10 rounded-xl 
                       text-white placeholder-white/40 focus:outline-none focus:border-cyan-500/50
                       transition-colors"
              autoFocus
              onBlur={() => setSearchOpen(false)}
            />
          )}
          <IconButton
            icon={<Search className="w-5 h-5" />}
            onClick={() => setSearchOpen(!searchOpen)}
            className={searchOpen ? "absolute right-1 top-1/2 -translate-y-1/2" : ""}
          />
        </motion.div>

        {/* Refresh */}
        {onRefresh && (
          <IconButton
            icon={
              <motion.div
                animate={isRefreshing ? { rotate: 360 } : { rotate: 0 }}
                transition={
                  isRefreshing
                    ? { duration: 1, repeat: Infinity, ease: "linear" }
                    : {}
                }
              >
                <RefreshCw className="w-5 h-5" />
              </motion.div>
            }
            onClick={onRefresh}
            tooltip="Refresh data"
          />
        )}

        {/* Notifications */}
        <div className="relative">
          <IconButton
            icon={<Bell className="w-5 h-5" />}
            tooltip="Notifications"
          />
          <motion.span
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            className="absolute -top-1 -right-1 w-5 h-5 bg-rose-500 rounded-full 
                     flex items-center justify-center text-xs font-bold text-white"
          >
            3
          </motion.span>
        </div>

        {/* Divider */}
        <div className="w-px h-8 bg-white/10 mx-2" />

        {/* User */}
        <motion.div
          whileHover={{ scale: 1.05 }}
          className="flex items-center gap-3 px-3 py-2 rounded-xl bg-white/5 
                   hover:bg-white/10 transition-colors cursor-pointer"
        >
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-violet-500 to-cyan-500 
                        flex items-center justify-center">
            <User className="w-4 h-4 text-white" />
          </div>
          <span className="text-sm font-medium text-white/80">Admin</span>
        </motion.div>
      </div>
    </motion.header>
  );
}

