import React, { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import apiService from '../services/api';

const CreatePostPage: React.FC = () => {
  const navigate = useNavigate();
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Form state
  const [content, setContent] = useState('');
  const [scheduledTime, setScheduledTime] = useState('');
  const [videoFile, setVideoFile] = useState<File | null>(null);
  const [videoPreview, setVideoPreview] = useState<string | null>(null);

  // UI state
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [uploadProgress, setUploadProgress] = useState(0);

  // TikTok content limits
  const MAX_CAPTION_LENGTH = 2200;
  const MAX_VIDEO_SIZE_MB = 287; // TikTok's max video size
  const SUPPORTED_VIDEO_FORMATS = ['video/mp4', 'video/quicktime', 'video/x-msvideo', 'video/webm'];

  // Get minimum datetime (now)
  const getMinDateTime = () => {
    const now = new Date();
    now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
    return now.toISOString().slice(0, 16);
  };

  // Handle video file selection
  const handleVideoChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];

    if (!file) {
      return;
    }

    // Validate file type
    if (!SUPPORTED_VIDEO_FORMATS.includes(file.type)) {
      setError('Please select a valid video file (MP4, MOV, AVI, or WebM)');
      return;
    }

    // Validate file size
    const fileSizeMB = file.size / (1024 * 1024);
    if (fileSizeMB > MAX_VIDEO_SIZE_MB) {
      setError(`Video file is too large (${fileSizeMB.toFixed(1)}MB). Maximum size is ${MAX_VIDEO_SIZE_MB}MB.`);
      return;
    }

    setError('');
    setVideoFile(file);

    // Create video preview
    const previewUrl = URL.createObjectURL(file);
    setVideoPreview(previewUrl);
  };

  // Remove video
  const handleRemoveVideo = () => {
    if (videoPreview) {
      URL.revokeObjectURL(videoPreview);
    }
    setVideoFile(null);
    setVideoPreview(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  // Handle form submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    // Validation
    if (!content.trim()) {
      setError('Please enter a caption for your post');
      return;
    }

    if (!scheduledTime) {
      setError('Please select a date and time to schedule your post');
      return;
    }

    if (!videoFile) {
      setError('Please select a video file to upload');
      return;
    }

    try {
      setIsSubmitting(true);
      setUploadProgress(0);

      // Create FormData for multipart upload
      const formData = new FormData();
      formData.append('content', content);
      formData.append('scheduled_time', new Date(scheduledTime).toISOString());
      formData.append('video', videoFile);

      // Simulate upload progress (axios doesn't provide real progress for FormData in browser)
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => Math.min(prev + 10, 90));
      }, 200);

      // Upload to API
      await apiService.createTikTokPost(formData);

      clearInterval(progressInterval);
      setUploadProgress(100);

      setSuccess('Post scheduled successfully!');

      // Clear form
      setTimeout(() => {
        navigate('/posts');
      }, 1500);

    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to schedule post. Please try again.');
      setUploadProgress(0);
    } finally {
      setIsSubmitting(false);
    }
  };

  // Calculate file size in MB
  const getFileSizeMB = (bytes: number) => {
    return (bytes / (1024 * 1024)).toFixed(2);
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Create TikTok Post</h1>
        <p className="text-gray-600 mt-2">Upload a video and schedule it for publishing.</p>
      </div>

      <form onSubmit={handleSubmit} className="card space-y-6">
        {/* Video Upload Section */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Video <span className="text-red-500">*</span>
          </label>

          {!videoFile ? (
            <div
              onClick={() => fileInputRef.current?.click()}
              className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-tiktok-red hover:bg-gray-50 transition cursor-pointer"
            >
              <svg
                className="w-12 h-12 mx-auto mb-4 text-gray-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M7 4v16M17 4v16M3 8h4m10 0h4M3 12h18M3 16h4m10 0h4M4 20h16a1 1 0 001-1V5a1 1 0 00-1-1H4a1 1 0 00-1 1v14a1 1 0 001 1z"
                />
              </svg>
              <p className="text-gray-700 font-medium mb-1">Click to upload video</p>
              <p className="text-sm text-gray-500">
                MP4, MOV, AVI, or WebM (max {MAX_VIDEO_SIZE_MB}MB)
              </p>
            </div>
          ) : (
            <div className="border border-gray-300 rounded-lg p-4 space-y-4">
              {/* Video Preview */}
              <div className="relative">
                <video
                  src={videoPreview || undefined}
                  controls
                  className="w-full rounded-lg bg-black"
                  style={{ maxHeight: '400px' }}
                >
                  Your browser does not support the video tag.
                </video>
                <button
                  type="button"
                  onClick={handleRemoveVideo}
                  className="absolute top-2 right-2 bg-red-500 text-white rounded-full p-2 hover:bg-red-600 transition"
                  title="Remove video"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>

              {/* Video Info */}
              <div className="flex items-center justify-between text-sm text-gray-600">
                <span className="flex items-center">
                  <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                  </svg>
                  {videoFile.name}
                </span>
                <span className="text-gray-500">
                  {getFileSizeMB(videoFile.size)} MB
                </span>
              </div>
            </div>
          )}

          <input
            ref={fileInputRef}
            type="file"
            accept="video/mp4,video/quicktime,video/x-msvideo,video/webm"
            onChange={handleVideoChange}
            className="hidden"
          />
        </div>

        {/* Caption */}
        <div>
          <label htmlFor="content" className="block text-sm font-medium text-gray-700 mb-2">
            Caption <span className="text-red-500">*</span>
          </label>
          <textarea
            id="content"
            value={content}
            onChange={(e) => setContent(e.target.value.slice(0, MAX_CAPTION_LENGTH))}
            placeholder="Write a catchy caption for your TikTok video..."
            rows={4}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-tiktok-red focus:border-transparent resize-none"
            required
          />
          <div className="flex justify-between items-center mt-2">
            <p className="text-sm text-gray-500">
              {content.length} / {MAX_CAPTION_LENGTH} characters
            </p>
            {content.length >= MAX_CAPTION_LENGTH && (
              <p className="text-sm text-red-500">Maximum length reached</p>
            )}
          </div>
        </div>

        {/* Scheduled Time */}
        <div>
          <label htmlFor="scheduledTime" className="block text-sm font-medium text-gray-700 mb-2">
            Schedule for <span className="text-red-500">*</span>
          </label>
          <input
            type="datetime-local"
            id="scheduledTime"
            value={scheduledTime}
            onChange={(e) => setScheduledTime(e.target.value)}
            min={getMinDateTime()}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-tiktok-red focus:border-transparent"
            required
          />
          <p className="text-sm text-gray-500 mt-2">
            Select when you want this post to be published
          </p>
        </div>

        {/* Upload Progress */}
        {isSubmitting && uploadProgress > 0 && (
          <div>
            <div className="flex justify-between text-sm text-gray-600 mb-1">
              <span>Uploading...</span>
              <span>{uploadProgress}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-tiktok-red h-2 rounded-full transition-all duration-300"
                style={{ width: `${uploadProgress}%` }}
              />
            </div>
          </div>
        )}

        {/* Error Message */}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg flex items-start">
            <svg className="w-5 h-5 mr-2 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
            <span>{error}</span>
          </div>
        )}

        {/* Success Message */}
        {success && (
          <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg flex items-start">
            <svg className="w-5 h-5 mr-2 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
            </svg>
            <span>{success}</span>
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex gap-4">
          <button
            type="submit"
            disabled={isSubmitting || !videoFile || !content.trim() || !scheduledTime}
            className="flex-1 btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isSubmitting ? (
              <span className="flex items-center justify-center">
                <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                Uploading...
              </span>
            ) : (
              'Schedule Post'
            )}
          </button>
          <button
            type="button"
            onClick={() => navigate('/posts')}
            disabled={isSubmitting}
            className="px-6 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
};

export default CreatePostPage;
