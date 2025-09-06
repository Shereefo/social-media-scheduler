import React from 'react';

const TikTokCallbackPage: React.FC = () => {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="card max-w-md w-full text-center">
        <h1 className="text-2xl font-bold text-gray-900 mb-4">TikTok OAuth Callback</h1>
        <p className="text-gray-600">
          TikTok OAuth integration will be implemented here to handle the callback from TikTok.
        </p>
      </div>
    </div>
  );
};

export default TikTokCallbackPage;