import { sqliteTable, text, real } from 'drizzle-orm/sqlite-core';

export const measurements = sqliteTable('measurements', {
  timestamp: text('timestamp').primaryKey(),
  site: text('site').notNull(),
  temperature: real('temperature'),
  humidness: real('humidness'),
  EC_conductivity: real('EC_conductivity'),
  PH: real('PH'),
  Nitrogen: real('Nitrogen'),
  Phosphorus: real('Phosphorus'),
  Potassium: real('Potassium'),
});

export type Measurement = typeof measurements.$inferSelect;
export type NewMeasurement = typeof measurements.$inferInsert;
