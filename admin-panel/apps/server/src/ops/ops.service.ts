import { Injectable } from '@nestjs/common';
import type { OpsStatus, ProbeStatus } from './ops-status.types';

@Injectable()
export class OpsService {
  private async probe(baseUrl: string | undefined, enabled: boolean): Promise<ProbeStatus> {
    if (!enabled) return 'disabled';
    if (!baseUrl?.trim()) return 'not_configured';

    const url = baseUrl.trim().replace(/\/$/, '');
    try {
      const response = await fetch(`${url}/health`, {
        method: 'GET',
        headers: { Accept: 'application/json' },
        signal: AbortSignal.timeout(5000),
        cache: 'no-store',
      });
      if (!response.ok) return 'unavailable';
      const body: unknown = await response.json().catch(() => null);
      if (
        typeof body === 'object' &&
        body !== null &&
        'status' in body &&
        (body as { status?: unknown }).status === 'ok'
      ) {
        return 'healthy';
      }
      return 'unavailable';
    } catch {
      // Never expose target URLs, exception strings or internal network details.
      return 'unavailable';
    }
  }

  async getStatus(): Promise<OpsStatus> {
    const enabled = process.env.MARKETSAGE_ADMIN_OPS_ENABLED === 'true';
    const [userBackend, analysisEngine] = await Promise.all([
      this.probe(process.env.MARKETSAGE_USER_API_URL, enabled),
      this.probe(process.env.ANALYSIS_ENGINE_URL, enabled),
    ]);

    return {
      enabled,
      checkedAt: new Date().toISOString(),
      access: 'read_only',
      services: { userBackend, analysisEngine },
    };
  }
}
