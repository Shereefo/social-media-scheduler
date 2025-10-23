import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import apiService from '../services/api';

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

const PostsPage: React.FC = () => {
  const [posts, setPosts] = useState<Post[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [filter, setFilter] = useState<'all' | 'scheduled' | 'published' | 'failed'>('all');

  useEffect(() => {
    fetchPosts();
  }, []);

  const fetchPosts = async () => {
    try {
      setLoading(true);
      setError('');
      const data = await apiService.getPosts();
      setPosts(data);
    } catch (err: any) {
      setError('Failed to load posts. Please try again.');
      console.error('Error fetching posts:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (postId: number) => {
    if (!confirm('Are you sure you want to delete this post?')) {
      return;
    }

    try {
      await apiService.deletePost(postId);
      setPosts(posts.filter(post => post.id !== postId));
    } catch (err: any) {
      alert('Failed to delete post. Please try again.');
      console.error('Error deleting post:', err);
    }
  };

  const formatDateTime = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
      hour12: true
    });
  };

  const getStatusBadge = (status: string) => {
    const badges = {
      scheduled: 'bg-yellow-100 text-yellow-800 border-yellow-200',
      published: 'bg-green-100 text-green-800 border-green-200',
      failed: 'bg-red-100 text-red-800 border-red-200'
    };
    return badges[status as keyof typeof badges] || 'bg-gray-100 text-gray-800 border-gray-200';
  };

  const filteredPosts = filter === 'all'
    ? posts
    : posts.filter(post => post.status === filter);

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <h1 className="text-3xl font-bold text-gray-900">My Posts</h1>
        </div>
        <div className="card">
          <div className="text-center py-12">
            <svg className="animate-spin h-12 w-12 mx-auto mb-4 text-gray-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <p className="text-gray-600">Loading posts...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">My Posts</h1>
          <p className="text-gray-600 mt-1">{posts.length} total posts</p>
        </div>
        <Link to="/create" className="btn-primary">
          Create New Post
        </Link>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
          {error}
        </div>
      )}

      {/* Filter Tabs */}
      <div className="flex gap-2 border-b border-gray-200">
        <button
          onClick={() => setFilter('all')}
          className={`px-4 py-2 font-medium text-sm border-b-2 transition-colors ${
            filter === 'all'
              ? 'border-tiktok-red text-tiktok-red'
              : 'border-transparent text-gray-600 hover:text-gray-900'
          }`}
        >
          All ({posts.length})
        </button>
        <button
          onClick={() => setFilter('scheduled')}
          className={`px-4 py-2 font-medium text-sm border-b-2 transition-colors ${
            filter === 'scheduled'
              ? 'border-tiktok-red text-tiktok-red'
              : 'border-transparent text-gray-600 hover:text-gray-900'
          }`}
        >
          Scheduled ({posts.filter(p => p.status === 'scheduled').length})
        </button>
        <button
          onClick={() => setFilter('published')}
          className={`px-4 py-2 font-medium text-sm border-b-2 transition-colors ${
            filter === 'published'
              ? 'border-tiktok-red text-tiktok-red'
              : 'border-transparent text-gray-600 hover:text-gray-900'
          }`}
        >
          Published ({posts.filter(p => p.status === 'published').length})
        </button>
        <button
          onClick={() => setFilter('failed')}
          className={`px-4 py-2 font-medium text-sm border-b-2 transition-colors ${
            filter === 'failed'
              ? 'border-tiktok-red text-tiktok-red'
              : 'border-transparent text-gray-600 hover:text-gray-900'
          }`}
        >
          Failed ({posts.filter(p => p.status === 'failed').length})
        </button>
      </div>

      {/* Posts List */}
      {filteredPosts.length === 0 ? (
        <div className="card">
          <div className="text-center py-12">
            <svg className="w-16 h-16 mx-auto mb-4 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              {filter === 'all' ? 'No posts yet' : `No ${filter} posts`}
            </h3>
            <p className="text-gray-600 mb-6">
              {filter === 'all'
                ? 'Create your first TikTok post to get started with scheduling.'
                : `You don't have any ${filter} posts.`}
            </p>
            <Link to="/create" className="btn-primary">
              Create Your First Post
            </Link>
          </div>
        </div>
      ) : (
        <div className="space-y-4">
          {filteredPosts.map((post) => (
            <div key={post.id} className="card hover:shadow-lg transition-shadow">
              <div className="p-6">
                <div className="flex justify-between items-start mb-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <span className={`px-3 py-1 text-xs font-medium rounded-full border ${getStatusBadge(post.status)}`}>
                        {post.status.charAt(0).toUpperCase() + post.status.slice(1)}
                      </span>
                      <span className="text-sm text-gray-500">
                        {post.platform.charAt(0).toUpperCase() + post.platform.slice(1)}
                      </span>
                    </div>
                    <p className="text-gray-900 whitespace-pre-wrap break-words">
                      {post.content}
                    </p>
                  </div>
                </div>

                <div className="flex items-center justify-between pt-4 border-t border-gray-200">
                  <div className="flex items-center gap-6 text-sm text-gray-600">
                    <div className="flex items-center gap-2">
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                      </svg>
                      <span>Scheduled: {formatDateTime(post.scheduled_time)}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      <span>Created: {formatDateTime(post.created_at)}</span>
                    </div>
                  </div>

                  <div className="flex gap-2">
                    <button
                      onClick={() => handleDelete(post.id)}
                      className="px-4 py-2 text-sm font-medium text-red-600 hover:text-red-700 hover:bg-red-50 rounded-lg transition-colors"
                    >
                      Delete
                    </button>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default PostsPage;