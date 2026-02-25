# Frontend Forms Implementation - Next Session

## 🎯 Session Goal
Build the missing frontend UI components to complete the TikTimer application:
1. Create Post form with video upload
2. Posts list view with management actions
3. Make the app fully functional locally

---

## ✅ Current Status

### **What's Working:**
- ✅ Backend API (FastAPI) - Fully functional
- ✅ Database (PostgreSQL) - Storing users and posts
- ✅ Authentication - Login/register/JWT tokens
- ✅ Frontend Dashboard - Shows user stats
- ✅ Navigation - All routes load
- ✅ Health Check - Returns proper status codes
- ✅ CI/CD Pipeline - 100% implemented (migrations + health checks)

### **What's Missing (Frontend Only):**
- ❌ Create Post form UI
- ❌ Posts list view UI
- ❌ Video upload component

---

## 🧪 Verified Backend Endpoints

### **Authentication:**
```bash
# Login
POST http://localhost:8000/token
Content-Type: application/x-www-form-urlencoded
Body: username=demo_user&password=demo123

# Returns:
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer"
}
```

### **Posts:**
```bash
# Create Post
POST http://localhost:8000/posts/
Authorization: Bearer {token}
Content-Type: application/json
Body: {
  "content": "My first scheduled TikTok post!",
  "scheduled_time": "2025-10-20T15:00:00",
  "platform": "tiktok"
}

# Returns:
{
  "id": 2,
  "content": "My first scheduled TikTok post!",
  "scheduled_time": "2025-10-20T15:00:00",
  "platform": "tiktok",
  "status": "scheduled",
  "created_at": "2025-10-17T01:51:20.383695",
  "updated_at": "2025-10-17T01:51:20.383695"
}

# List Posts
GET http://localhost:8000/posts/
Authorization: Bearer {token}

# Returns: Array of posts
```

**✅ All endpoints tested and working!**

---

## 📋 Implementation Checklist

### **Priority 1: Create Post Form**
**File:** `tiktimer-frontend/src/pages/CreatePostPage.tsx`

**Current State:** Placeholder with "Coming Soon" message

**Needs:**
- [ ] Form with content textarea
- [ ] Datetime picker for scheduled_time
- [ ] Platform selector (defaulting to "tiktok")
- [ ] Form validation
- [ ] API integration to POST /posts/
- [ ] Success/error notifications
- [ ] Redirect to dashboard or posts list after creation

**Design Considerations:**
- Use React Hook Form for form management (already in dependencies)
- Match existing TikTok branding (red buttons, clean layout)
- Show loading state during submission
- Display validation errors clearly

---

### **Priority 2: Posts List View**
**File:** `tiktimer-frontend/src/pages/PostsPage.tsx`

**Current State:** Likely a placeholder

**Needs:**
- [ ] Fetch posts from GET /posts/
- [ ] Display posts in a table or card layout
- [ ] Show post content, scheduled time, status, platform
- [ ] Filter by status (scheduled/published/failed)
- [ ] Delete button for each post
- [ ] Edit button (optional - can use modal or navigate to edit page)
- [ ] Loading skeleton while fetching
- [ ] Empty state when no posts

**Design Considerations:**
- Use React Query for data fetching (already in dependencies)
- Color-code status badges (green=published, red=failed, yellow=scheduled)
- Add confirm dialog before delete
- Update dashboard stats after delete

---

### **Priority 3: Video Upload Component (Optional)**
**File:** `tiktimer-frontend/src/components/VideoUpload.tsx`

**Current State:** Doesn't exist

**Needs:**
- [ ] Drag-and-drop file upload
- [ ] File validation (video formats, size limits)
- [ ] Upload progress indicator
- [ ] Video preview
- [ ] Integration with S3 upload endpoint (if backend supports it)

**Note:** This can be deferred if backend video upload isn't implemented yet.

---

## 🎨 UI/UX Guidelines

### **Existing Design System:**
```css
/* From index.css */
Primary Color: #fe2c55 (TikTok red)
Accent Color: #25f4ee (TikTok blue)
Background: White/light gray
Font: System fonts, clean and modern
```

### **Component Patterns to Follow:**
- Look at `DashboardPage.tsx` for card layouts
- Look at `LoginPage.tsx` for form styling
- Use `.btn-primary` and `.btn-secondary` classes
- Use `.card` class for containers
- Use `.input-field` for form inputs

---

## 🔧 Development Environment

### **Start Services:**
```bash
# Backend (Docker)
docker-compose up -d

# Frontend (Vite)
cd tiktimer-frontend
npm run dev
```

### **Access Points:**
- Frontend: http://localhost:5173
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/docs

### **Demo Credentials:**
- Username: `demo_user`
- Password: `demo123`

---

## 📝 Example Implementation (CreatePostPage)

```typescript
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import apiService from '../services/api';

const CreatePostPage: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [content, setContent] = useState('');
  const [scheduledTime, setScheduledTime] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      await apiService.createPost({
        content,
        scheduled_time: scheduledTime,
        platform: 'tiktok'
      });

      // Success - redirect to posts or dashboard
      navigate('/posts');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create post');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container mx-auto p-6">
      <h1 className="text-3xl font-bold mb-4">Create TikTok Post</h1>

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="card p-6">
        <div className="mb-4">
          <label className="block text-sm font-medium mb-2">
            Post Content
          </label>
          <textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            className="input-field w-full h-32"
            placeholder="Enter your post content..."
            required
          />
        </div>

        <div className="mb-4">
          <label className="block text-sm font-medium mb-2">
            Schedule For
          </label>
          <input
            type="datetime-local"
            value={scheduledTime}
            onChange={(e) => setScheduledTime(e.target.value)}
            className="input-field w-full"
            required
          />
        </div>

        <button
          type="submit"
          disabled={loading}
          className="btn-primary w-full"
        >
          {loading ? 'Creating...' : 'Schedule Post'}
        </button>
      </form>
    </div>
  );
};

export default CreatePostPage;
```

**Don't forget to add the API method:**
```typescript
// In src/services/api.ts
createPost: async (postData: {
  content: string;
  scheduled_time: string;
  platform: string;
}) => {
  const response = await api.post('/posts/', postData);
  return response.data;
}
```

---

## 🧪 Testing Workflow

### **1. Create Post Form:**
1. Navigate to http://localhost:5173/create
2. Fill in content and scheduled time
3. Submit form
4. Verify post appears in browser DevTools Network tab
5. Check dashboard - should show 1 scheduled post

### **2. Posts List:**
1. Navigate to http://localhost:5173/posts
2. Verify post from step 1 appears
3. Test delete button
4. Verify post is removed from list
5. Check dashboard - should show 0 posts

### **3. End-to-End Flow:**
1. Create multiple posts
2. Verify dashboard stats update
3. View posts list
4. Delete a post
5. Stats update correctly

---

## 📚 Resources

### **React Hook Form:**
- Docs: https://react-hook-form.com/
- Already in your dependencies
- Makes form validation easy

### **React Query:**
- Docs: https://tanstack.com/query/latest
- Already in your dependencies
- Use for fetching posts list

### **Date/Time Input:**
- Use HTML5 `<input type="datetime-local">`
- Or install a library like `react-datepicker`

---

## 🎯 Session Success Criteria

By the end of the session, you should be able to:

1. ✅ Create a new post via the UI
2. ✅ See the post in the posts list
3. ✅ Delete a post via the UI
4. ✅ See dashboard stats update automatically
5. ✅ Have a fully functional app locally

---

## 🚀 After Frontend is Complete

Once the forms are built and working locally, you'll have:

1. **Fully functional app** - Can create, view, and delete posts
2. **Testable locally** - No need for AWS to test features
3. **Deployment ready** - CI/CD pipeline will deploy working code
4. **Portfolio piece** - Complete full-stack application

**Next steps after frontend:**
- Deploy to AWS and test migrations
- Test TikTok OAuth in production
- Add video upload functionality
- Implement actual post publishing to TikTok

---

## 💡 Tips for Next Session

1. **Start with CreatePostPage** - It's the most important
2. **Test frequently** - Check backend responses in DevTools
3. **Reuse existing patterns** - Look at LoginPage for form structure
4. **Keep it simple** - Basic functionality first, polish later
5. **Check the docs** - Your Development Session Summary has component examples

---

**Good luck with the frontend build! The backend is solid, so this should be straightforward.** 🎉
