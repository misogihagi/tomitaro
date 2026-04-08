import { describe, expect, it, beforeAll, afterAll } from 'bun:test'
import { prepareCheckAlert } from '@repo/server'
import { Database } from 'bun:sqlite'
import { drizzle } from 'drizzle-orm/bun-sqlite'
import { sqliteCommands } from '@repo/schema/commands'
import * as fs from 'node:fs'

// Helper to generate realistic-looking test payload
function createPayload(daysAgo: number, humidness: number) {
    const date = new Date();
    date.setDate(date.getDate() - daysAgo);

    return {
        timestamp: date.toISOString(), // Elysia typically parses this into Date with t.Date()
        site: 'test-bonsai',
        temperature: 25.0,
        humidness,
        EC_conductivity: 1.0,
        PH: 6.0,
        Nitrogen: 100,
        Phosphorus: 50,
        Potassium: 150
    };
}

const LEARNING_DAYS = 30;
const TEST_DB_PATH = `test-${Date.now()}.sqlite`;
let sqliteDb: Database;
let db: ReturnType<typeof drizzle>;
let commands: ReturnType<typeof sqliteCommands>;
let checkAlert: ReturnType<typeof prepareCheckAlert>;

beforeAll(() => {
    sqliteDb = new Database(TEST_DB_PATH);
    db = drizzle(sqliteDb);

    // Create the measurements table manually for the test
    sqliteDb.run(`
        CREATE TABLE IF NOT EXISTS measurements (
            timestamp TEXT PRIMARY KEY,
            site TEXT NOT NULL,
            temperature REAL NOT NULL,
            humidness REAL NOT NULL,
            EC_conductivity REAL NOT NULL,
            PH REAL NOT NULL,
            Nitrogen REAL NOT NULL,
            Phosphorus REAL NOT NULL,
            Potassium REAL NOT NULL
        );
        CREATE TABLE IF NOT EXISTS alerts (
            site TEXT PRIMARY KEY,
            timestamp TEXT NOT NULL
        );
    `);

    commands = sqliteCommands(db);
    const { getHumidnessStats, getAlert, setAlert, removeAlert } = commands;
    checkAlert = prepareCheckAlert(getHumidnessStats, getAlert, setAlert, removeAlert);
});

afterAll(() => {
    if (sqliteDb) {
        sqliteDb.close();
    }
    if (fs.existsSync(TEST_DB_PATH)) {
        fs.unlinkSync(TEST_DB_PATH);
    }
});

describe('prepareCheckAlert with SQLite', () => {
    it('returns false when stats are not enough', async () => {
        const payload = createPayload(0, 50);
        payload.site = 'site-not-enough';
        await commands.insertMeasurement(payload);

        const result = await checkAlert(payload);
        expect(result).toBe(false);
    });

    it('returns false when stats are uniform (spread is 0, so < 5)', async () => {
        for (let i = 1; i < LEARNING_DAYS + 1; i++) {
            const payload = createPayload(i, 50);
            payload.site = 'site-null-stats';
            await commands.insertMeasurement(payload);
        }
        const payload = createPayload(0, 50);
        payload.site = 'site-null-stats';
        await commands.insertMeasurement(payload);

        const result = await checkAlert(payload);
        expect(result).toBe(false);
    });

    it('returns false when spread is less than MIN_SPREAD_REQUIRED (5)', async () => {
        for (let i = 2; i < LEARNING_DAYS + 2; i++) {
            const payload = createPayload(i, 20);
            payload.site = 'site-small-spread';
            await commands.insertMeasurement(payload);
        }
        const payload1 = createPayload(1, 20);
        payload1.site = 'site-small-spread';
        await commands.insertMeasurement(payload1);

        const payload2 = createPayload(0, 22);
        payload2.site = 'site-small-spread';
        await commands.insertMeasurement(payload2);

        const result = await checkAlert(payload2);
        expect(result).toBe(false);
    });

    it('returns true when relative moisture is less than 5%', async () => {
        for (let i = 3; i < LEARNING_DAYS + 3; i++) {
            const payload = createPayload(i, 20);
            payload.site = 'site-trigger';
            await commands.insertMeasurement(payload);
        }
        const payload1 = createPayload(2, 20);
        payload1.site = 'site-trigger';
        await commands.insertMeasurement(payload1);

        const payload2 = createPayload(1, 120); // Creates a spread of 100
        payload2.site = 'site-trigger';
        await commands.insertMeasurement(payload2);

        const payload3 = createPayload(0, 24); // (24-20)/100 = 4%
        payload3.site = 'site-trigger';
        await commands.insertMeasurement(payload3);

        const result = await checkAlert(payload3);
        expect(result).toBe(true);
    });

    it('returns false if moisture is below 5% but within cooldown period', async () => {
        for (let i = 4; i < LEARNING_DAYS + 4; i++) {
            const payload = createPayload(i, 20);
            payload.site = 'site-cooldown';
            await commands.insertMeasurement(payload);
        }
        const payload1 = createPayload(3, 20);
        payload1.site = 'site-cooldown';
        await commands.insertMeasurement(payload1);

        const payload2 = createPayload(2, 120);
        payload2.site = 'site-cooldown';
        await commands.insertMeasurement(payload2);

        const payload3 = createPayload(1, 24); // triggers alert
        payload3.site = 'site-cooldown';
        await commands.insertMeasurement(payload3);
        const result1 = await checkAlert(payload3);
        expect(result1).toBe(true);

        const payload4 = createPayload(0, 23); // within cooldown
        payload4.site = 'site-cooldown';
        await commands.insertMeasurement(payload4);
        const result2 = await checkAlert(payload4);
        expect(result2).toBe(false);
    });

    it('resets cooldown and can alert again if moisture goes above 15% in between', async () => {
        for (let i = 5; i < LEARNING_DAYS + 5; i++) {
            const payload = createPayload(i, 20);
            payload.site = 'site-reset';
            await commands.insertMeasurement(payload);
        }
        const payload1 = createPayload(4, 20);
        payload1.site = 'site-reset';
        await commands.insertMeasurement(payload1);

        const payload2 = createPayload(3, 120);
        payload2.site = 'site-reset';
        await commands.insertMeasurement(payload2);

        const payload3 = createPayload(2, 24); // triggers alert
        payload3.site = 'site-reset';
        await commands.insertMeasurement(payload3);
        const result1 = await checkAlert(payload3);
        expect(result1).toBe(true);

        // Above 15% threshold (relativeMoisture > 15), meaning value is > 35
        const payload4 = createPayload(1, 40);
        payload4.site = 'site-reset';
        await commands.insertMeasurement(payload4);
        const result2 = await checkAlert(payload4);
        expect(result2).toBe(false);

        // Below threshold again
        const payload5 = createPayload(0, 24); // should trigger alert again
        payload5.site = 'site-reset';
        await commands.insertMeasurement(payload5);
        const result3 = await checkAlert(payload5);
        expect(result3).toBe(true);
    });
});
