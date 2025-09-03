import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Slider } from '@/components/ui/slider';
import { 
  Download, 
  Eye, 
  RotateCcw, 
  ZoomIn, 
  ZoomOut, 
  Settings,
  Play,
  Pause,
  SkipBack,
  SkipForward,
  Loader2
} from 'lucide-react';
import { toast } from 'sonner';
import { apiService, type AnalysisResults, type JobStatus } from '@/services/api';

const Results = () => {
  const [searchParams] = useSearchParams();
  const jobId = searchParams.get('jobId');
  
  const [currentSlice, setCurrentSlice] = useState([50]);
  const [isPlaying, setIsPlaying] = useState(false);
  const [zoomLevel, setZoomLevel] = useState([100]);
  const [rotationX, setRotationX] = useState([0]);
  const [rotationY, setRotationY] = useState([0]);
  const [rotationZ, setRotationZ] = useState([0]);
  
  // Real data states
  const [results, setResults] = useState<AnalysisResults | null>(null);
  const [jobStatus, setJobStatus] = useState<JobStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Load results when component mounts
  useEffect(() => {
    if (!jobId) {
      setError('No job ID provided');
      setLoading(false);
      return;
    }

    const loadResults = async () => {
      try {
        console.log('Loading results for job:', jobId);
        
        // Get job status first
        const status = await apiService.getJobStatus(jobId);
        setJobStatus(status);
        
        if (status.status === 'completed') {
          // Get detailed results
          const jobResults = await apiService.getJobResults(jobId);
          setResults(jobResults);
          console.log('Results loaded:', jobResults);
        } else if (status.status === 'error') {
          setError(`Processing failed: ${status.error || 'Unknown error'}`);
        } else {
          setError('Processing not yet completed');
        }
      } catch (error: any) {
        console.error('Failed to load results:', error);
        setError(`Failed to load results: ${error.message}`);
      } finally {
        setLoading(false);
      }
    };

    loadResults();
  }, [jobId]);

  // Use real data or fallback to mock data
  const processingInfo = results ? {
    totalSlices: results.total_slices || 0,
    processingTime: results.processing_time || 'N/A',
    boneVolume: results.bone_volume || 'N/A',
    surfaceArea: results.surface_area_cm2 || results.surface_area || 'N/A',
    resolution: results.resolution || 'N/A',
    boneLength: results.bone_length || 'N/A',
    boneDensity: results.bone_density_percent || results.bone_density || 'N/A'
  } : {
    totalSlices: 100,
    processingTime: 'Loading...',
    boneVolume: 'Loading...',
    surfaceArea: 'Loading...',
    resolution: 'Loading...',
    boneLength: 'Loading...',
    boneDensity: 'Loading...'
  };

  const downloadModel = async (format: 'stl' | 'obj' | 'ply' | 'report') => {
    if (!jobId) {
      toast.error('No job ID available for download');
      return;
    }

    try {
      await apiService.downloadAndSaveFile(jobId, format);
      toast.success(`${format.toUpperCase()} file downloaded successfully`);
    } catch (error: any) {
      console.error('Download failed:', error);
      toast.error(`Download failed: ${error.message}`);
    }
  };

  // Loading state
  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-background to-muted/20 flex items-center justify-center">
        <div className="text-center space-y-4">
          <Loader2 className="h-8 w-8 animate-spin mx-auto" />
          <p className="text-lg">Loading results...</p>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-background to-muted/20 flex items-center justify-center">
        <Card className="max-w-md">
          <CardHeader>
            <CardTitle className="text-destructive">Results Not Available</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-muted-foreground">{error}</p>
            {error.includes('No job ID provided') && (
              <div className="p-4 bg-muted/30 rounded-lg">
                <p className="text-sm text-muted-foreground">
                  To view results, you need to:
                </p>
                <ol className="text-sm text-muted-foreground mt-2 space-y-1 list-decimal list-inside">
                  <li>Upload DICOM files on the Upload page</li>
                  <li>Wait for processing to complete</li>
                  <li>You'll be automatically redirected here</li>
                </ol>
              </div>
            )}
            <div className="flex gap-2">
              <Button 
                onClick={() => window.location.href = '/upload'}
                className="flex-1"
              >
                Upload DICOM Files
              </Button>
              <Button 
                variant="outline"
                onClick={() => window.history.back()}
              >
                Go Back
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-background to-muted/20 p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">3D Reconstruction Results</h1>
            <p className="text-muted-foreground mt-1">
              Interactive visualization of your bone reconstruction
            </p>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => downloadModel('stl')}>
              <Download className="h-4 w-4 mr-2" />
              Download STL
            </Button>
            <Button variant="outline" onClick={() => downloadModel('obj')}>
              <Download className="h-4 w-4 mr-2" />
              Download OBJ
            </Button>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Main Visualization Area */}
          <div className="lg:col-span-3 space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  3D Bone Model
                  <div className="flex gap-2">
                    <Button variant="outline" size="sm">
                      <Eye className="h-4 w-4" />
                    </Button>
                    <Button variant="outline" size="sm">
                      <RotateCcw className="h-4 w-4" />
                    </Button>
                    <Button variant="outline" size="sm">
                      <Settings className="h-4 w-4" />
                    </Button>
                  </div>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="aspect-[4/3] bg-gradient-to-br from-muted/50 to-muted/20 rounded-lg border-2 border-dashed border-muted-foreground/20 flex items-center justify-center">
                  <div className="text-center space-y-4">
                    <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center mx-auto">
                      <div className="w-8 h-8 bg-primary/20 rounded-full flex items-center justify-center">
                        <div className="w-4 h-4 bg-primary rounded-full animate-pulse" />
                      </div>
                    </div>
                    <div>
                      <p className="font-medium text-lg">3D Model Viewer</p>
                      <p className="text-sm text-muted-foreground">
                        Interactive 3D bone reconstruction would render here
                      </p>
                    </div>
                  </div>
                </div>
                
                {/* 3D Controls */}
                <div className="mt-4 p-4 bg-muted/30 rounded-lg space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="space-y-2">
                      <label className="text-sm font-medium">Rotation X</label>
                      <Slider
                        value={rotationX}
                        onValueChange={setRotationX}
                        max={360}
                        step={1}
                        className="w-full"
                      />
                      <span className="text-xs text-muted-foreground">{rotationX[0]}°</span>
                    </div>
                    <div className="space-y-2">
                      <label className="text-sm font-medium">Rotation Y</label>
                      <Slider
                        value={rotationY}
                        onValueChange={setRotationY}
                        max={360}
                        step={1}
                        className="w-full"
                      />
                      <span className="text-xs text-muted-foreground">{rotationY[0]}°</span>
                    </div>
                    <div className="space-y-2">
                      <label className="text-sm font-medium">Rotation Z</label>
                      <Slider
                        value={rotationZ}
                        onValueChange={setRotationZ}
                        max={360}
                        step={1}
                        className="w-full"
                      />
                      <span className="text-xs text-muted-foreground">{rotationZ[0]}°</span>
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-4">
                    <div className="flex items-center gap-2">
                      <Button variant="outline" size="sm">
                        <ZoomOut className="h-4 w-4" />
                      </Button>
                      <div className="w-24">
                        <Slider
                          value={zoomLevel}
                          onValueChange={setZoomLevel}
                          min={50}
                          max={200}
                          step={10}
                          className="w-full"
                        />
                      </div>
                      <Button variant="outline" size="sm">
                        <ZoomIn className="h-4 w-4" />
                      </Button>
                      <span className="text-sm text-muted-foreground min-w-12">
                        {zoomLevel[0]}%
                      </span>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Tabs defaultValue="slices" className="w-full">
              <TabsList className="grid w-full grid-cols-2">
                <TabsTrigger value="slices">2D Slices</TabsTrigger>
                <TabsTrigger value="analysis">Analysis</TabsTrigger>
              </TabsList>
              
              <TabsContent value="slices">
                <Card>
                  <CardHeader>
                    <CardTitle>CT Slice Viewer</CardTitle>
                    <CardDescription>
                      Navigate through the CT scan slices
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="aspect-video bg-gradient-to-br from-muted/50 to-muted/20 rounded-lg border-2 border-dashed border-muted-foreground/20 flex items-center justify-center">
                      <div className="text-center space-y-2">
                        <div className="text-lg font-medium">Slice {currentSlice[0]} of {processingInfo.totalSlices}</div>
                        <p className="text-sm text-muted-foreground">
                          2D CT slice would render here
                        </p>
                      </div>
                    </div>
                    
                    <div className="mt-4 space-y-4">
                      <div className="flex items-center gap-4">
                        <Button variant="outline" size="sm">
                          <SkipBack className="h-4 w-4" />
                        </Button>
                        <Button 
                          variant="outline" 
                          size="sm"
                          onClick={() => setIsPlaying(!isPlaying)}
                        >
                          {isPlaying ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
                        </Button>
                        <Button variant="outline" size="sm">
                          <SkipForward className="h-4 w-4" />
                        </Button>
                        
                        <div className="flex-1">
                          <Slider
                            value={currentSlice}
                            onValueChange={setCurrentSlice}
                            max={processingInfo.totalSlices}
                            min={1}
                            step={1}
                            className="w-full"
                          />
                        </div>
                        
                        <span className="text-sm text-muted-foreground min-w-16 text-right">
                          {currentSlice[0]}/{processingInfo.totalSlices}
                        </span>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>
              
              <TabsContent value="analysis">
                <Card>
                  <CardHeader>
                    <CardTitle>Bone Analysis Results</CardTitle>
                    <CardDescription>
                      Detailed measurements and characteristics
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      <div className="p-4 bg-muted/30 rounded-lg text-center">
                        <div className="text-2xl font-bold text-primary">156.7</div>
                        <div className="text-sm text-muted-foreground">Volume (cm³)</div>
                      </div>
                      <div className="p-4 bg-muted/30 rounded-lg text-center">
                        <div className="text-2xl font-bold text-primary">234.5</div>
                        <div className="text-sm text-muted-foreground">Surface Area (cm²)</div>
                      </div>
                      <div className="p-4 bg-muted/30 rounded-lg text-center">
                        <div className="text-2xl font-bold text-primary">97.3</div>
                        <div className="text-sm text-muted-foreground">Bone Density (%)</div>
                      </div>
                      <div className="p-4 bg-muted/30 rounded-lg text-center">
                        <div className="text-2xl font-bold text-primary">12.4</div>
                        <div className="text-sm text-muted-foreground">Length (cm)</div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>
            </Tabs>
          </div>

          {/* Side Panel */}
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Processing Info</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-sm text-muted-foreground">Status</span>
                  <Badge variant="default" className="bg-green-500">
                    Completed
                  </Badge>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-muted-foreground">Total Slices</span>
                  <span className="text-sm font-medium">{processingInfo.totalSlices}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-muted-foreground">Processing Time</span>
                  <span className="text-sm font-medium">{processingInfo.processingTime}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-muted-foreground">Resolution</span>
                  <span className="text-sm font-medium">{processingInfo.resolution}</span>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Export Options</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <Button variant="outline" className="w-full justify-start" onClick={() => downloadModel('stl')}>
                  <Download className="h-4 w-4 mr-2" />
                  STL Format
                </Button>
                <Button variant="outline" className="w-full justify-start" onClick={() => downloadModel('obj')}>
                  <Download className="h-4 w-4 mr-2" />
                  OBJ Format
                </Button>
                <Button variant="outline" className="w-full justify-start" onClick={() => downloadModel('ply')}>
                  <Download className="h-4 w-4 mr-2" />
                  PLY Format
                </Button>
                <Button variant="outline" className="w-full justify-start" onClick={() => downloadModel('report')}>
                  <Download className="h-4 w-4 mr-2" />
                  Analysis Report
                </Button>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-lg">View Settings</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium">Opacity</label>
                  <Slider
                    defaultValue={[100]}
                    max={100}
                    step={5}
                    className="w-full"
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">Brightness</label>
                  <Slider
                    defaultValue={[50]}
                    max={100}
                    step={5}
                    className="w-full"
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">Contrast</label>
                  <Slider
                    defaultValue={[50]}
                    max={100}
                    step={5}
                    className="w-full"
                  />
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Results;