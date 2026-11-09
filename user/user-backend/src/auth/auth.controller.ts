import {
  BadRequestException,
  Body,
  Controller,
  Get,
  Post,
  Req,
  Res,
} from '@nestjs/common';
import type { Request, Response } from 'express';
import { AuthService } from './auth.service';
import { Public } from './public.decorator';

const COOKIE_NAME = 'marketsage_session';

interface AuthenticatedRequest extends Request {
  user?: { id: number; nickname: string; role: 'owner' };
}

function cookieOptions() {
  return {
    httpOnly: true,
    secure: process.env.NODE_ENV === 'production',
    sameSite: 'lax' as const,
    path: '/',
  };
}

@Controller('auth')
export class AuthController {
  constructor(private readonly authService: AuthService) {}

  @Public()
  @Post('login')
  async login(
    @Body() body: unknown,
    @Res({ passthrough: true }) response: Response,
  ) {
    const input = body as { username?: unknown; password?: unknown } | null;
    if (
      !input ||
      typeof input.username !== 'string' ||
      typeof input.password !== 'string' ||
      input.username.length === 0 ||
      input.username.length > 128 ||
      input.password.length === 0 ||
      input.password.length > 1024
    ) {
      throw new BadRequestException('نام کاربری و گذرواژه معتبر وارد کنید.');
    }

    const { accessToken } = await this.authService.login(
      input.username,
      input.password,
    );
    response.cookie(COOKIE_NAME, accessToken, {
      ...cookieOptions(),
      maxAge: this.authService.sessionTtlSeconds * 1000,
    });
    return { authenticated: true };
  }

  @Get('me')
  getCurrentUser(@Req() request: AuthenticatedRequest) {
    return request.user ?? null;
  }

  @Public()
  @Post('logout')
  logout(@Res({ passthrough: true }) response: Response) {
    response.clearCookie(COOKIE_NAME, cookieOptions());
    return { authenticated: false };
  }
}
