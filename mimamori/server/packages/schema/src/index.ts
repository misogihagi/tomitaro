import { sqliteTable, text, real, unique, AnySQLiteColumn } from 'drizzle-orm/sqlite-core';
import { createInsertSchema } from "drizzle-typebox";
import { t } from 'elysia';

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

export const alerts = sqliteTable('alerts', {
  site: text('site').primaryKey().references((): AnySQLiteColumn => measurements.site),
  timestamp: text('timestamp'),
});

export type Measurement = typeof measurements.$inferSelect;
export type NewMeasurement = typeof measurements.$inferInsert;


export const createMeasurement = createInsertSchema(measurements, {
  timestamp: t.Date(),
}); 