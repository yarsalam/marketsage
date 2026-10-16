import { Injectable, ServiceUnavailableException } from '@nestjs/common';
import axios from 'axios';

@Injectable()
export class MarketsService {
  private get baseUrl() {
    return (process.env.ANALYSIS_ENGINE_URL ?? 'http://analysis-engine:8000').replace(/\/$/, '');
  }

  private async getAnalysis(path: string) {
    try {
      const { data } = await axios.get(`${this.baseUrl}${path}`, {
        timeout: 12_000,
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
}
