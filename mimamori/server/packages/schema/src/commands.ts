import { measurements, NewMeasurement, alerts } from "./index";
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
        max: sql<number>`MAX(${measurements.humidness})`,
        count: sql<number>`COUNT(*)`
    })
        .from(measurements)
        .where(and(
            eq(measurements.site, siteSpec),
            gt(measurements.timestamp, sinceDate.toISOString())
        ));
    return res[0]; // 1件しか返ってこないはず
}

export async function getAlertDB(db: Database, site: string) {
    const res = await db.select({
        timestamp: alerts.timestamp,
    })
        .from(alerts)
        .where(and(
            eq(alerts.site, site),
        ));
    return res[0]; // 1件しか返ってこないはず
}

export async function setAlertDB(db: Database, site: string, date: Date) {
    return db.insert(alerts).values({
        site,
        timestamp: date.toISOString(),
    })
        .onConflictDoUpdate({
            target: alerts.site,
            set: { timestamp: date.toISOString() },
        });
}

export async function removeAlertDB(db: Database, site: string) {
    return db.delete(alerts).where(eq(alerts.site, site));
}

export function sqliteCommands(db: Database) {
    return {
        insertMeasurement: (measurement: NewMeasurement) => insertMeasurementDB(db, measurement),
        getHumidnessStats: (site: string, sinceDate: Date) => getHumidnessStatsDB(db, site, sinceDate),
        getAlert: (site: string) => getAlertDB(db, site),
        setAlert: (site: string, date: Date) => setAlertDB(db, site, date),
        removeAlert: (site: string) => removeAlertDB(db, site),
    }
}
