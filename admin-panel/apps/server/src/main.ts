import { NestFactory } from '@nestjs/core';
import { AppModule } from './app.module';

async function bootstrap() {
  const app = await NestFactory.create(AppModule);
  const origins = (process.env.CORS_ORIGINS ?? 'http://localhost:3001')
    .split(',')
    .map((value) => value.trim())
    .filter(Boolean);

  app.enableCors({
    origin: origins,
    methods: ['GET', 'HEAD', 'OPTIONS'],
    credentials: false,
  });

  await app.listen(Number(process.env.PORT ?? 4000), '0.0.0.0');
}
void bootstrap();
