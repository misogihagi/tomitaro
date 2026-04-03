// cloudflareRemoteCallback.ts
import type { AsyncRemoteCallback } from "drizzle-orm/sqlite-proxy";
import Cloudflare, { APIError } from "cloudflare";

const { CLOUDFLARE_D1_TOKEN, CLOUDFLARE_ACCOUNT_ID, CLOUDFLARE_DATABASE_ID } =
    process.env as {
        [key: string]: string;
    };

const client = new Cloudflare({
    apiToken: CLOUDFLARE_D1_TOKEN,
});

const cloudflareRemoteCallback: AsyncRemoteCallback = async (
    sql: string,
    params: any[],
    method: "run" | "all" | "values" | "get",
) => {
    try {
        const queryResult = await client.d1.database.raw(CLOUDFLARE_DATABASE_ID, {
            account_id: CLOUDFLARE_ACCOUNT_ID,
            sql: sql,
            params: params,
        });

        const result = queryResult.result?.[0]?.results;

        if (!result) {
            throw new Error("Unexpected response format from Cloudflare D1");
        }

        const rows = result.rows || [];

        if (method === "get") {
            if (rows.length === 0) {
                return Promise.resolve({ rows: [] });
            }
            return Promise.resolve({ rows: rows[0] });
        }

        return Promise.resolve({ rows });
    } catch (error) {
        let handledError = String(error);

        if (error instanceof APIError) {
            handledError = error.errors
                .map((err) => `${err.code}: ${err.message}`)
                .join(", ");
        } else if (error instanceof Error) {
            handledError = error.message;
        }

        throw new Error(handledError, {});
    }
};

export default cloudflareRemoteCallback;