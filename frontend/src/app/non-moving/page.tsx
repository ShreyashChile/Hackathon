"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Sidebar } from "@/components/layout/Sidebar";
import { Header } from "@/components/layout/Header";
import { PageTransition } from "@/components/layout/PageTransition";
import { GlassCard, StatCard } from "@/components/ui/GlassCard";
import { MovementBadge } from "@/components/ui/Badge";
import { DonutChart } from "@/components/charts/AnimatedPieChart";
import { AnimatedBarChart } from "@/components/charts/AnimatedBarChart";
import { TableSkeleton, ChartSkeleton } from "@/components/ui/LoadingSkeleton";
import { useNonMoving } from "@/hooks/useAPI";
import { Package, Clock, DollarSign, AlertTriangle, Filter, Download } from "lucide-react";
import { GlowButton, IconButton } from "@/components/ui/GlowButton";
import { AnimatedCounter } from "@/components/ui/AnimatedCounter";
import Link from "next/link";

export default function NonMovingPage() {
  const [locationFilter, setLocationFilter] = useState<string | undefined>();
  const [categoryFilter, setCategoryFilter] = useState<string | undefined>();

  const { data: items, isLoading, refetch } = useNonMoving({
    location: locationFilter,
    category: categoryFilter,
  });

  // Calculate stats - using lowercase category names from API
  const stats = {
    total: items?.length || 0,
    slowMoving: items?.filter((i) => i.movement_category === "slow_moving").length || 0,
    nonMoving: items?.filter((i) => i.movement_category === "non_moving").length || 0,
    deadStock: items?.filter((i) => i.movement_category === "dead_stock").length || 0,
    totalValue: items?.reduce((sum, i) => sum + (i.non_moving_risk_score || 0), 0) || 0,
  };

  const categoryData = [
    { name: "Active", value: items?.filter((i) => i.movement_category === "active").length || 0, color: "#10b981" },
    { name: "Slow Moving", value: stats.slowMoving, color: "#06b6d4" },
    { name: "Non-Moving", value: stats.nonMoving, color: "#f59e0b" },
    { name: "Dead Stock", value: stats.deadStock, color: "#f43f5e" },
  ];

  const locations = [...new Set(items?.map((i) => i.location_id) || [])];

  // Group by location for bar chart
  const locationData = locations.map((loc) => ({
    name: loc,
    value: items?.filter((i) => i.location_id === loc && i.movement_category !== "active").length || 0,
  }));

  return (
    <div className="flex min-h-screen">
      <Sidebar />

      <main className="flex-1 ml-64 p-6">
        <Header
          title="Non-Moving Inventory"
          subtitle="Identify slow-moving and dead stock items"
          onRefresh={refetch}
          isRefreshing={isLoading}
        />

        <PageTransition>
          {/* Stats Row */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            <StatCard
              title="Total Items"
              value={stats.total}
              icon={<Package className="w-6 h-6" />}
              color="cyan"
              delay={0}
            />
            <StatCard
              title="Slow Moving"
              value={stats.slowMoving}
              icon={<Clock className="w-6 h-6" />}
              color="amber"
              delay={0.1}
            />
            <StatCard
              title="Dead Stock"
              value={stats.deadStock}
              icon={<AlertTriangle className="w-6 h-6" />}
              color="rose"
              delay={0.2}
            />
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
              className="relative overflow-hidden rounded-2xl p-6 bg-gradient-to-br from-violet-500/20 to-violet-500/5 border border-violet-500/30 backdrop-blur-xl"
            >
              <div className="absolute -top-12 -right-12 w-32 h-32 rounded-full blur-3xl opacity-30 bg-violet-500" />
              <div className="relative">
                <p className="text-sm text-white/60 font-medium mb-1">At Risk Value</p>
                <p className="text-3xl font-bold text-white">
                  $<AnimatedCounter value={stats.totalValue} decimals={0} />
                </p>
              </div>
              <DollarSign className="absolute top-4 right-4 w-8 h-8 text-violet-400/50" />
            </motion.div>
          </div>

          <div className="grid grid-cols-1 xl:grid-cols-3 gap-6 mb-6">
            {/* Category Distribution */}
            <div>
              {isLoading ? (
                <ChartSkeleton height={300} />
              ) : (
                <DonutChart
                  data={categoryData}
                  title="Movement Category"
                  height={250}
                />
              )}
            </div>

            {/* By Location */}
            <div>
              {isLoading ? (
                <ChartSkeleton height={300} />
              ) : (
                <AnimatedBarChart
                  data={locationData}
                  title="Non-Moving by Location"
                  height={250}
                  color="#8b5cf6"
                />
              )}
            </div>

            {/* Filters */}
            <GlassCard className="p-6" hover={false}>
              <h3 className="text-lg font-semibold text-white mb-4">Filters</h3>

              <div className="space-y-4">
                <div>
                  <label className="text-sm text-white/60 mb-2 block">Location</label>
                  <select
                    value={locationFilter || ""}
                    onChange={(e) => setLocationFilter(e.target.value || undefined)}
                    className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-white
                             focus:outline-none focus:border-cyan-500/50"
                  >
                    <option value="">All Locations</option>
                    {locations.map((loc) => (
                      <option key={loc} value={loc}>
                        {loc}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="text-sm text-white/60 mb-2 block">Category</label>
                  <select
                    value={categoryFilter || ""}
                    onChange={(e) => setCategoryFilter(e.target.value || undefined)}
                    className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-white
                             focus:outline-none focus:border-cyan-500/50"
                  >
                    <option value="">All Categories</option>
                    <option value="SLOW_MOVING">Slow Moving</option>
                    <option value="NON_MOVING">Non-Moving</option>
                    <option value="DEAD_STOCK">Dead Stock</option>
                  </select>
                </div>

                <div className="flex gap-2 pt-2">
                  <GlowButton
                    variant="secondary"
                    size="sm"
                    className="flex-1"
                    onClick={() => {
                      setLocationFilter(undefined);
                      setCategoryFilter(undefined);
                    }}
                  >
                    Clear
                  </GlowButton>
                  <IconButton
                    icon={<Download className="w-5 h-5" />}
                    tooltip="Export CSV"
                    color="cyan"
                  />
                </div>
              </div>
            </GlassCard>
          </div>

          {/* Table */}
          <GlassCard className="p-6" hover={false}>
            <h3 className="text-lg font-semibold text-white mb-4">Non-Moving Inventory Details</h3>

            {isLoading ? (
              <TableSkeleton rows={8} />
            ) : (
              <div className="overflow-x-auto">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>SKU ID</th>
                      <th>Location</th>
                      <th>Status</th>
                      <th>Days Since Movement</th>
                      <th>Inventory</th>
                      <th>Risk Score</th>
                      <th>Last Movement</th>
                      <th>Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {items
                      ?.filter((i) => i.movement_category !== "active")
                      .slice(0, 20)
                      .map((item, index) => (
                        <motion.tr
                          key={`${item.item_id}-${item.location_id}`}
                          initial={{ opacity: 0, y: 10 }}
                          animate={{ opacity: 1, y: 0 }}
                          transition={{ delay: index * 0.03 }}
                        >
                          <td>
                            <Link
                              href={`/sku/${item.item_id}`}
                              className="text-cyan-400 hover:text-cyan-300 font-medium"
                            >
                              {item.item_id}
                            </Link>
                          </td>
                          <td className="text-white/70">{item.location_id}</td>
                          <td>
                            <MovementBadge status={item.movement_category.toUpperCase() as any} />
                          </td>
                          <td>
                            <span
                              className={`font-medium ${
                                item.days_since_movement > 180
                                  ? "text-rose-400"
                                  : item.days_since_movement > 90
                                  ? "text-amber-400"
                                  : "text-cyan-400"
                              }`}
                            >
                              {item.days_since_movement} days
                            </span>
                          </td>
                          <td className="text-white">{item.current_inventory?.toLocaleString() || 0}</td>
                          <td className="text-white">
                            {item.non_moving_risk_score?.toFixed(0) || 0}%
                          </td>
                          <td className="text-white/50 text-sm">
                            {new Date(item.last_movement_date).toLocaleDateString()}
                          </td>
                          <td>
                            <Link href={`/sku/${item.item_id}`}>
                              <GlowButton variant="secondary" size="sm">
                                View
                              </GlowButton>
                            </Link>
                          </td>
                        </motion.tr>
                      ))}
                  </tbody>
                </table>
              </div>
            )}
          </GlassCard>
        </PageTransition>
      </main>
    </div>
  );
}

