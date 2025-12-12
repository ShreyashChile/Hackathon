"use client";

import { motion, AnimatePresence } from "framer-motion";
import { AlertTriangle, AlertCircle, Info, CheckCircle, Clock } from "lucide-react";
import { GlassCard } from "../ui/GlassCard";
import { PriorityBadge } from "../ui/Badge";
import type { Alert } from "@/lib/api";

interface AlertsFeedProps {
  alerts: Alert[];
  maxItems?: number;
  title?: string;
}

const priorityIcons = {
  P1_CRITICAL: <AlertTriangle className="w-5 h-5" />,
  P2_HIGH: <AlertCircle className="w-5 h-5" />,
  P3_MEDIUM: <Info className="w-5 h-5" />,
  P4_LOW: <CheckCircle className="w-5 h-5" />,
  P5_INFO: <Info className="w-5 h-5" />,
};

const priorityColors = {
  P1_CRITICAL: "text-rose-400 bg-rose-500/20",
  P2_HIGH: "text-amber-400 bg-amber-500/20",
  P3_MEDIUM: "text-cyan-400 bg-cyan-500/20",
  P4_LOW: "text-white/60 bg-white/10",
  P5_INFO: "text-emerald-400 bg-emerald-500/20",
};

export function AlertsFeed({ alerts, maxItems = 5, title = "Recent Alerts" }: AlertsFeedProps) {
  const displayAlerts = alerts.slice(0, maxItems);

  return (
    <GlassCard className="p-6 h-full" hover={false}>
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-white">{title}</h3>
        {alerts.length > maxItems && (
          <span className="text-sm text-white/50">
            +{alerts.length - maxItems} more
          </span>
        )}
      </div>

      <div className="space-y-3">
        <AnimatePresence mode="popLayout">
          {displayAlerts.map((alert, index) => (
            <motion.div
              key={alert.alert_id}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              transition={{ delay: index * 0.1 }}
              className="group"
            >
              <div className="flex items-start gap-3 p-3 rounded-xl bg-white/5 hover:bg-white/10 transition-all cursor-pointer">
                {/* Icon */}
                <div
                  className={`p-2 rounded-lg shrink-0 ${priorityColors[alert.priority]}`}
                >
                  {priorityIcons[alert.priority]}
                </div>

                {/* Content */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-sm font-medium text-white truncate">
                      {alert.item_id}
                    </span>
                    <PriorityBadge priority={alert.priority} />
                  </div>
                  <p className="text-sm text-white/60 line-clamp-2">
                    {alert.message}
                  </p>
                  <div className="flex items-center gap-2 mt-2">
                    <Clock className="w-3 h-3 text-white/40" />
                    <span className="text-xs text-white/40">
                      {new Date(alert.created_at).toLocaleString()}
                    </span>
                    <span className="text-xs text-white/30">•</span>
                    <span className="text-xs text-white/40">{alert.location_id}</span>
                  </div>
                </div>

                {/* Hover indicator */}
                <motion.div
                  initial={{ opacity: 0 }}
                  whileHover={{ opacity: 1 }}
                  className="w-1 h-full rounded-full bg-gradient-to-b from-cyan-500 to-violet-500 opacity-0 group-hover:opacity-100 transition-opacity"
                />
              </div>
            </motion.div>
          ))}
        </AnimatePresence>

        {alerts.length === 0 && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="text-center py-8"
          >
            <CheckCircle className="w-12 h-12 text-emerald-400/50 mx-auto mb-3" />
            <p className="text-white/50">No active alerts</p>
          </motion.div>
        )}
      </div>
    </GlassCard>
  );
}

// Compact alert item for lists
export function AlertItem({ alert }: { alert: Alert }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ x: 4 }}
      className="flex items-center gap-3 p-2 rounded-lg hover:bg-white/5 transition-colors cursor-pointer"
    >
      <div className={`p-1.5 rounded ${priorityColors[alert.priority]}`}>
        {priorityIcons[alert.priority]}
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm text-white truncate">{alert.message}</p>
        <p className="text-xs text-white/40">{alert.item_id}</p>
      </div>
      <PriorityBadge priority={alert.priority} />
    </motion.div>
  );
}

