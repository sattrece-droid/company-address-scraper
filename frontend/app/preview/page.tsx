"use client";

import { useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { getJobStatus } from "@/lib/api";
import { StatusBadge } from "@/components/StatusBadge";
import { AdPlaceholder } from "@/components/AdPlaceholder";
import { Spinner } from "@/components/Spinner";
import { formatConfidence } from "@/lib/utils";

interface Address {
  name?: string;
  address: string;
  city: string;
  state?: string;
  zip?: string;
  country?: string;
}

interface CompanyResult {
  company_name: string;
  input_zip_code?: string;
  website?: string;
  status: string;
  confidence: string;
  addresses: Address[];
  cached: boolean;
  timestamp: string;
}

export default function PreviewPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const jobId = searchParams.get("job_id");

  const [results, setResults] = useState<CompanyResult[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState(0);
  const [statistics, setStatistics] = useState<any>(null);

  const itemsPerPage = 5;

  useEffect(() => {
    if (!jobId) {
      router.push("/");
      return;
    }

    const fetchResults = async () => {
      try {
        const jobStatus = await getJobStatus(jobId);

        if (jobStatus.status !== "completed") {
          router.push(`/processing?job_id=${jobId}`);
          return;
        }

        setResults(jobStatus.results || []);
        setStatistics(jobStatus);
        setIsLoading(false);
      } catch (err: any) {
        setError(err.message || "Failed to load results");
        setIsLoading(false);
      }
    };

    fetchResults();
  }, [jobId, router]);

  const paginatedResults = results.slice(
    currentPage * itemsPerPage,
    (currentPage + 1) * itemsPerPage
  );

  const totalPages = Math.ceil(results.length / itemsPerPage);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Spinner label="Loading results..." />
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-2xl mx-auto py-8">
        <div className="alert alert-error">
          <span className="text-lg">❌</span>
          <div>
            <p className="font-semibold">Error Loading Results</p>
            <p className="text-sm">{error}</p>
            <button
              onClick={() => router.push("/")}
              className="btn btn-secondary text-sm mt-2"
            >
              Start Over
            </button>
          </div>
        </div>
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
            Results Preview
          </h2>
          <p className="text-gray-600">
            Review the scraped company locations below. You can download all results or upload another file.
          </p>
        </div>

        {/* Ad Banner */}
        <AdPlaceholder size="banner" />

        {/* Statistics */}
        {statistics && (
          <div className="card">
            <h3 className="card-title mb-4">Summary</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-blue-50 rounded-lg p-3 text-center">
                <p className="text-sm text-gray-600">Total Companies</p>
                <p className="text-2xl font-bold text-blue-600">
                  {statistics.companies_processed}
                </p>
              </div>
              <div className="bg-green-50 rounded-lg p-3 text-center">
                <p className="text-sm text-gray-600">Locations Found</p>
                <p className="text-2xl font-bold text-green-600">
                  {statistics.statistics?.total_addresses_found || 0}
                </p>
              </div>
              <div className="bg-purple-50 rounded-lg p-3 text-center">
                <p className="text-sm text-gray-600">Avg Per Company</p>
                <p className="text-2xl font-bold text-purple-600">
                  {(
                    (statistics.statistics?.total_addresses_found || 0) /
                    (statistics.companies_processed || 1)
                  ).toFixed(1)}
                </p>
              </div>
              <div className="bg-orange-50 rounded-lg p-3 text-center">
                <p className="text-sm text-gray-600">Cached Results</p>
                <p className="text-2xl font-bold text-orange-600">
                  {results.filter((r) => r.cached).length}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Results Table */}
        <div className="card">
          <h3 className="card-title mb-4">
            Locations ({currentPage * itemsPerPage + 1}-
            {Math.min((currentPage + 1) * itemsPerPage, results.length)} of{" "}
            {results.length})
          </h3>

          <div className="space-y-4">
            {paginatedResults.length === 0 ? (
              <p className="text-gray-600 text-center py-8">No results to display</p>
            ) : (
              paginatedResults.map((result, idx) => (
                <div
                  key={`${result.company_name}-${idx}`}
                  className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 transition"
                >
                  {/* Company Header */}
                  <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-2 mb-3 pb-3 border-b border-gray-200">
                    <div>
                      <h4 className="text-lg font-bold text-gray-900">
                        {result.company_name}
                      </h4>
                      {result.input_zip_code && (
                        <p className="text-xs text-gray-500">
                          Input Zip: {result.input_zip_code}
                        </p>
                      )}
                    </div>
                    <div className="flex items-center gap-2">
                      <StatusBadge status={result.status} />
                      {result.cached && (
                        <span className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded-full">
                          ⚡ Cached
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Addresses */}
                  {result.addresses.length > 0 ? (
                    <div className="space-y-2">
                      {result.addresses.map((address, addrIdx) => (
                        <div
                          key={addrIdx}
                          className="bg-gray-50 rounded p-3 text-sm"
                        >
                          {address.name && (
                            <p className="font-semibold text-gray-900">
                              {address.name}
                            </p>
                          )}
                          <p className="text-gray-700">{address.address}</p>
                          <p className="text-gray-600">
                            {address.city}
                            {address.state ? `, ${address.state}` : ""}{" "}
                            {address.zip || ""}
                            {address.country ? ` (${address.country})` : ""}
                          </p>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-gray-600 italic">No addresses found</p>
                  )}

                  {/* Footer */}
                  <div className="mt-3 pt-3 border-t border-gray-200 flex justify-between items-center text-xs text-gray-500">
                    <span>
                      {result.addresses.length} location
                      {result.addresses.length !== 1 ? "s" : ""}
                    </span>
                    <span>
                      Confidence:{" "}
                      <span className={formatConfidence(result.confidence).color}>
                        {formatConfidence(result.confidence).label}
                      </span>
                    </span>
                  </div>
                </div>
              ))
            )}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="mt-6 flex items-center justify-between">
              <button
                onClick={() => setCurrentPage((p) => Math.max(0, p - 1))}
                disabled={currentPage === 0}
                className="btn btn-secondary disabled:opacity-50"
              >
                ← Previous
              </button>
              <p className="text-sm text-gray-600">
                Page {currentPage + 1} of {totalPages}
              </p>
              <button
                onClick={() => setCurrentPage((p) => Math.min(totalPages - 1, p + 1))}
                disabled={currentPage === totalPages - 1}
                className="btn btn-secondary disabled:opacity-50"
              >
                Next →
              </button>
            </div>
          )}
        </div>

        {/* Action Buttons */}
        <div className="flex gap-3">
          <button
            onClick={() => router.push(`/download?job_id=${jobId}`)}
            className="btn btn-primary flex-1"
          >
            Proceed to Download
          </button>
          <button
            onClick={() => router.push("/")}
            className="btn btn-secondary"
          >
            Upload New File
          </button>
        </div>
      </div>

      {/* Sidebar */}
      <div className="space-y-6">
        {/* Sidebar Ad */}
        <AdPlaceholder size="sidebar" />

        {/* Status Breakdown */}
        {statistics?.statistics?.status_breakdown && (
          <div className="card">
            <h3 className="card-title text-base mb-3">Status Breakdown</h3>
            <div className="space-y-2 text-sm">
              {Object.entries(statistics.statistics.status_breakdown).map(
                ([status, count]: [string, any]) => (
                  <div key={status} className="flex justify-between">
                    <span className="text-gray-600 capitalize">{status}:</span>
                    <span className="font-semibold">{count}</span>
                  </div>
                )
              )}
            </div>
          </div>
        )}

        {/* Download Info */}
        <div className="card">
          <h3 className="card-title text-base mb-3">Next Step</h3>
          <p className="text-sm text-gray-600 mb-3">
            Click "Proceed to Download" to generate your Excel file and download all results.
          </p>
          <p className="text-xs text-gray-500">
            You'll see an ad briefly before download starts.
          </p>
        </div>
      </div>
    </div>
  );
}
