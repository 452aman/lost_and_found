export type Kind = 'lost' | 'found'
export type ItemStatus = 'open' | 'matched' | 'claimed' | 'returned' | 'archived'
export type ClaimStatus = 'pending' | 'approved' | 'rejected' | 'expired'

export interface UserPublic { id: number; name: string; karma: number }
export interface User extends UserPublic { email: string; role: 'student' | 'admin'; is_active: boolean; created_at: string }

export interface Item {
  id: number; kind: Kind; status: ItemStatus; title: string; description: string
  category: string; location: string; event_time: string; image_url: string | null
  owner: UserPublic; created_at: string; secret_detail: string | null; claim_count: number
}
export interface Page<T> { items: T[]; total: number; page: number; size: number }

export interface Match {
  id: number; score: number; created_at: string
  breakdown: { text: number; category: number; location: number; time: number }
  lost: Item; found: Item
}
export interface Claim {
  id: number; item_id: number; item_title: string; claimant: UserPublic; answer: string
  verification_score: number; status: ClaimStatus; reviewer_note: string | null
  created_at: string; resolved_at: string | null
}
export interface Notification { id: number; kind: string; message: string; link: string | null; read: boolean; created_at: string }
export interface Stats {
  total_items: number; open_lost: number; open_found: number; returned: number
  pending_claims: number; return_rate: number
  by_category: Record<string, number>; by_location: Record<string, number>
  daily: { date: string; count: number }[]
}
export interface AuditEntry { id: number; actor_id: number | null; action: string; entity: string; entity_id: number | null; detail: Record<string, unknown>; created_at: string }
