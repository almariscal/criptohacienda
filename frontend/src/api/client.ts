export type UploadResponse = {
  session_id: string;
};

export type SummaryResponse = {
  totalInvested: number;
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

export type DashboardResponse = {
  summary: SummaryResponse;
  gains: GainPoint[];
  operations: Operation[];
  holdings: Holding[];
};

export type DashboardFilters = {
  groupBy?: 'day' | 'month' | 'year';
  startDate?: string;
  endDate?: string;
  asset?: string;
  type?: string;
};

class ApiClient {
  constructor(private readonly baseUrl: string = '') {}

  async uploadBinanceCsv(file: File): Promise<UploadResponse> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${this.baseUrl}/api/upload/binance-csv`, {
      method: 'POST',
      body: formData
    });

    if (!response.ok) {
      throw new Error('No se pudo subir el archivo. Inténtalo de nuevo.');
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
      throw new Error('No se pudo obtener la información del dashboard.');
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
      throw new Error('No se pudo exportar el CSV.');
    }

    return response.blob();
  }
}

export const apiClient = new ApiClient();
