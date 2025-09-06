export interface User {
  id: number;
  email: string;
  username: string;
  is_active: boolean;
  is_superuser: boolean;
  created_at: string;
  tiktok_access_token?: string;
  tiktok_open_id?: string;
  tiktok_token_expires_at?: string;
}

export interface Post {
  id: number;
  content: string;
  scheduled_time: string;
  created_at: string;
  updated_at: string;
  platform: string;
  status: 'scheduled' | 'published' | 'failed';
  video_filename?: string;
}

export interface CreatePost {
  content: string;
  scheduled_time: string;
  platform?: string;
}

export interface Token {
  access_token: string;
  token_type: string;
}

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface RegisterData {
  email: string;
  username: string;
  password: string;
}

export interface TikTokAuthResponse {
  authorization_url: string;
}

export interface ApiError {
  detail: string;
}

export interface HealthStatus {
  status: string;
  api_version: string;
  timestamp: string;
  database: string;
}