import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Link } from 'react-router-dom';
import apiService from '../services/api';

interface Post {
  id: number;
  content: string;
  scheduled_time: string;
  created_at: string;
  platform: string;
  status: 'scheduled' | 'published' | 'failed';
  video_filename?: string;
}

const DashboardPage: React.FC = () => {
  const { user } = useAuth();
  const [posts, setPosts] = useState<Post[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchPosts();
  }, []);

  const fetchPosts = async () => {
    try {
      setLoading(true);
      const data = await apiService.getPosts();
      setPosts(data);
    } catch (err) {
      console.error('Error fetching posts:', err);
    } finally {
      setLoading(false);
    }
  };

  const hasTikTokConnection = user?.tiktok_access_token && user?.tiktok_token_expires_at;

  // Calculate stats
  const stats = {
    scheduled: posts.filter(p => p.status === 'scheduled').length,
    published: posts.filter(p => p.status === 'published').length,
    failed: posts.filter(p => p.status === 'failed').length,
  };

  // Get upcoming scheduled posts (next 5)
  const upcomingPosts = posts
    .filter(p => p.status === 'scheduled')
    .sort((a, b) => new Date(a.scheduled_time).getTime() - new Date(b.scheduled_time).getTime())
    .slice(0, 5);

  // Get recent activity (last 5 posts)
  const recentPosts = [...posts]
    .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
    .slice(0, 5);

  // Format relative time
  const getRelativeTime = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = date.getTime() - now.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMs < 0) {
      return 'Past due';
    } else if (diffMins < 60) {
      return `in ${diffMins} minute${diffMins !== 1 ? 's' : ''}`;
    } else if (diffHours < 24) {
      return `in ${diffHours} hour${diffHours !== 1 ? 's' : ''}`;
    } else {
      return `in ${diffDays} day${diffDays !== 1 ? 's' : ''}`;
    }
  };

  // Get status badge styling
  const getStatusBadge = (status: string) => {
    const badges = {
      scheduled: 'bg-yellow-100 text-yellow-800 border-yellow-200',
      published: 'bg-green-100 text-green-800 border-green-200',
      failed: 'bg-red-100 text-red-800 border-red-200',
    };
    return badges[status as keyof typeof badges] || 'bg-gray-100 text-gray-800 border-gray-200';
  };

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Welcome back, {user?.username}!</h1>
        <p className="text-gray-600 mt-2">Manage your TikTok content scheduling from here.</p>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="card">
          <div className="text-center">
            {loading ? (
              <div className="animate-pulse">
                <div className="h-8 bg-gray-200 rounded w-12 mx-auto"></div>
              </div>
            ) : (
              <div className="text-3xl font-bold text-tiktok-red">{stats.scheduled}</div>
            )}
            <div className="text-gray-600 mt-1">Scheduled Posts</div>
          </div>
        </div>
        <div className="card">
          <div className="text-center">
            {loading ? (
              <div className="animate-pulse">
                <div className="h-8 bg-gray-200 rounded w-12 mx-auto"></div>
              </div>
            ) : (
              <div className="text-3xl font-bold text-green-600">{stats.published}</div>
            )}
            <div className="text-gray-600 mt-1">Published Posts</div>
          </div>
        </div>
        <div className="card">
          <div className="text-center">
            {loading ? (
              <div className="animate-pulse">
                <div className="h-8 bg-gray-200 rounded w-12 mx-auto"></div>
              </div>
            ) : (
              <div className="text-3xl font-bold text-red-600">{stats.failed}</div>
            )}
            <div className="text-gray-600 mt-1">Failed Posts</div>
          </div>
        </div>
      </div>

      {/* TikTok Connection Status */}
      <div className="card">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">TikTok Connection</h2>
        {hasTikTokConnection ? (
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-3 h-3 bg-green-500 rounded-full"></div>
              <div>
                <div className="font-medium text-gray-900">Connected to TikTok</div>
                <div className="text-sm text-gray-500">
                  Account ID: {user?.tiktok_open_id}
                </div>
              </div>
            </div>
            <button className="btn-secondary">
              Disconnect
            </button>
          </div>
        ) : (
          <div className="text-center py-6">
            <div className="w-12 h-12 mx-auto bg-gray-100 rounded-full flex items-center justify-center mb-4">
              <svg className="w-6 h-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
              </svg>
            </div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">Connect Your TikTok Account</h3>
            <p className="text-gray-600 mb-6">
              Connect your TikTok account to start scheduling and publishing content directly to your profile.
            </p>
            <button className="btn-primary">
              Connect TikTok Account
            </button>
          </div>
        )}
      </div>

      {/* Upcoming Posts */}
      {upcomingPosts.length > 0 && (
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-gray-900">Upcoming Posts</h2>
            <Link to="/posts?filter=scheduled" className="text-sm text-tiktok-red hover:text-red-700">
              View all →
            </Link>
          </div>
          <div className="space-y-3">
            {upcomingPosts.map((post) => (
              <div key={post.id} className="flex items-start justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    {post.video_filename && (
                      <span className="flex items-center text-xs text-gray-600 bg-white px-2 py-1 rounded-full">
                        <svg className="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                        </svg>
                        Video
                      </span>
                    )}
                    <span className="text-xs text-gray-500">
                      {post.platform.toUpperCase()}
                    </span>
                  </div>
                  <p className="text-sm text-gray-900 line-clamp-1 mb-1">{post.content}</p>
                  <div className="flex items-center text-xs text-gray-500">
                    <svg className="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    {new Date(post.scheduled_time).toLocaleString()} · {getRelativeTime(post.scheduled_time)}
                  </div>
                </div>
                <Link
                  to={`/posts`}
                  className="ml-2 text-tiktok-red hover:text-red-700 text-sm font-medium whitespace-nowrap"
                >
                  View →
                </Link>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Quick Actions */}
      <div className="card">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Link to="/create" className="btn-primary text-center block">
            Create New Post
          </Link>
          <Link to="/posts" className="btn-secondary text-center block">
            View All Posts
          </Link>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="card">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Recent Activity</h2>
        {loading ? (
          <div className="text-center py-8">
            <svg className="animate-spin h-8 w-8 text-tiktok-red mx-auto" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
            </svg>
          </div>
        ) : recentPosts.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <svg className="w-12 h-12 mx-auto mb-4 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v8a2 2 0 002 2h8a2 2 0 002-2V9a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
            </svg>
            <p>No recent activity yet</p>
            <p className="text-sm">Start by creating your first post!</p>
          </div>
        ) : (
          <div className="space-y-3">
            {recentPosts.map((post) => (
              <div key={post.id} className="flex items-start justify-between p-3 border border-gray-200 rounded-lg hover:border-gray-300 transition">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium border ${getStatusBadge(post.status)}`}>
                      {post.status.charAt(0).toUpperCase() + post.status.slice(1)}
                    </span>
                    {post.video_filename && (
                      <span className="flex items-center text-xs text-gray-600 bg-gray-100 px-2 py-1 rounded-full">
                        <svg className="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                        </svg>
                        Video
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-gray-900 line-clamp-1 mb-1">{post.content}</p>
                  <div className="text-xs text-gray-500">
                    Created {new Date(post.created_at).toLocaleString()}
                  </div>
                </div>
                <Link
                  to={`/posts`}
                  className="ml-2 text-tiktok-red hover:text-red-700 text-sm font-medium whitespace-nowrap"
                >
                  View →
                </Link>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default DashboardPage;
