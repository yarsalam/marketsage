import { BadRequestException } from '@nestjs/common';
import { MarketsController } from './markets.controller';

describe('MarketsController', () => {
  const marketsService = {
    listMarkets: jest.fn(),
    getScores: jest.fn(),
    getBacktest: jest.fn(),
    getDataStatus: jest.fn(),
    getSources: jest.fn(),
    getDataQuality: jest.fn(),
    getIranProviders: jest.fn(),
  };
  let controller: MarketsController;

  beforeEach(() => {
    jest.clearAllMocks();
    controller = new MarketsController(marketsService as never);
  });

  it('rejects invalid top_n before calling the analysis service', () => {
    expect(() => controller.getBacktest('0', '10')).toThrow(BadRequestException);
    expect(marketsService.getBacktest).not.toHaveBeenCalled();
  });

  it('rejects invalid transaction-cost assumptions', () => {
    expect(() => controller.getBacktest('3', '1001')).toThrow(BadRequestException);
    expect(marketsService.getBacktest).not.toHaveBeenCalled();
  });

  it('forwards the source registry request', () => {
    controller.getSources();
    expect(marketsService.getSources).toHaveBeenCalledTimes(1);
  });

  it('forwards the data-quality request', () => {
    controller.getDataQuality();
    expect(marketsService.getDataQuality).toHaveBeenCalledTimes(1);
  });

  it('forwards the Iranian provider readiness request', () => {
    controller.getIranProviders();
    expect(marketsService.getIranProviders).toHaveBeenCalledTimes(1);
  });

  it('forwards validated backtest parameters', () => {
    controller.getBacktest('4', '15');
    expect(marketsService.getBacktest).toHaveBeenCalledWith('4', '15');
  });
});
