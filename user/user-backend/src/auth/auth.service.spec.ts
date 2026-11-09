import {
  ServiceUnavailableException,
  UnauthorizedException,
} from '@nestjs/common';
import { JwtService } from '@nestjs/jwt';
import { scryptSync } from 'node:crypto';
import { AuthService } from './auth.service';

describe('AuthService', () => {
  const originalEnv = process.env;
  let jwt: { signAsync: jest.Mock; verifyAsync: jest.Mock };
  let service: AuthService;

  beforeEach(() => {
    process.env = { ...originalEnv };
    delete process.env.MARKETSAGE_AUTH_USERNAME;
    delete process.env.MARKETSAGE_AUTH_PASSWORD_SCRYPT;
    delete process.env.MARKETSAGE_JWT_SECRET;
    jwt = {
      signAsync: jest.fn().mockResolvedValue('signed-session'),
      verifyAsync: jest.fn().mockResolvedValue({ sub: 'owner', role: 'owner' }),
    };
    service = new AuthService(jwt as unknown as JwtService);
  });

  afterAll(() => {
    process.env = originalEnv;
  });

  function configure(password = 'correct horse battery staple') {
    const salt = '0123456789abcdef0123456789abcdef';
    const digest = scryptSync(password, Buffer.from(salt, 'hex'), 64, {
      N: 16384,
      r: 8,
      p: 1,
      maxmem: 64 * 1024 * 1024,
    }).toString('hex');
    process.env.MARKETSAGE_AUTH_USERNAME = 'owner';
    process.env.MARKETSAGE_AUTH_PASSWORD_SCRYPT = `scrypt$16384$8$1$${salt}$${digest}`;
    process.env.MARKETSAGE_JWT_SECRET = 'test-secret-that-is-long-enough-for-local-tests';
  }

  it('fails closed when auth secrets are not configured', async () => {
    await expect(service.login('owner', 'password')).rejects.toBeInstanceOf(
      ServiceUnavailableException,
    );
  });

  it('issues a bounded owner session for valid credentials', async () => {
    configure();
    await expect(
      service.login('owner', 'correct horse battery staple'),
    ).resolves.toEqual({ accessToken: 'signed-session' });
    expect(jwt.signAsync).toHaveBeenCalledWith(
      { sub: 'owner', role: 'owner' },
      expect.objectContaining({ expiresIn: 28800 }),
    );
  });

  it('rejects invalid credentials', async () => {
    configure();
    await expect(service.login('owner', 'wrong')).rejects.toBeInstanceOf(
      UnauthorizedException,
    );
    expect(jwt.signAsync).not.toHaveBeenCalled();
  });

  it('rejects a signed token with a non-owner role', async () => {
    configure();
    jwt.verifyAsync.mockResolvedValue({ sub: 'owner', role: 'admin' });
    await expect(service.verifyAccessToken('token')).rejects.toBeInstanceOf(
      UnauthorizedException,
    );
  });
});
