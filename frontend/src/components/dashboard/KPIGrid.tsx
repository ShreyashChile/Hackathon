"use client";

import { motion } from "framer-motion";
import {
  TrendingUp,
  TrendingDown,
  Package,
  AlertTriangle,
  Activity,
  MapPin,
} from "lucide-react";
import { StatCard } from "../ui/GlassCard";
import { AnimatedCounter } from "../ui/AnimatedCounter";

interface KPIGridProps {
  totalSkus: number;
  totalLocations: number;
  demandShiftsCount: number;
  nonMovingCount: number;
  criticalAlerts: number;
}

export function KPIGrid({
  totalSkus,
  totalLocations,
  demandShiftsCount,
  nonMovingCount,
  criticalAlerts,
}: KPIGridProps) {
  const kpis = [
    {
      title: "Total SKUs",
      value: totalSkus,
      icon: <Package className="w-6 h-6" />,
      color: "cyan" as const,
      trend: { value: 2.5, isPositive: true },
    },
    {
      title: "Locations",
      value: totalLocations,
      icon: <MapPin className="w-6 h-6" />,
      color: "violet" as const,
    },
    {
      title: "Demand Shifts",
      value: demandShiftsCount,
      icon: <Activity className="w-6 h-6" />,
      color: "emerald" as const,
      trend: { value: 12, isPositive: false },
    },
    {
      title: "Non-Moving Items",
      value: nonMovingCount,
      icon: <TrendingDown className="w-6 h-6" />,
      color: "amber" as const,
      trend: { value: 5, isPositive: false },
    },
    {
      title: "Critical Alerts",
      value: criticalAlerts,
      icon: <AlertTriangle className="w-6 h-6" />,
      color: "rose" as const,
      trend: { value: 3, isPositive: false },
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4">
      {kpis.map((kpi, index) => (
        <StatCard
          key={kpi.title}
          title={kpi.title}
          value={kpi.value}
          icon={kpi.icon}
          color={kpi.color}
          trend={kpi.trend}
          delay={index * 0.1}
        />
      ))}
    </div>
  );
}

// Mini KPI card for sidebar or compact views
interface MiniKPIProps {
  title: string;
  value: number;
  icon: React.ReactNode;
  color?: string;
}

export function MiniKPI({ title, value, icon, color = "#06b6d4" }: MiniKPIProps) {
  return (
    <motion.div
      initial={{ opacity: 0, x: -10 }}
      animate={{ opacity: 1, x: 0 }}
      className="flex items-center gap-3 p-3 rounded-xl bg-white/5 hover:bg-white/10 transition-colors"
    >
      <div
        className="p-2 rounded-lg"
        style={{ backgroundColor: `${color}20` }}
      >
        <span style={{ color }}>{icon}</span>
      </div>
      <div>
        <p className="text-lg font-bold text-white">
          <AnimatedCounter value={value} />
        </p>
        <p className="text-xs text-white/50">{title}</p>
      </div>
    </motion.div>
  );
}

