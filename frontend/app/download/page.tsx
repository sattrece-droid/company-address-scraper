"use client";

import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { getJobStatus, downloadResults } from "@/lib/api";
import { AdPlaceholder } from "@/components/AdPlaceholder";
import { Spinner } from "@/components/Spinner";
import { downloadFile, generateTimestamp } from "@/lib/utils";

function DownloadContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const jobId = searchParams.get("job_id");

  const [countdown, setCountdown] = useState(10);
  const [isDownloading, setIsDownloading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [totalLocations, setTotalLocations] = useState(0);
  const [companiesCount, setCompaniesCount] = useState(0);

  // Countdown timer
  useEffect(() => {
    if (countdown <= 0) return;

    const timer = setTimeout(() => {
      setCountdown(countdown - 1);
    }, 1000);

    return () => clearTimeout(timer);
  }, [countdown]);

  // Load job details
  useEffect(() => {
    if (!jobId) {
      router.push("/");
      return;
    }

    const fetchJobDetails = async () => {
      try {
        const jobStatus = await getJobStatus(jobId);
        const locations = jobStatus.results?.reduce(
          (sum: number, r: any) => sum + (r.addresses?.length || 0),
          0
        ) || 0;
        setTotalLocations(locations);
        setCompaniesCount(jobStatus.companies_processed || 0);
      } catch (err) {
        console.error("Error loading job details:", err);
      }
    };

    fetchJobDetails();
  }, [jobId]);

  const handleDownload = async () => {
    if (!jobId) return;

    setIsDownloading(true);
    setError(null);

    try {
      const blob = await downloadResults(jobId);
      const filename = `company-addresses-${generateTimestamp()}.xlsx`;
      downloadFile(blob, filename);

      // Redirect to thank you page after delay
      setTimeout(() => {
        router.push("/");
      }, 2000);
    } catch (err: any) {
      setError(err.message || "Failed to download file");
      setIsDownloading(false);
    }
  };

  const canDownload = countdown === 0 || countdown < 5;

  return (
    <div className="min-h-screen flex flex-col">
      {/* Interstitial Ad Section */}
      <div className="flex-1 flex items-center justify-center bg-gradient-to-br from-gray-50 to-gray-100 p-4">
        <div className="max-w-2xl w-full space-y-6 text-center">
          {/* Large Ad Placeholder */}
          <AdPlaceholder size="interstitial" />

          {/* Countdown Timer */}
          <div className="space-y-4">
            <p className="text-gray-600">
              Your download will be ready in{" "}
              <span className="font-bold text-blue-600">{countdown}</span> seconds
            </p>

            {/* Animated Countdown Circle */}
            <div className="flex justify-center">
              <div className="relative w-32 h-32 flex items-center justify-center">
                <svg className="absolute w-full h-full -rotate-90" viewBox="0 0 100 100">
                  <circle
                    cx="50"
                    cy="50"
                    r="45"
                    fill="none"
                    stroke="#e5e7eb"
                    strokeWidth="4"
                  />
                  <circle
                    cx="50"
                    cy="50"
                    r="45"
                    fill="none"
                    stroke="#3b82f6"
                    strokeWidth="4"
                    strokeDasharray={`${(countdown / 10) * 282.7} 282.7`}
                    className="transition-all duration-1000"
                  />
                </svg>
                <div className="text-center z-10">
                  <div className="text-5xl font-bold text-blue-600">{countdown}</div>
                  <div className="text-sm text-gray-600">seconds</div>
                </div>
              </div>
            </div>

            {/* Skip Button (appears after 5 seconds) */}
            {countdown <= 5 && countdown > 0 && (
              <p className="text-sm text-gray-500 animate-pulse">
                ✓ You can skip the ad now
              </p>
            )}
          </div>

          {/* Download Button */}
          {canDownload && (
            <div className="space-y-3">
              <button
                onClick={handleDownload}
                disabled={isDownloading}
                className="btn btn-success w-full text-lg py-3"
              >
                {isDownloading ? (
                  <span className="flex items-center justify-center gap-2">
                    <Spinner size="sm" />
                    Downloading...
                  </span>
                ) : (
                  "📥 Download Results (Excel)"
                )}
              </button>

              {!isDownloading && (
                <p className="text-xs text-gray-500">
                  File: company-addresses-[date].xlsx
                </p>
              )}
            </div>
          )}

          {/* Error Message */}
          {error && (
            <div className="alert alert-error">
              <span className="text-lg">❌</span>
              <div>
                <p className="font-semibold">Download Failed</p>
                <p className="text-sm">{error}</p>
              </div>
            </div>
          )}

          {/* Info Section */}
          {!error && (
            <div className="bg-white rounded-lg p-6 border border-gray-200">
              <h3 className="font-bold text-gray-900 mb-4">Your Results Summary</h3>
              <div className="grid grid-cols-2 gap-4">
                <div className="text-center">
                  <div className="text-3xl font-bold text-blue-600">
                    {companiesCount}
                  </div>
                  <p className="text-sm text-gray-600">Companies</p>
                </div>
                <div className="text-center">
                  <div className="text-3xl font-bold text-green-600">
                    {totalLocations}
                  </div>
                  <p className="text-sm text-gray-600">Locations</p>
                </div>
              </div>
              <p className="text-xs text-gray-500 mt-4">
                Your Excel file includes company names, addresses, cities, states,
                zip codes, and processing status for all locations.
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 py-4 px-4">
        <div className="max-w-2xl mx-auto text-center text-sm text-gray-600">
          <p>
            Questions? Check our{" "}
            <a href="#" className="text-blue-600 hover:underline">
              FAQ
            </a>{" "}
            or{" "}
            <a href="#" className="text-blue-600 hover:underline">
              contact us
            </a>
          </p>
          <p className="mt-2 text-xs">
            <a href="/" className="text-blue-600 hover:underline">
              Upload another file
            </a>
          </p>
        </div>
      </footer>
    </div>
  );
}

export default function DownloadPage() {
  return (
    <Suspense fallback={<div className="text-center py-12"><Spinner label="Loading..." /></div>}>
      <DownloadContent />
    </Suspense>
  );
}
