import { Module } from '@nestjs/common';
import { AppController } from './app.controller';
import { AppService } from './app.service';
import { DecisionModule } from './decision/decision.module';
import { MarketsModule } from './markets/markets.module';

@Module({
  imports: [DecisionModule, MarketsModule],
  controllers: [AppController],
  providers: [AppService],
})
export class AppModule {}
