import { Controller, Get } from '@nestjs/common';
import { MarketsService } from './markets.service';

@Controller('markets')
export class MarketsController {
  constructor(private readonly marketsService: MarketsService) {}

  @Get()
  getMarkets() {
    return this.marketsService.listMarkets();
  }
}
