import { measurements, NewMeasurement } from "./index";
import { type BunSQLiteDatabase } from "drizzle-orm/bun-sqlite";
import { type AnyD1Database } from "drizzle-orm/d1";
import { and, eq, gt, sql } from "drizzle-orm";

export type Database = BunSQLiteDatabase | AnyD1Database;


export function insertMeasurementDB(db: Database, measurement: NewMeasurement) {
    return db.insert(measurements).values(measurement);
}

export async function getHumidnessStatsDB(db: Database, siteSpec: string, sinceDate: Date) {
    const res = await db.select({
        min: sql<number>`MIN(${measurements.humidness})`,
        max: sql<number>`MAX(${measurements.humidness})`
    })
        .from(measurements)
        .where(and(
            eq(measurements.site, siteSpec),
            gt(measurements.timestamp, sinceDate.toISOString())
        ));
    return res[0];
}

export function sqliteCommands(db: Database) {
    return {
        insertMeasurement: (measurement: NewMeasurement) => insertMeasurementDB(db, measurement),
        getHumidnessStats: (site: string, sinceDate: Date) => getHumidnessStatsDB(db, site, sinceDate),
    }
}
