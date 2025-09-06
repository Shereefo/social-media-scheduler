import axios from 'axios';
// Temporary inline types to avoid module resolution issues
interface User {
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

interface Token {
  access_token: string;
  token_type: string;
}

interface LoginCredentials {
  username: string;
  password: string;
}

interface RegisterData {
  email: string;
  username: string;
  password: string;
}

interface Post {
  id: number;
  content: string;
  scheduled_time: string;
  created_at: string;
  updated_at: string;
  platform: string;
  status: 'scheduled' | 'published' | 'failed';
  video_filename?: string;
}

interface CreatePost {
  content: string;
  scheduled_time: string;
  platform?: string;
}

interface TikTokAuthResponse {
  authorization_url: string;
}

interface HealthStatus {
  status: string;
  api_version: string;
  timestamp: string;
  database: string;
}

// Base API URL - matches your CORS configuration
const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const API_PREFIX = '/api/v1';

// Create axios instance
const api = axios.create({
  baseURL: BASE_URL,
  timeout: 30000,
});

// Request interceptor to add auth token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor to handle auth errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export const apiService = {
  // Authentication
  async login(credentials: LoginCredentials): Promise<Token> {
    const formData = new FormData();
    formData.append('username', credentials.username);
    formData.append('password', credentials.password);
    
    const response = await api.post<Token>('/token', formData);
    return response.data;
  },

  async register(userData: RegisterData): Promise<User> {
    const response = await api.post<User>('/register', userData);
    return response.data;
  },

  async getCurrentUser(): Promise<User> {
    const response = await api.get<User>('/users/me');
    return response.data;
  },

  // Health check
  async getHealth(): Promise<HealthStatus> {
    const response = await api.get<HealthStatus>('/health');
    return response.data;
  },

  // Posts management
  async getPosts(): Promise<Post[]> {
    const response = await api.get<Post[]>('/posts/');
    return response.data;
  },

  async getPost(postId: number): Promise<Post> {
    const response = await api.get<Post>(`/posts/${postId}`);
    return response.data;
  },

  async createPost(postData: CreatePost): Promise<Post> {
    const response = await api.post<Post>('/posts/', postData);
    return response.data;
  },

  async updatePost(postId: number, postData: Partial<CreatePost>): Promise<Post> {
    const response = await api.patch<Post>(`/posts/${postId}`, postData);
    return response.data;
  },

  async deletePost(postId: number): Promise<void> {
    await api.delete(`/posts/${postId}`);
  },

  // TikTok OAuth
  async getTikTokAuthUrl(): Promise<TikTokAuthResponse> {
    const response = await api.get<TikTokAuthResponse>(`${API_PREFIX}/auth/tiktok/authorize`);
    return response.data;
  },

  async exchangeTikTokCode(code: string): Promise<{ message: string; user_id?: number }> {
    const response = await api.post(`${API_PREFIX}/auth/tiktok/exchange-token`, { code });
    return response.data;
  },

  async disconnectTikTok(): Promise<{ message: string }> {
    const response = await api.delete(`${API_PREFIX}/auth/tiktok/disconnect`);
    return response.data;
  },

  // TikTok Posts
  async createTikTokPost(formData: FormData): Promise<Post> {
    const response = await api.post<Post>(`${API_PREFIX}/tiktok/posts/`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  async publishTikTokPost(postId: number): Promise<{ message: string; tiktok_post_id?: string }> {
    const response = await api.post(`${API_PREFIX}/tiktok/posts/${postId}/publish`);
    return response.data;
  },
};

export default apiService;