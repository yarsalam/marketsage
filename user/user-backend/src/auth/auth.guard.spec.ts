import { UnauthorizedException } from '@nestjs/common';
import { AuthGuard } from './auth.guard';

describe('AuthGuard', () => {
  const reflector = { getAllAndOverride: jest.fn() };
  const authService = { verifyAccessToken: jest.fn() };
  const guard = new AuthGuard(reflector as never, authService as never);

  function context(request: Record<string, unknown>, handler = jest.fn()) {
    return {
      getHandler: () => handler,
      getClass: () => class TestController {},
      switchToHttp: () => ({ getRequest: () => request }),
    } as never;
  }

  beforeEach(() => {
    jest.clearAllMocks();
    reflector.getAllAndOverride.mockReturnValue(false);
    authService.verifyAccessToken.mockResolvedValue({ sub: 'owner', role: 'owner' });
  });

  it('allows explicitly public routes without a session', async () => {
    reflector.getAllAndOverride.mockReturnValue(true);
    await expect(guard.canActivate(context({ headers: {} }))).resolves.toBe(true);
    expect(authService.verifyAccessToken).not.toHaveBeenCalled();
  });

  it('rejects private routes without a session', async () => {
    await expect(guard.canActivate(context({ headers: {} }))).rejects.toBeInstanceOf(
      UnauthorizedException,
    );
  });

  it('accepts a valid HttpOnly session cookie', async () => {
    const request = { headers: { cookie: 'other=value; marketsage_session=valid-token' } };
    await expect(guard.canActivate(context(request))).resolves.toBe(true);
    expect(authService.verifyAccessToken).toHaveBeenCalledWith('valid-token');
  });

  it('accepts a bearer token for trusted API clients', async () => {
    const request = { headers: { authorization: 'Bearer valid-token' } };
    await expect(guard.canActivate(context(request))).resolves.toBe(true);
    expect(authService.verifyAccessToken).toHaveBeenCalledWith('valid-token');
  });

  it('does not accept a malformed cookie value', async () => {
    const request = { headers: { cookie: 'marketsage_session=%E0%A4%A' } };
    await expect(guard.canActivate(context(request))).rejects.toBeInstanceOf(
      UnauthorizedException,
    );
  });
});
