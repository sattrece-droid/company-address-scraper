export const formatStatus = (status: string): { label: string; color: string } => {
  const statusMap: Record<string, { label: string; color: string }> = {
    complete: { label: "✓ Complete", color: "text-green-600" },
    partial: { label: "⚠ Partial", color: "text-yellow-600" },
    hq_only: { label: "HQ Only", color: "text-blue-600" },
    manual_required: { label: "Manual Review", color: "text-orange-600" },
    blocked: { label: "⛔ Blocked", color: "text-red-600" },
    not_found: { label: "Not Found", color: "text-gray-600" },
    zip_mismatch: { label: "Zip Mismatch", color: "text-red-600" },
    error: { label: "Error", color: "text-red-600" },
  };

  return statusMap[status] || { label: status, color: "text-gray-600" };
};

export const formatConfidence = (
  confidence: string | number
): { label: string; color: string } => {
  // Handle string values from backend (e.g., "high", "medium", "low")
  if (typeof confidence === "string") {
    const lowerConfidence = confidence.toLowerCase();
    if (lowerConfidence === "high") {
      return { label: "High", color: "text-green-600" };
    } else if (lowerConfidence === "medium") {
      return { label: "Medium", color: "text-yellow-600" };
    } else if (lowerConfidence === "low") {
      return { label: "Low", color: "text-orange-600" };
    }
    return { label: confidence, color: "text-gray-600" };
  }

  // Handle numeric values (0.0 - 1.0 scale)
  const value = confidence;
  if (value >= 0.9) {
    return { label: "High", color: "text-green-600" };
  } else if (value >= 0.7) {
    return { label: "Medium", color: "text-yellow-600" };
  } else if (value >= 0.5) {
    return { label: "Low", color: "text-orange-600" };
  }

  return { label: "Very Low", color: "text-red-600" };
};

export const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return "0 Bytes";

  const k = 1024;
  const sizes = ["Bytes", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + " " + sizes[i];
};

export const downloadFile = (blob: Blob, filename: string) => {
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  window.URL.revokeObjectURL(url);
};

export const generateTimestamp = (): string => {
  const now = new Date();
  return now.toISOString().replace(/[:.]/g, "-").slice(0, -5);
};

export const formatDate = (date: Date | string): string => {
  if (typeof date === "string") {
    date = new Date(date);
  }

  return date.toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
};

export const parseExcelDate = (excelDate: number): Date => {
  // Excel date serial number (days since 1900-01-01)
  const date = new Date((excelDate - 25569) * 86400 * 1000);
  return date;
};
