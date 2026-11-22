import { Module } from '@nestjs/common';
import { AppController } from './app.controller';
import { OpsService } from './ops/ops.service';

@Module({
  imports: [],
  controllers: [AppController],
  providers: [OpsService],
})
export class AppModule {}
