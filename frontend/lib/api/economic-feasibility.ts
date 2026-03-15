/**
 * API client for Economic Feasibility Analysis endpoints
 */

import axios from 'axios';
import type {
  FeasibilityAnalysis,
  FeasibilityRequest,
  CostIndices
} from '../types/economic-feasibility';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 60000, // 60 seconds for complex calculations
});

export const EconomicFeasibilityAPI = {
  /**
   * Compute economic feasibility analysis for a development scenario
   */
  async computeFeasibility(request: FeasibilityRequest): Promise<FeasibilityAnalysis> {
    const response = await apiClient.post<FeasibilityAnalysis>(
      '/api/v1/economic-feasibility/compute',
      request
    );
    return response.data;
  },

  /**
   * Get cost indices for a specific county
   */
  async getCostIndices(county?: string): Promise<CostIndices> {
    const response = await apiClient.get<CostIndices>(
      '/api/v1/economic-feasibility/cost-indices',
      { params: { county } }
    );
    return response.data;
  },

  /**
   * Get default assumptions for a county
   */
  async getDefaultAssumptions(county?: string): Promise<any> {
    const response = await apiClient.get(
      '/api/v1/economic-feasibility/defaults',
      { params: { county } }
    );
    return response.data;
  },
};

export default EconomicFeasibilityAPI;
