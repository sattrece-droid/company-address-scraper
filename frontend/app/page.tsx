"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { FileUpload } from "@/components/FileUpload";
import { AdPlaceholder } from "@/components/AdPlaceholder";
import { validateFile, uploadFile } from "@/lib/api";

export default function Home() {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const handleFileSelect = (file: File) => {
    setError(null);
    const validationError = validateFile(file);

    if (validationError) {
      setError(validationError);
      return;
    }

    setSelectedFile(file);
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      setError("Please select a file first");
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const { job_id } = await uploadFile(selectedFile);
      // Redirect to processing page with job ID
      router.push(`/processing?job_id=${job_id}`);
    } catch (err: any) {
      setError(err.response?.data?.error || "Failed to upload file. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 py-8">
      {/* Main Content */}
      <div className="lg:col-span-3 space-y-6">
        {/* Header Section */}
        <div className="card">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">
            Find All Company Locations
          </h2>
          <p className="text-gray-600">
            Upload an Excel file with company names, and we'll automatically
            find all their physical locations and addresses.
          </p>
        </div>

        {/* Ad Banner */}
        <AdPlaceholder size="banner" />

        {/* File Upload */}
        <div className="card">
          <h3 className="card-title mb-4">Upload Your File</h3>
          <FileUpload onFileSelect={handleFileSelect} disabled={isLoading} />
          {selectedFile && (
            <div className="mt-4 p-3 bg-blue-50 rounded-lg">
              <p className="text-sm text-blue-800">
                ✓ File selected: <span className="font-semibold">{selectedFile.name}</span>
              </p>
            </div>
          )}
        </div>

        {/* Instructions */}
        <div className="card">
          <h3 className="card-title mb-4">File Format</h3>
          <p className="text-sm text-gray-600 mb-4">
            Your Excel file should have the following columns:
          </p>
          <div className="bg-gray-50 rounded-lg p-4 overflow-x-auto">
            <table className="text-sm w-full">
              <thead>
                <tr className="text-gray-700 font-semibold border-b border-gray-200">
                  <th className="text-left py-2 px-2">Column</th>
                  <th className="text-left py-2 px-2">Required</th>
                  <th className="text-left py-2 px-2">Example</th>
                </tr>
              </thead>
              <tbody>
                <tr className="border-b border-gray-100">
                  <td className="py-2 px-2">Company Name</td>
                  <td className="py-2 px-2">✓ Yes</td>
                  <td className="py-2 px-2">Starbucks</td>
                </tr>
                <tr className="border-b border-gray-100">
                  <td className="py-2 px-2">Zip Code</td>
                  <td className="py-2 px-2">✗ Optional</td>
                  <td className="py-2 px-2">90210</td>
                </tr>
                <tr>
                  <td className="py-2 px-2">Website</td>
                  <td className="py-2 px-2">✗ Optional</td>
                  <td className="py-2 px-2">starbucks.com</td>
                </tr>
              </tbody>
            </table>
          </div>
          <p className="text-xs text-gray-500 mt-4">
            💡 Tip: Adding a zip code greatly improves accuracy for companies with
            multiple locations
          </p>
        </div>

        {/* Error Message */}
        {error && (
          <div className="alert alert-error">
            <span className="text-lg">⚠️</span>
            <div>
              <p className="font-semibold">Error</p>
              <p className="text-sm">{error}</p>
            </div>
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex gap-3">
          <button
            onClick={handleUpload}
            disabled={!selectedFile || isLoading}
            className="btn btn-primary flex-1"
          >
            {isLoading ? "Uploading..." : "Start Processing"}
          </button>
          {selectedFile && (
            <button
              onClick={() => {
                setSelectedFile(null);
                setError(null);
              }}
              disabled={isLoading}
              className="btn btn-secondary"
            >
              Clear
            </button>
          )}
        </div>
      </div>

      {/* Sidebar */}
      <div className="space-y-6">
        {/* Sidebar Ad */}
        <AdPlaceholder size="sidebar" />

        {/* Features */}
        <div className="card">
          <h3 className="card-title text-base mb-3">Features</h3>
          <ul className="space-y-2 text-sm text-gray-600">
            <li>✓ Automatic address extraction</li>
            <li>✓ JavaScript-rendered sites</li>
            <li>✓ Interactive forms</li>
            <li>✓ Pagination support</li>
            <li>✓ 7-day cache</li>
            <li>✓ Excel download</li>
          </ul>
        </div>

        {/* Pricing */}
        <div className="card">
          <h3 className="card-title text-base mb-3">Pricing</h3>
          <div className="space-y-3">
            <div>
              <h4 className="font-semibold text-sm">Free</h4>
              <p className="text-xs text-gray-600">10 companies/day</p>
            </div>
            <div className="border-t border-gray-200 pt-3">
              <h4 className="font-semibold text-sm">Premium</h4>
              <p className="text-xs text-gray-600">$5/month - 500 companies</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
