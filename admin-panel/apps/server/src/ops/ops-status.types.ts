export type ProbeStatus = 'healthy' | 'unavailable' | 'not_configured' | 'disabled';

export interface OpsStatus {
  enabled: boolean;
  checkedAt: string;
  access: 'read_only';
  services: {
    userBackend: ProbeStatus;
    analysisEngine: ProbeStatus;
  };
}
