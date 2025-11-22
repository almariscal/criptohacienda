export type UploadResponse = {
  session_id: string;
};

export type SummaryResponse = {
  totalInvested: number;
  totalWithdrawn: number;
  currentBalance: number;
  totalFees: number;
  realizedGains: number;
  unrealizedGains: number;
};

export type GainPoint = {
  period: string;
  gain: number;
};

export type Operation = {
  id: string;
  date: string;
  asset: string;
  type: string;
  amount: number;
  price: number;
  fee?: number;
  total?: number;
};

export type Holding = {
  asset: string;
  quantity: number;
  averagePrice: number;
  currentValue: number;
};

export type PortfolioSnapshot = {
  timestamp: string;
  totalValue: number;
  assetValues: Record<string, number>;
};

export type DashboardResponse = {
  summary: SummaryResponse;
  gains: GainPoint[];
  operations: Operation[];
  holdings: Holding[];
  portfolioHistory: PortfolioSnapshot[];
};

export type DashboardFilters = {
  groupBy?: 'day' | 'month' | 'year';
  startDate?: string;
  endDate?: string;
  asset?: string;
  type?: string;
};

const FALLBACK_API_PORT = import.meta.env.VITE_API_PORT?.trim() || '8000';

const normalizeBaseUrl = (value: string): string => value.replace(/\/+$/, '');

const resolveApiBaseUrl = (): string => {
  const configured = import.meta.env.VITE_API_BASE_URL?.trim();
  if (configured) {
    return normalizeBaseUrl(configured);
  }

  if (typeof window !== 'undefined') {
    const { protocol, hostname } = window.location;
    return normalizeBaseUrl(`${protocol}//${hostname}:${FALLBACK_API_PORT}`);
  }

  return '';
};

const API_BASE_URL = resolveApiBaseUrl();

class ApiClient {
  constructor(private readonly baseUrl: string = '') {}

  private async buildError(response: Response, fallbackMessage: string): Promise<Error> {
    try {
      const data = await response.json();
      if (typeof data === 'string' && data.trim().length > 0) {
        return new Error(data);
      }
      if (typeof data?.detail === 'string' && data.detail.trim().length > 0) {
        return new Error(data.detail);
      }
      if (data?.detail && typeof data.detail === 'object') {
        return new Error(JSON.stringify(data.detail));
      }
      if (typeof data?.message === 'string' && data.message.trim().length > 0) {
        return new Error(data.message);
      }
    } catch {
      // Ignore parser errors and fall back to the provided message.
    }
    return new Error(fallbackMessage);
  }

  async uploadBinanceCsv(file: File): Promise<UploadResponse> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${this.baseUrl}/api/upload/binance-csv`, {
      method: 'POST',
      body: formData
    });

    if (!response.ok) {
      throw await this.buildError(response, 'No se pudo subir el archivo. Inténtalo de nuevo.');
    }

    return response.json();
  }

  async fetchDashboard(sessionId: string, filters: DashboardFilters): Promise<DashboardResponse> {
    const params = new URLSearchParams();
    params.append('session_id', sessionId);
    if (filters.groupBy) params.append('group_by', filters.groupBy);
    if (filters.startDate) params.append('start_date', filters.startDate);
    if (filters.endDate) params.append('end_date', filters.endDate);
    if (filters.asset) params.append('asset', filters.asset);
    if (filters.type) params.append('type', filters.type);

    const response = await fetch(`${this.baseUrl}/api/dashboard?${params.toString()}`);
    if (!response.ok) {
      throw await this.buildError(response, 'No se pudo obtener la información del dashboard.');
    }

    return response.json();
  }

  async exportOperationsCsv(sessionId: string, filters: DashboardFilters): Promise<Blob> {
    const params = new URLSearchParams();
    params.append('session_id', sessionId);
    if (filters.startDate) params.append('start_date', filters.startDate);
    if (filters.endDate) params.append('end_date', filters.endDate);
    if (filters.asset) params.append('asset', filters.asset);
    if (filters.type) params.append('type', filters.type);

    const response = await fetch(`${this.baseUrl}/api/export/operations?${params.toString()}`);
    if (!response.ok) {
      throw await this.buildError(response, 'No se pudo exportar el CSV.');
    }

    return response.blob();
  }
}

export const apiClient = new ApiClient(API_BASE_URL);
