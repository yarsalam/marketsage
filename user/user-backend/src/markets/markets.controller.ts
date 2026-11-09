import {
  BadRequestException,
  Controller,
  Get,
  Query,
  ServiceUnavailableException,
} from '@nestjs/common';
import { MarketsService } from './markets.service';

@Controller('api/markets')
export class MarketsController {
  constructor(private readonly marketsService: MarketsService) {}

  @Get()
  getMarkets() {
    return this.marketsService.listMarkets();
  }

  @Get('scores')
  getScores() {
    this.assertResearchOutputsEnabled();
    return this.marketsService.getScores();
  }

  @Get('backtest')
  getBacktest(
    @Query('top_n') topN = '3',
    @Query('transaction_cost_bps') transactionCostBps = '10',
  ) {
    this.assertResearchOutputsEnabled();
    const topNValue = Number(topN);
    const costValue = Number(transactionCostBps);
    if (!Number.isInteger(topNValue) || topNValue < 1 || topNValue > 10) {
      throw new BadRequestException('top_n must be an integer between 1 and 10');
    }
    if (!Number.isFinite(costValue) || costValue < 0 || costValue > 1000) {
      throw new BadRequestException('transaction_cost_bps must be between 0 and 1000');
    }
    return this.marketsService.getBacktest(String(topNValue), String(costValue));
  }

  @Get('data-status')
  getDataStatus() {
    return this.marketsService.getDataStatus();
  }

  @Get('instruments')
  getInstruments() {
    return this.marketsService.getInstruments();
  }

  @Get('sources')
  getSources() {
    return this.marketsService.getSources();
  }

  @Get('data-quality')
  getDataQuality() {
    return this.marketsService.getDataQuality();
  }

  @Get('iran-providers')
  getIranProviders() {
    return this.marketsService.getIranProviders();
  }

  private assertResearchOutputsEnabled(): void {
    if (process.env.MARKETSAGE_RESEARCH_OUTPUTS_ENABLED !== 'true') {
      throw new ServiceUnavailableException(
        'Research outputs are disabled until source and methodology validation is approved.',
      );
    }
  }
}
