import { Elysia, t } from "elysia";
import { createMeasurement } from "@repo/schema";


const app = new Elysia()
    .post("/", ({ body }) => console.log(body), { body: createMeasurement })
    .listen(3000);

console.log(
    `🦊 Elysia is running at ${app.server?.hostname}:${app.server?.port}`,
);

export type App = typeof app;
