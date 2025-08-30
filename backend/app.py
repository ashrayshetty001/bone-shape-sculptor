#!/usr/bin/env python3
"""
Flask Backend for 3D Bone Reconstruction AI
Integrates the existing Python DICOM processing code with a REST API
"""

import os
import sys
import json
import uuid
import tempfile
import shutil
import zipfile
from pathlib import Path
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
import threading
import traceback
from datetime import datetime

# Import the existing DICOM processing modules
try:
    from dicom_processing import EnhancedDicom2D, DicomTo3D
except ImportError:
    print("Warning: DICOM processing modules not found. Please ensure dicom_2d_main.py and paste-2.py are available.")
    EnhancedDicom2D = None
    DicomTo3D = None

app = Flask(__name__)
CORS(app)

# Configuration
UPLOAD_FOLDER = 'uploads'
RESULTS_FOLDER = 'results'
ALLOWED_EXTENSIONS = {'dcm', 'dicom', 'zip'}
MAX_CONTENT_LENGTH = 500 * 1024 * 1024  # 500MB max file size

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['RESULTS_FOLDER'] = RESULTS_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# Ensure directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULTS_FOLDER, exist_ok=True)

# Store processing jobs
processing_jobs = {}

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def process_dicom_files(job_id, file_paths):
    """Process DICOM files using real algorithms from the repository"""
    try:
        processing_jobs[job_id]['status'] = 'processing'
        processing_jobs[job_id]['progress'] = 5
        
        # Create job result directory
        job_result_dir = os.path.join(RESULTS_FOLDER, job_id)
        os.makedirs(job_result_dir, exist_ok=True)
        
        processing_jobs[job_id]['progress'] = 10
        
        # Real processing starts here
        print(f"Starting real DICOM processing for job {job_id}")
        print(f"Processing {len(file_paths)} files: {[os.path.basename(f) for f in file_paths]}")
        
        # Initialize results
        analysis_results = {
            'job_id': job_id,
            'processed_files': len(file_paths),
            'files_info': [],
            'timestamp': datetime.now().isoformat()
        }
        
        # Process 2D analysis first for each individual file
        if EnhancedDicom2D:
            processing_jobs[job_id]['progress'] = 15
            print("Starting 2D DICOM analysis...")
            
            dicom_2d = EnhancedDicom2D()
            
            for i, file_path in enumerate(file_paths):
                try:
                    print(f"Processing 2D analysis for: {os.path.basename(file_path)}")
                    
                    # Load and analyze each DICOM file
                    if dicom_2d.load_dicom(file_path):
                        file_analysis = dicom_2d.analyze_image()
                        if file_analysis:
                            file_info = {
                                'filename': os.path.basename(file_path),
                                'patient_info': dicom_2d.patient_info,
                                'analysis': file_analysis
                            }
                            analysis_results['files_info'].append(file_info)
                    
                    # Update progress for 2D processing (15-35%)
                    progress = 15 + (i + 1) * 20 // len(file_paths)
                    processing_jobs[job_id]['progress'] = progress
                    
                except Exception as e:
                    print(f"Error processing 2D analysis for {file_path}: {e}")
                    continue
        
        processing_jobs[job_id]['progress'] = 40
        
        # Process 3D reconstruction using all files
        if DicomTo3D and file_paths:
            print("Starting 3D reconstruction...")
            
            # Use directory containing the files for batch processing
            dicom_dir = os.path.dirname(file_paths[0])
            
            try:
                dicom_3d = DicomTo3D(dicom_dir)
                processing_jobs[job_id]['progress'] = 45
                
                # Load DICOM series
                print("Loading DICOM series for 3D reconstruction...")
                if dicom_3d.load_dicom_series():
                    processing_jobs[job_id]['progress'] = 55
                    
                    # Create 3D model
                    print("Creating 3D bone model...")
                    if dicom_3d.create_3d_model():
                        processing_jobs[job_id]['progress'] = 75
                        
                        # Save models in multiple formats
                        print("Saving 3D models...")
                        
                        # Save STL
                        stl_path = os.path.join(job_result_dir, '3d_model.stl')
                        if dicom_3d.save_model(stl_path, 'stl'):
                            print(f"STL model saved: {stl_path}")
                        
                        # Save OBJ
                        obj_path = os.path.join(job_result_dir, '3d_model.obj')
                        if dicom_3d.save_model(obj_path, 'obj'):
                            print(f"OBJ model saved: {obj_path}")
                        
                        # Save PLY
                        ply_path = os.path.join(job_result_dir, '3d_model.ply')
                        if dicom_3d.save_model(ply_path, 'ply'):
                            print(f"PLY model saved: {ply_path}")
                        
                        processing_jobs[job_id]['progress'] = 85
                        
                        # Get comprehensive 3D analysis
                        model_info = dicom_3d.get_analysis_info()
                        analysis_results.update({
                            'total_slices': model_info.get('total_slices', 0),
                            'volume_shape': model_info.get('volume_shape'),
                            'spacing_mm': model_info.get('spacing_mm'),
                            'bone_volume_cm3': model_info.get('bone_volume_cm3', 'N/A'),
                            'bone_density_percent': model_info.get('bone_density_percent', 'N/A'),
                            'mesh_vertices': model_info.get('mesh_vertices', model_info.get('vtk_points', 'N/A')),
                            'mesh_faces': model_info.get('mesh_faces', model_info.get('vtk_cells', 'N/A')),
                            'mesh_type': model_info.get('mesh_type', 'unknown')
                        })
                        
                        # Calculate derived metrics
                        if 'bone_volume_cm3' in model_info and model_info['bone_volume_cm3'] != 'N/A':
                            # Estimate surface area (rough approximation)
                            volume_cm3 = model_info['bone_volume_cm3']
                            # Surface area approximation: SA ≈ 4.84 * V^(2/3) for roughly spherical objects
                            surface_area_cm2 = 4.84 * (volume_cm3 ** (2/3))
                            analysis_results['surface_area_cm2'] = f"{surface_area_cm2:.1f} cm²"
                            analysis_results['bone_volume'] = f"{volume_cm3:.1f} cm³"
                        else:
                            analysis_results['surface_area_cm2'] = "N/A"
                            analysis_results['bone_volume'] = "N/A"
                        
                        # Calculate resolution based on spacing
                        if model_info.get('spacing_mm'):
                            spacing = model_info['spacing_mm']
                            analysis_results['resolution'] = f"{spacing[0]:.1f}mm × {spacing[1]:.1f}mm × {spacing[2]:.1f}mm"
                        else:
                            analysis_results['resolution'] = "N/A"
                        
                        print("3D reconstruction completed successfully")
                    else:
                        print("Failed to create 3D model")
                        analysis_results['error'] = "Failed to create 3D model"
                else:
                    print("Failed to load DICOM series for 3D reconstruction")
                    analysis_results['error'] = "Failed to load DICOM series"
                    
            except Exception as e:
                print(f"Error in 3D processing: {e}")
                traceback.print_exc()
                analysis_results['error'] = f"3D processing failed: {str(e)}"
        
        processing_jobs[job_id]['progress'] = 90
        
        # Generate final analysis report
        processing_end_time = datetime.now()
        processing_start_time = datetime.fromisoformat(processing_jobs[job_id]['created_at'])
        processing_duration = processing_end_time - processing_start_time
        
        # Format processing time
        total_seconds = int(processing_duration.total_seconds())
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        analysis_results['processing_time'] = f"{minutes}m {seconds}s"
        
        # Add additional computed metrics
        analysis_results.update({
            'bone_length': "N/A",  # Would need specific measurement algorithm
            'bone_density': analysis_results.get('bone_density_percent', 'N/A')
        })
        
        # Save comprehensive analysis report
        report_path = os.path.join(job_result_dir, 'analysis_report.json')
        with open(report_path, 'w') as f:
            json.dump(analysis_results, f, indent=2, default=str)
        
        print(f"Analysis report saved: {report_path}")
        
        processing_jobs[job_id]['status'] = 'completed'
        processing_jobs[job_id]['progress'] = 100
        processing_jobs[job_id]['results'] = analysis_results
        processing_jobs[job_id]['result_dir'] = job_result_dir
        
        print(f"Job {job_id} completed successfully!")
        print(f"Results: {analysis_results.get('bone_volume', 'N/A')} volume, {analysis_results.get('surface_area_cm2', 'N/A')} surface area")
        
    except Exception as e:
        error_msg = f"Processing failed: {str(e)}"
        print(f"Error processing job {job_id}: {error_msg}")
        traceback.print_exc()
        
        processing_jobs[job_id]['status'] = 'error'
        processing_jobs[job_id]['error'] = error_msg
        processing_jobs[job_id]['traceback'] = traceback.format_exc()

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'modules_available': {
            'dicom_2d': EnhancedDicom2D is not None,
            'dicom_3d': DicomTo3D is not None
        }
    })

@app.route('/api/upload', methods=['POST'])
def upload_files():
    """Upload DICOM files for processing"""
    try:
        if 'files' not in request.files:
            return jsonify({'error': 'No files provided'}), 400
        
        files = request.files.getlist('files')
        
        if not files or all(file.filename == '' for file in files):
            return jsonify({'error': 'No files selected'}), 400
        
        # Generate job ID
        job_id = str(uuid.uuid4())
        
        # Create job directory
        job_dir = os.path.join(UPLOAD_FOLDER, job_id)
        os.makedirs(job_dir, exist_ok=True)
        
        # Save uploaded files
        file_paths = []
        uploaded_files = []
        
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = os.path.join(job_dir, filename)
                file.save(file_path)
                
                # Handle ZIP files
                if filename.lower().endswith('.zip'):
                    try:
                        with zipfile.ZipFile(file_path, 'r') as zip_ref:
                            for zip_info in zip_ref.infolist():
                                if not zip_info.is_dir() and (zip_info.filename.lower().endswith('.dcm') or zip_info.filename.lower().endswith('.dicom')):
                                    # Extract DICOM file
                                    extracted_path = os.path.join(job_dir, os.path.basename(zip_info.filename))
                                    with zip_ref.open(zip_info) as source, open(extracted_path, 'wb') as target:
                                        target.write(source.read())
                                    file_paths.append(extracted_path)
                                    uploaded_files.append({
                                        'filename': f"{filename}:{os.path.basename(zip_info.filename)}",
                                        'size': zip_info.file_size
                                    })
                        # Remove the ZIP file after extraction
                        os.remove(file_path)
                    except zipfile.BadZipFile:
                        print(f"Invalid ZIP file: {filename}")
                else:
                    # Regular DICOM file
                    file_paths.append(file_path)
                    uploaded_files.append({
                        'filename': filename,
                        'size': os.path.getsize(file_path)
                    })
        
        if not file_paths:
            return jsonify({'error': 'No valid DICOM files uploaded'}), 400
        
        # Initialize job status
        processing_jobs[job_id] = {
            'status': 'queued',
            'progress': 0,
            'files': uploaded_files,
            'created_at': datetime.now().isoformat()
        }
        
        # Start processing in background thread
        thread = threading.Thread(
            target=process_dicom_files,
            args=(job_id, file_paths)
        )
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'job_id': job_id,
            'status': 'queued',
            'files_uploaded': len(file_paths),
            'message': 'Files uploaded successfully, processing started'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/jobs/<job_id>/status', methods=['GET'])
def get_job_status(job_id):
    """Get processing job status"""
    if job_id not in processing_jobs:
        return jsonify({'error': 'Job not found'}), 404
    
    job = processing_jobs[job_id]
    return jsonify(job)

@app.route('/api/jobs/<job_id>/results', methods=['GET'])
def get_job_results(job_id):
    """Get processing job results"""
    if job_id not in processing_jobs:
        return jsonify({'error': 'Job not found'}), 404
    
    job = processing_jobs[job_id]
    
    if job['status'] != 'completed':
        return jsonify({'error': 'Job not completed yet'}), 400
    
    return jsonify(job.get('results', {}))

@app.route('/api/jobs/<job_id>/download/<file_type>', methods=['GET'])
def download_result_file(job_id, file_type):
    """Download result files (STL, OBJ, report, etc.)"""
    if job_id not in processing_jobs:
        return jsonify({'error': 'Job not found'}), 404
    
    job = processing_jobs[job_id]
    
    if job['status'] != 'completed':
        return jsonify({'error': 'Job not completed yet'}), 400
    
    result_dir = job.get('result_dir')
    if not result_dir or not os.path.exists(result_dir):
        return jsonify({'error': 'Result files not found'}), 404
    
    # Map file types to actual files
    file_mapping = {
        'stl': '3d_model.stl',
        'obj': '3d_model.obj',
        'ply': '3d_model.ply',
        'report': 'analysis_report.json'
    }
    
    if file_type not in file_mapping:
        return jsonify({'error': 'Invalid file type'}), 400
    
    file_path = os.path.join(result_dir, file_mapping[file_type])
    
    if not os.path.exists(file_path):
        return jsonify({'error': f'{file_type.upper()} file not found'}), 404
    
    return send_file(file_path, as_attachment=True)

@app.route('/api/jobs', methods=['GET'])
def list_jobs():
    """List all processing jobs"""
    return jsonify([
        {
            'job_id': job_id,
            'status': job_data['status'],
            'progress': job_data.get('progress', 0),
            'created_at': job_data.get('created_at'),
            'files_count': len(job_data.get('files', []))
        }
        for job_id, job_data in processing_jobs.items()
    ])

@app.route('/api/jobs/<job_id>', methods=['DELETE'])
def delete_job(job_id):
    """Delete a processing job and its files"""
    if job_id not in processing_jobs:
        return jsonify({'error': 'Job not found'}), 404
    
    try:
        # Remove upload directory
        job_upload_dir = os.path.join(UPLOAD_FOLDER, job_id)
        if os.path.exists(job_upload_dir):
            shutil.rmtree(job_upload_dir)
        
        # Remove result directory
        job_result_dir = os.path.join(RESULTS_FOLDER, job_id)
        if os.path.exists(job_result_dir):
            shutil.rmtree(job_result_dir)
        
        # Remove from memory
        del processing_jobs[job_id]
        
        return jsonify({'message': 'Job deleted successfully'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.errorhandler(413)
def too_large(e):
    return jsonify({'error': 'File too large'}), 413

@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(e):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    print("Starting 3D Bone Reconstruction AI Backend")
    print(f"Upload folder: {UPLOAD_FOLDER}")
    print(f"Results folder: {RESULTS_FOLDER}")
    print(f"Max file size: {MAX_CONTENT_LENGTH / (1024*1024)}MB")
    
    # Run the Flask app
    app.run(
        debug=True,
        host='0.0.0.0',
        port=5000,
        threaded=True
    )