export interface DiscoveredSourceSummary {
  provider: string;
  connected: boolean;
  status: string;
  item_count: number;
  error: string | null;
}

export interface DiscoveredItem {
  id: number;
  source_type: 'google_drive' | 'github_repo';
  external_id: string;
  title: string;
  subtitle: string | null;
  url: string | null;
  is_relevant: boolean;
  is_selected: boolean;
  details: {
    relevance_reason?: string;
    size_bytes?: number | null;
    modified_time?: string | null;
    description?: string | null;
    stars?: number;
    has_readme?: boolean;
    manifests?: string[];
    relevant_files_count?: number;
    sample_files?: string[];
    [key: string]: unknown;
  };
  discovered_at: string;
}

export interface DiscoveryWorkflowResponse {
  sources: DiscoveredSourceSummary[];
  total_items: number;
  selected_count: number;
  items: DiscoveredItem[];
}

