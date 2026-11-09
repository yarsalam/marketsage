import { ServiceUnavailableException } from '@nestjs/common';
import axios from 'axios';
import { MarketsService } from './markets.service';

jest.mock('axios');

const mockedAxios = jest.mocked(axios);

describe('MarketsService source observability endpoints', () => {
  let service: MarketsService;
  const originalAnalysisUrl = process.env.ANALYSIS_ENGINE_URL;

  beforeEach(() => {
    jest.clearAllMocks();
    process.env.ANALYSIS_ENGINE_URL = 'http://analysis-engine:8000/';
    service = new MarketsService();
  });

  afterAll(() => {
    if (originalAnalysisUrl === undefined) {
      delete process.env.ANALYSIS_ENGINE_URL;
    } else {
      process.env.ANALYSIS_ENGINE_URL = originalAnalysisUrl;
    }
  });

  it.each([
    ['getSources', '/sources'],
    ['getInstruments', '/instruments'],
    ['getDataQuality', '/data-quality'],
    ['getIranProviders', '/iran-market/providers'],
  ] as const)('forwards %s to the matching analysis endpoint', async (method, path) => {
    const response = { data: { source: path, verified: false } };
    mockedAxios.get.mockResolvedValue(response as never);

    const result = await service[method]();

    expect(result).toEqual(response.data);
    expect(mockedAxios.get).toHaveBeenCalledWith(
      `http://analysis-engine:8000${path}`,
      expect.objectContaining({
        timeout: 45_000,
        headers: { Accept: 'application/json' },
      }),
    );
  });

  it('returns a bounded service-unavailable error when the analysis engine is unreachable', async () => {
    mockedAxios.get.mockRejectedValue(new Error('internal network detail'));

    await expect(service.getSources()).rejects.toBeInstanceOf(ServiceUnavailableException);
    await expect(service.getInstruments()).rejects.toBeInstanceOf(ServiceUnavailableException);
    await expect(service.getDataQuality()).rejects.toBeInstanceOf(ServiceUnavailableException);
    await expect(service.getIranProviders()).rejects.toBeInstanceOf(ServiceUnavailableException);
  });
});
