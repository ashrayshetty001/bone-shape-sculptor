import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { Upload as UploadIcon, FileImage, X, CheckCircle, Archive } from 'lucide-react';
import { toast } from 'sonner';
import { apiService, type JobStatus } from '@/services/api';

interface UploadedFile {
  file: File;
  id: string;
  status: 'pending' | 'uploading' | 'completed' | 'error';
  progress: number;
  isZip?: boolean;
}

const Upload = () => {
  const navigate = useNavigate();
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [currentJobId, setCurrentJobId] = useState<string | null>(null);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const newFiles = acceptedFiles.map(file => ({
      file,
      id: Math.random().toString(36).substr(2, 9),
      status: 'pending' as const,
      progress: 0,
      isZip: file.name.toLowerCase().endsWith('.zip'),
    }));
    
    setFiles(prev => [...prev, ...newFiles]);
    
    // Count ZIP files and DICOM files separately
    const zipFiles = acceptedFiles.filter(f => f.name.toLowerCase().endsWith('.zip'));
    const dicomFiles = acceptedFiles.filter(f => f.name.toLowerCase().endsWith('.dcm') || f.name.toLowerCase().endsWith('.dicom'));
    
    let message = '';
    if (zipFiles.length > 0 && dicomFiles.length > 0) {
      message = `${zipFiles.length} ZIP file(s) and ${dicomFiles.length} DICOM file(s) added`;
    } else if (zipFiles.length > 0) {
      message = `${zipFiles.length} ZIP file(s) added`;
    } else {
      message = `${dicomFiles.length} DICOM file(s) added`;
    }
    
    toast.success(message);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/dicom': ['.dcm', '.dicom'],
      'application/octet-stream': ['.dcm', '.dicom'],
      'application/zip': ['.zip'],
      'application/x-zip-compressed': ['.zip'],
    },
    multiple: true,
  });

  const removeFile = (id: string) => {
    setFiles(prev => prev.filter(f => f.id !== id));
  };

  const processFiles = async () => {
    if (files.length === 0) {
      toast.error('Please upload DICOM files first');
      return;
    }

    setIsProcessing(true);
    
    try {
      // Get actual File objects from the uploaded files
      const filesToUpload = files.map(f => f.file);
      
      // Call the real API to process files
      const result = await apiService.processFiles(
        filesToUpload,
        (status: JobStatus) => {
          // Update progress based on backend status
          console.log('Processing status:', status);
          setCurrentJobId(status.job_id);
          
          // Update file statuses based on backend progress
          setFiles(prev => prev.map(f => ({
            ...f,
            status: status.status === 'completed' ? 'completed' : 'uploading',
            progress: status.progress
          })));
        }
      );

      // Navigate to results page with job ID
      toast.success('Processing completed successfully!');
      navigate(`/results?jobId=${result.jobId}`);
      
    } catch (error: any) {
      console.error('Processing failed:', error);
      toast.error(`Processing failed: ${error.message}`);
      
      // Mark all files as error
      setFiles(prev => prev.map(f => ({
        ...f,
        status: 'error'
      })));
    } finally {
      setIsProcessing(false);
    }
  };

  const getStatusColor = (status: UploadedFile['status']) => {
    switch (status) {
      case 'pending': return 'bg-muted';
      case 'uploading': return 'bg-primary';
      case 'completed': return 'bg-green-500';
      case 'error': return 'bg-destructive';
      default: return 'bg-muted';
    }
  };

  const getStatusText = (status: UploadedFile['status']) => {
    switch (status) {
      case 'pending': return 'Pending';
      case 'uploading': return 'Processing';
      case 'completed': return 'Completed';
      case 'error': return 'Error';
      default: return 'Unknown';
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-background to-muted/20 p-6">
      <div className="max-w-4xl mx-auto space-y-8">
        <div className="text-center space-y-4">
          <h1 className="text-4xl font-bold bg-gradient-to-r from-primary to-primary/60 bg-clip-text text-transparent">
            3D Bone Reconstruction AI
          </h1>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            Upload DICOM files from CT scans to generate 3D bone reconstructions using advanced AI algorithms
          </p>
        </div>

        <Card className="border-2 border-dashed border-primary/20 hover:border-primary/40 transition-colors">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <UploadIcon className="h-5 w-5" />
              Upload DICOM Files
            </CardTitle>
            <CardDescription>
<<<<<<< HEAD
              Drag and drop your DICOM (.dcm) files or ZIP archives containing DICOM files here, or click to browse
=======
              Drag and drop your DICOM (.dcm) files or ZIP archives here, or click to browse
>>>>>>> 7b675b3b930315b3e12c8f0c9a276d80f9f3b831
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div
              {...getRootProps()}
              className={`
                p-8 border-2 border-dashed rounded-lg cursor-pointer transition-all
                ${isDragActive 
                  ? 'border-primary bg-primary/5' 
                  : 'border-muted-foreground/25 hover:border-primary/50'
                }
              `}
            >
              <input {...getInputProps()} />
              <div className="text-center space-y-4">
                <div className="mx-auto w-12 h-12 bg-primary/10 rounded-full flex items-center justify-center">
                  <FileImage className="h-6 w-6 text-primary" />
                </div>
                {isDragActive ? (
                  <p className="text-primary font-medium">Drop the files here...</p>
                ) : (
                  <div className="space-y-2">
                    <p className="text-foreground font-medium">
                      Click to upload or drag and drop
                    </p>
                    <p className="text-sm text-muted-foreground">
<<<<<<< HEAD
                      DICOM files (.dcm, .dicom) or ZIP archives (.zip) containing DICOM files
=======
                      DICOM files (.dcm, .dicom) or ZIP archives
>>>>>>> 7b675b3b930315b3e12c8f0c9a276d80f9f3b831
                    </p>
                  </div>
                )}
              </div>
            </div>
          </CardContent>
        </Card>

        {files.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>Uploaded Files ({files.length})</CardTitle>
              <CardDescription>
                Review your DICOM files before processing
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                {files.map((file) => (
                  <div
                    key={file.id}
                    className="flex items-center justify-between p-3 border rounded-lg"
                  >
                    <div className="flex items-center gap-3 flex-1">
                      {file.isZip ? (
                        <Archive className="h-4 w-4 text-blue-500" />
                      ) : (
                        <FileImage className="h-4 w-4 text-muted-foreground" />
                      )}
                      <span className="font-medium truncate">{file.file.name}</span>
                      {file.isZip && (
                        <Badge variant="outline" className="text-xs">
                          ZIP Archive
                        </Badge>
                      )}
                      <Badge 
                        variant="secondary" 
                        className={getStatusColor(file.status)}
                      >
                        {getStatusText(file.status)}
                      </Badge>
                    </div>
                    
                    <div className="flex items-center gap-2">
                      {file.status === 'uploading' && (
                        <div className="w-24">
                          <Progress value={file.progress} className="h-2" />
                        </div>
                      )}
                      {file.status === 'completed' && (
                        <CheckCircle className="h-4 w-4 text-green-500" />
                      )}
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => removeFile(file.id)}
                        disabled={isProcessing}
                      >
                        <X className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
              
              <div className="flex gap-2 pt-4">
                <Button 
                  onClick={processFiles} 
                  disabled={isProcessing || files.length === 0}
                  className="flex-1"
                >
                  {isProcessing ? 'Processing...' : 'Start 3D Reconstruction'}
                </Button>
                <Button 
                  variant="outline" 
                  onClick={() => setFiles([])}
                  disabled={isProcessing}
                >
                  Clear All
                </Button>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
};

export default Upload;