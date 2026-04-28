"use client";

import { useState, useRef, ChangeEvent, DragEvent } from "react";

interface FileUploadProps {
  onFileSelect: (file: File) => void;
  disabled?: boolean;
}

export function FileUpload({ onFileSelect, disabled = false }: FileUploadProps) {
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragEnter = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDragOver = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    const files = e.dataTransfer.files;
    if (files.length > 0) {
      onFileSelect(files[0]);
    }
  };

  const handleFileInput = (e: ChangeEvent<HTMLInputElement>) => {
    const files = e.currentTarget.files;
    if (files && files.length > 0) {
      onFileSelect(files[0]);
    }
  };

  return (
    <div
      onDragEnter={handleDragEnter}
      onDragLeave={handleDragLeave}
      onDragOver={handleDragOver}
      onDrop={handleDrop}
      className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-all ${
        isDragging
          ? "border-blue-500 bg-blue-50"
          : "border-gray-300 bg-gray-50 hover:border-gray-400"
      } ${disabled ? "opacity-50 cursor-not-allowed" : ""}`}
      onClick={() => !disabled && fileInputRef.current?.click()}
    >
      <input
        ref={fileInputRef}
        type="file"
        accept=".xlsx,.csv"
        onChange={handleFileInput}
        disabled={disabled}
        className="hidden"
        aria-label="Upload Excel file"
      />

      <div className="space-y-2">
        <div className="text-4xl">📁</div>
        <h3 className="text-lg font-semibold text-gray-900">
          Drop your Excel file here
        </h3>
        <p className="text-sm text-gray-600">
          or click to browse (.xlsx or .csv, max 5MB)
        </p>
      </div>
    </div>
  );
}
