import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { Upload as UploadIcon, FileImage, X, CheckCircle } from 'lucide-react';
import { toast } from 'sonner';

interface UploadedFile {
  file: File;
  id: string;
  status: 'pending' | 'uploading' | 'completed' | 'error';
  progress: number;
}

const Upload = () => {
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const newFiles = acceptedFiles.map(file => ({
      file,
      id: Math.random().toString(36).substr(2, 9),
      status: 'pending' as const,
      progress: 0,
    }));
    
    setFiles(prev => [...prev, ...newFiles]);
    toast.success(`${acceptedFiles.length} DICOM file(s) added`);
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
    
    // Simulate file processing
    for (let i = 0; i < files.length; i++) {
      setFiles(prev => prev.map(f => 
        f.id === files[i].id 
          ? { ...f, status: 'uploading' }
          : f
      ));

      // Simulate progress
      for (let progress = 0; progress <= 100; progress += 10) {
        await new Promise(resolve => setTimeout(resolve, 100));
        setFiles(prev => prev.map(f => 
          f.id === files[i].id 
            ? { ...f, progress }
            : f
        ));
      }

      setFiles(prev => prev.map(f => 
        f.id === files[i].id 
          ? { ...f, status: 'completed' }
          : f
      ));
    }

    setIsProcessing(false);
    toast.success('All files processed successfully!');
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
              Drag and drop your DICOM (.dcm) files or ZIP archives here, or click to browse
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
                      DICOM files (.dcm, .dicom) or ZIP archives
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
                      <FileImage className="h-4 w-4 text-muted-foreground" />
                      <span className="font-medium truncate">{file.file.name}</span>
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