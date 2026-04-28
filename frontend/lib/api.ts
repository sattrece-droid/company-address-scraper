import axios, { AxiosInstance } from "axios";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const api: AxiosInstance = axios.create({
  baseURL: API_URL,
  timeout: 30000,
  headers: {
    "Content-Type": "application/json",
  },
});

export interface CompanyInput {
  company_name: string;
  zip_code?: string;
  website?: string;
}

export interface JobResponse {
  job_id: string;
  status: string;
  companies_processed?: number;
  results?: any[];
  statistics?: any;
  error?: string;
}

export interface JobStatus {
  job_id: string;
  status: "pending" | "processing" | "completed" | "failed";
  progress?: number;
  companies_processed?: number;
  total_companies?: number;
  results?: any[];
  error?: string;
}

export const uploadFile = async (
  file: File
): Promise<{ job_id: string; total_companies: number }> => {
  const formData = new FormData();
  formData.append("file", file);

  const response = await api.post("/api/jobs/upload", formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });

  return response.data;
};

export const getJobStatus = async (jobId: string): Promise<JobStatus> => {
  const response = await api.get(`/api/jobs/${jobId}`);
  return response.data;
};

export const downloadResults = async (jobId: string): Promise<Blob> => {
  const response = await api.get(`/api/jobs/${jobId}/download`, {
    responseType: "blob",
  });
  return response.data;
};

export const validateFile = (file: File): string | null => {
  const validTypes = ["application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "text/csv"];
  const validExtensions = [".xlsx", ".csv"];

  if (!validTypes.includes(file.type)) {
    const ext = "." + file.name.split(".").pop()?.toLowerCase();
    if (!validExtensions.includes(ext)) {
      return "Invalid file type. Please upload .xlsx or .csv";
    }
  }

  if (file.size > 5 * 1024 * 1024) {
    // 5MB limit
    return "File size exceeds 5MB limit";
  }

  return null;
};

export default api;
