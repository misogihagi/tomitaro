import { measurements, NewMeasurement } from "./index";
import { type BunSQLiteDatabase } from "drizzle-orm/bun-sqlite";
import { type AnyD1Database } from "drizzle-orm/d1";

export type Database = BunSQLiteDatabase | AnyD1Database;


export function insertMeasurementDB(db: Database, measurement: NewMeasurement) {
    return db.insert(measurements).values(measurement);
}

export function sqliteCommands(db: Database) {
    return {
        insertMeasurement: (measurement: NewMeasurement) => insertMeasurementDB(db, measurement),
    }
}
