"use client";

import { motion, Variants } from "framer-motion";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  TrendingUp,
  Package,
  Grid3X3,
  Bell,
  Settings,
  Boxes,
  Activity,
} from "lucide-react";

const navItems = [
  {
    name: "Dashboard",
    href: "/",
    icon: LayoutDashboard,
  },
  {
    name: "Demand Shifts",
    href: "/demand-shifts",
    icon: TrendingUp,
  },
  {
    name: "Non-Moving",
    href: "/non-moving",
    icon: Package,
  },
  {
    name: "Segmentation",
    href: "/segmentation",
    icon: Grid3X3,
  },
  {
    name: "Alerts",
    href: "/alerts",
    icon: Bell,
  },
];

const sidebarVariants: Variants = {
  hidden: { x: -280, opacity: 0 },
  visible: {
    x: 0,
    opacity: 1,
    transition: {
      type: "spring" as const,
      stiffness: 100,
      damping: 20,
      staggerChildren: 0.1,
      delayChildren: 0.2,
    },
  },
};

const itemVariants: Variants = {
  hidden: { x: -20, opacity: 0 },
  visible: { x: 0, opacity: 1 },
};

export function Sidebar() {
  const pathname = usePathname();

  return (
    <motion.aside
      initial="hidden"
      animate="visible"
      variants={sidebarVariants}
      className="sidebar fixed left-0 top-0 bottom-0 w-64 z-40 flex flex-col"
    >
      {/* Logo */}
      <motion.div
        variants={itemVariants}
        className="p-6 border-b border-white/5"
      >
        <Link href="/" className="flex items-center gap-3 group">
          <motion.div
            whileHover={{ rotate: 180, scale: 1.1 }}
            transition={{ duration: 0.5 }}
            className="p-2 rounded-xl bg-gradient-to-br from-violet-500/20 to-cyan-500/20 border border-white/10"
          >
            <Boxes className="w-6 h-6 text-cyan-400" />
          </motion.div>
          <div>
            <h1 className="text-lg font-bold text-white group-hover:text-cyan-400 transition-colors">
              ML Inventory
            </h1>
            <p className="text-xs text-white/40">Agent Dashboard</p>
          </div>
        </Link>
      </motion.div>

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-1">
        {navItems.map((item, index) => {
          const isActive = pathname === item.href;
          const Icon = item.icon;

          return (
            <motion.div key={item.href} variants={itemVariants}>
              <Link href={item.href}>
                <motion.div
                  whileHover={{ x: 4 }}
                  whileTap={{ scale: 0.98 }}
                  className={`nav-item ${isActive ? "active" : ""}`}
                >
                  <motion.div
                    animate={
                      isActive
                        ? {
                            scale: [1, 1.2, 1],
                            transition: { duration: 0.3 },
                          }
                        : {}
                    }
                  >
                    <Icon
                      className={`w-5 h-5 ${
                        isActive ? "text-cyan-400" : "text-white/50"
                      }`}
                    />
                  </motion.div>
                  <span
                    className={`font-medium ${
                      isActive ? "text-white" : "text-white/70"
                    }`}
                  >
                    {item.name}
                  </span>

                  {/* Active indicator dot */}
                  {isActive && (
                    <motion.div
                      layoutId="activeNav"
                      className="absolute right-4 w-2 h-2 rounded-full bg-cyan-400"
                      initial={false}
                      transition={{
                        type: "spring",
                        stiffness: 500,
                        damping: 30,
                      }}
                    />
                  )}
                </motion.div>
              </Link>
            </motion.div>
          );
        })}
      </nav>

      {/* Status indicator */}
      <motion.div variants={itemVariants} className="p-4 border-t border-white/5">
        <div className="glass rounded-xl p-4">
          <div className="flex items-center gap-3">
            <div className="relative">
              <Activity className="w-5 h-5 text-emerald-400" />
              <span className="absolute -top-1 -right-1 w-2 h-2 bg-emerald-400 rounded-full animate-pulse" />
            </div>
            <div>
              <p className="text-sm font-medium text-white">System Active</p>
              <p className="text-xs text-white/40">API Connected</p>
            </div>
          </div>
        </div>
      </motion.div>

      {/* Settings */}
      <motion.div variants={itemVariants} className="p-4">
        <Link href="/settings">
          <motion.div
            whileHover={{ x: 4 }}
            whileTap={{ scale: 0.98 }}
            className="nav-item"
          >
            <Settings className="w-5 h-5 text-white/50" />
            <span className="font-medium text-white/70">Settings</span>
          </motion.div>
        </Link>
      </motion.div>
    </motion.aside>
  );
}

