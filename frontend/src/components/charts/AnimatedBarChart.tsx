"use client";

import { motion } from "framer-motion";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  Cell,
} from "recharts";

interface BarChartData {
  name: string;
  value: number;
  color?: string;
}

interface AnimatedBarChartProps {
  data: BarChartData[];
  title?: string;
  height?: number;
  color?: string;
  showGrid?: boolean;
  horizontal?: boolean;
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="glass px-4 py-3 rounded-xl border border-white/10">
        <p className="text-white font-medium">{label}</p>
        <p className="text-cyan-400 font-semibold">{payload[0].value}</p>
      </div>
    );
  }
  return null;
};

export function AnimatedBarChart({
  data,
  title,
  height = 300,
  color = "#06b6d4",
  showGrid = true,
  horizontal = false,
}: AnimatedBarChartProps) {
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
        <BarChart
          data={data}
          layout={horizontal ? "vertical" : "horizontal"}
          margin={{ top: 10, right: 10, left: 10, bottom: 10 }}
        >
          {showGrid && (
            <CartesianGrid
              strokeDasharray="3 3"
              stroke="rgba(255,255,255,0.05)"
              vertical={!horizontal}
              horizontal={horizontal}
            />
          )}
          {horizontal ? (
            <>
              <XAxis type="number" stroke="rgba(255,255,255,0.3)" fontSize={12} />
              <YAxis
                type="category"
                dataKey="name"
                stroke="rgba(255,255,255,0.3)"
                fontSize={12}
                width={100}
              />
            </>
          ) : (
            <>
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
            </>
          )}
          <Tooltip content={<CustomTooltip />} cursor={{ fill: "rgba(255,255,255,0.05)" }} />
          <Bar
            dataKey="value"
            radius={[4, 4, 4, 4]}
            animationBegin={0}
            animationDuration={1000}
            animationEasing="ease-out"
          >
            {data.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={entry.color || color}
                fillOpacity={0.8}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </motion.div>
  );
}

// Stacked bar chart variant
interface StackedBarData {
  name: string;
  [key: string]: string | number;
}

interface StackedBarChartProps {
  data: StackedBarData[];
  keys: { key: string; color: string; label: string }[];
  title?: string;
  height?: number;
}

export function StackedBarChart({
  data,
  keys,
  title,
  height = 300,
}: StackedBarChartProps) {
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
        <BarChart data={data} margin={{ top: 10, right: 10, left: 10, bottom: 10 }}>
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
          <Tooltip content={<CustomTooltip />} cursor={{ fill: "rgba(255,255,255,0.05)" }} />
          {keys.map(({ key, color }, index) => (
            <Bar
              key={key}
              dataKey={key}
              stackId="stack"
              fill={color}
              radius={index === keys.length - 1 ? [4, 4, 0, 0] : [0, 0, 0, 0]}
              animationBegin={index * 200}
              animationDuration={800}
            />
          ))}
        </BarChart>
      </ResponsiveContainer>
      {/* Legend */}
      <div className="flex flex-wrap justify-center gap-4 mt-4">
        {keys.map(({ key, color, label }) => (
          <div key={key} className="flex items-center gap-2">
            <span
              className="w-3 h-3 rounded"
              style={{ backgroundColor: color }}
            />
            <span className="text-sm text-white/70">{label}</span>
          </div>
        ))}
      </div>
    </motion.div>
  );
}

