/**
 * Types for the Distillation Workbench feature.
 * Extracted from DistillationWorkbench.tsx for modularity.
 */

export interface Domain {
  id: string
  name: string
  description?: string
  icon?: string
  color?: string
  topic_count: number
}

export interface Topic {
  id: string
  domain_id: string
  name: string
  description?: string
}

export interface TagItem {
  id: string
  name: string
  color?: string
}

export interface Task {
  id: string
  name: string
  description?: string
  task_type: string
  target_models: string[]
  domain_id?: string
  topic_id?: string
  is_active: boolean
}

export interface Response {
  id: string
  run_id: string
  provider: string
  model: string
  prompt_sent: string
  response_text: string
  latency_ms?: number
  created_at: string
  domain_id?: string
  topic_id?: string
  quality_rating?: number
  tags?: TagItem[]
}

export interface BankedItem {
  id: string
  response_id: string
  quality_score?: number
  status: string
  notes?: string
  banked_at: string
}

export interface Comparison {
  id: string
  comparison_type: string
  prompt_used: string
  status: string
  created_at: string
}

export interface ComparisonDetail {
  comparison: Comparison
  responses: Array<{
    response: Response
    display_order: number
    display_label?: string
  }>
  votes: Vote[]
  vote_count: number
}

export interface Vote {
  id: string
  comparison_id: string
  winner_response_id?: string
  vote_type: string
  voter?: string
  notes?: string
  created_at: string
}

export interface Statistics {
  total_responses: number
  total_banked: number
  by_provider: Record<string, number>
  by_model: Record<string, number>
}

export interface ModelPreferences {
  model_wins: Record<string, number>
  model_appearances: Record<string, number>
  win_rates: Record<string, number>
  total_votes: number
}

export interface SchemaDefinition {
  key: string
  name: string
  description: string
  fields: Record<string, { type: string; required: boolean; description?: string }>
}

export interface StructuredItem {
  id: string
  banked_id: string
  schema_name: string
  structured_data: Record<string, any>
  extraction_method?: string
  extracted_at: string
}

export interface Dataset {
  id: string
  name: string
  version: string
  description?: string
  dataset_type: string
  item_count: number
  status: string
  created_at: string
}

export interface DatasetStats {
  total_items: number
  by_split: Record<string, number>
  by_schema: Record<string, number>
  has_structured: number
  has_banked_only: number
}

export interface ReviewQueue {
  id: string
  name: string
  description?: string
  domain_id?: string
  topic_id?: string
  min_quality_score?: number
  assigned_experts: string[]
  is_active: boolean
  created_at: string
  pending_count?: number
  completed_count?: number
}

export interface ReviewItem {
  id: string
  queue_id: string
  banked_id: string
  status: string
  assigned_to?: string
  review_notes?: string
  review_score?: number
  reviewed_by?: string
  reviewed_at?: string
  priority: number
  created_at: string
  banked?: BankedItem
}

export interface AvailableModel {
  id: string
  name: string
  provider: string
}

export interface NewTask {
  name: string
  description: string
  task_type: string
  prompt_template: string
  system_prompt: string
  target_models: string[]
  domain_id: string
  topic_id: string
}

export interface NewDataset {
  name: string
  version: string
  description: string
  dataset_type: string
}

export interface NewQueue {
  name: string
  description: string
}

export type ViewMode = 'chat' | 'tasks' | 'bank' | 'compare' | 'structure' | 'datasets' | 'review' | 'stats'
