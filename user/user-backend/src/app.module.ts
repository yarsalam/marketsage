import { Module } from '@nestjs/common';
import { AppController } from './app.controller';
import { AppService } from './app.service';
import { AuthModule } from './auth/auth.module';
import { DecisionModule } from './decision/decision.module';
import { MarketsModule } from './markets/markets.module';

@Module({
  imports: [AuthModule, DecisionModule, MarketsModule],
  controllers: [AppController],
  providers: [AppService],
})
export class AppModule {}
