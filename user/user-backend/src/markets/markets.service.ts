import { Injectable, ServiceUnavailableException } from '@nestjs/common';
import axios from 'axios';

@Injectable()
export class MarketsService {
  async listMarkets() {
    const baseUrl = (process.env.ANALYSIS_ENGINE_URL ?? 'http://analysis-engine:8000')
      .replace(/\/$/, '');

    try {
      const { data } = await axios.get(`${baseUrl}/markets`, {
        timeout: 5_000,
        headers: { Accept: 'application/json' },
      });
      return data;
    } catch {
      throw new ServiceUnavailableException(
        'Market universe metadata is temporarily unavailable.',
      );
    }
  }
}
