import React from 'react';

const TermsOfServicePage: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4">
        <div className="bg-white rounded-lg shadow-md p-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-6">Terms of Service</h1>

          <div className="prose max-w-none">
            <p className="text-sm text-gray-600 mb-6">Last Updated: October 19, 2025</p>

            <section className="mb-8">
              <h2 className="text-2xl font-semibold text-gray-800 mb-4">1. Acceptance of Terms</h2>
              <p className="text-gray-700 mb-4">
                By accessing and using TikTimer ("the Service"), you accept and agree to be bound by the terms
                and provision of this agreement. If you do not agree to these Terms of Service, please do not
                use the Service.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-semibold text-gray-800 mb-4">2. Description of Service</h2>
              <p className="text-gray-700 mb-4">
                TikTimer is a social media scheduling application that allows users to schedule and manage
                posts for TikTok. The Service integrates with TikTok's API to provide posting functionality.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-semibold text-gray-800 mb-4">3. User Accounts</h2>
              <p className="text-gray-700 mb-4">
                To use the Service, you must:
              </p>
              <ul className="list-disc pl-6 text-gray-700 mb-4">
                <li>Create an account with accurate information</li>
                <li>Maintain the security of your account credentials</li>
                <li>Be responsible for all activities under your account</li>
                <li>Notify us immediately of any unauthorized use</li>
              </ul>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-semibold text-gray-800 mb-4">4. TikTok Integration</h2>
              <p className="text-gray-700 mb-4">
                By connecting your TikTok account, you authorize TikTimer to:
              </p>
              <ul className="list-disc pl-6 text-gray-700 mb-4">
                <li>Access your TikTok account information</li>
                <li>Post content on your behalf according to your scheduled posts</li>
                <li>Retrieve account analytics and post performance data</li>
              </ul>
              <p className="text-gray-700 mb-4">
                You can revoke this access at any time through your TikTimer dashboard or TikTok settings.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-semibold text-gray-800 mb-4">5. Acceptable Use</h2>
              <p className="text-gray-700 mb-4">
                You agree not to use the Service to:
              </p>
              <ul className="list-disc pl-6 text-gray-700 mb-4">
                <li>Violate any laws or regulations</li>
                <li>Infringe on intellectual property rights</li>
                <li>Post spam, malicious content, or harmful material</li>
                <li>Attempt to access unauthorized parts of the Service</li>
                <li>Violate TikTok's Terms of Service or Community Guidelines</li>
              </ul>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-semibold text-gray-800 mb-4">6. Content Responsibility</h2>
              <p className="text-gray-700 mb-4">
                You are solely responsible for the content you schedule and post through the Service.
                TikTimer does not monitor, edit, or control user content and assumes no responsibility
                for content posted through the Service.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-semibold text-gray-800 mb-4">7. Service Availability</h2>
              <p className="text-gray-700 mb-4">
                We strive to maintain Service availability but do not guarantee uninterrupted access.
                The Service may be temporarily unavailable due to maintenance, updates, or circumstances
                beyond our control.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-semibold text-gray-800 mb-4">8. Limitation of Liability</h2>
              <p className="text-gray-700 mb-4">
                TikTimer is provided "as is" without warranties of any kind. We are not liable for any
                damages arising from your use of the Service, including but not limited to failed posts,
                data loss, or account suspension on third-party platforms.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-semibold text-gray-800 mb-4">9. Termination</h2>
              <p className="text-gray-700 mb-4">
                We reserve the right to suspend or terminate your access to the Service at any time,
                with or without notice, for conduct that we believe violates these Terms of Service or
                is harmful to other users or the Service.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-semibold text-gray-800 mb-4">10. Changes to Terms</h2>
              <p className="text-gray-700 mb-4">
                We may modify these Terms of Service at any time. Continued use of the Service after
                changes constitutes acceptance of the modified terms.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-semibold text-gray-800 mb-4">11. Contact Information</h2>
              <p className="text-gray-700 mb-4">
                For questions about these Terms of Service, please contact us at: support@tiktimer.com
              </p>
            </section>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TermsOfServicePage;
