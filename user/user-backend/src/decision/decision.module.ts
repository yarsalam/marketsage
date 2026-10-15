import { Module } from '@nestjs/common';
import { DecisionController } from './decision.controller';

@Module({
  controllers: [DecisionController],
})
export class DecisionModule {}
