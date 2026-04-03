import { defineConfig } from 'drizzle-kit';

export default defineConfig({
  schema: '../../packages/schema/src/index.ts',
  out: './drizzle',
  dialect: 'sqlite',
});
