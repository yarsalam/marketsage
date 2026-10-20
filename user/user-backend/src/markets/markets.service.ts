import { Injectable, ServiceUnavailableException, UnprocessableEntityException } from '@nestjs/common';
import axios from 'axios';

@Injectable()
export class MarketsService {
  private get baseUrl() {
    return (process.env.ANALYSIS_ENGINE_URL ?? 'http://analysis-engine:8000').replace(/\/$/, '');
  }

  private async getAnalysis(path: string) {
    try {
      const { data } = await axios.get(`${this.baseUrl}${path}`, {
        timeout: 45_000,
        headers: { Accept: 'application/json' },
      });
      return data;
    } catch {
      throw new ServiceUnavailableException(
        'Market data or analysis is temporarily unavailable.',
      );
    }
  }

  listMarkets() {
    return this.getAnalysis('/markets');
  }

  getScores() {
    return this.getAnalysis('/scores');
  }

  getBacktest(topN = '3', transactionCostBps = '10') {
    return this.getAnalysis(`/backtest?top_n=${encodeURIComponent(topN)}&transaction_cost_bps=${encodeURIComponent(transactionCostBps)}`);
  }

  getDataStatus() {
    return this.getAnalysis('/data-status');
  }

  async getResearchSnapshot(payload: Record<string, unknown>) {
    try {
      const { data } = await axios.post(`${this.baseUrl}/research/snapshot`, payload, {
        timeout: 45_000,
        headers: { Accept: 'application/json', 'Content-Type': 'application/json' },
      });
      return data;
    } catch (error) {
      if (axios.isAxiosError(error) && error.response?.status === 422) {
        throw new UnprocessableEntityException('Research snapshot input failed validation.');
      }
      throw new ServiceUnavailableException(
        'Research snapshot is temporarily unavailable.',
      );
    }
  }
}
