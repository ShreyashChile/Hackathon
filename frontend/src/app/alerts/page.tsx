"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Sidebar } from "@/components/layout/Sidebar";
import { Header } from "@/components/layout/Header";
import { PageTransition } from "@/components/layout/PageTransition";
import { GlassCard, StatCard } from "@/components/ui/GlassCard";
import { PriorityBadge, Badge } from "@/components/ui/Badge";
import { AnimatedBarChart } from "@/components/charts/AnimatedBarChart";
import { TableSkeleton, ChartSkeleton } from "@/components/ui/LoadingSkeleton";
import { useAlerts } from "@/hooks/useAPI";
import {
  Bell,
  AlertTriangle,
  AlertCircle,
  Info,
  CheckCircle,
  Clock,
  Filter,
  X,
} from "lucide-react";
import { GlowButton, IconButton } from "@/components/ui/GlowButton";
import Link from "next/link";

const priorityIcons = {
  P1_CRITICAL: <AlertTriangle className="w-5 h-5" />,
  P2_HIGH: <AlertCircle className="w-5 h-5" />,
  P3_MEDIUM: <Info className="w-5 h-5" />,
  P4_LOW: <CheckCircle className="w-5 h-5" />,
  P5_INFO: <Info className="w-5 h-5" />,
};

const priorityColors = {
  P1_CRITICAL: "from-rose-500/20 to-rose-500/5 border-rose-500/30 text-rose-400",
  P2_HIGH: "from-amber-500/20 to-amber-500/5 border-amber-500/30 text-amber-400",
  P3_MEDIUM: "from-cyan-500/20 to-cyan-500/5 border-cyan-500/30 text-cyan-400",
  P4_LOW: "from-violet-500/20 to-violet-500/5 border-violet-500/30 text-violet-400",
  P5_INFO: "from-emerald-500/20 to-emerald-500/5 border-emerald-500/30 text-emerald-400",
};

export default function AlertsPage() {
  const [priorityFilter, setPriorityFilter] = useState<string | undefined>();
  const [activeOnly, setActiveOnly] = useState(true);
  const [expandedAlert, setExpandedAlert] = useState<string | null>(null);

  const { data: alerts, isLoading, refetch } = useAlerts({
    priority: priorityFilter,
    active_only: activeOnly,
  });

  // Calculate stats
  const stats = {
    total: alerts?.length || 0,
    critical: alerts?.filter((a) => a.priority === "P1_CRITICAL").length || 0,
    high: alerts?.filter((a) => a.priority === "P2_HIGH").length || 0,
    medium: alerts?.filter((a) => a.priority === "P3_MEDIUM").length || 0,
    low: alerts?.filter((a) => a.priority === "P4_LOW").length || 0,
  };

  const chartData = [
    { name: "Critical", value: stats.critical, color: "#f43f5e" },
    { name: "High", value: stats.high, color: "#f59e0b" },
    { name: "Medium", value: stats.medium, color: "#06b6d4" },
    { name: "Low", value: stats.low, color: "#8b5cf6" },
  ];

  return (
    <div className="flex min-h-screen">
      <Sidebar />

      <main className="flex-1 ml-64 p-6">
        <Header
          title="Alert Center"
          subtitle="Monitor and manage inventory alerts"
          onRefresh={refetch}
          isRefreshing={isLoading}
        />

        <PageTransition>
          {/* Stats Row */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4 mb-6">
            <StatCard
              title="Total Alerts"
              value={stats.total}
              icon={<Bell className="w-6 h-6" />}
              color="cyan"
              delay={0}
            />
            <StatCard
              title="Critical"
              value={stats.critical}
              icon={<AlertTriangle className="w-6 h-6" />}
              color="rose"
              delay={0.1}
            />
            <StatCard
              title="High"
              value={stats.high}
              icon={<AlertCircle className="w-6 h-6" />}
              color="amber"
              delay={0.2}
            />
            <StatCard
              title="Medium"
              value={stats.medium}
              icon={<Info className="w-6 h-6" />}
              color="cyan"
              delay={0.3}
            />
            <StatCard
              title="Low"
              value={stats.low}
              icon={<CheckCircle className="w-6 h-6" />}
              color="violet"
              delay={0.4}
            />
          </div>

          <div className="grid grid-cols-1 xl:grid-cols-3 gap-6 mb-6">
            {/* Chart */}
            <div>
              {isLoading ? (
                <ChartSkeleton height={280} />
              ) : (
                <AnimatedBarChart
                  data={chartData}
                  title="Alerts by Priority"
                  height={230}
                />
              )}
            </div>

            {/* Filters */}
            <div className="xl:col-span-2">
              <GlassCard className="p-6 h-full" hover={false}>
                <h3 className="text-lg font-semibold text-white mb-4">Filters</h3>

                <div className="flex flex-wrap gap-4 items-end">
                  <div>
                    <label className="text-sm text-white/60 mb-2 block">Priority</label>
                    <select
                      value={priorityFilter || ""}
                      onChange={(e) => setPriorityFilter(e.target.value || undefined)}
                      className="bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-white
                               focus:outline-none focus:border-cyan-500/50 min-w-[150px]"
                    >
                      <option value="">All Priorities</option>
                      <option value="P1_CRITICAL">Critical</option>
                      <option value="P2_HIGH">High</option>
                      <option value="P3_MEDIUM">Medium</option>
                      <option value="P4_LOW">Low</option>
                      <option value="P5_INFO">Info</option>
                    </select>
                  </div>

                  <div>
                    <label className="text-sm text-white/60 mb-2 block">Status</label>
                    <div className="flex gap-2">
                      <GlowButton
                        variant={activeOnly ? "primary" : "secondary"}
                        size="md"
                        onClick={() => setActiveOnly(true)}
                      >
                        Active
                      </GlowButton>
                      <GlowButton
                        variant={!activeOnly ? "primary" : "secondary"}
                        size="md"
                        onClick={() => setActiveOnly(false)}
                      >
                        All
                      </GlowButton>
                    </div>
                  </div>

                  <GlowButton
                    variant="secondary"
                    size="md"
                    onClick={() => {
                      setPriorityFilter(undefined);
                      setActiveOnly(true);
                    }}
                    className="ml-auto"
                  >
                    Clear Filters
                  </GlowButton>
                </div>
              </GlassCard>
            </div>
          </div>

          {/* Alert List */}
          <GlassCard className="p-6" hover={false}>
            <h3 className="text-lg font-semibold text-white mb-4">Alert Feed</h3>

            {isLoading ? (
              <div className="space-y-4">
                {[...Array(5)].map((_, i) => (
                  <div key={i} className="h-24 skeleton rounded-xl" />
                ))}
              </div>
            ) : (
              <div className="space-y-3">
                <AnimatePresence>
                  {alerts?.map((alert, index) => (
                    <motion.div
                      key={alert.alert_id}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, x: -20 }}
                      transition={{ delay: index * 0.05 }}
                      layout
                    >
                      <motion.div
                        className={`
                          p-4 rounded-xl border cursor-pointer
                          bg-gradient-to-r ${priorityColors[alert.priority]}
                          hover:scale-[1.01] transition-transform
                        `}
                        onClick={() =>
                          setExpandedAlert(
                            expandedAlert === alert.alert_id ? null : alert.alert_id
                          )
                        }
                      >
                        <div className="flex items-start gap-4">
                          {/* Icon */}
                          <div className="p-2 rounded-lg bg-white/10">
                            {priorityIcons[alert.priority]}
                          </div>

                          {/* Content */}
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 mb-1">
                              <Link
                                href={`/sku/${alert.item_id}`}
                                className="font-semibold text-white hover:text-cyan-400 transition-colors"
                                onClick={(e) => e.stopPropagation()}
                              >
                                {alert.item_id}
                              </Link>
                              <PriorityBadge priority={alert.priority} />
                              {!alert.is_active && (
                                <Badge variant="default">Resolved</Badge>
                              )}
                            </div>
                            <p className="text-white/80">{alert.message}</p>
                            <div className="flex items-center gap-4 mt-2 text-sm text-white/50">
                              <span className="flex items-center gap-1">
                                <Clock className="w-3 h-3" />
                                {new Date(alert.created_at).toLocaleString()}
                              </span>
                              <span>{alert.location_id}</span>
                              <Badge variant="info" size="sm">
                                {alert.alert_type}
                              </Badge>
                            </div>

                            {/* Expanded content */}
                            <AnimatePresence>
                              {expandedAlert === alert.alert_id && (
                                <motion.div
                                  initial={{ height: 0, opacity: 0 }}
                                  animate={{ height: "auto", opacity: 1 }}
                                  exit={{ height: 0, opacity: 0 }}
                                  className="overflow-hidden"
                                >
                                  <div className="mt-4 pt-4 border-t border-white/10">
                                    <div className="flex gap-2">
                                      <Link href={`/sku/${alert.item_id}`}>
                                        <GlowButton size="sm">View SKU</GlowButton>
                                      </Link>
                                      <GlowButton variant="secondary" size="sm">
                                        Acknowledge
                                      </GlowButton>
                                      <GlowButton variant="success" size="sm">
                                        Resolve
                                      </GlowButton>
                                    </div>
                                  </div>
                                </motion.div>
                              )}
                            </AnimatePresence>
                          </div>

                          {/* Expand icon */}
                          <motion.div
                            animate={{
                              rotate: expandedAlert === alert.alert_id ? 45 : 0,
                            }}
                          >
                            <X className="w-5 h-5 text-white/30" />
                          </motion.div>
                        </div>
                      </motion.div>
                    </motion.div>
                  ))}
                </AnimatePresence>

                {alerts?.length === 0 && (
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="text-center py-12"
                  >
                    <CheckCircle className="w-16 h-16 text-emerald-400/50 mx-auto mb-4" />
                    <p className="text-white/60 text-lg">No alerts to display</p>
                    <p className="text-white/40 text-sm mt-1">
                      All systems operating normally
                    </p>
                  </motion.div>
                )}
              </div>
            )}
          </GlassCard>
        </PageTransition>
      </main>
    </div>
  );
}

