import { BadRequestException, Body, Controller, Get, Post, Query } from '@nestjs/common';
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
    return this.marketsService.getScores();
  }

  @Get('backtest')
  getBacktest(
    @Query('top_n') topN = '3',
    @Query('transaction_cost_bps') transactionCostBps = '10',
  ) {
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

  @Get('iran/data-status')
  getIranDataStatus() {
    return this.marketsService.getIranDataStatus();
  }

  @Get('iran/currency-rates')
  getIranCurrencyRates() {
    return this.marketsService.getIranCurrencyRates();
  }

  @Get('iran/opportunities')
  getIranOpportunities() {
    return this.marketsService.getIranOpportunities();
  }

  @Post('iran/refresh')
  refreshIranData() {
    return this.marketsService.refreshIranData();
  }

  @Get('data-status')
  getDataStatus() {
    return this.marketsService.getDataStatus();
  }

  @Post('research-snapshot')
  getResearchSnapshot(@Body() payload: Record<string, unknown>) {
    return this.marketsService.getResearchSnapshot(payload);
  }
}
