import React from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Link } from 'react-router-dom';

const DashboardPage: React.FC = () => {
  const { user } = useAuth();

  const hasTikTokConnection = user?.tiktok_access_token && user?.tiktok_token_expires_at;

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
            <div className="text-3xl font-bold text-tiktok-red">0</div>
            <div className="text-gray-600 mt-1">Scheduled Posts</div>
          </div>
        </div>
        <div className="card">
          <div className="text-center">
            <div className="text-3xl font-bold text-green-600">0</div>
            <div className="text-gray-600 mt-1">Published Posts</div>
          </div>
        </div>
        <div className="card">
          <div className="text-center">
            <div className="text-3xl font-bold text-gray-600">0</div>
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

      {/* Recent Activity Placeholder */}
      <div className="card">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Recent Activity</h2>
        <div className="text-center py-8 text-gray-500">
          <svg className="w-12 h-12 mx-auto mb-4 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v8a2 2 0 002 2h8a2 2 0 002-2V9a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
          </svg>
          <p>No recent activity yet</p>
          <p className="text-sm">Start by creating your first post!</p>
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;