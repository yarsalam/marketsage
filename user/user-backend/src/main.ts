// src/main.ts
import { NestFactory } from '@nestjs/core';
import { AppModule } from './app.module';

async function bootstrap() {
  const app = await NestFactory.create(AppModule);

  // فعال‌سازی CORS برای همه درخواست‌ها (در محیط توسعه)
  app.enableCors({
    origin: 'http://localhost:3000', // آدرس فرانت
    methods: 'GET,HEAD,PUT,PATCH,POST,DELETE',
    credentials: true,
  });

  await app.listen(process.env.PORT ?? 4500);
}
bootstrap();
