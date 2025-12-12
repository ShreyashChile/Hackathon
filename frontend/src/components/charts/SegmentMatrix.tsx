"use client";

import React from "react";
import { motion } from "framer-motion";

interface SegmentData {
  segment: string;
  count: number;
  percentage: number;
}

interface SegmentMatrixProps {
  data: SegmentData[];
  title?: string;
}

// ABC-XYZ color mapping
const segmentColors: Record<string, { bg: string; text: string; border: string }> = {
  AX: { bg: "bg-emerald-500/30", text: "text-emerald-300", border: "border-emerald-500/50" },
  AY: { bg: "bg-emerald-500/20", text: "text-emerald-400", border: "border-emerald-500/30" },
  AZ: { bg: "bg-amber-500/20", text: "text-amber-400", border: "border-amber-500/30" },
  BX: { bg: "bg-cyan-500/20", text: "text-cyan-400", border: "border-cyan-500/30" },
  BY: { bg: "bg-cyan-500/15", text: "text-cyan-400", border: "border-cyan-500/20" },
  BZ: { bg: "bg-amber-500/25", text: "text-amber-300", border: "border-amber-500/40" },
  CX: { bg: "bg-violet-500/15", text: "text-violet-400", border: "border-violet-500/20" },
  CY: { bg: "bg-violet-500/20", text: "text-violet-300", border: "border-violet-500/30" },
  CZ: { bg: "bg-rose-500/20", text: "text-rose-400", border: "border-rose-500/30" },
};

const segmentDescriptions: Record<string, string> = {
  AX: "High value, stable demand",
  AY: "High value, variable demand",
  AZ: "High value, erratic demand",
  BX: "Medium value, stable demand",
  BY: "Medium value, variable demand",
  BZ: "Medium value, erratic demand",
  CX: "Low value, stable demand",
  CY: "Low value, variable demand",
  CZ: "Low value, erratic demand",
};

export function SegmentMatrix({ data, title }: SegmentMatrixProps) {
  // Create a 3x3 matrix
  const abcRows = ["A", "B", "C"];
  const xyzCols = ["X", "Y", "Z"];

  const getSegmentData = (abc: string, xyz: string) => {
    const segment = `${abc}${xyz}`;
    return data.find((d) => d.segment === segment) || { segment, count: 0, percentage: 0 };
  };

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.5 }}
      className="glass-card p-6"
    >
      {title && (
        <h3 className="text-lg font-semibold text-white mb-6">{title}</h3>
      )}

      {/* Matrix header */}
      <div className="grid grid-cols-4 gap-2 mb-2">
        <div /> {/* Empty corner */}
        {xyzCols.map((col) => (
          <div key={col} className="text-center">
            <span className="text-sm font-semibold text-white/70">{col}</span>
            <p className="text-xs text-white/40">
              {col === "X" ? "Stable" : col === "Y" ? "Variable" : "Erratic"}
            </p>
          </div>
        ))}
      </div>

      {/* Matrix body */}
      <div className="grid grid-cols-4 gap-2">
        {abcRows.map((row) => (
          <React.Fragment key={row}>
            {/* Row label */}
            <div className="flex flex-col justify-center">
              <span className="text-sm font-semibold text-white/70">{row}</span>
              <p className="text-xs text-white/40">
                {row === "A" ? "High" : row === "B" ? "Medium" : "Low"}
              </p>
            </div>
            {/* Cells */}
            {xyzCols.map((col, colIndex) => {
              const segment = `${row}${col}`;
              const segmentData = getSegmentData(row, col);
              const colors = segmentColors[segment];

              return (
                <motion.div
                  key={segment}
                  initial={{ opacity: 0, scale: 0 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{
                    delay: 0.1 * (abcRows.indexOf(row) * 3 + colIndex),
                    type: "spring",
                    stiffness: 200,
                  }}
                  whileHover={{ scale: 1.05 }}
                  className={`
                    ${colors.bg} ${colors.border}
                    border rounded-xl p-4 text-center cursor-pointer
                    transition-all duration-300 hover:shadow-lg
                  `}
                  title={segmentDescriptions[segment]}
                >
                  <p className={`text-2xl font-bold ${colors.text}`}>
                    {segmentData.count}
                  </p>
                  <p className="text-xs text-white/50 mt-1">
                    {segmentData.percentage.toFixed(1)}%
                  </p>
                  <p className="text-xs text-white/30 mt-0.5">{segment}</p>
                </motion.div>
              );
            })}
          </React.Fragment>
        ))}
      </div>

      {/* Legend */}
      <div className="mt-6 pt-4 border-t border-white/10">
        <p className="text-xs text-white/40 mb-2">ABC: Volume/Value | XYZ: Demand Variability</p>
        <div className="flex flex-wrap gap-2">
          <span className="text-xs px-2 py-1 rounded bg-emerald-500/20 text-emerald-400">
            Best performers
          </span>
          <span className="text-xs px-2 py-1 rounded bg-amber-500/20 text-amber-400">
            Needs attention
          </span>
          <span className="text-xs px-2 py-1 rounded bg-rose-500/20 text-rose-400">
            High risk
          </span>
        </div>
      </div>
    </motion.div>
  );
}

// Simple segment badge component
export function SegmentBadge({ segment }: { segment: string }) {
  const colors = segmentColors[segment] || {
    bg: "bg-white/10",
    text: "text-white/70",
    border: "border-white/20",
  };

  return (
    <span
      className={`
        inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold
        ${colors.bg} ${colors.text} ${colors.border} border
      `}
    >
      {segment}
    </span>
  );
}

