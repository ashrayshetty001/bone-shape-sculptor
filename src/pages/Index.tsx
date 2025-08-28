import React from 'react';
import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { 
  Upload, 
  Brain, 
  Zap, 
  Shield, 
  ArrowRight, 
  FileImage,
  BarChart3,
  Download
} from 'lucide-react';

const Index = () => {
  const features = [
    {
      icon: FileImage,
      title: "DICOM Processing",
      description: "Upload and process DICOM files from CT scans with advanced image processing algorithms"
    },
    {
      icon: Brain,
      title: "AI-Powered Reconstruction",
      description: "Leverage machine learning to create accurate 3D bone models from 2D scan data"
    },
    {
      icon: BarChart3,
      title: "Advanced Analysis",
      description: "Get detailed measurements, volume calculations, and bone density analysis"
    },
    {
      icon: Download,
      title: "Multiple Export Formats",
      description: "Download your 3D models in STL, OBJ, PLY formats for further use"
    }
  ];

  const stats = [
    { number: "99.2%", label: "Accuracy Rate" },
    { number: "< 3min", label: "Processing Time" },
    { number: "50+", label: "Supported Formats" },
    { number: "24/7", label: "Availability" }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-muted/20 to-background">
      {/* Hero Section */}
      <section className="relative overflow-hidden px-6 py-20 sm:py-32">
        <div className="max-w-4xl mx-auto text-center space-y-8">
          <div className="space-y-4">
            <Badge variant="secondary" className="mb-4">
              <Zap className="h-3 w-3 mr-1" />
              Powered by AI
            </Badge>
            <h1 className="text-4xl sm:text-6xl font-bold bg-gradient-to-r from-primary via-primary to-primary/60 bg-clip-text text-transparent">
              3D Bone Reconstruction AI
            </h1>
            <p className="text-xl text-muted-foreground max-w-3xl mx-auto leading-relaxed">
              Transform your DICOM CT scans into detailed 3D bone models using advanced AI algorithms. 
              Perfect for medical research, education, and surgical planning.
            </p>
          </div>
          
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Button size="lg" asChild className="text-lg px-8 py-3">
              <Link to="/upload">
                <Upload className="h-5 w-5 mr-2" />
                Start Reconstruction
                <ArrowRight className="h-5 w-5 ml-2" />
              </Link>
            </Button>
            <Button size="lg" variant="outline" asChild className="text-lg px-8 py-3">
              <Link to="/results">
                <BarChart3 className="h-5 w-5 mr-2" />
                View Sample Results
              </Link>
            </Button>
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="px-6 py-16">
        <div className="max-w-6xl mx-auto">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
            {stats.map((stat, index) => (
              <div key={index} className="text-center space-y-2">
                <div className="text-3xl md:text-4xl font-bold text-primary">
                  {stat.number}
                </div>
                <div className="text-sm text-muted-foreground">
                  {stat.label}
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="px-6 py-20">
        <div className="max-w-6xl mx-auto space-y-16">
          <div className="text-center space-y-4">
            <h2 className="text-3xl sm:text-4xl font-bold">
              Powerful Features for Medical Imaging
            </h2>
            <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
              Our platform combines cutting-edge AI with medical imaging expertise
            </p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {features.map((feature, index) => {
              const Icon = feature.icon;
              return (
                <Card key={index} className="border-2 hover:border-primary/20 transition-colors">
                  <CardHeader>
                    <div className="flex items-center space-x-3">
                      <div className="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center">
                        <Icon className="h-5 w-5 text-primary" />
                      </div>
                      <CardTitle className="text-xl">{feature.title}</CardTitle>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <CardDescription className="text-base leading-relaxed">
                      {feature.description}
                    </CardDescription>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </div>
      </section>

      {/* How It Works Section */}
      <section className="px-6 py-20 bg-muted/30">
        <div className="max-w-6xl mx-auto space-y-16">
          <div className="text-center space-y-4">
            <h2 className="text-3xl sm:text-4xl font-bold">
              How It Works
            </h2>
            <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
              Simple three-step process to get your 3D bone reconstruction
            </p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="text-center space-y-4">
              <div className="w-12 h-12 bg-primary rounded-full flex items-center justify-center mx-auto text-white font-bold text-lg">
                1
              </div>
              <h3 className="text-xl font-semibold">Upload DICOM Files</h3>
              <p className="text-muted-foreground">
                Upload your CT scan DICOM files through our secure interface
              </p>
            </div>
            
            <div className="text-center space-y-4">
              <div className="w-12 h-12 bg-primary rounded-full flex items-center justify-center mx-auto text-white font-bold text-lg">
                2
              </div>
              <h3 className="text-xl font-semibold">AI Processing</h3>
              <p className="text-muted-foreground">
                Our AI algorithms analyze and reconstruct your 3D bone model
              </p>
            </div>
            
            <div className="text-center space-y-4">
              <div className="w-12 h-12 bg-primary rounded-full flex items-center justify-center mx-auto text-white font-bold text-lg">
                3
              </div>
              <h3 className="text-xl font-semibold">View & Export</h3>
              <p className="text-muted-foreground">
                Visualize, analyze, and export your 3D model in multiple formats
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="px-6 py-20">
        <div className="max-w-4xl mx-auto text-center space-y-8">
          <div className="space-y-4">
            <h2 className="text-3xl sm:text-4xl font-bold">
              Ready to Start Your 3D Reconstruction?
            </h2>
            <p className="text-lg text-muted-foreground">
              Join researchers and medical professionals using our AI-powered platform
            </p>
          </div>
          
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Button size="lg" asChild className="text-lg px-8 py-3">
              <Link to="/upload">
                <Upload className="h-5 w-5 mr-2" />
                Get Started Now
              </Link>
            </Button>
          </div>
          
          <div className="flex items-center justify-center space-x-2 text-sm text-muted-foreground">
            <Shield className="h-4 w-4" />
            <span>HIPAA Compliant • Secure Processing • No Data Retention</span>
          </div>
        </div>
      </section>
    </div>
  );
};

export default Index;
