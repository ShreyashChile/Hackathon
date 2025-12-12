"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Sidebar } from "@/components/layout/Sidebar";
import { Header } from "@/components/layout/Header";
import { PageTransition, StaggerContainer, StaggerItem } from "@/components/layout/PageTransition";
import { GlassCard, StatCard } from "@/components/ui/GlassCard";
import { Badge } from "@/components/ui/Badge";
import { DonutChart } from "@/components/charts/AnimatedPieChart";
import { TrendLineChart } from "@/components/charts/TrendLineChart";
import { TableSkeleton, ChartSkeleton } from "@/components/ui/LoadingSkeleton";
import { useDemandShifts } from "@/hooks/useAPI";
import { TrendingUp, TrendingDown, Minus, Filter, Download } from "lucide-react";
import { GlowButton, IconButton } from "@/components/ui/GlowButton";
import Link from "next/link";

export default function DemandShiftsPage() {
  const [locationFilter, setLocationFilter] = useState<string | undefined>();
  const [directionFilter, setDirectionFilter] = useState<string | undefined>();

  const { data: shifts, isLoading, refetch } = useDemandShifts({
    location: locationFilter,
    direction: directionFilter,
  });

  // Calculate stats - API returns lowercase values
  const stats = {
    total: shifts?.length || 0,
    increases: shifts?.filter((s) => s.shift_direction === "increase").length || 0,
    decreases: shifts?.filter((s) => s.shift_direction === "decrease").length || 0,
    stable: shifts?.filter((s) => s.shift_direction === "stable").length || 0,
  };

  const chartData = [
    { name: "Increase", value: stats.increases, color: "#10b981" },
    { name: "Decrease", value: stats.decreases, color: "#f43f5e" },
    { name: "Stable", value: stats.stable, color: "#6b7280" },
  ];

  const locations = [...new Set(shifts?.map((s) => s.location_id) || [])];

  return (
    <div className="flex min-h-screen">
      <Sidebar />

      <main className="flex-1 ml-64 p-6">
        <Header
          title="Demand Shifts"
          subtitle="Detect and analyze changes in demand patterns"
          onRefresh={refetch}
          isRefreshing={isLoading}
        />

        <PageTransition>
          {/* Stats Row */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <StatCard
              title="Total Shifts"
              value={stats.total}
              icon={<Filter className="w-6 h-6" />}
              color="cyan"
              delay={0}
            />
            <StatCard
              title="Increases"
              value={stats.increases}
              icon={<TrendingUp className="w-6 h-6" />}
              color="emerald"
              delay={0.1}
            />
            <StatCard
              title="Decreases"
              value={stats.decreases}
              icon={<TrendingDown className="w-6 h-6" />}
              color="rose"
              delay={0.2}
            />
            <StatCard
              title="Stable"
              value={stats.stable}
              icon={<Minus className="w-6 h-6" />}
              color="violet"
              delay={0.3}
            />
          </div>

          <div className="grid grid-cols-1 xl:grid-cols-3 gap-6 mb-6">
            {/* Chart */}
            <div className="xl:col-span-1">
              {isLoading ? (
                <ChartSkeleton height={300} />
              ) : (
                <DonutChart
                  data={chartData}
                  title="Shift Distribution"
                  height={250}
                />
              )}
            </div>

            {/* Filters & Actions */}
            <div className="xl:col-span-2">
              <GlassCard className="p-6 h-full" hover={false}>
                <h3 className="text-lg font-semibold text-white mb-4">Filters</h3>

                <div className="flex flex-wrap gap-4">
                  {/* Location Filter */}
                  <div>
                    <label className="text-sm text-white/60 mb-2 block">Location</label>
                    <select
                      value={locationFilter || ""}
                      onChange={(e) => setLocationFilter(e.target.value || undefined)}
                      className="bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-white
                               focus:outline-none focus:border-cyan-500/50 min-w-[150px]"
                    >
                      <option value="">All Locations</option>
                      {locations.map((loc) => (
                        <option key={loc} value={loc}>
                          {loc}
                        </option>
                      ))}
                    </select>
                  </div>

                  {/* Direction Filter */}
                  <div>
                    <label className="text-sm text-white/60 mb-2 block">Direction</label>
                    <select
                      value={directionFilter || ""}
                      onChange={(e) => setDirectionFilter(e.target.value || undefined)}
                      className="bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-white
                               focus:outline-none focus:border-cyan-500/50 min-w-[150px]"
                    >
                      <option value="">All Directions</option>
                      <option value="increase">Increase</option>
                      <option value="decrease">Decrease</option>
                      <option value="stable">Stable</option>
                    </select>
                  </div>

                  <div className="flex items-end gap-2 ml-auto">
                    <GlowButton
                      variant="secondary"
                      size="md"
                      onClick={() => {
                        setLocationFilter(undefined);
                        setDirectionFilter(undefined);
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
          </div>

          {/* Table */}
          <GlassCard className="p-6" hover={false}>
            <h3 className="text-lg font-semibold text-white mb-4">Demand Shift Details</h3>

            {isLoading ? (
              <TableSkeleton rows={8} />
            ) : (
              <div className="overflow-x-auto">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>SKU ID</th>
                      <th>Location</th>
                      <th>Direction</th>
                      <th>Magnitude</th>
                      <th>Confidence</th>
                      <th>Type</th>
                      <th>Detection Date</th>
                      <th>Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {shifts?.slice(0, 20).map((shift, index) => (
                      <motion.tr
                        key={`${shift.item_id}-${shift.location_id}`}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: index * 0.03 }}
                      >
                        <td>
                          <Link
                            href={`/sku/${shift.item_id}`}
                            className="text-cyan-400 hover:text-cyan-300 font-medium"
                          >
                            {shift.item_id}
                          </Link>
                        </td>
                        <td className="text-white/70">{shift.location_id}</td>
                        <td>
                          <Badge
                            variant={
                              shift.shift_direction === "increase"
                                ? "success"
                                : shift.shift_direction === "decrease"
                                ? "critical"
                                : "default"
                            }
                          >
                            {shift.shift_direction === "increase" && (
                              <TrendingUp className="w-3 h-3" />
                            )}
                            {shift.shift_direction === "decrease" && (
                              <TrendingDown className="w-3 h-3" />
                            )}
                            {shift.shift_direction === "stable" && (
                              <Minus className="w-3 h-3" />
                            )}
                            {shift.shift_direction.toUpperCase()}
                          </Badge>
                        </td>
                        <td className="text-white font-medium">
                          {shift.shift_magnitude?.toFixed(1) || 0}%
                        </td>
                        <td>
                          <div className="flex items-center gap-2">
                            <div className="w-16 h-2 bg-white/10 rounded-full overflow-hidden">
                              <motion.div
                                initial={{ width: 0 }}
                                animate={{ width: `${shift.confidence_score}%` }}
                                transition={{ delay: index * 0.03 + 0.2, duration: 0.5 }}
                                className="h-full bg-gradient-to-r from-cyan-500 to-violet-500"
                              />
                            </div>
                            <span className="text-white/60 text-sm">
                              {shift.confidence_score?.toFixed(0) || 0}%
                            </span>
                          </div>
                        </td>
                        <td className="text-white/50 text-sm">{shift.shift_type || "N/A"}</td>
                        <td className="text-white/50 text-sm">
                          {shift.detection_date ? new Date(shift.detection_date).toLocaleDateString() : "N/A"}
                        </td>
                        <td>
                          <Link href={`/sku/${shift.item_id}`}>
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

            {shifts && shifts.length > 20 && (
              <p className="text-center text-white/50 mt-4">
                Showing 20 of {shifts.length} results
              </p>
            )}
          </GlassCard>
        </PageTransition>
      </main>
    </div>
  );
}

