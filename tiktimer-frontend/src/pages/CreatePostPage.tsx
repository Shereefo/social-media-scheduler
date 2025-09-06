import React from 'react';

const CreatePostPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Create TikTok Post</h1>
        <p className="text-gray-600 mt-2">Upload a video and schedule it for publishing.</p>
      </div>

      <div className="card">
        <div className="text-center py-12">
          <svg className="w-16 h-16 mx-auto mb-4 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
          </svg>
          <h3 className="text-lg font-medium text-gray-900 mb-2">Coming Soon</h3>
          <p className="text-gray-600">
            Video upload and post scheduling functionality will be implemented next.
          </p>
        </div>
      </div>
    </div>
  );
};

export default CreatePostPage;