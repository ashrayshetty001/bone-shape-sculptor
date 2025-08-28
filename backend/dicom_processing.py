#!/usr/bin/env python3
"""
DICOM Processing Module - Simplified version of the original code
Integrates functionality from dicom_2d_main.py and paste-2.py
"""

import os
import sys
import numpy as np
import pydicom
from skimage import measure, filters, morphology, exposure, segmentation
import cv2
from scipy import ndimage
import matplotlib.pyplot as plt
from pathlib import Path

try:
    import vtk
    from vtk.util import numpy_support
    VTK_AVAILABLE = True
except ImportError:
    VTK_AVAILABLE = False
    print("Warning: VTK not available. 3D functionality will be limited.")

class EnhancedDicom2D:
    """Enhanced 2D DICOM Analysis - Simplified version"""
    
    def __init__(self):
        self.dicom_data = None
        self.pixel_array = None
        self.patient_info = {}
        self.processing_parameters = {
            'contrast_enhancement': True,
            'noise_reduction': True,
            'edge_enhancement': False,
            'histogram_equalization': False
        }

    def load_dicom(self, file_path):
        """Load a single DICOM file"""
        try:
            self.dicom_data = pydicom.dcmread(file_path)
            self.pixel_array = self.dicom_data.pixel_array.astype(np.float64)
            
            # Extract patient information
            self.patient_info = {
                'patient_id': getattr(self.dicom_data, 'PatientID', 'Unknown'),
                'patient_name': str(getattr(self.dicom_data, 'PatientName', 'Unknown')),
                'study_date': getattr(self.dicom_data, 'StudyDate', 'Unknown'),
                'modality': getattr(self.dicom_data, 'Modality', 'Unknown'),
                'slice_thickness': getattr(self.dicom_data, 'SliceThickness', 'Unknown'),
                'pixel_spacing': getattr(self.dicom_data, 'PixelSpacing', ['Unknown', 'Unknown'])
            }
            
            return True
            
        except Exception as e:
            print(f"Error loading DICOM file {file_path}: {e}")
            return False

    def enhance_image(self, image):
        """Apply image enhancement techniques"""
        enhanced = image.copy()
        
        # Contrast enhancement
        if self.processing_parameters['contrast_enhancement']:
            enhanced = exposure.rescale_intensity(enhanced)
        
        # Noise reduction
        if self.processing_parameters['noise_reduction']:
            enhanced = filters.gaussian(enhanced, sigma=0.5)
        
        # Edge enhancement
        if self.processing_parameters['edge_enhancement']:
            edges = filters.sobel(enhanced)
            enhanced = enhanced + 0.3 * edges
        
        # Histogram equalization
        if self.processing_parameters['histogram_equalization']:
            enhanced = exposure.equalize_hist(enhanced)
        
        return enhanced

    def segment_bones(self, image, threshold_method='otsu'):
        """Segment bone structures from the image"""
        try:
            if threshold_method == 'otsu':
                threshold = filters.threshold_otsu(image)
            elif threshold_method == 'manual':
                threshold = 0.5  # Adjust as needed
            else:
                threshold = filters.threshold_otsu(image)
            
            binary = image > threshold
            
            # Morphological operations to clean up
            binary = morphology.remove_small_objects(binary, min_size=100)
            binary = morphology.binary_closing(binary, morphology.disk(3))
            
            return binary
            
        except Exception as e:
            print(f"Error in bone segmentation: {e}")
            return np.zeros_like(image, dtype=bool)

    def analyze_image(self):
        """Perform comprehensive image analysis"""
        if self.pixel_array is None:
            return None
        
        analysis_results = {
            'image_shape': self.pixel_array.shape,
            'pixel_value_range': (self.pixel_array.min(), self.pixel_array.max()),
            'mean_intensity': self.pixel_array.mean(),
            'std_intensity': self.pixel_array.std(),
        }
        
        # Enhanced image
        enhanced = self.enhance_image(self.pixel_array)
        
        # Bone segmentation
        bone_mask = self.segment_bones(enhanced)
        
        # Bone analysis
        if bone_mask.any():
            analysis_results.update({
                'bone_area_pixels': np.sum(bone_mask),
                'bone_percentage': (np.sum(bone_mask) / bone_mask.size) * 100,
            })
        
        return analysis_results

class DicomTo3D:
    """3D DICOM Reconstruction - Simplified version"""
    
    def __init__(self, dicom_dir):
        self.dicom_dir = dicom_dir
        self.slices = []
        self.volume = None
        self.spacing = None
        self.origin = None
        
        # Processing parameters
        self.bone_lower = 200  # HU threshold for bone
        self.bone_upper = 3000
        self.smoothing_iterations = 25
        self.smoothing_pass_band = 0.05
        self.min_size_percent = 0.1

    def is_dicom_file(self, filepath):
        """Check if a file is a DICOM file"""
        try:
            with open(filepath, 'rb') as f:
                f.seek(128)
                magic = f.read(4)
                return magic == b'DICM'
        except:
            return False

    def load_dicom_series(self):
        """Load all DICOM files from the directory"""
        try:
            dicom_files = []
            
            # Find all DICOM files
            for root, dirs, files in os.walk(self.dicom_dir):
                for file in files:
                    filepath = os.path.join(root, file)
                    if self.is_dicom_file(filepath):
                        dicom_files.append(filepath)
            
            if not dicom_files:
                print(f"No DICOM files found in {self.dicom_dir}")
                return False
            
            print(f"Found {len(dicom_files)} DICOM files")
            
            # Load and sort slices
            slices = []
            for filepath in dicom_files:
                try:
                    ds = pydicom.dcmread(filepath)
                    if hasattr(ds, 'pixel_array'):
                        slices.append(ds)
                except Exception as e:
                    print(f"Error reading {filepath}: {e}")
            
            if not slices:
                print("No valid DICOM slices loaded")
                return False
            
            # Sort slices by position
            try:
                slices.sort(key=lambda x: float(x.ImagePositionPatient[2]))
            except:
                print("Warning: Could not sort slices by position")
            
            self.slices = slices
            print(f"Loaded {len(self.slices)} DICOM slices")
            
            # Extract spacing information
            try:
                self.spacing = [
                    float(slices[0].PixelSpacing[0]),
                    float(slices[0].PixelSpacing[1]),
                    float(slices[0].SliceThickness) if hasattr(slices[0], 'SliceThickness') else 1.0
                ]
                self.origin = slices[0].ImagePositionPatient
            except:
                self.spacing = [1.0, 1.0, 1.0]
                self.origin = [0.0, 0.0, 0.0]
            
            return True
            
        except Exception as e:
            print(f"Error loading DICOM series: {e}")
            return False

    def create_volume(self):
        """Create 3D volume from DICOM slices"""
        if not self.slices:
            return False
        
        try:
            # Get dimensions
            slice_shape = self.slices[0].pixel_array.shape
            volume_shape = (len(self.slices), slice_shape[0], slice_shape[1])
            
            # Create volume array
            self.volume = np.zeros(volume_shape, dtype=np.float32)
            
            # Fill volume with slice data
            for i, slice_data in enumerate(self.slices):
                pixel_array = slice_data.pixel_array.astype(np.float32)
                
                # Convert to Hounsfield units if possible
                if hasattr(slice_data, 'RescaleSlope') and hasattr(slice_data, 'RescaleIntercept'):
                    pixel_array = pixel_array * slice_data.RescaleSlope + slice_data.RescaleIntercept
                
                self.volume[i] = pixel_array
            
            print(f"Created volume with shape: {self.volume.shape}")
            print(f"Volume value range: {self.volume.min()} to {self.volume.max()}")
            
            return True
            
        except Exception as e:
            print(f"Error creating volume: {e}")
            return False

    def segment_bones(self):
        """Segment bone structures from the volume"""
        if self.volume is None:
            return None
        
        try:
            # Apply bone thresholding
            bone_mask = (self.volume >= self.bone_lower) & (self.volume <= self.bone_upper)
            
            # Morphological operations to clean up
            from scipy import ndimage
            bone_mask = ndimage.binary_fill_holes(bone_mask)
            bone_mask = ndimage.binary_erosion(bone_mask, iterations=1)
            bone_mask = ndimage.binary_dilation(bone_mask, iterations=2)
            
            print(f"Bone segmentation complete. Bone voxels: {np.sum(bone_mask)}")
            
            return bone_mask
            
        except Exception as e:
            print(f"Error in bone segmentation: {e}")
            return None

    def create_3d_model(self):
        """Create 3D model from the volume data"""
        if not self.create_volume():
            return False
        
        bone_mask = self.segment_bones()
        if bone_mask is None:
            return False
        
        try:
            if not VTK_AVAILABLE:
                print("VTK not available. Using scikit-image for mesh generation.")
                # Use scikit-image marching cubes as fallback
                from skimage import measure
                
                # Generate mesh using marching cubes
                verts, faces, normals, values = measure.marching_cubes(
                    bone_mask.astype(np.uint8), 
                    level=0.5,
                    spacing=self.spacing
                )
                
                self.vertices = verts
                self.faces = faces
                self.normals = normals
                
                print(f"Generated mesh: {len(verts)} vertices, {len(faces)} faces")
                return True
            
            else:
                # Use VTK for advanced processing
                return self._create_vtk_model(bone_mask)
                
        except Exception as e:
            print(f"Error creating 3D model: {e}")
            return False

    def _create_vtk_model(self, bone_mask):
        """Create 3D model using VTK"""
        try:
            # Convert numpy array to VTK
            vtk_data = numpy_support.numpy_to_vtk(
                bone_mask.ravel(), 
                deep=True, 
                array_type=vtk.VTK_UNSIGNED_CHAR
            )
            
            # Create VTK image data
            img = vtk.vtkImageData()
            img.SetDimensions(bone_mask.shape)
            img.SetSpacing(self.spacing)
            img.SetOrigin(self.origin)
            img.GetPointData().SetScalars(vtk_data)
            
            # Create surface using marching cubes
            surface = vtk.vtkMarchingCubes()
            surface.SetInputData(img)
            surface.SetValue(0, 0.5)
            surface.Update()
            
            # Smooth the surface
            smoother = vtk.vtkSmoothPolyDataFilter()
            smoother.SetInputConnection(surface.GetOutputPort())
            smoother.SetNumberOfIterations(self.smoothing_iterations)
            smoother.SetRelaxationFactor(0.1)
            smoother.Update()
            
            # Store the result
            self.vtk_polydata = smoother.GetOutput()
            
            print(f"VTK model created with {self.vtk_polydata.GetNumberOfPoints()} points")
            return True
            
        except Exception as e:
            print(f"Error in VTK model creation: {e}")
            return False

    def save_model(self, output_path, format='stl'):
        """Save the 3D model to file"""
        try:
            output_dir = os.path.dirname(output_path)
            os.makedirs(output_dir, exist_ok=True)
            
            if VTK_AVAILABLE and hasattr(self, 'vtk_polydata'):
                # Save using VTK
                if format.lower() == 'stl':
                    writer = vtk.vtkSTLWriter()
                elif format.lower() == 'obj':
                    writer = vtk.vtkOBJWriter()
                elif format.lower() == 'ply':
                    writer = vtk.vtkPLYWriter()
                else:
                    writer = vtk.vtkSTLWriter()
                
                writer.SetFileName(output_path)
                writer.SetInputData(self.vtk_polydata)
                writer.Write()
                
            else:
                # Fallback: save as simple mesh format
                if hasattr(self, 'vertices') and hasattr(self, 'faces'):
                    self._save_simple_mesh(output_path, format)
                else:
                    print("No mesh data available to save")
                    return False
            
            print(f"Model saved to: {output_path}")
            return True
            
        except Exception as e:
            print(f"Error saving model: {e}")
            return False

    def _save_simple_mesh(self, output_path, format):
        """Save simple mesh data (fallback when VTK not available)"""
        if format.lower() == 'obj':
            with open(output_path, 'w') as f:
                # Write vertices
                for v in self.vertices:
                    f.write(f"v {v[0]} {v[1]} {v[2]}\n")
                
                # Write faces
                for face in self.faces:
                    f.write(f"f {face[0]+1} {face[1]+1} {face[2]+1}\n")
        else:
            # For STL and other formats, we'd need additional libraries
            print(f"Format {format} not supported without VTK. Saved as OBJ instead.")
            self._save_simple_mesh(output_path.replace('.stl', '.obj').replace('.ply', '.obj'), 'obj')

    def get_analysis_info(self):
        """Get analysis information about the 3D model"""
        info = {
            'total_slices': len(self.slices) if self.slices else 0,
            'volume_shape': self.volume.shape if self.volume is not None else None,
            'spacing': self.spacing,
            'origin': self.origin,
        }
        
        if hasattr(self, 'vertices'):
            info['vertex_count'] = len(self.vertices)
            info['face_count'] = len(self.faces)
        
        if hasattr(self, 'vtk_polydata'):
            info['vtk_points'] = self.vtk_polydata.GetNumberOfPoints()
            info['vtk_cells'] = self.vtk_polydata.GetNumberOfCells()
        
        return info