import client from './client'

export async function checkBackendHealth(): Promise<boolean> {
  try {
    const response = await client.get('/api/v1/health')
    return response.data?.status === 'ok' || response.status === 200
  } catch {
    return false
  }
}
