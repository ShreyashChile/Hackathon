"use client";

import { motion } from "framer-motion";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  Area,
  AreaChart,
  ReferenceLine,
} from "recharts";

interface LineChartData {
  name: string;
  value: number;
  [key: string]: string | number;
}

interface TrendLineChartProps {
  data: LineChartData[];
  title?: string;
  height?: number;
  color?: string;
  showArea?: boolean;
  showGrid?: boolean;
  showDots?: boolean;
  referenceLine?: number;
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="glass px-4 py-3 rounded-xl border border-white/10 shadow-xl">
        <p className="text-white/60 text-sm mb-1">{label}</p>
        {payload.map((entry: any, index: number) => (
          <p key={index} className="font-semibold" style={{ color: entry.color }}>
            {entry.name}: {entry.value}
          </p>
        ))}
      </div>
    );
  }
  return null;
};

export function TrendLineChart({
  data,
  title,
  height = 300,
  color = "#06b6d4",
  showArea = false,
  showGrid = true,
  showDots = true,
  referenceLine,
}: TrendLineChartProps) {
  const ChartComponent = showArea ? AreaChart : LineChart;
  const DataComponent = showArea ? Area : Line;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="glass-card p-6"
    >
      {title && (
        <h3 className="text-lg font-semibold text-white mb-4">{title}</h3>
      )}
      <ResponsiveContainer width="100%" height={height}>
        <ChartComponent data={data} margin={{ top: 10, right: 10, left: 10, bottom: 10 }}>
          <defs>
            <linearGradient id={`gradient-${color}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={color} stopOpacity={0.3} />
              <stop offset="100%" stopColor={color} stopOpacity={0} />
            </linearGradient>
          </defs>
          {showGrid && (
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
          )}
          <XAxis
            dataKey="name"
            stroke="rgba(255,255,255,0.3)"
            fontSize={12}
            tickLine={false}
          />
          <YAxis
            stroke="rgba(255,255,255,0.3)"
            fontSize={12}
            tickLine={false}
            axisLine={false}
          />
          <Tooltip content={<CustomTooltip />} />
          {referenceLine !== undefined && (
            <ReferenceLine
              y={referenceLine}
              stroke="rgba(244, 63, 94, 0.5)"
              strokeDasharray="5 5"
              label={{
                value: "Threshold",
                position: "right",
                fill: "rgba(244, 63, 94, 0.7)",
                fontSize: 12,
              }}
            />
          )}
          {showArea ? (
            <Area
              type="monotone"
              dataKey="value"
              stroke={color}
              strokeWidth={2}
              fill={`url(#gradient-${color})`}
              animationBegin={0}
              animationDuration={1500}
              animationEasing="ease-out"
              dot={showDots ? { fill: color, strokeWidth: 0, r: 4 } : false}
              activeDot={{ r: 6, fill: color, stroke: "white", strokeWidth: 2 }}
            />
          ) : (
            <Line
              type="monotone"
              dataKey="value"
              stroke={color}
              strokeWidth={2}
              animationBegin={0}
              animationDuration={1500}
              animationEasing="ease-out"
              dot={showDots ? { fill: color, strokeWidth: 0, r: 4 } : false}
              activeDot={{ r: 6, fill: color, stroke: "white", strokeWidth: 2 }}
            />
          )}
        </ChartComponent>
      </ResponsiveContainer>
    </motion.div>
  );
}

// Multi-line chart
interface MultiLineData {
  name: string;
  [key: string]: string | number;
}

interface MultiLineChartProps {
  data: MultiLineData[];
  lines: { key: string; color: string; label: string }[];
  title?: string;
  height?: number;
}

export function MultiLineChart({
  data,
  lines,
  title,
  height = 300,
}: MultiLineChartProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="glass-card p-6"
    >
      {title && (
        <h3 className="text-lg font-semibold text-white mb-4">{title}</h3>
      )}
      <ResponsiveContainer width="100%" height={height}>
        <LineChart data={data} margin={{ top: 10, right: 10, left: 10, bottom: 10 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
          <XAxis
            dataKey="name"
            stroke="rgba(255,255,255,0.3)"
            fontSize={12}
            tickLine={false}
          />
          <YAxis
            stroke="rgba(255,255,255,0.3)"
            fontSize={12}
            tickLine={false}
            axisLine={false}
          />
          <Tooltip content={<CustomTooltip />} />
          {lines.map(({ key, color }, index) => (
            <Line
              key={key}
              type="monotone"
              dataKey={key}
              stroke={color}
              strokeWidth={2}
              animationBegin={index * 300}
              animationDuration={1200}
              dot={false}
              activeDot={{ r: 6, fill: color, stroke: "white", strokeWidth: 2 }}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
      {/* Legend */}
      <div className="flex flex-wrap justify-center gap-4 mt-4">
        {lines.map(({ key, color, label }) => (
          <div key={key} className="flex items-center gap-2">
            <span
              className="w-6 h-0.5 rounded"
              style={{ backgroundColor: color }}
            />
            <span className="text-sm text-white/70">{label}</span>
          </div>
        ))}
      </div>
    </motion.div>
  );
}

// Sparkline (mini chart without axes)
interface SparklineProps {
  data: number[];
  color?: string;
  height?: number;
  width?: number;
}

export function Sparkline({
  data,
  color = "#06b6d4",
  height = 40,
  width = 100,
}: SparklineProps) {
  const chartData = data.map((value, index) => ({ value, index }));

  return (
    <ResponsiveContainer width={width} height={height}>
      <AreaChart data={chartData} margin={{ top: 2, right: 2, left: 2, bottom: 2 }}>
        <defs>
          <linearGradient id={`spark-${color}`} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={color} stopOpacity={0.3} />
            <stop offset="100%" stopColor={color} stopOpacity={0} />
          </linearGradient>
        </defs>
        <Area
          type="monotone"
          dataKey="value"
          stroke={color}
          strokeWidth={1.5}
          fill={`url(#spark-${color})`}
          animationDuration={1000}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}

