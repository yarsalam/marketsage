import { Controller, Get, Query } from '@nestjs/common';
import axios from 'axios';

@Controller('api/decision')
export class DecisionController {
  @Get()
  async getDecision(
    @Query('horizon') horizon = '1M',
    @Query('capital') capital = 500000000,
  ) {
    const { data } = await axios.get(
      `http://localhost:8000/decision?horizon=${horizon}&capital=${capital}`,
    );
    return data;
  }
}
