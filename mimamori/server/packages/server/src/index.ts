import { Elysia, t } from "elysia";
import { createMeasurement, NewMeasurement } from "@repo/schema";
import { sqliteCommands, Database } from "@repo/schema/commands";


export function createElysiaApplication(db: Database, commands: typeof sqliteCommands) {
    const { insertMeasurement } = commands(db);
    const app = new Elysia()
        .post("/", async ({ body }) => {
            try {
                const measurement: NewMeasurement = {
                    ...body,
                    timestamp: body.timestamp.toISOString()
                }
                await insertMeasurement(measurement);
            } catch (error) {
                console.error(error);
            }
        }, { body: createMeasurement })
    return app;
}

export type App = ReturnType<typeof createElysiaApplication>;
