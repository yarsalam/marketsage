import { Module } from '@nestjs/common';
import { AppController } from './app.controller';
import { AppService } from './app.service';
import { DecisionModule } from './decision/decision.module'; // اضافه شود

@Module({
  imports: [DecisionModule],
  controllers: [AppController],
  providers: [AppService],
})
export class AppModule {}