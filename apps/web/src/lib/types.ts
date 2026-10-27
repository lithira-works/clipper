// Mirrors apps/api/app/schemas.py. Keep in sync (see .claude/skills/add-api-endpoint).

export type JobStatus = "queued" | "running" | "succeeded" | "failed";
export type Stage =
  | "queued"
  | "downloading"
  | "transcribing"
  | "analyzing"
  | "reframing"
  | "rendering"
  | "done";
export type CaptionStyle = "bold" | "minimal" | "none";

export interface JobCreate {
  url: string;
  max_clips: number;
  min_duration: number;
  max_duration: number;
  caption_style: CaptionStyle;
  language?: string | null;
}

export interface Clip {
  id: string;
  rank: number;
  start: number;
  end: number;
  duration: number;
  title: string;
  hook: string;
  reason: string;
  virality_score: number;
  hashtags: string[];
  video_url: string;
  thumbnail_url: string;
}

export interface SourceVideo {
  id: string;
  title: string;
  channel: string | null;
  duration: number;
  thumbnail: string | null;
  has_heatmap: boolean;
}

export interface Job {
  id: string;
  status: JobStatus;
  stage: Stage;
  progress: number;
  message: string;
  request: JobCreate;
  source: SourceVideo | null;
  clips: Clip[];
  error: string | null;
  created_at: string;
  updated_at: string;
}
