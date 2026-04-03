import { Elysia } from "elysia";
import { CloudflareAdapter } from 'elysia/adapter/cloudflare-worker'
import { addMeasurementRoute } from "@repo/server";
import { sqliteCommands } from "@repo/schema/commands";
import { drizzle } from "drizzle-orm/sqlite-proxy";
import cloudflareRemoteCallback from "./cloudflareRemoteCallback";
import * as schema from "@repo/schema";

export const db = drizzle(cloudflareRemoteCallback, { schema });


class BasicAuthError extends Error {
    public code = 'BASIC_AUTH_ERROR'

    constructor(
        readonly message: string,
        readonly realm: string
    ) {
        super(message)
        this.realm = realm
    }
}

const options = {
    credentials: { env: 'BASIC_AUTH_CREDENTIALS' },
    header: 'Authorization',
    realm: 'Secure Area',
    unauthorizedMessage: 'Unauthorized',
    unauthorizedStatus: 401,
    scope: '/',
    skipCorsPreflight: false,
}

const app = addMeasurementRoute(
    new Elysia({
        adapter: CloudflareAdapter
    }), db, sqliteCommands)
    .error({ BASIC_AUTH_ERROR: BasicAuthError })
    .onError({ as: 'global' }, ({ code, error }) => {
        if (code === 'BASIC_AUTH_ERROR' && error.realm === options.realm) {
            return new Response(options.unauthorizedMessage, {
                status: options.unauthorizedStatus,
                headers: { 'WWW-Authenticate': `Basic realm="${options.realm}"` },
            })
        }
    })
    .onRequest(ctx => {
        const authHeader = ctx.request.headers.get(options.header)
        if (!authHeader || !authHeader.toLowerCase().startsWith('bearer ')) {
            throw new BasicAuthError('Invalid header', options.realm)
        }

        const [_, token] = authHeader.split(' ')
        if (token !== process.env[options.credentials.env]) {
            throw new BasicAuthError('Invalid credentials', options.realm)
        }
    })
    .compile()

export default app
