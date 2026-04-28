import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Company Address Scraper",
  description:
    "Automatically find and scrape all company locations from their websites",
  viewport: "width=device-width, initial-scale=1",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <meta charSet="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
      </head>
      <body>
        <div className="min-h-screen flex flex-col">
          {/* Header */}
          <header className="bg-white border-b border-gray-200">
            <div className="container">
              <div className="py-4">
                <h1 className="text-3xl font-bold text-blue-600">
                  Company Address Scraper
                </h1>
                <p className="text-gray-600 mt-1">
                  Find all physical locations for any company in seconds
                </p>
              </div>
            </div>
          </header>

          {/* Main Content */}
          <main className="flex-1">
            <div className="container">{children}</div>
          </main>

          {/* Footer */}
          <footer className="bg-gray-100 border-t border-gray-200 mt-12">
            <div className="container py-8">
              <div className="grid grid-cols-3 gap-8 mb-8">
                <div>
                  <h3 className="font-semibold mb-2">About</h3>
                  <p className="text-sm text-gray-600">
                    Automatically scrape company locations from their official
                    websites using AI.
                  </p>
                </div>
                <div>
                  <h3 className="font-semibold mb-2">Features</h3>
                  <ul className="text-sm text-gray-600 space-y-1">
                    <li>✓ Automatic address extraction</li>
                    <li>✓ Interactive form handling</li>
                    <li>✓ Pagination support</li>
                  </ul>
                </div>
                <div>
                  <h3 className="font-semibold mb-2">Limits</h3>
                  <ul className="text-sm text-gray-600 space-y-1">
                    <li>Free: 10 companies/day</li>
                    <li>Premium: 500/month</li>
                  </ul>
                </div>
              </div>
              <div className="border-t border-gray-300 pt-4 text-center text-sm text-gray-600">
                <p>
                  © 2026 Company Address Scraper. All rights reserved.{" "}
                  <a href="#" className="text-blue-600 hover:underline">
                    Privacy
                  </a>{" "}
                  •{" "}
                  <a href="#" className="text-blue-600 hover:underline">
                    Terms
                  </a>
                </p>
              </div>
            </div>
          </footer>
        </div>

        {/* Google AdSense Script */}
        {process.env.NEXT_PUBLIC_ADSENSE_ID && (
          <script
            async
            src={`https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=${process.env.NEXT_PUBLIC_ADSENSE_ID}`}
            crossOrigin="anonymous"
          ></script>
        )}
      </body>
    </html>
  );
}
