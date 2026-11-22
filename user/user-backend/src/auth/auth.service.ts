import {
  Injectable,
  ServiceUnavailableException,
  UnauthorizedException,
} from '@nestjs/common';
import { JwtService } from '@nestjs/jwt';
import { scryptSync, timingSafeEqual } from 'node:crypto';

export interface OwnerSession {
  sub: 'owner';
  role: 'owner';
}

const ACCESS_TOKEN_TTL_SECONDS = 8 * 60 * 60;

@Injectable()
export class AuthService {
  constructor(private readonly jwtService: JwtService) {}

  private configuration() {
    const username = process.env.MARKETSAGE_AUTH_USERNAME;
    const passwordHash = process.env.MARKETSAGE_AUTH_PASSWORD_SCRYPT;
    const secret = process.env.MARKETSAGE_JWT_SECRET;

    if (
      !username ||
      username.length > 128 ||
      !passwordHash ||
      !secret ||
      secret.length < 32
    ) {
      throw new ServiceUnavailableException(
        'Authentication is not configured. Private routes remain unavailable.',
      );
    }

    return { username, passwordHash, secret };
  }

  private verifyPassword(password: string, encoded: string): boolean {
    const parts = encoded.split('$');
    if (parts.length !== 6 || parts[0] !== 'scrypt') return false;

    const n = Number(parts[1]);
    const r = Number(parts[2]);
    const p = Number(parts[3]);
    const saltHex = parts[4];
    const expectedHex = parts[5];

    // Bound the work factor and memory use even if the environment value is malformed.
    if (
      !Number.isInteger(n) || n < 16384 || n > 32768 ||
      r !== 8 || p !== 1 ||
      !/^[a-fA-F0-9]{32,128}$/.test(saltHex) ||
      !/^[a-fA-F0-9]{64,128}$/.test(expectedHex)
    ) {
      return false;
    }

    try {
      const salt = Buffer.from(saltHex, 'hex');
      const expected = Buffer.from(expectedHex, 'hex');
      const actual = scryptSync(password, salt, expected.length, {
        N: n,
        r,
        p,
        maxmem: 128 * 1024 * 1024,
      });
      return actual.length === expected.length && timingSafeEqual(actual, expected);
    } catch {
      return false;
    }
  }

  async login(username: string, password: string): Promise<{ accessToken: string }> {
    const config = this.configuration();
    if (
      username !== config.username ||
      !password ||
      password.length > 1024 ||
      !this.verifyPassword(password, config.passwordHash)
    ) {
      throw new UnauthorizedException('نام کاربری یا گذرواژه نادرست است.');
    }

    const accessToken = await this.jwtService.signAsync(
      { sub: 'owner', role: 'owner' } satisfies OwnerSession,
      {
        secret: config.secret,
        expiresIn: ACCESS_TOKEN_TTL_SECONDS,
        issuer: 'marketsage-user-backend',
        audience: 'marketsage-user-frontend',
      },
    );
    return { accessToken };
  }

  async verifyAccessToken(token: string): Promise<OwnerSession> {
    const { secret } = this.configuration();
    try {
      const payload = await this.jwtService.verifyAsync<OwnerSession>(token, {
        secret,
        issuer: 'marketsage-user-backend',
        audience: 'marketsage-user-frontend',
      });
      if (payload.sub !== 'owner' || payload.role !== 'owner') {
        throw new UnauthorizedException('نشست معتبر نیست.');
      }
      return payload;
    } catch (error) {
      if (error instanceof UnauthorizedException) throw error;
      throw new UnauthorizedException('نشست معتبر نیست.');
    }
  }

  get sessionTtlSeconds(): number {
    return ACCESS_TOKEN_TTL_SECONDS;
  }
}
