/**
 * API client for the Parcel Feasibility Engine backend
 */

import axios from 'axios';
import type { AnalysisRequest, AnalysisResponse, StateLawInfo, HealthCheck } from './types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
});

export class ParcelAPI {
  /**
   * Health check
   */
  static async healthCheck(): Promise<HealthCheck> {
    const response = await api.get<HealthCheck>('/health');
    return response.data;
  }

  /**
   * Analyze a parcel for development feasibility
   */
  static async analyzeParcel(request: AnalysisRequest): Promise<AnalysisResponse> {
    const response = await api.post<AnalysisResponse>('/api/v1/analyze', request);
    return response.data;
  }

  /**
   * Quick analysis returning only key metrics
   */
  static async quickAnalysis(request: AnalysisRequest): Promise<{
    parcel_apn: string;
    max_units_base: number;
    max_units_optimized: number;
    recommended_scenario: string;
    applicable_laws: string[];
    key_opportunities: string[];
  }> {
    const response = await api.post('/api/v1/quick-analysis', request);
    return response.data;
  }

  /**
   * Get information about a specific state housing law
   */
  static async getStateLawInfo(lawCode: string): Promise<StateLawInfo> {
    const response = await api.get<StateLawInfo>(`/api/v1/rules/${lawCode}`);
    return response.data;
  }

  /**
   * Get all available state laws
   */
  static async getAllStateLaws(): Promise<StateLawInfo[]> {
    const laws = ['sb9', 'sb35', 'ab2011', 'ab2097', 'density_bonus'];
    const promises = laws.map(law => this.getStateLawInfo(law));
    return Promise.all(promises);
  }

  /**
   * Export feasibility analysis as PDF
   * @param analysis - The analysis response to export
   * @returns Promise with PDF blob
   */
  static async exportFeasibilityPDF(analysis: AnalysisResponse): Promise<Blob> {
    const response = await api.post('/api/v1/export/pdf', analysis, {
      responseType: 'blob',  // Important: tells axios to return blob
    });

    return response.data;
  }
}

export default ParcelAPI;
