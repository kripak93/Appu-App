import axios from "axios";

const API_BASE = "http://localhost:8000";

// --- Simulation Types ---

export interface PeriodInput {
  price_level: string;
  restrictions: number;
  push: number;
}

export interface SimulationRequest {
  p: number;
  q: number;
  M: number;
  beta1: number;
  beta2: number;
  beta3: number;
  r: number;
  period_inputs: PeriodInput[];
}

export interface SimulationResponse {
  periods: number[];
  cumulative_adoption: number[];
  new_adopters: number[];
  replacement_sales: number[];
  total_sales: number[];
  cumulative_sales: number[];
}

// --- Estimation Types ---

export interface EstimationResponse {
  p: number;
  q: number;
  M: number;
  sse: number;
  mse: number;
  rmse: number;
  mae: number;
  mape: number;
  r_squared: number;
  predicted_sales: number[];
  observed_sales: number[];
  periods: number[];
}

// --- API Calls ---

export async function runSimulation(
  request: SimulationRequest
): Promise<SimulationResponse> {
  const response = await axios.post<SimulationResponse>(
    `${API_BASE}/simulate`,
    request
  );
  return response.data;
}

export async function estimateFromData(
  salesData: number[]
): Promise<EstimationResponse> {
  const response = await axios.post<EstimationResponse>(
    `${API_BASE}/estimate`,
    { sales_data: salesData }
  );
  return response.data;
}

export async function estimateFromCSV(
  file: File
): Promise<EstimationResponse> {
  const formData = new FormData();
  formData.append("file", file);
  const response = await axios.post<EstimationResponse>(
    `${API_BASE}/estimate/csv`,
    formData,
    { headers: { "Content-Type": "multipart/form-data" } }
  );
  return response.data;
}

export async function getDefaults() {
  const response = await axios.get(`${API_BASE}/defaults`);
  return response.data;
}
