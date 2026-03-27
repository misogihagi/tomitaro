import { Elysia, t } from "elysia";
import { createInsertSchema } from "drizzle-typebox";
import { measurements } from "./db/schema";

const _createMeasurement = createInsertSchema(measurements, {
  timestamp: t.Date(),
});

const app = new Elysia()
  .post("/", ({ body }) => console.log, { body: _createMeasurement })
  .listen(3000);

console.log(
  `🦊 Elysia is running at ${app.server?.hostname}:${app.server?.port}`,
);

export type App = typeof app;
