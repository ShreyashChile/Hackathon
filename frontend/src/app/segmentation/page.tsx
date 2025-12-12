"use client";

import { useState, useMemo } from "react";
import { motion } from "framer-motion";
import { Sidebar } from "@/components/layout/Sidebar";
import { Header } from "@/components/layout/Header";
import { PageTransition } from "@/components/layout/PageTransition";
import { GlassCard, StatCard } from "@/components/ui/GlassCard";
import { SegmentMatrix, SegmentBadge } from "@/components/charts/SegmentMatrix";
import { DonutChart } from "@/components/charts/AnimatedPieChart";
import { AnimatedBarChart } from "@/components/charts/AnimatedBarChart";
import { TableSkeleton, ChartSkeleton } from "@/components/ui/LoadingSkeleton";
import { useSegmentation } from "@/hooks/useAPI";
import { Grid3X3, TrendingUp, BarChart3, Layers } from "lucide-react";
import { GlowButton } from "@/components/ui/GlowButton";
import Link from "next/link";

const segmentColors: Record<string, string> = {
  AX: "#10b981",
  AY: "#34d399",
  AZ: "#f59e0b",
  BX: "#06b6d4",
  BY: "#22d3ee",
  BZ: "#fbbf24",
  CX: "#8b5cf6",
  CY: "#a78bfa",
  CZ: "#f43f5e",
};

export default function SegmentationPage() {
  const [selectedSegment, setSelectedSegment] = useState<string | undefined>();
  const { data: items, isLoading, refetch } = useSegmentation({
    segment: selectedSegment,
  });

  // Calculate stats
  const segmentCounts = useMemo(() => {
    if (!items) return {};
    return items.reduce((acc, item) => {
      acc[item.segment] = (acc[item.segment] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);
  }, [items]);

  const totalItems = items?.length || 0;

  const segmentMatrixData = Object.entries(segmentCounts).map(([segment, count]) => ({
    segment,
    count,
    percentage: totalItems > 0 ? (count / totalItems) * 100 : 0,
  }));

  // ABC distribution
  const abcData = useMemo(() => {
    if (!items) return [];
    const abc: Record<string, number> = { A: 0, B: 0, C: 0 };
    items.forEach((i) => (abc[i.abc_class] = (abc[i.abc_class] || 0) + 1));
    return [
      { name: "A (High Value)", value: abc.A, color: "#10b981" },
      { name: "B (Medium)", value: abc.B, color: "#06b6d4" },
      { name: "C (Low Value)", value: abc.C, color: "#8b5cf6" },
    ];
  }, [items]);

  // XYZ distribution
  const xyzData = useMemo(() => {
    if (!items) return [];
    const xyz: Record<string, number> = { X: 0, Y: 0, Z: 0 };
    items.forEach((i) => (xyz[i.xyz_class] = (xyz[i.xyz_class] || 0) + 1));
    return [
      { name: "X (Stable)", value: xyz.X, color: "#10b981" },
      { name: "Y (Variable)", value: xyz.Y, color: "#f59e0b" },
      { name: "Z (Erratic)", value: xyz.Z, color: "#f43f5e" },
    ];
  }, [items]);

  // Segment chart data
  const segmentChartData = Object.entries(segmentCounts)
    .sort((a, b) => b[1] - a[1])
    .map(([segment, count]) => ({
      name: segment,
      value: count,
      color: segmentColors[segment] || "#6b7280",
    }));

  return (
    <div className="flex min-h-screen">
      <Sidebar />

      <main className="flex-1 ml-64 p-6">
        <Header
          title="ABC-XYZ Segmentation"
          subtitle="Classify SKUs by value and demand variability"
          onRefresh={refetch}
          isRefreshing={isLoading}
        />

        <PageTransition>
          {/* Stats Row */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <StatCard
              title="Total SKUs"
              value={totalItems}
              icon={<Layers className="w-6 h-6" />}
              color="cyan"
              delay={0}
            />
            <StatCard
              title="Segments"
              value={Object.keys(segmentCounts).length}
              icon={<Grid3X3 className="w-6 h-6" />}
              color="violet"
              delay={0.1}
            />
            <StatCard
              title="High Value (A)"
              value={abcData.find((d) => d.name.startsWith("A"))?.value || 0}
              icon={<TrendingUp className="w-6 h-6" />}
              color="emerald"
              delay={0.2}
            />
            <StatCard
              title="Erratic Demand (Z)"
              value={xyzData.find((d) => d.name.startsWith("Z"))?.value || 0}
              icon={<BarChart3 className="w-6 h-6" />}
              color="rose"
              delay={0.3}
            />
          </div>

          <div className="grid grid-cols-1 xl:grid-cols-2 gap-6 mb-6">
            {/* Segment Matrix */}
            {isLoading ? (
              <ChartSkeleton height={400} />
            ) : (
              <SegmentMatrix data={segmentMatrixData} title="ABC-XYZ Matrix" />
            )}

            {/* Segment Distribution */}
            {isLoading ? (
              <ChartSkeleton height={400} />
            ) : (
              <AnimatedBarChart
                data={segmentChartData}
                title="SKUs by Segment"
                height={350}
              />
            )}
          </div>

          <div className="grid grid-cols-1 xl:grid-cols-2 gap-6 mb-6">
            {/* ABC Distribution */}
            {isLoading ? (
              <ChartSkeleton height={300} />
            ) : (
              <DonutChart
                data={abcData}
                title="ABC Classification (Value)"
                height={250}
              />
            )}

            {/* XYZ Distribution */}
            {isLoading ? (
              <ChartSkeleton height={300} />
            ) : (
              <DonutChart
                data={xyzData}
                title="XYZ Classification (Variability)"
                height={250}
              />
            )}
          </div>

          {/* Segment Filter & Table */}
          <GlassCard className="p-6" hover={false}>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-white">SKU Details</h3>
              <div className="flex items-center gap-2">
                <span className="text-sm text-white/60">Filter by segment:</span>
                <select
                  value={selectedSegment || ""}
                  onChange={(e) => setSelectedSegment(e.target.value || undefined)}
                  className="bg-white/5 border border-white/10 rounded-xl px-4 py-2 text-white
                           focus:outline-none focus:border-cyan-500/50"
                >
                  <option value="">All Segments</option>
                  {Object.keys(segmentCounts)
                    .sort()
                    .map((seg) => (
                      <option key={seg} value={seg}>
                        {seg}
                      </option>
                    ))}
                </select>
              </div>
            </div>

            {isLoading ? (
              <TableSkeleton rows={8} />
            ) : (
              <div className="overflow-x-auto">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>SKU ID</th>
                      <th>Location</th>
                      <th>Segment</th>
                      <th>ABC</th>
                      <th>XYZ</th>
                      <th>Total Quantity</th>
                      <th>CV</th>
                      <th>Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {items?.slice(0, 20).map((item, index) => (
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
                          <SegmentBadge segment={item.segment} />
                        </td>
                        <td>
                          <span
                            className={`font-medium ${
                              item.abc_class === "A"
                                ? "text-emerald-400"
                                : item.abc_class === "B"
                                ? "text-cyan-400"
                                : "text-violet-400"
                            }`}
                          >
                            {item.abc_class}
                          </span>
                        </td>
                        <td>
                          <span
                            className={`font-medium ${
                              item.xyz_class === "X"
                                ? "text-emerald-400"
                                : item.xyz_class === "Y"
                                ? "text-amber-400"
                                : "text-rose-400"
                            }`}
                          >
                            {item.xyz_class}
                          </span>
                        </td>
                        <td className="text-white">{item.total_qty?.toLocaleString() || 0}</td>
                        <td className="text-white/70">{item.cv?.toFixed(2) || 0}</td>
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

