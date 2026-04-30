"use client";

import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { getJobStatus } from "@/lib/api";
import { ProgressBar } from "@/components/ProgressBar";
import { Spinner } from "@/components/Spinner";
import { AdPlaceholder } from "@/components/AdPlaceholder";

function ProcessingContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const jobId = searchParams.get("job_id");

  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState<"pending" | "processing" | "completed" | "failed">(
    "pending"
  );
  const [companiesProcessed, setCompaniesProcessed] = useState(0);
  const [totalCompanies, setTotalCompanies] = useState(0);
  const [currentCompany, setCurrentCompany] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [elapsedTime, setElapsedTime] = useState(0);

  useEffect(() => {
    if (!jobId) {
      router.push("/");
      return;
    }

    const startTime = Date.now();
    let pollInterval: NodeJS.Timeout;
    let timeInterval: NodeJS.Timeout;

    const pollStatus = async () => {
      try {
        const jobStatus = await getJobStatus(jobId);

        setStatus(jobStatus.status);
        setProgress(jobStatus.progress || 0);
        setCompaniesProcessed(jobStatus.companies_processed || 0);
        setTotalCompanies(jobStatus.total_companies || 0);

        // Set current company being processed
        if (jobStatus.results && jobStatus.results.length > 0) {
          const lastResult = jobStatus.results[jobStatus.results.length - 1];
          setCurrentCompany(lastResult.company_name || "");
        }

        // Redirect to preview when completed
        if (jobStatus.status === "completed") {
          clearInterval(pollInterval);
          clearInterval(timeInterval);
          setTimeout(() => {
            router.push(`/preview?job_id=${jobId}`);
          }, 1000);
        }

        if (jobStatus.status === "failed") {
          setError(jobStatus.error || "Job failed");
          clearInterval(pollInterval);
          clearInterval(timeInterval);
        }
      } catch (err: any) {
        console.error("Error polling job status:", err);
        setError(err.message || "Failed to get job status");
      }
    };

    // Start polling immediately
    pollStatus();
    pollInterval = setInterval(pollStatus, 2000);

    // Update elapsed time
    timeInterval = setInterval(() => {
      setElapsedTime(Math.floor((Date.now() - startTime) / 1000));
    }, 100);

    // Timeout after 5 minutes
    const timeoutHandle = setTimeout(() => {
      clearInterval(pollInterval);
      clearInterval(timeInterval);
      setError("Processing timed out after 5 minutes");
    }, 5 * 60 * 1000);

    return () => {
      clearInterval(pollInterval);
      clearInterval(timeInterval);
      clearTimeout(timeoutHandle);
    };
  }, [jobId, router]);

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  };

  if (!jobId) {
    return (
      <div className="text-center py-12">
        <Spinner label="Loading..." />
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 py-8">
      {/* Main Content */}
      <div className="lg:col-span-3 space-y-6">
        {/* Header */}
        <div className="card">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">
            Processing Your File
          </h2>
          <p className="text-gray-600">
            We're finding and scraping all company locations. This may take a few minutes...
          </p>
        </div>

        {/* Ad Banner */}
        <AdPlaceholder size="banner" />

        {/* Progress Section */}
        <div className="card space-y-6">
          <div>
            <h3 className="card-title mb-4">Progress</h3>
            <ProgressBar progress={progress} label="Overall Progress" />
            <div className="mt-4 grid grid-cols-3 gap-4 text-center">
              <div className="bg-blue-50 rounded-lg p-3">
                <p className="text-sm text-gray-600">Processed</p>
                <p className="text-2xl font-bold text-blue-600">
                  {companiesProcessed}/{totalCompanies}
                </p>
              </div>
              <div className="bg-purple-50 rounded-lg p-3">
                <p className="text-sm text-gray-600">Status</p>
                <p className="text-xl font-bold text-purple-600 capitalize">
                  {status === "processing" ? "Running..." : status}
                </p>
              </div>
              <div className="bg-green-50 rounded-lg p-3">
                <p className="text-sm text-gray-600">Elapsed Time</p>
                <p className="text-2xl font-bold text-green-600">
                  {formatTime(elapsedTime)}
                </p>
              </div>
            </div>
          </div>

          {/* Current Company */}
          {currentCompany && (
            <div className="border-t border-gray-200 pt-4">
              <p className="text-sm text-gray-600 mb-2">Currently Processing:</p>
              <div className="flex items-center gap-2">
                <Spinner size="sm" />
                <p className="font-semibold text-gray-900">{currentCompany}</p>
              </div>
            </div>
          )}
        </div>

        {/* Error Message */}
        {error && (
          <div className="alert alert-error">
            <span className="text-lg">❌</span>
            <div>
              <p className="font-semibold">Processing Error</p>
              <p className="text-sm">{error}</p>
              <button
                onClick={() => router.push("/")}
                className="btn btn-secondary text-sm mt-2"
              >
                Start Over
              </button>
            </div>
          </div>
        )}

        {/* Status Info */}
        {!error && status !== "completed" && (
          <div className="alert alert-info">
            <span className="text-lg">ℹ️</span>
            <div>
              <p className="font-semibold">Processing in Progress</p>
              <p className="text-sm">
                Please keep this page open. You'll be automatically redirected when complete.
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Sidebar */}
      <div className="space-y-6">
        {/* Sidebar Ad */}
        <AdPlaceholder size="sidebar" />

        {/* Processing Tips */}
        <div className="card">
          <h3 className="card-title text-base mb-3">Processing Tips</h3>
          <ul className="space-y-2 text-sm text-gray-600">
            <li>✓ Keep this tab open</li>
            <li>✓ Don't refresh the page</li>
            <li>✓ Processing takes 1-5 min</li>
            <li>✓ You'll see results soon</li>
          </ul>
        </div>

        {/* Estimated Time */}
        <div className="card">
          <h3 className="card-title text-base mb-3">Estimate</h3>
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-gray-600">Companies:</span>
              <span className="font-semibold">{totalCompanies}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-600">Est. Time:</span>
              <span className="font-semibold">
                {totalCompanies ? `${Math.ceil(totalCompanies * 0.5)} min` : "-"}
              </span>
            </div>
            <div className="border-t border-gray-200 pt-2 mt-2">
              <p className="text-xs text-gray-500">
                Cached results process instantly. Fresh results take longer.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function ProcessingPage() {
  return (
    <Suspense fallback={<div className="text-center py-12"><Spinner label="Loading..." /></div>}>
      <ProcessingContent />
    </Suspense>
  );
}
