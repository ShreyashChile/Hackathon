"use client";

import { use } from "react";
import { motion } from "framer-motion";
import { useRouter } from "next/navigation";
import { Sidebar } from "@/components/layout/Sidebar";
import { Header } from "@/components/layout/Header";
import { PageTransition, StaggerContainer, StaggerItem } from "@/components/layout/PageTransition";
import { GlassCard } from "@/components/ui/GlassCard";
import { Badge, MovementBadge, PriorityBadge } from "@/components/ui/Badge";
import { SegmentBadge } from "@/components/charts/SegmentMatrix";
import { TrendLineChart } from "@/components/charts/TrendLineChart";
import { PageLoader, CardSkeleton, ChartSkeleton } from "@/components/ui/LoadingSkeleton";
import { useSKUAnalysis } from "@/hooks/useAPI";
import { GlowButton } from "@/components/ui/GlowButton";
import {
  ArrowLeft,
  Package,
  MapPin,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  Clock,
  BarChart3,
  Activity,
} from "lucide-react";
import Link from "next/link";

export default function SKUDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = use(params);
  const skuId = resolvedParams.id;
  const router = useRouter();
  const { data: analysis, isLoading, error, refetch } = useSKUAnalysis(skuId);

  if (isLoading) {
    return (
      <div className="flex min-h-screen">
        <Sidebar />
        <main className="flex-1 ml-64 p-6">
          <Header title="Loading..." subtitle="Fetching SKU data" />
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <CardSkeleton />
            <CardSkeleton />
            <ChartSkeleton height={300} />
            <ChartSkeleton height={300} />
          </div>
        </main>
      </div>
    );
  }

  if (error || !analysis) {
    return (
      <div className="flex min-h-screen">
        <Sidebar />
        <main className="flex-1 ml-64 p-6">
          <Header title="Error" subtitle="Failed to load SKU data" />
          <GlassCard className="p-8 text-center">
            <AlertTriangle className="w-16 h-16 text-amber-400 mx-auto mb-4" />
            <h2 className="text-xl font-semibold text-white mb-2">SKU Not Found</h2>
            <p className="text-white/60 mb-6">
              The SKU &quot;{skuId}&quot; could not be found or there was an error loading the data.
            </p>
            <div className="flex justify-center gap-4">
              <GlowButton onClick={() => router.back()}>
                <ArrowLeft className="w-4 h-4" />
                Go Back
              </GlowButton>
              <GlowButton variant="secondary" onClick={() => refetch()}>
                Try Again
              </GlowButton>
            </div>
          </GlassCard>
        </main>
      </div>
    );
  }

  // Get primary data from arrays
  const primaryShift = analysis.demand_shifts?.[0];
  const primaryMovement = analysis.non_moving_status?.[0];
  const primarySegment = analysis.segmentation?.[0];
  const primaryRisk = analysis.risk_scores?.[0];

  return (
    <div className="flex min-h-screen">
      <Sidebar />

      <main className="flex-1 ml-64 p-6">
        <Header
          title={`SKU: ${analysis.item_id}`}
          subtitle={`Analysis across ${analysis.locations.length} location(s)`}
          onRefresh={refetch}
        />

        <PageTransition>
          {/* Back button and status */}
          <div className="flex items-center justify-between mb-6">
            <button
              onClick={() => router.back()}
              className="flex items-center gap-2 text-white/60 hover:text-white transition-colors"
            >
              <ArrowLeft className="w-5 h-5" />
              <span>Back</span>
            </button>

            <div className="flex items-center gap-3">
              <Badge
                variant={
                  analysis.overall_status === "CRITICAL"
                    ? "critical"
                    : analysis.overall_status === "WARNING"
                    ? "warning"
                    : "success"
                }
                pulse={analysis.overall_status === "CRITICAL"}
              >
                {analysis.overall_status}
              </Badge>
            </div>
          </div>

          <StaggerContainer className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-4 gap-4 mb-6">
            {/* SKU Info Card */}
            <StaggerItem>
              <GlassCard className="p-5 h-full">
                <div className="flex items-center gap-3 mb-4">
                  <div className="p-3 rounded-xl bg-cyan-500/20">
                    <Package className="w-6 h-6 text-cyan-400" />
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-white">{analysis.item_id}</h3>
                    <p className="text-sm text-white/50">SKU Details</p>
                  </div>
                </div>
                <div className="space-y-2">
                  <div className="flex items-center gap-2 text-sm">
                    <MapPin className="w-4 h-4 text-white/40" />
                    <span className="text-white/60">Locations:</span>
                    <span className="text-white">{analysis.locations.join(", ")}</span>
                  </div>
                </div>
              </GlassCard>
            </StaggerItem>

            {/* Demand Shift Card */}
            <StaggerItem>
              <GlassCard className="p-5 h-full">
                <div className="flex items-center gap-3 mb-4">
                  <div
                    className={`p-3 rounded-xl ${
                      primaryShift?.shift_direction === "INCREASE"
                        ? "bg-emerald-500/20"
                        : primaryShift?.shift_direction === "DECREASE"
                        ? "bg-rose-500/20"
                        : "bg-gray-500/20"
                    }`}
                  >
                    {primaryShift?.shift_direction === "INCREASE" ? (
                      <TrendingUp className="w-6 h-6 text-emerald-400" />
                    ) : primaryShift?.shift_direction === "DECREASE" ? (
                      <TrendingDown className="w-6 h-6 text-rose-400" />
                    ) : (
                      <Activity className="w-6 h-6 text-gray-400" />
                    )}
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-white">Demand Shift</h3>
                    <p className="text-sm text-white/50">Trend Analysis</p>
                  </div>
                </div>
                {primaryShift ? (
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-white/60">Direction:</span>
                      <Badge
                        variant={
                          primaryShift.shift_direction === "INCREASE"
                            ? "success"
                            : primaryShift.shift_direction === "DECREASE"
                            ? "critical"
                            : "default"
                        }
                      >
                        {primaryShift.shift_direction}
                      </Badge>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-white/60">Magnitude:</span>
                      <span className="text-white font-medium">
                        {(primaryShift.shift_magnitude * 100).toFixed(1)}%
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-white/60">Confidence:</span>
                      <span className="text-white font-medium">
                        {(primaryShift.confidence_score * 100).toFixed(0)}%
                      </span>
                    </div>
                  </div>
                ) : (
                  <p className="text-white/50">No shift detected</p>
                )}
              </GlassCard>
            </StaggerItem>

            {/* Movement Status Card */}
            <StaggerItem>
              <GlassCard className="p-5 h-full">
                <div className="flex items-center gap-3 mb-4">
                  <div className="p-3 rounded-xl bg-amber-500/20">
                    <Clock className="w-6 h-6 text-amber-400" />
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-white">Movement</h3>
                    <p className="text-sm text-white/50">Inventory Status</p>
                  </div>
                </div>
                {primaryMovement ? (
                  <div className="space-y-2">
                    <div className="flex justify-between items-center">
                      <span className="text-white/60">Status:</span>
                      <MovementBadge status={primaryMovement.movement_category} />
                    </div>
                    <div className="flex justify-between">
                      <span className="text-white/60">Days Idle:</span>
                      <span
                        className={`font-medium ${
                          primaryMovement.days_since_last_movement > 180
                            ? "text-rose-400"
                            : primaryMovement.days_since_last_movement > 90
                            ? "text-amber-400"
                            : "text-emerald-400"
                        }`}
                      >
                        {primaryMovement.days_since_last_movement}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-white/60">On Hand:</span>
                      <span className="text-white font-medium">
                        {primaryMovement.on_hand_quantity?.toLocaleString() ?? "N/A"}
                      </span>
                    </div>
                  </div>
                ) : (
                  <p className="text-white/50">No movement data</p>
                )}
              </GlassCard>
            </StaggerItem>

            {/* Segmentation Card */}
            <StaggerItem>
              <GlassCard className="p-5 h-full">
                <div className="flex items-center gap-3 mb-4">
                  <div className="p-3 rounded-xl bg-violet-500/20">
                    <BarChart3 className="w-6 h-6 text-violet-400" />
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-white">Segment</h3>
                    <p className="text-sm text-white/50">ABC-XYZ Class</p>
                  </div>
                </div>
                {primarySegment ? (
                  <div className="space-y-2">
                    <div className="flex justify-between items-center">
                      <span className="text-white/60">Segment:</span>
                      <SegmentBadge segment={primarySegment.segment} />
                    </div>
                    <div className="flex justify-between">
                      <span className="text-white/60">ABC Class:</span>
                      <span
                        className={`font-medium ${
                          primarySegment.abc_class === "A"
                            ? "text-emerald-400"
                            : primarySegment.abc_class === "B"
                            ? "text-cyan-400"
                            : "text-violet-400"
                        }`}
                      >
                        {primarySegment.abc_class}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-white/60">XYZ Class:</span>
                      <span
                        className={`font-medium ${
                          primarySegment.xyz_class === "X"
                            ? "text-emerald-400"
                            : primarySegment.xyz_class === "Y"
                            ? "text-amber-400"
                            : "text-rose-400"
                        }`}
                      >
                        {primarySegment.xyz_class}
                      </span>
                    </div>
                  </div>
                ) : (
                  <p className="text-white/50">No segmentation data</p>
                )}
              </GlassCard>
            </StaggerItem>
          </StaggerContainer>

          {/* Risk Score Card */}
          {primaryRisk && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
              className="mb-6"
            >
              <GlassCard className="p-6">
                <div className="flex items-center gap-3 mb-4">
                  <div className="p-3 rounded-xl bg-rose-500/20">
                    <AlertTriangle className="w-6 h-6 text-rose-400" />
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-white">Risk Assessment</h3>
                    <p className="text-sm text-white/50">Composite risk score and factors</p>
                  </div>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                  {/* Risk Score */}
                  <div className="text-center">
                    <motion.div
                      initial={{ scale: 0 }}
                      animate={{ scale: 1 }}
                      transition={{ delay: 0.5, type: "spring" }}
                      className={`
                        inline-flex items-center justify-center w-32 h-32 rounded-full
                        border-4 ${
                          primaryRisk.risk_score > 70
                            ? "border-rose-500"
                            : primaryRisk.risk_score > 40
                            ? "border-amber-500"
                            : "border-emerald-500"
                        }
                      `}
                    >
                      <span className="text-4xl font-bold text-white">
                        {primaryRisk.risk_score.toFixed(0)}
                      </span>
                    </motion.div>
                    <p className="text-white/60 mt-2">Risk Score</p>
                  </div>

                  {/* Risk Factors */}
                  <div className="lg:col-span-2">
                    <h4 className="text-sm font-semibold text-white/70 mb-3 uppercase tracking-wider">
                      Risk Factors
                    </h4>
                    <div className="space-y-3">
                      {Object.entries(primaryRisk.risk_factors || {}).map(
                        ([factor, value], index) => (
                          <motion.div
                            key={factor}
                            initial={{ opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: 0.4 + index * 0.1 }}
                          >
                            <div className="flex justify-between text-sm mb-1">
                              <span className="text-white/60 capitalize">
                                {factor.replace(/_/g, " ")}
                              </span>
                              <span className="text-white font-medium">
                                {((value as number) * 100).toFixed(0)}%
                              </span>
                            </div>
                            <div className="w-full h-2 bg-white/10 rounded-full overflow-hidden">
                              <motion.div
                                initial={{ width: 0 }}
                                animate={{ width: `${(value as number) * 100}%` }}
                                transition={{ delay: 0.6 + index * 0.1, duration: 0.5 }}
                                className={`h-full rounded-full ${
                                  (value as number) > 0.7
                                    ? "bg-rose-500"
                                    : (value as number) > 0.4
                                    ? "bg-amber-500"
                                    : "bg-emerald-500"
                                }`}
                              />
                            </div>
                          </motion.div>
                        )
                      )}
                    </div>

                    {/* Recommendation */}
                    {primaryRisk.recommendation && (
                      <div className="mt-4 p-4 rounded-xl bg-white/5 border border-white/10">
                        <p className="text-sm text-white/80">
                          <span className="font-semibold text-white">Recommendation: </span>
                          {primaryRisk.recommendation}
                        </p>
                      </div>
                    )}
                  </div>
                </div>
              </GlassCard>
            </motion.div>
          )}

          {/* Location-wise breakdown */}
          {analysis.locations.length > 1 && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4 }}
            >
              <GlassCard className="p-6">
                <h3 className="text-lg font-semibold text-white mb-4">Location Breakdown</h3>
                <div className="overflow-x-auto">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Location</th>
                        <th>Demand Shift</th>
                        <th>Movement Status</th>
                        <th>Segment</th>
                        <th>Risk Score</th>
                      </tr>
                    </thead>
                    <tbody>
                      {analysis.locations.map((loc) => {
                        const shift = analysis.demand_shifts?.find(
                          (s) => s.location_id === loc
                        );
                        const movement = analysis.non_moving_status?.find(
                          (m) => m.location_id === loc
                        );
                        const segment = analysis.segmentation?.find(
                          (s) => s.location_id === loc
                        );
                        const risk = analysis.risk_scores?.find(
                          (r) => r.location_id === loc
                        );

                        return (
                          <tr key={loc}>
                            <td className="font-medium text-white">{loc}</td>
                            <td>
                              {shift ? (
                                <Badge
                                  variant={
                                    shift.shift_direction === "INCREASE"
                                      ? "success"
                                      : shift.shift_direction === "DECREASE"
                                      ? "critical"
                                      : "default"
                                  }
                                >
                                  {shift.shift_direction}
                                </Badge>
                              ) : (
                                <span className="text-white/40">-</span>
                              )}
                            </td>
                            <td>
                              {movement ? (
                                <MovementBadge status={movement.movement_category} />
                              ) : (
                                <span className="text-white/40">-</span>
                              )}
                            </td>
                            <td>
                              {segment ? (
                                <SegmentBadge segment={segment.segment} />
                              ) : (
                                <span className="text-white/40">-</span>
                              )}
                            </td>
                            <td>
                              {risk ? (
                                <span
                                  className={`font-medium ${
                                    risk.risk_score > 70
                                      ? "text-rose-400"
                                      : risk.risk_score > 40
                                      ? "text-amber-400"
                                      : "text-emerald-400"
                                  }`}
                                >
                                  {risk.risk_score.toFixed(0)}
                                </span>
                              ) : (
                                <span className="text-white/40">-</span>
                              )}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </GlassCard>
            </motion.div>
          )}

          {/* Quick Actions */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5 }}
            className="mt-6 flex gap-4"
          >
            <Link href="/demand-shifts">
              <GlowButton variant="secondary">View All Demand Shifts</GlowButton>
            </Link>
            <Link href="/non-moving">
              <GlowButton variant="secondary">View Non-Moving Inventory</GlowButton>
            </Link>
            <Link href="/alerts">
              <GlowButton variant="secondary">View Alerts</GlowButton>
            </Link>
          </motion.div>
        </PageTransition>
      </main>
    </div>
  );
}

