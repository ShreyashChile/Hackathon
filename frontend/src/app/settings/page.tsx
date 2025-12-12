"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Sidebar } from "@/components/layout/Sidebar";
import { Header } from "@/components/layout/Header";
import { PageTransition } from "@/components/layout/PageTransition";
import { GlassCard } from "@/components/ui/GlassCard";
import { GlowButton } from "@/components/ui/GlowButton";
import { Badge } from "@/components/ui/Badge";
import { useAPIStatus, useRunAnalysis } from "@/hooks/useAPI";
import {
  Settings,
  Server,
  Database,
  RefreshCw,
  CheckCircle,
  XCircle,
  Zap,
  Bell,
  Palette,
} from "lucide-react";

export default function SettingsPage() {
  const { isConnected, isChecking, checkConnection } = useAPIStatus();
  const { runAnalysis, isRunning } = useRunAnalysis();
  const [showNotification, setShowNotification] = useState(false);

  const handleRunAnalysis = async () => {
    try {
      await runAnalysis();
      setShowNotification(true);
      setTimeout(() => setShowNotification(false), 3000);
    } catch (error) {
      console.error("Analysis failed:", error);
    }
  };

  return (
    <div className="flex min-h-screen">
      <Sidebar />

      <main className="flex-1 ml-64 p-6">
        <Header title="Settings" subtitle="Configure your dashboard preferences" />

        <PageTransition>
          {/* Notification Toast */}
          {showNotification && (
            <motion.div
              initial={{ opacity: 0, y: -50 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -50 }}
              className="fixed top-6 right-6 z-50 glass px-6 py-4 rounded-xl border border-emerald-500/30 flex items-center gap-3"
            >
              <CheckCircle className="w-5 h-5 text-emerald-400" />
              <span className="text-white">Analysis completed successfully!</span>
            </motion.div>
          )}

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* API Connection */}
            <GlassCard className="p-6" hover={false}>
              <div className="flex items-center gap-3 mb-6">
                <div className="p-3 rounded-xl bg-cyan-500/20">
                  <Server className="w-6 h-6 text-cyan-400" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-white">API Connection</h3>
                  <p className="text-sm text-white/50">Backend server status</p>
                </div>
              </div>

              <div className="space-y-4">
                <div className="flex items-center justify-between p-4 rounded-xl bg-white/5">
                  <div className="flex items-center gap-3">
                    {isChecking ? (
                      <motion.div
                        animate={{ rotate: 360 }}
                        transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                      >
                        <RefreshCw className="w-5 h-5 text-white/50" />
                      </motion.div>
                    ) : isConnected ? (
                      <CheckCircle className="w-5 h-5 text-emerald-400" />
                    ) : (
                      <XCircle className="w-5 h-5 text-rose-400" />
                    )}
                    <span className="text-white">Backend Status</span>
                  </div>
                  <Badge variant={isConnected ? "success" : "critical"}>
                    {isChecking ? "Checking..." : isConnected ? "Connected" : "Disconnected"}
                  </Badge>
                </div>

                <div className="flex items-center justify-between p-4 rounded-xl bg-white/5">
                  <div className="flex items-center gap-3">
                    <Database className="w-5 h-5 text-violet-400" />
                    <span className="text-white">API URL</span>
                  </div>
                  <code className="text-sm text-white/60 bg-white/5 px-3 py-1 rounded">
                    {process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}
                  </code>
                </div>

                <GlowButton
                  variant="secondary"
                  onClick={checkConnection}
                  className="w-full"
                  disabled={isChecking}
                >
                  <RefreshCw className="w-4 h-4" />
                  Test Connection
                </GlowButton>
              </div>
            </GlassCard>

            {/* Run Analysis */}
            <GlassCard className="p-6" hover={false}>
              <div className="flex items-center gap-3 mb-6">
                <div className="p-3 rounded-xl bg-violet-500/20">
                  <Zap className="w-6 h-6 text-violet-400" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-white">Analysis Pipeline</h3>
                  <p className="text-sm text-white/50">Run ML analysis on your data</p>
                </div>
              </div>

              <div className="space-y-4">
                <div className="p-4 rounded-xl bg-white/5">
                  <p className="text-sm text-white/70 mb-4">
                    Running the analysis pipeline will:
                  </p>
                  <ul className="space-y-2 text-sm text-white/60">
                    <li className="flex items-center gap-2">
                      <div className="w-1.5 h-1.5 rounded-full bg-cyan-400" />
                      Detect demand shifts using CUSUM and Moving Averages
                    </li>
                    <li className="flex items-center gap-2">
                      <div className="w-1.5 h-1.5 rounded-full bg-violet-400" />
                      Identify non-moving and dead stock inventory
                    </li>
                    <li className="flex items-center gap-2">
                      <div className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                      Perform ABC-XYZ segmentation
                    </li>
                    <li className="flex items-center gap-2">
                      <div className="w-1.5 h-1.5 rounded-full bg-amber-400" />
                      Calculate risk scores and generate alerts
                    </li>
                  </ul>
                </div>

                <GlowButton
                  onClick={handleRunAnalysis}
                  className="w-full"
                  disabled={!isConnected || isRunning}
                  loading={isRunning}
                >
                  {isRunning ? "Running Analysis..." : "Run Full Analysis"}
                </GlowButton>
              </div>
            </GlassCard>

            {/* Notifications */}
            <GlassCard className="p-6" hover={false}>
              <div className="flex items-center gap-3 mb-6">
                <div className="p-3 rounded-xl bg-amber-500/20">
                  <Bell className="w-6 h-6 text-amber-400" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-white">Notifications</h3>
                  <p className="text-sm text-white/50">Alert preferences</p>
                </div>
              </div>

              <div className="space-y-4">
                {["Critical Alerts", "High Priority", "Demand Shifts", "Non-Moving Items"].map(
                  (item, index) => (
                    <div
                      key={item}
                      className="flex items-center justify-between p-3 rounded-xl bg-white/5"
                    >
                      <span className="text-white">{item}</span>
                      <motion.button
                        whileTap={{ scale: 0.95 }}
                        className="w-12 h-6 rounded-full bg-cyan-500/30 relative"
                      >
                        <motion.div
                          initial={false}
                          animate={{ x: index < 2 ? 24 : 0 }}
                          className={`w-5 h-5 rounded-full absolute top-0.5 left-0.5 ${
                            index < 2 ? "bg-cyan-400" : "bg-white/30"
                          }`}
                        />
                      </motion.button>
                    </div>
                  )
                )}
              </div>
            </GlassCard>

            {/* Theme */}
            <GlassCard className="p-6" hover={false}>
              <div className="flex items-center gap-3 mb-6">
                <div className="p-3 rounded-xl bg-rose-500/20">
                  <Palette className="w-6 h-6 text-rose-400" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-white">Appearance</h3>
                  <p className="text-sm text-white/50">Visual preferences</p>
                </div>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="text-sm text-white/60 mb-2 block">Theme</label>
                  <div className="grid grid-cols-2 gap-2">
                    <motion.button
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                      className="p-3 rounded-xl bg-gradient-to-r from-violet-500/20 to-cyan-500/20 border border-cyan-500/30 text-white text-sm font-medium"
                    >
                      Dark (Active)
                    </motion.button>
                    <motion.button
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                      className="p-3 rounded-xl bg-white/5 border border-white/10 text-white/50 text-sm font-medium"
                    >
                      Light
                    </motion.button>
                  </div>
                </div>

                <div>
                  <label className="text-sm text-white/60 mb-2 block">Accent Color</label>
                  <div className="flex gap-2">
                    {[
                      { color: "bg-cyan-500", name: "Cyan" },
                      { color: "bg-violet-500", name: "Violet" },
                      { color: "bg-rose-500", name: "Rose" },
                      { color: "bg-emerald-500", name: "Emerald" },
                      { color: "bg-amber-500", name: "Amber" },
                    ].map(({ color, name }) => (
                      <motion.button
                        key={name}
                        whileHover={{ scale: 1.1 }}
                        whileTap={{ scale: 0.95 }}
                        title={name}
                        className={`w-8 h-8 rounded-full ${color} ${
                          name === "Cyan" ? "ring-2 ring-white ring-offset-2 ring-offset-[#0f0f23]" : ""
                        }`}
                      />
                    ))}
                  </div>
                </div>
              </div>
            </GlassCard>
          </div>

          {/* About */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="mt-6"
          >
            <GlassCard className="p-6" hover={false}>
              <div className="flex items-center gap-3 mb-4">
                <div className="p-3 rounded-xl bg-gradient-to-br from-violet-500/20 to-cyan-500/20">
                  <Settings className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-white">ML Inventory Agent</h3>
                  <p className="text-sm text-white/50">Version 1.0.0</p>
                </div>
              </div>
              <p className="text-sm text-white/60">
                An AI-powered inventory management system that detects demand shifts, identifies
                non-moving inventory, performs ABC-XYZ segmentation, and generates intelligent
                alerts for proactive supply chain management.
              </p>
              <div className="flex gap-4 mt-4">
                <Badge variant="info">Next.js 14</Badge>
                <Badge variant="info">FastAPI</Badge>
                <Badge variant="info">Python ML</Badge>
                <Badge variant="info">Framer Motion</Badge>
              </div>
            </GlassCard>
          </motion.div>
        </PageTransition>
      </main>
    </div>
  );
}

