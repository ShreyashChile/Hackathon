"use client";

import { motion } from "framer-motion";
import { Sidebar } from "@/components/layout/Sidebar";
import { Header } from "@/components/layout/Header";
import { PageTransition, StaggerContainer, StaggerItem } from "@/components/layout/PageTransition";
import { KPIGrid } from "@/components/dashboard/KPIGrid";
import { AlertsFeed } from "@/components/dashboard/AlertsFeed";
import { DonutChart } from "@/components/charts/AnimatedPieChart";
import { AnimatedBarChart } from "@/components/charts/AnimatedBarChart";
import { SegmentMatrix } from "@/components/charts/SegmentMatrix";
import { CardSkeleton, ChartSkeleton } from "@/components/ui/LoadingSkeleton";
import { useDashboardSummary, useAlerts } from "@/hooks/useAPI";

export default function DashboardPage() {
  const { data: summary, isLoading: summaryLoading, refetch } = useDashboardSummary();
  const { data: alerts, isLoading: alertsLoading } = useAlerts({ active_only: true });

  const isLoading = summaryLoading || alertsLoading;

  // Transform data for charts using new API structure
  const shiftDistributionData = summary?.demand_shifts
    ? [
        { name: "Increase", value: summary.demand_shifts.increases, color: "#10b981" },
        { name: "Decrease", value: summary.demand_shifts.decreases, color: "#f43f5e" },
        { name: "Stable", value: summary.demand_shifts.total_shifts - summary.demand_shifts.increases - summary.demand_shifts.decreases, color: "#6b7280" },
      ].filter(d => d.value > 0)
    : [];

  const nonMovingData = summary?.non_moving
    ? [
        { name: "Active", value: summary.non_moving.active, color: "#10b981" },
        { name: "Slow Moving", value: summary.non_moving.slow_moving, color: "#06b6d4" },
        { name: "Non-Moving", value: summary.non_moving.non_moving, color: "#f59e0b" },
        { name: "Dead Stock", value: summary.non_moving.dead_stock, color: "#f43f5e" },
      ].filter(d => d.value > 0)
    : [];

  const riskLevelData = summary?.risk_levels
    ? Object.entries(summary.risk_levels).map(([name, value]) => ({
        name: name.charAt(0).toUpperCase() + name.slice(1),
        value,
        color:
          name === "critical"
            ? "#f43f5e"
            : name === "high"
            ? "#f59e0b"
            : name === "medium"
            ? "#06b6d4"
            : name === "low"
            ? "#8b5cf6"
            : "#10b981",
      }))
    : [];

  const alertsByPriorityData = summary?.alerts
    ? [
        { name: "Critical", value: summary.alerts.critical, color: "#f43f5e" },
        { name: "High", value: summary.alerts.high, color: "#f59e0b" },
        { name: "Other", value: summary.alerts.total - summary.alerts.critical - summary.alerts.high, color: "#06b6d4" },
      ].filter(d => d.value > 0)
    : [];

  // Empty segment data since the API doesn't return it
  const segmentData: { segment: string; count: number; percentage: number }[] = [];

  return (
    <div className="flex min-h-screen">
      <Sidebar />

      <main className="flex-1 ml-64 p-6">
        <Header
          title="Dashboard"
          subtitle="Overview of inventory health"
          onRefresh={refetch}
          isRefreshing={isLoading}
        />

        <PageTransition>
          {/* KPI Grid */}
          <div className="mb-6">
            {isLoading ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4">
                {[...Array(5)].map((_, i) => (
                  <CardSkeleton key={i} />
                ))}
              </div>
            ) : (
              <KPIGrid
                totalSkus={summary?.overview?.unique_skus || 0}
                totalLocations={summary?.overview?.unique_locations || 0}
                demandShiftsCount={summary?.demand_shifts?.total_shifts || 0}
                nonMovingCount={(summary?.non_moving?.dead_stock || 0) + (summary?.non_moving?.non_moving || 0) + (summary?.non_moving?.slow_moving || 0)}
                criticalAlerts={summary?.alerts?.critical || 0}
              />
            )}
          </div>

          <StaggerContainer className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
            {/* Demand Shift Distribution */}
            <StaggerItem>
              {isLoading ? (
                <ChartSkeleton height={350} />
              ) : (
                <DonutChart
                  data={shiftDistributionData}
                  title="Demand Shift Distribution"
                  centerLabel="Total Shifts"
                  centerValue={summary?.demand_shifts?.total_shifts}
                  height={280}
                />
              )}
            </StaggerItem>

            {/* Non-Moving by Category */}
            <StaggerItem>
              {isLoading ? (
                <ChartSkeleton height={350} />
              ) : (
                <DonutChart
                  data={nonMovingData}
                  title="Inventory Movement"
                  centerLabel="Total Items"
                  centerValue={summary?.overview?.total_sku_locations}
                  height={280}
                />
              )}
            </StaggerItem>

            {/* Alerts by Priority */}
            <StaggerItem>
              {isLoading ? (
                <ChartSkeleton height={350} />
              ) : (
                <AnimatedBarChart
                  data={alertsByPriorityData}
                  title="Alerts by Priority"
                  height={280}
                  horizontal
                />
              )}
            </StaggerItem>
          </StaggerContainer>

          <div className="grid grid-cols-1 xl:grid-cols-2 gap-6 mt-6">
            {/* Risk Levels */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4 }}
            >
              {isLoading ? (
                <ChartSkeleton height={400} />
              ) : (
                <AnimatedBarChart
                  data={riskLevelData}
                  title="Risk Level Distribution"
                  height={300}
                />
              )}
            </motion.div>

            {/* Recent Alerts */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.5 }}
            >
              {alertsLoading ? (
                <ChartSkeleton height={400} />
              ) : (
                <AlertsFeed alerts={alerts || []} maxItems={6} title="Recent Alerts" />
              )}
            </motion.div>
          </div>
        </PageTransition>
      </main>
    </div>
  );
}
