import { AppController } from './app.controller';
import { AppService } from './app.service';

describe('AppController', () => {
  it('returns the service response from getHello', () => {
    const appService = {
      getHello: jest.fn().mockReturnValue('Hello World!'),
    } as unknown as AppService;
    const controller = new AppController(appService);

    expect(controller.getHello()).toBe('Hello World!');
    expect(appService.getHello).toHaveBeenCalledTimes(1);
  });
});
