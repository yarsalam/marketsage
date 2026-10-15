import {
  BadRequestException,
  Controller,
  Get,
  Query,
  ServiceUnavailableException,
} from '@nestjs/common';
import axios from 'axios';

const ALLOWED_HORIZONS = new Set(['1W', '1M', '3M', '6M']);

@Controller('api/decision')
export class DecisionController {
  @Get()
  async getDecision(
    @Query('horizon') horizon = '1M',
    @Query('capital') capitalInput = '500000000',
    @Query('top_n') topNInput = '5',
  ) {
    if (!ALLOWED_HORIZONS.has(horizon)) {
      throw new BadRequestException('Unsupported horizon. Use 1W, 1M, 3M, or 6M.');
    }

    const capital = Number(capitalInput);
    const topN = Number(topNInput);
    if (!Number.isFinite(capital) || capital < 0 || capital > 1e15) {
      throw new BadRequestException('capital must be a number between 0 and 1e15.');
    }
    if (!Number.isInteger(topN) || topN < 1 || topN > 10) {
      throw new BadRequestException('top_n must be an integer between 1 and 10.');
    }

    const baseUrl = (process.env.ANALYSIS_ENGINE_URL ?? 'http://analysis-engine:8000')
      .replace(/\/$/, '');

    try {
      const { data } = await axios.get(`${baseUrl}/decision`, {
        params: { horizon, capital, top_n: topN },
        timeout: 12_000,
        headers: { Accept: 'application/json' },
      });
      return data;
    } catch (error) {
      if (axios.isAxiosError(error)) {
        throw new ServiceUnavailableException(
          error.response?.status === 503
            ? 'Analysis engine or market data is temporarily unavailable.'
            : 'Unable to obtain a decision from the analysis engine.',
        );
      }
      throw error;
    }
  }
}
