import { AppController } from './app.controller';

describe('AppController', () => {
  const opsService = {
    getStatus: jest.fn(),
  };
  let controller: AppController;

  beforeEach(() => {
    jest.clearAllMocks();
    controller = new AppController(opsService as never);
  });

  it('returns a public health response', () => {
    expect(controller.getHealth()).toEqual({
      status: 'ok',
      service: 'admin-ops-api',
    });
  });

  it('delegates the read-only status request', async () => {
    const status = {
      enabled: false,
      checkedAt: '2026-11-09T15:00:00.000Z',
      access: 'read_only',
      services: { userBackend: 'disabled', analysisEngine: 'disabled' },
    };
    opsService.getStatus.mockResolvedValue(status);
    await expect(controller.getOpsStatus()).resolves.toEqual(status);
    expect(opsService.getStatus).toHaveBeenCalledTimes(1);
  });
});
