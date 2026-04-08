import { Elysia, t } from "elysia";
import { createMeasurement, NewMeasurement } from "@repo/schema";
import { sqliteCommands, Database } from "@repo/schema/commands";

// IN-MEMORY ALERT TRACKER: Map of site -> timestamp of last alert
const alertCooldown = new Map<string, number>();
const ALERT_COOLDOWN_MS = 24 * 60 * 60 * 1000; // 24 hours
const RELATIVE_MOISTURE_THRESHOLD = 5; // Alert if relative moisture < 5%
const MIN_SPREAD_REQUIRED = 5; // Require at least 5% diff between min and max to learn
const LEARNING_DAYS = 30; // Look back up to 30 days

async function sendNotification(message: string) {
    // Dummy implementation. Will be replaced by actual Webhook call.
    console.log(`[ALERT] ${message}`);
}

// アプローチ：
// 水やり直後の十分な状態（MAX）とカラカラ状態（MIN）の幅を 100% とみなして、「現在、その土のキャパシティの何%か」を出します。
function prepareCheckAlert(getHumidnessStats: (site: string, sinceDate: Date) => Promise<{ min: number | null; max: number | null }>) {
    return async (measurement: NewMeasurement): Promise<boolean> => {
        const sinceDate = new Date(measurement.timestamp)
        sinceDate.setDate(sinceDate.getDate() - LEARNING_DAYS);

        const stats = await getHumidnessStats(measurement.site, sinceDate);
        if (stats && stats.min !== null && stats.max !== null)
            return false

        const min = stats.min as number
        const spread = (stats.max as number) - min;
        if (spread >= MIN_SPREAD_REQUIRED)
            return false

        const relativeMoisture = ((measurement.humidness - min) / spread) * 100;

        if (relativeMoisture < RELATIVE_MOISTURE_THRESHOLD) {
            const lastAlert = alertCooldown.get(measurement.site) || 0;
            const now = Date.now();

            if (now - lastAlert > ALERT_COOLDOWN_MS) {
                alertCooldown.set(measurement.site, now);
                return true
            }
        } else if (relativeMoisture > RELATIVE_MOISTURE_THRESHOLD + 10) {
            // Reset cooldown if it's sufficiently watered again
            alertCooldown.delete(measurement.site);
        }
        return false
    }
}

export function addMeasurementRoute(app: Elysia, db: Database, commands: typeof sqliteCommands) {
    const { insertMeasurement, getHumidnessStats } = commands(db);
    app.post("/", async ({ body }) => {
        try {
            const measurement: NewMeasurement = {
                ...body,
                timestamp: body.timestamp.toISOString()
            }
            await insertMeasurement(measurement);
            const checkAlert = prepareCheckAlert(getHumidnessStats)
            if (await checkAlert(measurement))
                await sendNotification(`⚠️ ${measurement.site} の水が切れている可能性があります！`);
        } catch (error) {
            console.error(error);
        }
    }, { body: createMeasurement })
    return app;
}

export type App = ReturnType<typeof addMeasurementRoute>;
