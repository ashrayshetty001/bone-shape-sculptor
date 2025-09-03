/**
 * API Service for 3D Bone Reconstruction Backend
 * Handles communication with Flask backend
 */

const API_BASE_URL = 'http://localhost:5000/api';

export interface JobStatus {
  job_id: string;
  status: 'queued' | 'processing' | 'completed' | 'error';
  progress: number;
  files?: Array<{
    filename: string;
    size: number;
    source?: 'direct' | 'zip';
  }>;
  created_at?: string;
  error?: string;
  traceback?: string;
  results?: AnalysisResults;
  result_dir?: string;
}

export interface AnalysisResults {
  job_id: string;
  processed_files: number;
  processing_time: string;
  bone_volume: string;
  surface_area: string;
  surface_area_cm2?: string;
  resolution: string;
  total_slices: number;
  bone_density: string;
  bone_density_percent?: string;
  bone_length: string;
  timestamp: string;
  bone_volume_cm3?: string;
  mesh_vertices?: number;
  mesh_faces?: number;
  files_info?: Array<{
    filename: string;
    patient_info: any;
    analysis: any;
  }>;
}

export interface UploadResponse {
  job_id: string;
  status: string;
  files_uploaded: number;
  message: string;
}

export interface JobSummary {
  job_id: string;
  status: string;
  progress: number;
  created_at?: string;
  files_count: number;
}

class ApiService {
  private async request<T>(
    endpoint: string,
    options: RequestInit = {},
    retries: number = 3
  ): Promise<T> {
    const url = `${API_BASE_URL}${endpoint}`;
    
    for (let attempt = 0; attempt <= retries; attempt++) {
      try {
        const response = await fetch(url, {
          headers: {
            'Content-Type': 'application/json',
            ...options.headers,
          },
          ...options,
        });

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          throw new Error(errorData.error || `HTTP ${response.status}: ${response.statusText}`);
        }

        return response.json();
      } catch (error) {
        const isNetworkError = error instanceof TypeError && 
          (error.message.includes('Failed to fetch') || 
           error.message.includes('NetworkError') ||
           error.message.includes('ERR_NETWORK_CHANGED'));
        
        if (isNetworkError && attempt < retries) {
          // Exponential backoff: wait 1s, 2s, 4s
          const delay = Math.pow(2, attempt) * 1000;
          console.log(`Network error on attempt ${attempt + 1}, retrying in ${delay}ms...`);
          await new Promise(resolve => setTimeout(resolve, delay));
          continue;
        }
        
        throw error;
      }
    }
    
    throw new Error('Max retries exceeded');
  }

  /**
   * Check backend health status
   */
  async healthCheck(): Promise<{
    status: string;
    timestamp: string;
    modules_available: {
      dicom_2d: boolean;
      dicom_3d: boolean;
    };
  }> {
    return this.request('/health');
  }

  /**
   * Upload DICOM files for processing
   */
  async uploadFiles(files: File[]): Promise<UploadResponse> {
    const formData = new FormData();
    
    files.forEach((file) => {
      formData.append('files', file);
    });

    const response = await fetch(`${API_BASE_URL}/upload`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.error || `Upload failed: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Get job processing status
   */
  async getJobStatus(jobId: string): Promise<JobStatus> {
    return this.request(`/jobs/${jobId}/status`, {}, 2); // Fewer retries for polling
  }

  /**
   * Get job results after completion
   */
  async getJobResults(jobId: string): Promise<AnalysisResults> {
    return this.request(`/jobs/${jobId}/results`);
  }

  /**
   * Download result file
   */
  async downloadResultFile(
    jobId: string, 
    fileType: 'stl' | 'obj' | 'ply' | 'report'
  ): Promise<Blob> {
    const response = await fetch(`${API_BASE_URL}/jobs/${jobId}/download/${fileType}`);
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.error || `Download failed: ${response.statusText}`);
    }

    return response.blob();
  }

  /**
   * List all jobs
   */
  async listJobs(): Promise<JobSummary[]> {
    return this.request('/jobs');
  }

  /**
   * Delete a job and its files
   */
  async deleteJob(jobId: string): Promise<{ message: string }> {
    return this.request(`/jobs/${jobId}`, {
      method: 'DELETE',
    });
  }

  /**
   * Poll job status until completion
   */
  async pollJobStatus(
    jobId: string,
    onProgress?: (status: JobStatus) => void,
    intervalMs: number = 2000
  ): Promise<JobStatus> {
    return new Promise((resolve, reject) => {
      let consecutiveErrors = 0;
      const maxConsecutiveErrors = 3;
      
      const poll = async () => {
        try {
          const status = await this.getJobStatus(jobId);
          consecutiveErrors = 0; // Reset error count on success
          
          if (onProgress) {
            onProgress(status);
          }

          if (status.status === 'completed') {
            resolve(status);
          } else if (status.status === 'error') {
            reject(new Error(status.error || 'Job failed'));
          } else {
            // Continue polling with adaptive interval
            const adaptiveInterval = Math.min(intervalMs * Math.pow(1.5, consecutiveErrors), 10000);
            setTimeout(poll, adaptiveInterval);
          }
        } catch (error) {
          consecutiveErrors++;
          console.warn(`Polling error ${consecutiveErrors}/${maxConsecutiveErrors}:`, error);
          
          if (consecutiveErrors >= maxConsecutiveErrors) {
            reject(new Error(`Failed to poll job status after ${maxConsecutiveErrors} consecutive errors: ${error instanceof Error ? error.message : 'Unknown error'}`));
            return;
          }
          
          // Exponential backoff for polling errors
          const backoffInterval = intervalMs * Math.pow(2, consecutiveErrors);
          setTimeout(poll, Math.min(backoffInterval, 30000)); // Cap at 30 seconds
        }
      };

      poll();
    });
  }

  /**
   * Upload files and wait for completion
   */
  async processFiles(
    files: File[],
    onProgress?: (status: JobStatus) => void
  ): Promise<{
    jobId: string;
    results: AnalysisResults;
  }> {
    // Upload files
    const uploadResponse = await this.uploadFiles(files);
    
    // Poll for completion
    const finalStatus = await this.pollJobStatus(
      uploadResponse.job_id,
      onProgress
    );

    if (!finalStatus.results) {
      throw new Error('No results available');
    }

    return {
      jobId: uploadResponse.job_id,
      results: finalStatus.results,
    };
  }

  /**
   * Download and save file to user's device
   */
  async downloadAndSaveFile(
    jobId: string,
    fileType: 'stl' | 'obj' | 'ply' | 'report',
    filename?: string
  ): Promise<void> {
    const blob = await this.downloadResultFile(jobId, fileType);
    
    // Create download link
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    
    // Set filename
    const extension = fileType === 'report' ? 'json' : fileType;
    link.download = filename || `3d_bone_model_${jobId}.${extension}`;
    
    // Trigger download
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    // Cleanup
    window.URL.revokeObjectURL(url);
  }
}

// Export singleton instance
export const apiService = new ApiService();

// Utility function to format file size
export const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes';
  
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

// Utility function to format processing time
export const formatProcessingTime = (seconds: number): string => {
  if (seconds < 60) {
    return `${seconds}s`;
  } else if (seconds < 3600) {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}m ${remainingSeconds}s`;
  } else {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${hours}h ${minutes}m`;
  }
};