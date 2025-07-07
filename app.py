import os
import pandas as pd
import math
import uuid
import time
from datetime import datetime
from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import io
import threading

app = Flask(__name__)
CORS(app)

# Create directories if they don't exist
UPLOAD_FOLDER = 'uploads'
PDF_FOLDER = '/tmp/generated_pdfs'  # Use temp directory for Render free tier
for folder in [UPLOAD_FOLDER, PDF_FOLDER]:
    if not os.path.exists(folder):
        os.makedirs(folder)

# Clean up any existing files in temp directory on startup
def cleanup_temp_directory():
    """Clean up temp directory on startup"""
    try:
        if os.path.exists(PDF_FOLDER):
            for filename in os.listdir(PDF_FOLDER):
                filepath = os.path.join(PDF_FOLDER, filename)
                if os.path.isfile(filepath):
                    os.remove(filepath)
            print("Cleaned up temporary files on startup")
    except Exception as e:
        print(f"Error cleaning up temp directory: {str(e)}")

# Clean up on startup
cleanup_temp_directory()

# Store batch processing status
batch_jobs = {}

def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate the great circle distance between two points on Earth in KM"""
    R = 6371  # Earth's radius in kilometers
    
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    return R * c

def parse_timestamp(timestamp_str):
    """Parse timestamp from various formats"""
    try:
        # Handle pandas datetime objects (when Excel auto-converts)
        if hasattr(timestamp_str, 'strftime'):
            return timestamp_str
        
        # Convert to string if it's not already
        timestamp_str = str(timestamp_str).strip()
        
        # Skip empty or invalid values
        if not timestamp_str or timestamp_str.lower() in ['', 'nan', 'none', 'null']:
            return None
        
        # List of formats to try
        formats = [
            '%d/%m/%y %H:%M',      # 04/02/25 16:19
            '%m/%d/%y %H:%M',      # 02/04/25 16:19
            '%d/%m/%Y %H:%M',      # 04/02/2025 16:19
            '%m/%d/%Y %H:%M',      # 02/04/2025 16:19
            '%Y-%m-%d %H:%M:%S',   # 2025-02-04 16:19:00
            '%Y-%m-%d %H:%M',      # 2025-02-04 16:19
            '%d-%m-%Y %H:%M',      # 04-02-2025 16:19
            '%m-%d-%Y %H:%M',      # 02-04-2025 16:19
            '%d/%m/%y %H:%M:%S',   # 04/02/25 16:19:30
            '%m/%d/%y %H:%M:%S',   # 02/04/25 16:19:30
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(timestamp_str, fmt)
            except ValueError:
                continue
        
        # If all formats fail, print debug info for first few failures
        print(f"Failed to parse timestamp: '{timestamp_str}' (type: {type(timestamp_str)})")
        return None
        
    except Exception as e:
        print(f"Error parsing timestamp '{timestamp_str}': {str(e)}")
        return None

def process_trip_data(df):
    """Process trip data to calculate distances, durations, and speeds"""
    # Input validation
    if df is None or len(df) == 0:
        raise ValueError("DataFrame is empty")
    
    if len(df) < 2:
        raise ValueError("Trip must have at least 2 pings to calculate distances")
    
    # Required columns check
    required_columns = ['latitude', 'longitude', 'device_timestamp']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")
    
    # Sort by timestamp
    df = df.copy()
    df['parsed_timestamp'] = df['device_timestamp'].apply(parse_timestamp)
    
    # Remove rows with invalid timestamps
    df = df.dropna(subset=['parsed_timestamp']).sort_values('parsed_timestamp')
    
    # Check again after filtering
    if len(df) < 2:
        raise ValueError("Trip has insufficient valid data after filtering")
    
    # Reset index to avoid indexing issues
    df = df.reset_index(drop=True)
    
    # Calculate distances and durations
    distances = []
    durations = []
    speeds = []
    
    for i in range(len(df)):
        if i == 0:
            distances.append(0)
            durations.append(0)
            speeds.append(0)
        else:
            try:
                # Calculate distance
                prev_row = df.iloc[i-1]
                curr_row = df.iloc[i]
                
                distance = haversine_distance(
                    prev_row['latitude'], prev_row['longitude'],
                    curr_row['latitude'], curr_row['longitude']
                )
                distances.append(distance)
                
                # Calculate duration in hours
                time_diff = (curr_row['parsed_timestamp'] - prev_row['parsed_timestamp']).total_seconds() / 3600
                durations.append(time_diff)
                
                # Calculate speed (km/h)
                speed = distance / time_diff if time_diff > 0 else 0
                speeds.append(speed)
                
            except Exception as e:
                print(f"Error calculating metrics for row {i}: {str(e)}")
                distances.append(0)
                durations.append(0)
                speeds.append(0)
    
    df['distance_km'] = distances
    df['duration_hours'] = durations
    df['speed_kmh'] = speeds
    
    return df

def generate_pdf_report(trip_data, trip_id):
    """Generate PDF report for a trip"""
    # Input validation
    if trip_data is None or len(trip_data) == 0:
        raise ValueError("Trip data is empty")
    
    if 'parsed_timestamp' not in trip_data.columns:
        raise ValueError("Missing parsed_timestamp column")
    
    buffer = io.BytesIO()
    
    # Reduce margins for better space utilization
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=letter,
        rightMargin=30,
        leftMargin=30,
        topMargin=30,
        bottomMargin=30
    )
    story = []
    
    styles = getSampleStyleSheet()
    
    # Header section with logo on top left (no text)
    if os.path.exists('Freight Tiger Logo.webp'):
        try:
            logo = Image('Freight Tiger Logo.webp', width=2*inch, height=0.8*inch)
            logo.hAlign = 'LEFT'
            story.append(logo)
            story.append(Spacer(1, 20))
        except:
            pass
    
    # Trip information header
    try:
        first_row = trip_data.iloc[0]
        last_row = trip_data.iloc[-1]
    except IndexError:
        raise ValueError("Cannot access trip data rows")
    
    # Header info - removed stoppage time, origin, destination
    report_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Safe calculations with error handling
    try:
        avg_speed = float(trip_data['speed_kmh'].mean())
        total_distance = float(trip_data['distance_km'].sum())
        total_duration = float(trip_data['duration_hours'].sum())
    except (KeyError, ValueError, TypeError):
        avg_speed = 0.0
        total_distance = 0.0
        total_duration = 0.0
    
    header_data = [
        ["Report Generation Timestamp", report_time],
        ["", ""],
        ["Vehicle No:", "TN93C4414"],
        ["Trip ID:", str(trip_id)],
        ["Date of Journey:", first_row['parsed_timestamp'].strftime("%Y-%m-%d %H:%M:%S")],
        ["", ""],
        ["Average Speed:", f"{avg_speed:.2f} KM/Hr"],
        ["Distance Covered:", f"{total_distance:.2f} KM"],
        ["Running Time:", f"{total_duration:.2f} Hrs"]
    ]
    
    header_table = Table(header_data, colWidths=[2.5*inch, 3*inch])
    header_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),  # Bold the first column (headings)
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),       # Regular font for values
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    
    story.append(header_table)
    story.append(Spacer(1, 20))
    
    # Trip details table - removed device label and address columns
    table_data = [
        ["Updated At", "Latitude", "Longitude", "Distance (Km)", "Duration (Minutes)", "Avg Speed (Km/hr)"]
    ]
    
    for i, row in trip_data.iterrows():
        duration_minutes = int(row['duration_hours'] * 60)  # Convert hours to minutes
        table_data.append([
            row['parsed_timestamp'].strftime("%Y-%m-%d %H:%M:%S"),
            f"{row['latitude']:.5f}",
            f"{row['longitude']:.5f}",
            f"{row['distance_km']:.2f}",
            str(duration_minutes),
            f"{row['speed_kmh']:.0f}"  # No decimal places for speed
        ])
    
    # Create table with increased column widths for Distance and Duration
    table = Table(table_data, colWidths=[1.4*inch, 1.1*inch, 1.1*inch, 1.2*inch, 1.2*inch, 1*inch])
    table.setStyle(TableStyle([
        # Header row styling - no background color
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        
        # Data rows styling - no background color
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
        
        # Grid lines
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(table)
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    
    return buffer.getvalue()

def generate_batch_pdfs(batch_id, df):
    """Generate PDFs for multiple trips in background"""
    try:
        # Initialize batch job status
        batch_jobs[batch_id] = {
            'status': 'processing',
            'total_trips': 0,
            'completed_trips': 0,
            'pdfs': [],
            'error': None
        }
        
        # Group by trip_id
        if 'trip_id' in df.columns:
            trip_ids = df['trip_id'].unique()
            batch_jobs[batch_id]['total_trips'] = int(len(trip_ids))  # Convert to native Python int
            
            for i, trip_id in enumerate(trip_ids):
                try:
                    trip_data = df[df['trip_id'] == trip_id]
                    
                    # Enhanced validation before processing
                    if len(trip_data) < 2:
                        print(f"Skipping trip {trip_id}: insufficient data (only {len(trip_data)} pings)")
                        continue
                    
                    # Check for required columns
                    required_columns = ['latitude', 'longitude', 'device_timestamp']
                    missing_columns = [col for col in required_columns if col not in trip_data.columns]
                    if missing_columns:
                        print(f"Skipping trip {trip_id}: missing columns {missing_columns}")
                        continue
                    
                    # Process the trip data
                    processed_data = process_trip_data(trip_data)
                    
                    # Generate PDF
                    pdf_content = generate_pdf_report(processed_data, trip_id)
                    filename = f"trip_report_{trip_id}_{batch_id}.pdf"
                    
                    # Save PDF to the correct directory
                    pdf_path = os.path.join(PDF_FOLDER, filename)
                    with open(pdf_path, 'wb') as f:
                        f.write(pdf_content)
                    
                    # Update batch status
                    batch_jobs[batch_id]['completed_trips'] += 1
                    batch_jobs[batch_id]['pdfs'].append({
                        'filename': filename,
                        'trip_id': int(trip_id),
                        'ping_count': int(len(processed_data)),
                        'total_distance': float(processed_data['distance_km'].sum()),
                        'avg_speed': float(processed_data['speed_kmh'].mean())
                    })
                    
                    print(f"Generated PDF for trip {trip_id} ({i+1}/{len(trip_ids)})")
                    
                except Exception as e:
                    print(f"Error processing trip {trip_id}: {str(e)}")
                    continue
        
        # Mark batch as completed
        batch_jobs[batch_id]['status'] = 'completed'
        print(f"Batch {batch_id} completed: {batch_jobs[batch_id]['completed_trips']} PDFs generated")
        
        # Schedule cleanup after 1 hour (files in /tmp are temporary)
        cleanup_thread = threading.Timer(3600, cleanup_old_files, args=[batch_id])
        cleanup_thread.daemon = True
        cleanup_thread.start()
        
    except Exception as e:
        print(f"Batch processing error: {str(e)}")
        batch_jobs[batch_id]['status'] = 'error'
        batch_jobs[batch_id]['error'] = str(e)

def cleanup_old_files(batch_id):
    """Clean up old PDF files and batch job data"""
    try:
        # Clean up batch job data
        if batch_id in batch_jobs:
            batch_data = batch_jobs[batch_id]
            
            # Remove PDF files from temp directory
            if 'pdfs' in batch_data:
                for pdf_info in batch_data['pdfs']:
                    filename = pdf_info['filename']
                    filepath = os.path.join(PDF_FOLDER, filename)
                    if os.path.exists(filepath):
                        os.remove(filepath)
                        print(f"Cleaned up file: {filename}")
            
            # Remove batch job data
            del batch_jobs[batch_id]
            print(f"Cleaned up batch job: {batch_id}")
            
    except Exception as e:
        print(f"Error during cleanup: {str(e)}")

@app.route('/', methods=['GET'])
def index():
    # Serve React frontend if available
    if os.path.exists('frontend/build/index.html'):
        return send_from_directory('frontend/build', 'index.html')
    return jsonify({'message': 'Trip Analytics API is running'})

@app.route('/<path:path>')
def serve_react_app(path):
    """Serve React app static files"""
    if os.path.exists(f'frontend/build/{path}'):
        return send_from_directory('frontend/build', path)
    # For React Router, return index.html for all other paths
    if os.path.exists('frontend/build/index.html'):
        return send_from_directory('frontend/build', 'index.html')
    return jsonify({'error': 'Frontend not found'}), 404

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not (file.filename.endswith('.csv') or file.filename.endswith('.xlsx')):
        return jsonify({'error': 'Only CSV and Excel (.xlsx) files are allowed'}), 400
    
    try:
        # Read file based on type
        if file.filename.endswith('.xlsx'):
            # For Excel files, read the first sheet by default
            df = pd.read_excel(file, sheet_name=0)
        else:
            # For CSV files
            df = pd.read_csv(file)
        
        # Check required columns
        required_columns = ['latitude', 'longitude', 'device_timestamp']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            return jsonify({
                'error': f'Missing required columns: {missing_columns}',
                'required_columns': required_columns,
                'found_columns': list(df.columns)
            }), 400
        
        # Group by trip_id if available, otherwise treat as single trip
        if 'trip_id' in df.columns:
            trip_ids = df['trip_id'].unique()
            reports = []
            
            for trip_id in trip_ids:
                trip_data = df[df['trip_id'] == trip_id]
                if len(trip_data) > 1:  # Only process trips with multiple pings
                    processed_data = process_trip_data(trip_data)
                    reports.append({
                        'trip_id': int(trip_id),
                        'ping_count': int(len(processed_data)),
                        'total_distance': float(processed_data['distance_km'].sum()),
                        'total_duration': float(processed_data['duration_hours'].sum()),
                        'avg_speed': float(processed_data['speed_kmh'].mean())
                    })
            
            return jsonify({
                'message': 'File processed successfully',
                'trip_count': int(len(reports)),
                'reports': reports
            })
        
        else:
            # Single trip
            processed_data = process_trip_data(df)
            return jsonify({
                'message': 'File processed successfully',
                'trip_count': 1,
                'reports': [{
                    'trip_id': 'single_trip',
                    'ping_count': int(len(processed_data)),
                    'total_distance': float(processed_data['distance_km'].sum()),
                    'total_duration': float(processed_data['duration_hours'].sum()),
                    'avg_speed': float(processed_data['speed_kmh'].mean())
                }]
            })
    
    except Exception as e:
        return jsonify({'error': f'Error processing file: {str(e)}'}), 500

@app.route('/generate-report', methods=['POST'])
def generate_report():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    trip_id = request.form.get('trip_id', 'single_trip')
    worksheet_name = request.form.get('worksheet_name', None)
    
    try:
        # Read file based on type
        if file.filename.endswith('.xlsx'):
            if worksheet_name:
                df = pd.read_excel(file, sheet_name=worksheet_name)
            else:
                # Default to first sheet if no worksheet specified
                df = pd.read_excel(file, sheet_name=0)
        else:
            # For CSV files
            df = pd.read_csv(file)
        
        # Filter by trip_id if specified and column exists
        if trip_id != 'single_trip' and 'trip_id' in df.columns:
            df = df[df['trip_id'] == int(trip_id)]
        
        if len(df) < 2:
            return jsonify({'error': 'Not enough data points for trip analysis'}), 400
        
        # Process data
        processed_data = process_trip_data(df)
        
        # Generate PDF
        pdf_buffer = generate_pdf_report(processed_data, trip_id)
        
        # Return PDF file
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'trip_report_{trip_id}.pdf'
        )
    
    except Exception as e:
        return jsonify({'error': f'Error generating report: {str(e)}'}), 500

@app.route('/generate-batch-reports', methods=['POST'])
def generate_batch_reports():
    """Start batch PDF generation for multiple trips"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '' or not (file.filename.endswith('.csv') or file.filename.endswith('.xlsx')):
        return jsonify({'error': 'Please select a valid CSV or Excel (.xlsx) file'}), 400
    
    # Get worksheet name for Excel files
    worksheet_name = request.form.get('worksheet_name', None)
    
    try:
        # Read file based on type
        if file.filename.endswith('.xlsx'):
            if worksheet_name:
                df = pd.read_excel(file, sheet_name=worksheet_name)
            else:
                # Default to first sheet if no worksheet specified
                df = pd.read_excel(file, sheet_name=0)
        else:
            # For CSV files
            df = pd.read_csv(file)
        
        # Check required columns
        required_columns = ['latitude', 'longitude', 'device_timestamp']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            return jsonify({
                'error': f'Missing required columns: {missing_columns}',
                'required_columns': required_columns,
                'found_columns': list(df.columns)
            }), 400
        
        # Generate unique batch ID
        batch_id = str(uuid.uuid4())
        
        # Start background processing
        thread = threading.Thread(target=generate_batch_pdfs, args=(batch_id, df))
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'message': 'Batch PDF generation started',
            'batch_id': batch_id
        })
        
    except Exception as e:
        return jsonify({'error': f'Error starting batch generation: {str(e)}'}), 500

@app.route('/batch-status/<batch_id>', methods=['GET'])
def get_batch_status(batch_id):
    """Get status of batch PDF generation"""
    if batch_id not in batch_jobs:
        return jsonify({'error': 'Batch job not found'}), 404
    
    job = batch_jobs[batch_id]
    
    # Calculate progress percentage
    progress = 0
    if job['total_trips'] > 0:
        progress = (job['completed_trips'] / job['total_trips']) * 100
    
    return jsonify({
        'status': job['status'],
        'progress': round(progress, 2),
        'total_trips': job['total_trips'],
        'completed_trips': job['completed_trips'],
        'pdfs': job['pdfs'],
        'error': job['error']
    })

@app.route('/download-pdf/<filename>', methods=['GET'])
def download_pdf(filename):
    """Download individual PDF file"""
    try:
        pdf_path = os.path.join(PDF_FOLDER, filename)
        
        if not os.path.exists(pdf_path):
            return jsonify({'error': 'PDF file not found'}), 404
        
        return send_file(
            pdf_path,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        return jsonify({'error': f'Error downloading PDF: {str(e)}'}), 500

@app.route('/list-worksheets', methods=['POST'])
def list_worksheets():
    """List all worksheets in an Excel file"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '' or not file.filename.endswith('.xlsx'):
        return jsonify({'error': 'Please select a valid Excel (.xlsx) file'}), 400
    
    try:
        # Get all sheet names
        excel_file = pd.ExcelFile(file)
        worksheets = excel_file.sheet_names
        
        return jsonify({
            'worksheets': worksheets,
            'message': f'Found {len(worksheets)} worksheets'
        })
        
    except Exception as e:
        return jsonify({'error': f'Error reading Excel file: {str(e)}'}), 500

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port) 