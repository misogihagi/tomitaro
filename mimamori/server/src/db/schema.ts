import { sqliteTable, text, real } from 'drizzle-orm/sqlite-core';

export const measurements = sqliteTable('measurements', {
  timestamp: text('timestamp').primaryKey(),
  site: text('site').notNull(),
  temperature: real('temperature').notNull(),
  humidness: real('humidness').notNull(),
  EC_conductivity: real('EC_conductivity').notNull(),
  PH: real('PH').notNull(),
  Nitrogen: real('Nitrogen').notNull(),
  Phosphorus: real('Phosphorus').notNull(),
  Potassium: real('Potassium').notNull(),
}, (t) => [
  unique().on(t.timestamp, t.site),
]);

export type Measurement = typeof measurements.$inferSelect;
export type NewMeasurement = typeof measurements.$inferInsert;
