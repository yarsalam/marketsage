import { BadRequestException, ServiceUnavailableException } from '@nestjs/common';
import { DecisionController } from './decision.controller';

describe('DecisionController', () => {
  let controller: DecisionController;
  const originalResearchOutputsFlag = process.env.MARKETSAGE_RESEARCH_OUTPUTS_ENABLED;

  beforeEach(() => {
    process.env.MARKETSAGE_RESEARCH_OUTPUTS_ENABLED = 'true';
    controller = new DecisionController();
  });

  afterAll(() => {
    if (originalResearchOutputsFlag === undefined) {
      delete process.env.MARKETSAGE_RESEARCH_OUTPUTS_ENABLED;
    } else {
      process.env.MARKETSAGE_RESEARCH_OUTPUTS_ENABLED = originalResearchOutputsFlag;
    }
  });

  it('fails closed for decision and allocation output by default', async () => {
    delete process.env.MARKETSAGE_RESEARCH_OUTPUTS_ENABLED;
    await expect(controller.getDecision()).rejects.toBeInstanceOf(ServiceUnavailableException);
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
