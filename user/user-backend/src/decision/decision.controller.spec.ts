import { BadRequestException } from '@nestjs/common';
import { DecisionController } from './decision.controller';

describe('DecisionController', () => {
  let controller: DecisionController;

  beforeEach(() => {
    controller = new DecisionController();
  });

  it('rejects unsupported horizons before calling the analysis service', async () => {
    await expect(controller.getDecision('10Y')).rejects.toBeInstanceOf(
      BadRequestException,
    );
  });

  it('rejects negative capital', async () => {
    await expect(controller.getDecision('1M', '-1')).rejects.toBeInstanceOf(
      BadRequestException,
    );
  });

  it('rejects invalid top_n', async () => {
    await expect(controller.getDecision('1M', '1000', '0')).rejects.toBeInstanceOf(
      BadRequestException,
    );
  });
});
