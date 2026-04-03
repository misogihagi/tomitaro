import { Elysia, t } from "elysia";
import { createMeasurement } from "@repo/schema";
import { createElysiaApplication } from "@repo/server";
import { sqliteCommands } from "@repo/schema/commands";
import Database from "bun:sqlite";
import { drizzle } from "drizzle-orm/bun-sqlite";
import { migrate } from "drizzle-orm/bun-sqlite/migrator";

const sqlite = new Database("./drizzle/test.db");
const db = drizzle({ client: sqlite });

migrate(db, { migrationsFolder: "./drizzle" });

const app = createElysiaApplication(new Elysia(), db, sqliteCommands).listen(3000);

console.log(
    `🦊 Elysia is running at ${app.server?.hostname}:${app.server?.port}`,
);

