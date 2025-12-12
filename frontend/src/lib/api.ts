const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// Types based on FastAPI backend schemas
export interface DashboardSummary {
  overview: {
    total_sku_locations: number;
    unique_skus: number;
    unique_locations: number;
  };
  demand_shifts: {
    total_shifts: number;
    increases: number;
    decreases: number;
  };
  non_moving: {
    dead_stock: number;
    non_moving: number;
    slow_moving: number;
    active: number;
  };
  risk_levels: Record<string, number>;
  alerts: {
    total: number;
    critical: number;
    high: number;
  };
}

export interface DemandShift {
  item_id: string;
  location_id: string;
  shift_detected: boolean;
  shift_type?: string;
  shift_direction: string;
  shift_magnitude: number;
  confidence_score: number;
  detection_date?: string;
  baseline_demand?: number;
  current_demand?: number;
  category?: string;
}

export interface NonMovingItem {
  item_id: string;
  location_id: string;
  days_since_movement: number;
  movement_category: string;
  current_inventory: number;
  non_moving_risk_score: number;
  last_movement_date: string;
  category?: string;
  recommended_action?: string;
  shelf_life_at_risk?: boolean;
}

export interface SegmentationResult {
  item_id: string;
  location_id: string;
  abc_class: string;
  xyz_class: string;
  segment: string;
  total_qty: number;
  cv: number;
  category?: string;
  description?: string;
}

export interface Alert {
  alert_id: string;
  item_id: string;
  location_id: string;
  alert_type: string;
  priority: "P1_CRITICAL" | "P2_HIGH" | "P3_MEDIUM" | "P4_LOW" | "P5_INFO";
  message: string;
  created_at: string;
  is_active: boolean;
  category?: string;
}

export interface RiskScore {
  item_id: string;
  location_id: string;
  risk_score: number;
  risk_factors: Record<string, number>;
  recommendation: string;
  category?: string;
}

export interface SKUAnalysis {
  item_id: string;
  locations: string[];
  demand_shifts: DemandShift[];
  non_moving_status: NonMovingItem[];
  segmentation: SegmentationResult[];
  risk_scores: RiskScore[];
  overall_status: string;
}

// API functions
async function fetchAPI<T>(endpoint: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${endpoint}`);
  if (!response.ok) {
    throw new Error(`API Error: ${response.status} ${response.statusText}`);
  }
  return response.json();
}

async function postAPI<T>(endpoint: string, data?: unknown): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: data ? JSON.stringify(data) : undefined,
  });
  if (!response.ok) {
    throw new Error(`API Error: ${response.status} ${response.statusText}`);
  }
  return response.json();
}

// Response wrapper type for list endpoints
interface ListResponse<T> {
  total: number;
  data: T[];
}

export const api = {
  // Dashboard
  getDashboardSummary: () => fetchAPI<DashboardSummary>("/api/dashboard/summary"),

  // Demand Shifts
  getDemandShifts: async (params?: { location?: string; direction?: string }): Promise<DemandShift[]> => {
    const searchParams = new URLSearchParams();
    if (params?.location) searchParams.set("location_id", params.location);
    if (params?.direction) searchParams.set("shift_direction", params.direction);
    const query = searchParams.toString();
    const response = await fetchAPI<ListResponse<DemandShift>>(`/api/demand-shifts${query ? `?${query}` : ""}`);
    return response.data || [];
  },

  // Non-Moving
  getNonMoving: async (params?: { location?: string; category?: string }): Promise<NonMovingItem[]> => {
    const searchParams = new URLSearchParams();
    if (params?.location) searchParams.set("location_id", params.location);
    if (params?.category) searchParams.set("category", params.category);
    const query = searchParams.toString();
    const response = await fetchAPI<ListResponse<NonMovingItem>>(`/api/non-moving${query ? `?${query}` : ""}`);
    return response.data || [];
  },

  // Segmentation
  getSegmentation: async (params?: { segment?: string }): Promise<SegmentationResult[]> => {
    const searchParams = new URLSearchParams();
    if (params?.segment) searchParams.set("segment", params.segment);
    const query = searchParams.toString();
    const response = await fetchAPI<ListResponse<SegmentationResult>>(`/api/segmentation${query ? `?${query}` : ""}`);
    return response.data || [];
  },

  // Alerts
  getAlerts: async (params?: { priority?: string; active_only?: boolean }): Promise<Alert[]> => {
    const searchParams = new URLSearchParams();
    if (params?.priority) searchParams.set("priority", params.priority);
    if (params?.active_only !== undefined) searchParams.set("active_only", String(params.active_only));
    const query = searchParams.toString();
    const response = await fetchAPI<ListResponse<Alert>>(`/api/alerts${query ? `?${query}` : ""}`);
    return response.data || [];
  },

  // Risk Scores
  getRiskScores: async (params?: { min_score?: number }): Promise<RiskScore[]> => {
    const searchParams = new URLSearchParams();
    if (params?.min_score) searchParams.set("min_score", String(params.min_score));
    const query = searchParams.toString();
    const response = await fetchAPI<ListResponse<RiskScore>>(`/api/risk-scores${query ? `?${query}` : ""}`);
    return response.data || [];
  },

  // SKU Analysis
  getSKUAnalysis: (skuId: string) => fetchAPI<SKUAnalysis>(`/api/sku/${skuId}/analysis`),

  // Run Analysis
  runAnalysis: () => postAPI<{ status: string; message: string }>("/api/run-analysis"),

  // Health check
  getStatus: () => fetchAPI<{ status: string; version: string }>("/api/status"),
};

