import React from 'react';

const PrivacyPolicyPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4">
        <div className="bg-white rounded-lg shadow-md p-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-6">Privacy Policy</h1>

          <div className="prose max-w-none">
            <p className="text-sm text-gray-600 mb-6">Last Updated: October 19, 2025</p>

            <section className="mb-8">
              <h2 className="text-2xl font-semibold text-gray-800 mb-4">1. Introduction</h2>
              <p className="text-gray-700 mb-4">
                TikTimer ("we", "our", or "us") is committed to protecting your privacy. This Privacy Policy
                explains how we collect, use, disclose, and safeguard your information when you use our
                social media scheduling service.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-semibold text-gray-800 mb-4">2. Information We Collect</h2>

              <h3 className="text-xl font-semibold text-gray-800 mb-3 mt-4">Account Information</h3>
              <p className="text-gray-700 mb-4">
                When you create an account, we collect:
              </p>
              <ul className="list-disc pl-6 text-gray-700 mb-4">
                <li>Email address</li>
                <li>Username</li>
                <li>Password (encrypted)</li>
                <li>Account creation date</li>
              </ul>

              <h3 className="text-xl font-semibold text-gray-800 mb-3 mt-4">TikTok Integration Data</h3>
              <p className="text-gray-700 mb-4">
                When you connect your TikTok account, we collect:
              </p>
              <ul className="list-disc pl-6 text-gray-700 mb-4">
                <li>TikTok access tokens (encrypted)</li>
                <li>TikTok refresh tokens (encrypted)</li>
                <li>Token expiration dates</li>
                <li>TikTok user ID</li>
              </ul>

              <h3 className="text-xl font-semibold text-gray-800 mb-3 mt-4">Content Data</h3>
              <p className="text-gray-700 mb-4">
                We store the content you create and schedule:
              </p>
              <ul className="list-disc pl-6 text-gray-700 mb-4">
                <li>Post content and captions</li>
                <li>Scheduled posting times</li>
                <li>Post status (scheduled, published, failed)</li>
                <li>Media files uploaded for posts</li>
              </ul>

              <h3 className="text-xl font-semibold text-gray-800 mb-3 mt-4">Usage Information</h3>
              <p className="text-gray-700 mb-4">
                We automatically collect:
              </p>
              <ul className="list-disc pl-6 text-gray-700 mb-4">
                <li>Log data (IP address, browser type, access times)</li>
                <li>Device information</li>
                <li>Service usage patterns</li>
              </ul>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-semibold text-gray-800 mb-4">3. How We Use Your Information</h2>
              <p className="text-gray-700 mb-4">
                We use collected information to:
              </p>
              <ul className="list-disc pl-6 text-gray-700 mb-4">
                <li>Provide and maintain the Service</li>
                <li>Schedule and publish posts to your TikTok account</li>
                <li>Authenticate your identity</li>
                <li>Communicate with you about the Service</li>
                <li>Improve and optimize the Service</li>
                <li>Detect and prevent fraud or abuse</li>
                <li>Comply with legal obligations</li>
              </ul>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-semibold text-gray-800 mb-4">4. Data Sharing and Disclosure</h2>

              <h3 className="text-xl font-semibold text-gray-800 mb-3 mt-4">With TikTok</h3>
              <p className="text-gray-700 mb-4">
                We share your scheduled content with TikTok's API to publish posts on your behalf.
                This data transfer is necessary for the Service to function.
              </p>

              <h3 className="text-xl font-semibold text-gray-800 mb-3 mt-4">We Do Not Sell Your Data</h3>
              <p className="text-gray-700 mb-4">
                We do not sell, rent, or trade your personal information to third parties for marketing purposes.
              </p>

              <h3 className="text-xl font-semibold text-gray-800 mb-3 mt-4">Legal Requirements</h3>
              <p className="text-gray-700 mb-4">
                We may disclose your information if required by law or in response to valid requests by
                public authorities.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-semibold text-gray-800 mb-4">5. Data Security</h2>
              <p className="text-gray-700 mb-4">
                We implement security measures to protect your information:
              </p>
              <ul className="list-disc pl-6 text-gray-700 mb-4">
                <li>Encryption of sensitive data in transit (HTTPS) and at rest</li>
                <li>Password hashing using industry-standard algorithms</li>
                <li>Secure token storage for TikTok authentication</li>
                <li>Regular security updates and monitoring</li>
              </ul>
              <p className="text-gray-700 mb-4">
                However, no method of transmission over the Internet is 100% secure. While we strive to
                protect your information, we cannot guarantee absolute security.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-semibold text-gray-800 mb-4">6. Data Retention</h2>
              <p className="text-gray-700 mb-4">
                We retain your information for as long as your account is active or as needed to provide
                the Service. You may request deletion of your account and associated data at any time.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-semibold text-gray-800 mb-4">7. Your Rights</h2>
              <p className="text-gray-700 mb-4">
                You have the right to:
              </p>
              <ul className="list-disc pl-6 text-gray-700 mb-4">
                <li>Access your personal information</li>
                <li>Correct inaccurate data</li>
                <li>Request deletion of your data</li>
                <li>Export your data</li>
                <li>Revoke TikTok account access</li>
                <li>Opt-out of communications</li>
              </ul>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-semibold text-gray-800 mb-4">8. Cookies and Tracking</h2>
              <p className="text-gray-700 mb-4">
                We use cookies and similar tracking technologies to:
              </p>
              <ul className="list-disc pl-6 text-gray-700 mb-4">
                <li>Maintain your login session</li>
                <li>Remember your preferences</li>
                <li>Analyze usage patterns</li>
              </ul>
              <p className="text-gray-700 mb-4">
                You can control cookie settings through your browser preferences.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-semibold text-gray-800 mb-4">9. Third-Party Services</h2>
              <p className="text-gray-700 mb-4">
                Our Service integrates with TikTok. Please review TikTok's Privacy Policy to understand
                how they collect, use, and share your information. We are not responsible for TikTok's
                privacy practices.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-semibold text-gray-800 mb-4">10. Children's Privacy</h2>
              <p className="text-gray-700 mb-4">
                Our Service is not intended for users under the age of 13. We do not knowingly collect
                personal information from children under 13. If you become aware that a child has provided
                us with personal information, please contact us.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-semibold text-gray-800 mb-4">11. International Data Transfers</h2>
              <p className="text-gray-700 mb-4">
                Your information may be transferred to and maintained on servers located outside of your
                jurisdiction where data protection laws may differ. By using the Service, you consent to
                this transfer.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-semibold text-gray-800 mb-4">12. Changes to Privacy Policy</h2>
              <p className="text-gray-700 mb-4">
                We may update this Privacy Policy from time to time. We will notify you of any changes by
                posting the new Privacy Policy on this page and updating the "Last Updated" date.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-semibold text-gray-800 mb-4">13. Contact Us</h2>
              <p className="text-gray-700 mb-4">
                If you have questions about this Privacy Policy or our data practices, please contact us at:
              </p>
              <p className="text-gray-700 mb-4">
                Email: privacy@tiktimer.com
              </p>
            </section>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PrivacyPolicyPage;
