import { OpsService } from './ops.service';

describe('OpsService', () => {
  const originalEnv = process.env;
  const originalFetch = global.fetch;

  beforeEach(() => {
    process.env = { ...originalEnv };
    delete process.env.MARKETSAGE_ADMIN_OPS_ENABLED;
    delete process.env.MARKETSAGE_USER_API_URL;
    delete process.env.ANALYSIS_ENGINE_URL;
  });

  afterAll(() => {
    process.env = originalEnv;
    global.fetch = originalFetch;
  });

  it('fails closed and does not probe services by default', async () => {
    const fetchMock = jest.fn();
    global.fetch = fetchMock as unknown as typeof fetch;
    const result = await new OpsService().getStatus();

    expect(result.enabled).toBe(false);
    expect(result.access).toBe('read_only');
    expect(result.services).toEqual({
      userBackend: 'disabled',
      analysisEngine: 'disabled',
    });
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it('reports missing service configuration without inventing health', async () => {
    process.env.MARKETSAGE_ADMIN_OPS_ENABLED = 'true';
    const result = await new OpsService().getStatus();

    expect(result.services).toEqual({
      userBackend: 'not_configured',
      analysisEngine: 'not_configured',
    });
  });

  it('sanitizes failed probes and never returns target/error details', async () => {
    process.env.MARKETSAGE_ADMIN_OPS_ENABLED = 'true';
    process.env.MARKETSAGE_USER_API_URL = 'http://private-host.invalid:4500';
    global.fetch = jest.fn().mockRejectedValue(new Error('private diagnostic value')) as unknown as typeof fetch;

    const result = await new OpsService().getStatus();
    expect(result.services.userBackend).toBe('unavailable');
    expect(JSON.stringify(result)).not.toContain('private-host');
    expect(JSON.stringify(result)).not.toContain('private diagnostic value');
  });

  it('marks only a valid health response healthy', async () => {
    process.env.MARKETSAGE_ADMIN_OPS_ENABLED = 'true';
    process.env.MARKETSAGE_USER_API_URL = 'http://localhost:4500';
    const response = {
      ok: true,
      json: async () => ({ status: 'ok', service: 'user-backend' }),
    };
    global.fetch = jest.fn().mockResolvedValue(response) as unknown as typeof fetch;

    const result = await new OpsService().getStatus();
    expect(result.services.userBackend).toBe('healthy');
    expect(global.fetch).toHaveBeenCalledWith(
      'http://localhost:4500/health',
      expect.objectContaining({ method: 'GET', signal: expect.any(AbortSignal) }),
    );
  });
});
