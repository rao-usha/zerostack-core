import client from './client'

export async function checkBackendHealth(): Promise<boolean> {
  try {
    const response = await client.get('/health')
    return response.data?.status === 'healthy' || response.status === 200
  } catch {
    return false
  }
}
