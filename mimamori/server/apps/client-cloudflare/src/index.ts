import { treaty } from '@elysiajs/eden'
import type { App } from '@repo/server'

const app = treaty<App>('localhost:3000', {
    headers: {
        'Authorization': 'Bearer xxxxxxxxxx'
    }
})

const testMeasurement = {
    timestamp: '2000-10-10T10:00:00Z',
    site: 'Greenhouse-A',
    temperature: 24.5,
    humidness: 65.2,
    EC_conductivity: 1.2,
    PH: 6.5,
    Nitrogen: 150.5,
    Phosphorus: 45.0,
    Potassium: 210.2,
}

console.log(await app.post(testMeasurement))
