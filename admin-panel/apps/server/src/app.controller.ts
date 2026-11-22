import { Controller, Get } from '@nestjs/common';
import { OpsService } from './ops/ops.service';

@Controller()
export class AppController {
  constructor(private readonly opsService: OpsService) {}

  @Get('health')
  getHealth() {
    return { status: 'ok', service: 'admin-ops-api' };
  }

  @Get('ops/status')
  getOpsStatus() {
    return this.opsService.getStatus();
  }
}
