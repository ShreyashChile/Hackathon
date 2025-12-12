"use client";

import { motion } from "framer-motion";
import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";

interface PieChartData {
  name: string;
  value: number;
  color: string;
}

interface AnimatedPieChartProps {
  data: PieChartData[];
  title?: string;
  innerRadius?: number;
  outerRadius?: number;
  showLegend?: boolean;
  height?: number;
}

const CustomTooltip = ({ active, payload }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="glass px-4 py-3 rounded-xl border border-white/10">
        <p className="text-white font-medium">{payload[0].name}</p>
        <p className="text-white/70 text-sm">
          Value: <span className="text-cyan-400 font-semibold">{payload[0].value}</span>
        </p>
        <p className="text-white/70 text-sm">
          Share: <span className="text-violet-400 font-semibold">
            {((payload[0].value / payload[0].payload.total) * 100).toFixed(1)}%
          </span>
        </p>
      </div>
    );
  }
  return null;
};

const renderCustomizedLabel = ({
  cx,
  cy,
  midAngle,
  innerRadius,
  outerRadius,
  percent,
}: any) => {
  const RADIAN = Math.PI / 180;
  const radius = innerRadius + (outerRadius - innerRadius) * 0.5;
  const x = cx + radius * Math.cos(-midAngle * RADIAN);
  const y = cy + radius * Math.sin(-midAngle * RADIAN);

  if (percent < 0.05) return null;

  return (
    <text
      x={x}
      y={y}
      fill="white"
      textAnchor="middle"
      dominantBaseline="central"
      className="text-xs font-semibold"
    >
      {`${(percent * 100).toFixed(0)}%`}
    </text>
  );
};

export function AnimatedPieChart({
  data,
  title,
  innerRadius = 60,
  outerRadius = 100,
  showLegend = true,
  height = 300,
}: AnimatedPieChartProps) {
  const total = data.reduce((sum, item) => sum + item.value, 0);
  const dataWithTotal = data.map((item) => ({ ...item, total }));

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.5 }}
      className="glass-card p-6"
    >
      {title && (
        <h3 className="text-lg font-semibold text-white mb-4">{title}</h3>
      )}
      <ResponsiveContainer width="100%" height={height}>
        <PieChart>
          <Pie
            data={dataWithTotal}
            cx="50%"
            cy="50%"
            labelLine={false}
            label={renderCustomizedLabel}
            innerRadius={innerRadius}
            outerRadius={outerRadius}
            paddingAngle={2}
            dataKey="value"
            animationBegin={0}
            animationDuration={1000}
            animationEasing="ease-out"
          >
            {dataWithTotal.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={entry.color}
                stroke="rgba(0,0,0,0.2)"
                strokeWidth={1}
              />
            ))}
          </Pie>
          <Tooltip content={<CustomTooltip />} />
          {showLegend && (
            <Legend
              verticalAlign="bottom"
              height={36}
              formatter={(value) => (
                <span className="text-white/70 text-sm">{value}</span>
              )}
            />
          )}
        </PieChart>
      </ResponsiveContainer>
      {/* Center text for donut chart */}
      {innerRadius > 0 && (
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
          <div className="text-center">
            <p className="text-3xl font-bold text-white">{total}</p>
            <p className="text-xs text-white/50 uppercase tracking-wider">Total</p>
          </div>
        </div>
      )}
    </motion.div>
  );
}

// Donut chart variant with center label
interface DonutChartProps extends AnimatedPieChartProps {
  centerLabel?: string;
  centerValue?: string | number;
}

export function DonutChart({
  data,
  title,
  centerLabel,
  centerValue,
  height = 300,
}: DonutChartProps) {
  const total = data.reduce((sum, item) => sum + item.value, 0);
  
  // Filter out zero values for cleaner chart display
  const filteredData = data.filter((item) => item.value > 0);
  const dataWithTotal = filteredData.map((item) => ({ ...item, total }));

  // Calculate percentages for all items (including zeros for legend)
  const dataWithPercent = data.map((item) => ({
    ...item,
    percent: total > 0 ? ((item.value / total) * 100).toFixed(1) : "0",
  }));

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.5 }}
      className="glass-card p-6 relative overflow-hidden"
    >
      {/* Glow effect behind chart */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-48 h-48 bg-cyan-500/10 rounded-full blur-3xl" />
      
      {title && (
        <h3 className="text-lg font-semibold text-white mb-2">{title}</h3>
      )}
      <div className="relative">
        <ResponsiveContainer width="100%" height={height}>
          <PieChart>
            <defs>
              {filteredData.map((entry, index) => (
                <linearGradient
                  key={`gradient-${index}`}
                  id={`gradient-${index}`}
                  x1="0"
                  y1="0"
                  x2="1"
                  y2="1"
                >
                  <stop offset="0%" stopColor={entry.color} stopOpacity={1} />
                  <stop offset="100%" stopColor={entry.color} stopOpacity={0.7} />
                </linearGradient>
              ))}
              <filter id="glow">
                <feGaussianBlur stdDeviation="3" result="coloredBlur" />
                <feMerge>
                  <feMergeNode in="coloredBlur" />
                  <feMergeNode in="SourceGraphic" />
                </feMerge>
              </filter>
            </defs>
            <Pie
              data={dataWithTotal}
              cx="50%"
              cy="50%"
              innerRadius={65}
              outerRadius={95}
              paddingAngle={4}
              dataKey="value"
              animationBegin={0}
              animationDuration={1200}
              animationEasing="ease-out"
              cornerRadius={5}
            >
              {dataWithTotal.map((entry, index) => (
                <Cell
                  key={`cell-${index}`}
                  fill={`url(#gradient-${index})`}
                  stroke={entry.color}
                  strokeWidth={2}
                  style={{ filter: "url(#glow)" }}
                />
              ))}
            </Pie>
            <Tooltip content={<CustomTooltip />} />
          </PieChart>
        </ResponsiveContainer>
        {/* Center content with ring effect */}
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
          <div className="relative">
            {/* Inner glow ring */}
            <div className="absolute inset-0 rounded-full bg-gradient-to-br from-cyan-500/20 to-violet-500/20 blur-md scale-150" />
            <div className="relative text-center bg-[#0f0f23]/80 rounded-full p-6 backdrop-blur-sm border border-white/5">
              <motion.p
                initial={{ scale: 0, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                transition={{ delay: 0.5, type: "spring", stiffness: 200 }}
                className="text-4xl font-bold bg-gradient-to-r from-white to-white/80 bg-clip-text text-transparent"
              >
                {centerValue ?? total}
              </motion.p>
              <motion.p 
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.7 }}
                className="text-sm text-white/50 mt-0.5 uppercase tracking-widest"
              >
                {centerLabel ?? "Total"}
              </motion.p>
            </div>
          </div>
        </div>
      </div>
      {/* Enhanced Legend */}
      <div className="flex flex-wrap justify-center gap-x-6 gap-y-2 mt-4">
        {dataWithPercent.map((item, index) => (
          <motion.div
            key={index}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.8 + index * 0.1 }}
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 transition-colors"
          >
            <span
              className="w-3 h-3 rounded-full shadow-lg"
              style={{ 
                backgroundColor: item.color,
                boxShadow: `0 0 8px ${item.color}50`
              }}
            />
            <span className="text-sm text-white/80 font-medium">{item.name}</span>
            <span className="text-xs text-white/50">({item.percent}%)</span>
          </motion.div>
        ))}
      </div>
    </motion.div>
  );
}

