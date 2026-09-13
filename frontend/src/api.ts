import type {
  Session,
  ClassifyResponse,
  QueryResponse,
  TKDLSearchResponse,
  ABSAssessResponse,
  Composition,
  Jurisdiction,
  ProtectionTarget,
  IntendedUse,
  ClassicalBasis,
  Novelty,
  IngredientSource,
  DevelopmentStatus,
  Objective,
} from './types'

const API_BASE = import.meta.env.VITE_API_BASE ?? ''

async function postJSON<T>(path: string, body: Record<string, unknown>): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) {
    throw new Error(`API error ${res.status}: ${res.statusText}`)
  }
  return res.json() as Promise<T>
}

export async function createSessionAPI(): Promise<Session> {
  return postJSON<Session>('/session', {})
}

interface IntakeBody {
  session_id: string
  jurisdiction?: Jurisdiction
  language?: string
  protection_target?: ProtectionTarget
  objective?: Objective[]
  product_name?: string
  composition?: Composition[]
  intended_use?: IntendedUse
  classical_basis?: ClassicalBasis
  classical_reference?: string
  novelty?: Novelty
  ingredient_sources?: IngredientSource[]
  biological_origin_known?: boolean
  biological_origin_region?: string
  development_status?: DevelopmentStatus
}

export async function intakeAPI(
  sessionId: string,
  fields: Partial<IntakeBody>,
): Promise<Session> {
  return postJSON<Session>('/intake', { session_id: sessionId, ...fields })
}

export async function classifyAPI(sessionId: string): Promise<ClassifyResponse> {
  return postJSON<ClassifyResponse>('/classify', { session_id: sessionId })
}

export async function queryAPI(sessionId: string, question: string): Promise<QueryResponse> {
  return postJSON<QueryResponse>('/query', { session_id: sessionId, question })
}

export async function tkdlSearchAPI(sessionId: string): Promise<TKDLSearchResponse> {
  return postJSON<TKDLSearchResponse>('/tkdl/search', { session_id: sessionId })
}

export async function absAssessAPI(sessionId: string): Promise<ABSAssessResponse> {
  return postJSON<ABSAssessResponse>('/abs/assess', { session_id: sessionId })
}
