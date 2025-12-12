"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { api } from "@/lib/api";
import type {
  DashboardSummary,
  DemandShift,
  NonMovingItem,
  SegmentationResult,
  Alert,
  RiskScore,
  SKUAnalysis,
} from "@/lib/api";

// Generic hook for data fetching with proper dependency handling
function useQuery<T>(
  fetcher: () => Promise<T>,
  deps: unknown[] = []
) {
  const [data, setData] = useState<T | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const fetcherRef = useRef(fetcher);
  const mountedRef = useRef(true);
  
  // Update fetcher ref when it changes
  fetcherRef.current = fetcher;

  const refetch = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const result = await fetcherRef.current();
      if (mountedRef.current) {
        setData(result);
      }
    } catch (e) {
      if (mountedRef.current) {
        setError(e instanceof Error ? e : new Error("Unknown error"));
      }
    } finally {
      if (mountedRef.current) {
        setIsLoading(false);
      }
    }
  }, []);

  useEffect(() => {
    mountedRef.current = true;
    refetch();
    return () => {
      mountedRef.current = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  return { data, isLoading, error, refetch };
}

// Dashboard summary hook
export function useDashboardSummary() {
  return useQuery<DashboardSummary>(
    () => api.getDashboardSummary(),
    []
  );
}

// Demand shifts hook
export function useDemandShifts(params?: { location?: string; direction?: string }) {
  return useQuery<DemandShift[]>(
    () => api.getDemandShifts(params),
    [params?.location, params?.direction]
  );
}

// Non-moving inventory hook
export function useNonMoving(params?: { location?: string; category?: string }) {
  return useQuery<NonMovingItem[]>(
    () => api.getNonMoving(params),
    [params?.location, params?.category]
  );
}

// Segmentation hook
export function useSegmentation(params?: { segment?: string }) {
  return useQuery<SegmentationResult[]>(
    () => api.getSegmentation(params),
    [params?.segment]
  );
}

// Alerts hook
export function useAlerts(params?: { priority?: string; active_only?: boolean }) {
  return useQuery<Alert[]>(
    () => api.getAlerts(params),
    [params?.priority, params?.active_only]
  );
}

// Risk scores hook
export function useRiskScores(params?: { min_score?: number }) {
  return useQuery<RiskScore[]>(
    () => api.getRiskScores(params),
    [params?.min_score]
  );
}

// SKU analysis hook
export function useSKUAnalysis(skuId: string | null) {
  const [data, setData] = useState<SKUAnalysis | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const refetch = useCallback(async () => {
    if (!skuId) {
      setData(null);
      return;
    }
    setIsLoading(true);
    setError(null);
    try {
      const result = await api.getSKUAnalysis(skuId);
      setData(result);
    } catch (e) {
      setError(e instanceof Error ? e : new Error("Unknown error"));
    } finally {
      setIsLoading(false);
    }
  }, [skuId]);

  useEffect(() => {
    refetch();
  }, [refetch]);

  return { data, isLoading, error, refetch };
}

// Run analysis mutation hook
export function useRunAnalysis() {
  const [isRunning, setIsRunning] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [result, setResult] = useState<{ status: string; message: string } | null>(null);

  const runAnalysis = useCallback(async () => {
    setIsRunning(true);
    setError(null);
    try {
      const response = await api.runAnalysis();
      setResult(response);
      return response;
    } catch (e) {
      setError(e instanceof Error ? e : new Error("Unknown error"));
      throw e;
    } finally {
      setIsRunning(false);
    }
  }, []);

  return { runAnalysis, isRunning, error, result };
}

// Connection status hook
export function useAPIStatus() {
  const [isConnected, setIsConnected] = useState(false);
  const [isChecking, setIsChecking] = useState(true);

  const checkConnection = useCallback(async () => {
    setIsChecking(true);
    try {
      await api.getStatus();
      setIsConnected(true);
    } catch {
      setIsConnected(false);
    } finally {
      setIsChecking(false);
    }
  }, []);

  useEffect(() => {
    checkConnection();
    // Check connection every 30 seconds
    const interval = setInterval(checkConnection, 30000);
    return () => clearInterval(interval);
  }, [checkConnection]);

  return { isConnected, isChecking, checkConnection };
}
