#!/usr/bin/env python3
"""
DICOM Processing Module - Real Implementation
Integrates the actual processing algorithms from the GitHub repository
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
import json
from datetime import datetime
import traceback

try:
    import vtk
    from vtk.util import numpy_support
    VTK_AVAILABLE = True
    print("VTK is available for advanced 3D processing")
except ImportError:
    VTK_AVAILABLE = False
    print("Warning: VTK not available. Using scikit-image for 3D processing.")

class EnhancedDicom2D:
    """Enhanced 2D DICOM Analysis with real processing algorithms"""
    
    def __init__(self):
        self.dicom_data = None
        self.pixel_array = None
        self.patient_info = {}
        self.enhanced_image = None
        self.bone_mask = None
        self.analysis_results = {}
        
        # Processing parameters from original code
        self.processing_parameters = {
            'contrast_enhancement': True,
            'noise_reduction': True,
            'edge_enhancement': True,
            'histogram_equalization': False,
            'bone_threshold_lower': 200,  # HU for bone
            'bone_threshold_upper': 3000,
            'gaussian_sigma': 0.8,
            'morphology_disk_size': 3
        }

    def load_dicom(self, file_path):
        """Load and validate a single DICOM file"""
        try:
            print(f"Loading DICOM file: {file_path}")
            
            # Read DICOM file with force=True for better compatibility
            self.dicom_data = pydicom.dcmread(file_path, force=True)
            
            if not hasattr(self.dicom_data, 'pixel_array'):
                print(f"Warning: No pixel data in {file_path}")
                return False
                
            # Get pixel array and convert to proper format
            self.pixel_array = self.dicom_data.pixel_array.astype(np.float64)
            
            # Convert to Hounsfield Units if possible
            if hasattr(self.dicom_data, 'RescaleIntercept') and hasattr(self.dicom_data, 'RescaleSlope'):
                intercept = self.dicom_data.RescaleIntercept
                slope = self.dicom_data.RescaleSlope
                self.pixel_array = self.pixel_array * slope + intercept
                print(f"Converted to Hounsfield Units using slope={slope}, intercept={intercept}")
            
            # Extract comprehensive patient information
            self.patient_info = {
                'patient_id': getattr(self.dicom_data, 'PatientID', 'Unknown'),
                'patient_name': str(getattr(self.dicom_data, 'PatientName', 'Unknown')),
                'study_date': getattr(self.dicom_data, 'StudyDate', 'Unknown'),
                'modality': getattr(self.dicom_data, 'Modality', 'Unknown'),
                'slice_thickness': getattr(self.dicom_data, 'SliceThickness', 'Unknown'),
                'pixel_spacing': getattr(self.dicom_data, 'PixelSpacing', ['Unknown', 'Unknown']),
                'image_orientation': getattr(self.dicom_data, 'ImageOrientationPatient', None),
                'image_position': getattr(self.dicom_data, 'ImagePositionPatient', None),
                'window_center': getattr(self.dicom_data, 'WindowCenter', None),
                'window_width': getattr(self.dicom_data, 'WindowWidth', None),
                'bits_stored': getattr(self.dicom_data, 'BitsStored', 16),
                'pixel_representation': getattr(self.dicom_data, 'PixelRepresentation', 0)
            }
            
            print(f"DICOM loaded successfully. Image shape: {self.pixel_array.shape}")
            print(f"Value range: [{self.pixel_array.min():.1f}, {self.pixel_array.max():.1f}]")
            
            return True
            
        except Exception as e:
            print(f"Error loading DICOM file {file_path}: {e}")
            traceback.print_exc()
            return False

    def enhance_image(self):
        """Apply advanced image enhancement techniques from original code"""
        if self.pixel_array is None:
            return False
            
        try:
            print("Applying image enhancement...")
            enhanced = self.pixel_array.copy()
            
            # Normalize to 0-1 range for processing
            enhanced = (enhanced - enhanced.min()) / (enhanced.max() - enhanced.min())
            
            # Apply Gaussian noise reduction
            if self.processing_parameters['noise_reduction']:
                enhanced = ndimage.gaussian_filter(enhanced, 
                                                 sigma=self.processing_parameters['gaussian_sigma'])
                print("Applied Gaussian noise reduction")
            
            # Contrast enhancement using adaptive histogram equalization
            if self.processing_parameters['contrast_enhancement']:
                enhanced = exposure.equalize_adapthist(enhanced, clip_limit=0.02)
                print("Applied adaptive histogram equalization")
            
            # Edge enhancement using unsharp masking
            if self.processing_parameters['edge_enhancement']:
                # Create unsharp mask
                blurred = ndimage.gaussian_filter(enhanced, sigma=2.0)
                unsharp_mask = enhanced - blurred
                enhanced = enhanced + 0.3 * unsharp_mask
                enhanced = np.clip(enhanced, 0, 1)
                print("Applied edge enhancement")
            
            # Global histogram equalization (optional)
            if self.processing_parameters['histogram_equalization']:
                enhanced = exposure.equalize_hist(enhanced)
                print("Applied global histogram equalization")
            
            self.enhanced_image = enhanced
            print("Image enhancement completed")
            return True
            
        except Exception as e:
            print(f"Error in image enhancement: {e}")
            traceback.print_exc()
            return False

    def segment_bones(self):
        """Advanced bone segmentation using multiple techniques"""
        if self.enhanced_image is None:
            if not self.enhance_image():
                return False
        
        try:
            print("Starting bone segmentation...")
            
            # Convert back to HU scale for thresholding if we have the original
            if hasattr(self.dicom_data, 'RescaleIntercept') and hasattr(self.dicom_data, 'RescaleSlope'):
                # Use HU thresholding
                hu_image = self.pixel_array
                bone_mask = (hu_image >= self.processing_parameters['bone_threshold_lower']) & \
                           (hu_image <= self.processing_parameters['bone_threshold_upper'])
                print(f"Applied HU thresholding: {self.processing_parameters['bone_threshold_lower']} to {self.processing_parameters['bone_threshold_upper']}")
            else:
                # Use Otsu thresholding on enhanced image
                threshold = filters.threshold_otsu(self.enhanced_image)
                bone_mask = self.enhanced_image > threshold
                print(f"Applied Otsu thresholding with threshold: {threshold:.3f}")
            
            # Morphological operations for cleanup
            print("Applying morphological operations...")
            
            # Remove small objects
            bone_mask = morphology.remove_small_objects(bone_mask, min_size=100)
            
            # Binary closing to fill gaps
            disk_size = self.processing_parameters['morphology_disk_size']
            bone_mask = morphology.binary_closing(bone_mask, morphology.disk(disk_size))
            
            # Binary opening to remove noise
            bone_mask = morphology.binary_opening(bone_mask, morphology.disk(disk_size))
            
            # Fill holes
            bone_mask = ndimage.binary_fill_holes(bone_mask)
            
            self.bone_mask = bone_mask
            
            bone_pixels = np.sum(bone_mask)
            total_pixels = bone_mask.size
            bone_percentage = (bone_pixels / total_pixels) * 100
            
            print(f"Bone segmentation completed:")
            print(f"  - Bone pixels: {bone_pixels}")
            print(f"  - Bone percentage: {bone_percentage:.2f}%")
            
            return True
            
        except Exception as e:
            print(f"Error in bone segmentation: {e}")
            traceback.print_exc()
            return False

    def analyze_image(self):
        """Comprehensive image analysis with real metrics"""
        if self.pixel_array is None:
            return None
        
        try:
            print("Performing comprehensive image analysis...")
            
            # Ensure enhancement and segmentation are done
            if not self.enhance_image():
                return None
            if not self.segment_bones():
                return None
            
            # Basic image statistics
            self.analysis_results = {
                'image_shape': self.pixel_array.shape,
                'pixel_value_range': [float(self.pixel_array.min()), float(self.pixel_array.max())],
                'mean_intensity': float(self.pixel_array.mean()),
                'std_intensity': float(self.pixel_array.std()),
                'enhanced_range': [float(self.enhanced_image.min()), float(self.enhanced_image.max())],
                'enhanced_mean': float(self.enhanced_image.mean()),
                'enhanced_std': float(self.enhanced_image.std())
            }
            
            # Bone analysis from segmentation
            if self.bone_mask is not None:
                bone_pixels = np.sum(self.bone_mask)
                total_pixels = self.bone_mask.size
                
                # Calculate bone area in real units if pixel spacing is available
                pixel_area = 1.0  # default
                if hasattr(self.dicom_data, 'PixelSpacing'):
                    try:
                        spacing = self.dicom_data.PixelSpacing
                        pixel_area = float(spacing[0]) * float(spacing[1])  # mm²
                    except:
                        pixel_area = 1.0
                
                bone_area_mm2 = bone_pixels * pixel_area
                
                self.analysis_results.update({
                    'bone_pixels': int(bone_pixels),
                    'total_pixels': int(total_pixels),
                    'bone_percentage': float((bone_pixels / total_pixels) * 100),
                    'bone_area_mm2': float(bone_area_mm2),
                    'pixel_area_mm2': float(pixel_area)
                })
                
                # Bone intensity statistics
                bone_intensities = self.pixel_array[self.bone_mask]
                if len(bone_intensities) > 0:
                    self.analysis_results.update({
                        'bone_mean_intensity': float(bone_intensities.mean()),
                        'bone_std_intensity': float(bone_intensities.std()),
                        'bone_min_intensity': float(bone_intensities.min()),
                        'bone_max_intensity': float(bone_intensities.max())
                    })
            
            # Add timestamp
            self.analysis_results['analysis_timestamp'] = datetime.now().isoformat()
            
            print("Image analysis completed successfully")
            return self.analysis_results
            
        except Exception as e:
            print(f"Error in image analysis: {e}")
            traceback.print_exc()
            return None

class DicomTo3D:
    """3D DICOM Reconstruction using real algorithms from the repository"""
    
    def __init__(self, dicom_dir):
        self.dicom_dir = dicom_dir
        self.slices = []
        self.volume = None
        self.spacing = None
        self.origin = None
        self.bone_mask_3d = None
        
        # Processing parameters from original code
        self.bone_lower = 200  # HU threshold for bone lower bound
        self.bone_upper = 3000  # HU threshold for bone upper bound
        self.smoothing_iterations = 25
        self.smoothing_pass_band = 0.05
        self.min_size_percent = 0.1  # % of largest component to keep
        
        # VTK objects
        self.vtk_polydata = None
        self.vertices = None
        self.faces = None
        self.normals = None

    def is_dicom_file(self, filepath):
        """Check if a file is a DICOM file by reading magic number"""
        try:
            with open(filepath, 'rb') as f:
                # DICOM files have 'DICM' at offset 128
                f.seek(128)
                magic = f.read(4)
                return magic == b'DICM'
        except:
            return False

    def load_dicom_series(self):
        """Load all DICOM files from directory with comprehensive error handling"""
        try:
            if not self.dicom_dir or not os.path.exists(self.dicom_dir):
                raise ValueError(f"Invalid DICOM directory: {self.dicom_dir}")

            print(f"Loading DICOM series from {self.dicom_dir}...")

            # Get list of all potential DICOM files
            dicom_files = []
            for root, dirs, files in os.walk(self.dicom_dir):
                for f in files:
                    file_path = os.path.join(root, f)
                    # Check by extension first, then by magic number
                    if (f.lower().endswith(('.dcm', '.dic', '.dicom', '.ima')) or 
                        self.is_dicom_file(file_path)):
                        dicom_files.append(file_path)

            if not dicom_files:
                # Fallback: try all files
                for f in os.listdir(self.dicom_dir):
                    file_path = os.path.join(self.dicom_dir, f)
                    if os.path.isfile(file_path) and self.is_dicom_file(file_path):
                        dicom_files.append(file_path)

            if not dicom_files:
                raise ValueError(f"No DICOM files found in {self.dicom_dir}")

            print(f"Found {len(dicom_files)} potential DICOM files")

            # Load each DICOM file with validation
            valid_slices = []
            for file_path in dicom_files:
                try:
                    ds = pydicom.dcmread(file_path, force=True)
                    if hasattr(ds, 'pixel_array') and ds.pixel_array is not None:
                        if ds.pixel_array.size > 0:
                            valid_slices.append(ds)
                            print(f"Loaded: {os.path.basename(file_path)}")
                except Exception as e:
                    print(f"Error reading {os.path.basename(file_path)}: {e}")
                    continue

            if not valid_slices:
                raise ValueError("No valid DICOM slices were loaded")

            # Sort slices by position for proper 3D ordering
            try:
                # Try InstanceNumber first
                valid_slices.sort(key=lambda x: float(getattr(x, 'InstanceNumber', 0)))
                print("Sorted slices by InstanceNumber")
            except:
                try:
                    # Try SliceLocation
                    valid_slices.sort(key=lambda x: float(getattr(x, 'SliceLocation', 0)))
                    print("Sorted slices by SliceLocation")
                except:
                    try:
                        # Try ImagePositionPatient Z coordinate
                        valid_slices.sort(key=lambda x: float(getattr(x, 'ImagePositionPatient', [0,0,0])[2]))
                        print("Sorted slices by ImagePositionPatient Z")
                    except:
                        print("Warning: Could not sort slices by position")

            self.slices = valid_slices
            print(f"Successfully loaded {len(self.slices)} valid DICOM slices")
            
            return True
            
        except Exception as e:
            print(f"Error loading DICOM series: {e}")
            traceback.print_exc()
            return False

    def process_volume(self):
        """Convert DICOM slices to 3D volume with Hounsfield Units"""
        if not self.slices:
            print("No DICOM slices loaded")
            return False
            
        try:
            print("Processing DICOM slices into 3D volume...")

            # Get slice dimensions
            img_shape = self.slices[0].pixel_array.shape
            
            # Create 3D volume array
            self.volume = np.zeros((img_shape[0], img_shape[1], len(self.slices)), dtype=np.float32)

            # Get spacing information
            first_slice = self.slices[0]
            pixel_spacing = getattr(first_slice, 'PixelSpacing', [1.0, 1.0])
            slice_thickness = getattr(first_slice, 'SliceThickness', 1.0)
            
            self.spacing = [float(pixel_spacing[0]), float(pixel_spacing[1]), float(slice_thickness)]
            
            # Get origin
            self.origin = getattr(first_slice, 'ImagePositionPatient', [0.0, 0.0, 0.0])
            
            print(f"Volume spacing: {self.spacing} mm")
            print(f"Volume origin: {self.origin}")

            # Fill the 3D volume with slice data and convert to Hounsfield Units
            for i, slice_data in enumerate(self.slices):
                # Get pixel data
                pixel_array = slice_data.pixel_array.astype(np.int16)

                # Convert to Hounsfield Units (HU) if rescale parameters available
                if hasattr(slice_data, 'RescaleIntercept') and hasattr(slice_data, 'RescaleSlope'):
                    intercept = slice_data.RescaleIntercept
                    slope = slice_data.RescaleSlope
                    hu_image = pixel_array * slope + intercept
                else:
                    hu_image = pixel_array.astype(np.float32)

                self.volume[:, :, i] = hu_image

            print(f"Volume dimensions: {self.volume.shape}")
            print(f"Volume value range: [{self.volume.min():.1f}, {self.volume.max():.1f}] HU")

            # Apply anisotropic diffusion filter to enhance boundaries while reducing noise
            print("Applying noise reduction filter...")
            self.volume = ndimage.gaussian_filter(self.volume, sigma=0.8)
            
            return True
            
        except Exception as e:
            print(f"Error processing volume: {e}")
            traceback.print_exc()
            return False

    def segment_bone_3d(self):
        """Segment bone structures from 3D volume using advanced techniques"""
        if self.volume is None:
            if not self.process_volume():
                return False
        
        try:
            print("Starting 3D bone segmentation...")
            print(f"Using HU thresholds: {self.bone_lower} to {self.bone_upper}")
            
            # Apply bone thresholding in Hounsfield Units
            bone_mask = (self.volume >= self.bone_lower) & (self.volume <= self.bone_upper)
            
            print(f"Initial bone voxels: {np.sum(bone_mask)}")
            
            # Advanced morphological operations for 3D cleanup
            print("Applying 3D morphological operations...")
            
            # Fill holes in 3D
            bone_mask = ndimage.binary_fill_holes(bone_mask)
            
            # 3D binary opening to remove small noise
            struct_elem = ndimage.generate_binary_structure(3, 1)  # 6-connected
            bone_mask = ndimage.binary_opening(bone_mask, structure=struct_elem, iterations=1)
            
            # 3D binary closing to connect nearby structures
            bone_mask = ndimage.binary_closing(bone_mask, structure=struct_elem, iterations=2)
            
            # Remove small connected components
            labeled, num_labels = ndimage.label(bone_mask, structure=struct_elem)
            
            if num_labels > 0:
                # Find sizes of all components
                component_sizes = ndimage.sum(bone_mask, labeled, range(1, num_labels + 1))
                
                # Keep only components larger than min_size_percent of the largest
                max_size = np.max(component_sizes)
                min_size = max_size * self.min_size_percent
                
                # Create mask of components to keep
                keep_components = np.where(component_sizes >= min_size)[0] + 1
                keep_mask = np.isin(labeled, keep_components)
                
                bone_mask = bone_mask & keep_mask
                
                print(f"Kept {len(keep_components)} out of {num_labels} components")
                print(f"Minimum component size: {min_size:.0f} voxels")
            
            self.bone_mask_3d = bone_mask
            
            final_bone_voxels = np.sum(bone_mask)
            total_voxels = bone_mask.size
            bone_volume_percent = (final_bone_voxels / total_voxels) * 100
            
            print(f"3D bone segmentation completed:")
            print(f"  - Final bone voxels: {final_bone_voxels}")
            print(f"  - Bone volume percentage: {bone_volume_percent:.2f}%")
            
            return True
            
        except Exception as e:
            print(f"Error in 3D bone segmentation: {e}")
            traceback.print_exc()
            return False

    def create_3d_model(self):
        """Create 3D model from segmented bone volume"""
        if not self.segment_bone_3d():
            return False
        
        try:
            if VTK_AVAILABLE:
                print("Creating 3D model using VTK...")
                return self._create_vtk_model()
            else:
                print("Creating 3D model using scikit-image...")
                return self._create_skimage_model()
                
        except Exception as e:
            print(f"Error creating 3D model: {e}")
            traceback.print_exc()
            return False

    def _create_vtk_model(self):
        """Create 3D model using VTK for high-quality results"""
        try:
            # Convert numpy array to VTK format
            vtk_data = numpy_support.numpy_to_vtk(
                self.bone_mask_3d.ravel(order='F'), 
                deep=True, 
                array_type=vtk.VTK_UNSIGNED_CHAR
            )
            
            # Create VTK image data
            img = vtk.vtkImageData()
            img.SetDimensions(self.bone_mask_3d.shape)
            img.SetSpacing(self.spacing)
            img.SetOrigin(self.origin)
            img.GetPointData().SetScalars(vtk_data)
            
            # Create surface using marching cubes
            print("Applying marching cubes algorithm...")
            surface = vtk.vtkMarchingCubes()
            surface.SetInputData(img)
            surface.SetValue(0, 0.5)  # Iso-value for surface extraction
            surface.Update()
            
            # Get initial surface
            initial_surface = surface.GetOutput()
            print(f"Initial surface: {initial_surface.GetNumberOfPoints()} points, {initial_surface.GetNumberOfCells()} cells")
            
            # Apply surface smoothing
            print(f"Smoothing surface ({self.smoothing_iterations} iterations)...")
            smoother = vtk.vtkSmoothPolyDataFilter()
            smoother.SetInputData(initial_surface)
            smoother.SetNumberOfIterations(self.smoothing_iterations)
            smoother.SetRelaxationFactor(0.1)
            smoother.SetFeatureAngle(60.0)
            smoother.BoundarySmoothinOn()
            smoother.Update()
            
            # Apply decimation to reduce polygon count while preserving quality
            print("Optimizing mesh...")
            decimate = vtk.vtkDecimatePro()
            decimate.SetInputConnection(smoother.GetOutputPort())
            decimate.SetTargetReduction(0.1)  # Reduce by 10%
            decimate.PreserveTopologyOn()
            decimate.Update()
            
            # Store the final result
            self.vtk_polydata = decimate.GetOutput()
            
            print(f"Final VTK model created:")
            print(f"  - Points: {self.vtk_polydata.GetNumberOfPoints()}")
            print(f"  - Polygons: {self.vtk_polydata.GetNumberOfCells()}")
            
            return True
            
        except Exception as e:
            print(f"Error in VTK model creation: {e}")
            traceback.print_exc()
            return False

    def _create_skimage_model(self):
        """Create 3D model using scikit-image as fallback"""
        try:
            print("Generating mesh using marching cubes (scikit-image)...")
            
            # Use scikit-image marching cubes
            verts, faces, normals, values = measure.marching_cubes(
                self.bone_mask_3d.astype(np.uint8),
                level=0.5,
                spacing=self.spacing,
                gradient_direction='descent'
            )
            
            # Store results
            self.vertices = verts
            self.faces = faces
            self.normals = normals
            
            print(f"Scikit-image model created:")
            print(f"  - Vertices: {len(verts)}")
            print(f"  - Faces: {len(faces)}")
            
            return True
            
        except Exception as e:
            print(f"Error in scikit-image model creation: {e}")
            traceback.print_exc()
            return False

    def save_model(self, output_path, format='stl'):
        """Save the 3D model to file with proper format support"""
        try:
            # Ensure output directory exists
            output_dir = os.path.dirname(output_path)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
            
            format = format.lower()
            
            if VTK_AVAILABLE and hasattr(self, 'vtk_polydata') and self.vtk_polydata:
                print(f"Saving VTK model as {format.upper()}...")
                return self._save_vtk_model(output_path, format)
            elif hasattr(self, 'vertices') and hasattr(self, 'faces'):
                print(f"Saving scikit-image model as {format.upper()}...")
                return self._save_mesh_model(output_path, format)
            else:
                print("Error: No 3D model data available to save")
                return False
                
        except Exception as e:
            print(f"Error saving model: {e}")
            traceback.print_exc()
            return False

    def _save_vtk_model(self, output_path, format):
        """Save VTK model in specified format"""
        try:
            if format == 'stl':
                writer = vtk.vtkSTLWriter()
                writer.SetFileTypeToBinary()  # Binary STL for smaller files
            elif format == 'obj':
                writer = vtk.vtkOBJWriter()
            elif format == 'ply':
                writer = vtk.vtkPLYWriter()
                writer.SetFileTypeToASCII()
            else:
                # Default to STL
                writer = vtk.vtkSTLWriter()
                writer.SetFileTypeToBinary()
                output_path = output_path.rsplit('.', 1)[0] + '.stl'
            
            writer.SetFileName(output_path)
            writer.SetInputData(self.vtk_polydata)
            writer.Write()
            
            print(f"VTK model saved successfully to: {output_path}")
            return True
            
        except Exception as e:
            print(f"Error saving VTK model: {e}")
            return False

    def _save_mesh_model(self, output_path, format):
        """Save mesh model using numpy arrays"""
        try:
            if format == 'obj':
                with open(output_path, 'w') as f:
                    f.write("# OBJ file created by 3D Bone Reconstruction AI\n")
                    f.write(f"# Vertices: {len(self.vertices)}\n")
                    f.write(f"# Faces: {len(self.faces)}\n\n")
                    
                    # Write vertices
                    for vertex in self.vertices:
                        f.write(f"v {vertex[0]:.6f} {vertex[1]:.6f} {vertex[2]:.6f}\n")
                    
                    # Write faces (OBJ uses 1-based indexing)
                    for face in self.faces:
                        f.write(f"f {face[0]+1} {face[1]+1} {face[2]+1}\n")
                        
            elif format == 'ply':
                vertex_count = len(self.vertices)
                face_count = len(self.faces)
                
                with open(output_path, 'w') as f:
                    # PLY header
                    f.write("ply\n")
                    f.write("format ascii 1.0\n")
                    f.write(f"element vertex {vertex_count}\n")
                    f.write("property float x\n")
                    f.write("property float y\n")
                    f.write("property float z\n")
                    f.write(f"element face {face_count}\n")
                    f.write("property list uchar int vertex_indices\n")
                    f.write("end_header\n")
                    
                    # Write vertices
                    for vertex in self.vertices:
                        f.write(f"{vertex[0]:.6f} {vertex[1]:.6f} {vertex[2]:.6f}\n")
                    
                    # Write faces
                    for face in self.faces:
                        f.write(f"3 {face[0]} {face[1]} {face[2]}\n")
            else:
                # For STL and unsupported formats, save as OBJ
                print(f"Format {format} not supported in fallback mode. Saving as OBJ.")
                return self._save_mesh_model(output_path.rsplit('.', 1)[0] + '.obj', 'obj')
            
            print(f"Mesh model saved successfully to: {output_path}")
            return True
            
        except Exception as e:
            print(f"Error saving mesh model: {e}")
            return False

    def get_analysis_info(self):
        """Get comprehensive analysis information about the 3D model"""
        info = {
            'total_slices': len(self.slices) if self.slices else 0,
            'volume_shape': list(self.volume.shape) if self.volume is not None else None,
            'spacing_mm': self.spacing,
            'origin': self.origin,
            'processing_parameters': {
                'bone_hu_lower': self.bone_lower,
                'bone_hu_upper': self.bone_upper,
                'smoothing_iterations': self.smoothing_iterations,
                'min_size_percent': self.min_size_percent
            }
        }
        
        # Calculate volume metrics
        if self.volume is not None:
            voxel_volume = self.spacing[0] * self.spacing[1] * self.spacing[2]  # mm³
            total_volume_mm3 = np.prod(self.volume.shape) * voxel_volume
            info['total_volume_mm3'] = total_volume_mm3
            info['total_volume_cm3'] = total_volume_mm3 / 1000.0
        
        # Bone segmentation metrics
        if self.bone_mask_3d is not None:
            bone_voxels = np.sum(self.bone_mask_3d)
            if self.volume is not None:
                voxel_volume = self.spacing[0] * self.spacing[1] * self.spacing[2]
                bone_volume_mm3 = bone_voxels * voxel_volume
                info['bone_volume_mm3'] = bone_volume_mm3
                info['bone_volume_cm3'] = bone_volume_mm3 / 1000.0
                info['bone_voxel_count'] = int(bone_voxels)
                info['bone_density_percent'] = float((bone_voxels / np.prod(self.volume.shape)) * 100)
        
        # Mesh information
        if hasattr(self, 'vertices') and self.vertices is not None:
            info['mesh_vertices'] = len(self.vertices)
            info['mesh_faces'] = len(self.faces) if hasattr(self, 'faces') else 0
            info['mesh_type'] = 'scikit-image'
        
        if hasattr(self, 'vtk_polydata') and self.vtk_polydata:
            info['vtk_points'] = self.vtk_polydata.GetNumberOfPoints()
            info['vtk_cells'] = self.vtk_polydata.GetNumberOfCells()
            info['mesh_type'] = 'vtk'
        
        # Add creation timestamp
        info['analysis_timestamp'] = datetime.now().isoformat()
        
        return info