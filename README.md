# Trip Analytics Tool

A web application for generating detailed trip analytics reports from GPS tracking data.

## Features

- Upload CSV files with GPS tracking data
- Calculate distances using Haversine formula
- Generate professional PDF reports
- Support for multiple trips in a single file
- **Batch processing with progress tracking**
- **Individual PDF downloads as reports are generated**
- Clean, minimal interface

## Requirements

### CSV File Format

Your CSV file must contain these columns:
- `latitude` - GPS latitude coordinates
- `longitude` - GPS longitude coordinates  
- `device_timestamp` - Timestamp in format `DD/MM/YY HH:MM` or `MM/DD/YY HH:MM`

Optional columns:
- `trip_id` - Groups data by trip (if missing, treats all data as one trip)

## Setup Instructions

### Backend Setup

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Make sure the Freight Tiger logo file is in the root directory:
   - `Freight Tiger Logo.webp`

3. Run the Flask backend:
```bash
python app.py
```

The backend will run on `http://localhost:5000`

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install Node.js dependencies:
```bash
npm install
```

3. Start the React development server:
```bash
npm start
```

The frontend will run on `http://localhost:3000`

## Usage

1. Open your browser and go to `http://localhost:3000`
2. Click "Choose CSV File" and select your trip data file
3. Click "Generate Reports" to start batch processing
4. Watch the progress bar as reports are generated one by one
5. Download individual PDF reports as they become available
6. PDF reports will be automatically downloaded to your browser's download folder

### Batch Processing

- **Multiple trips**: If your CSV contains multiple trip_id values, each trip will be processed separately
- **Progress tracking**: Real-time progress bar shows completion percentage
- **Individual downloads**: Download each PDF report as soon as it's generated
- **No waiting**: You don't have to wait for all reports to complete before downloading

## Report Contents

Each PDF report includes:
- Trip metadata (ID, dates, vehicle info)
- Summary statistics (distance, duration, average speed)
- Detailed ping-by-ping analysis table
- Professional formatting with Freight Tiger branding

## Supported Data Formats

- CSV files only
- Timestamps in DD/MM/YY HH:MM or MM/DD/YY HH:MM format
- Latitude/longitude in decimal degrees
- Multiple trips can be included in one file (using trip_id column)

## Technical Details

- **Backend**: Python Flask with pandas for data processing
- **Frontend**: React.js with axios for API calls
- **PDF Generation**: ReportLab library
- **Distance Calculation**: Haversine formula for accurate GPS distances
- **CORS**: Enabled for local development

## File Structure

```
trip-analyser/
├── app.py                 # Flask backend
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── Freight Tiger Logo.webp # Logo for PDF reports
├── frontend/
│   ├── package.json      # React dependencies
│   ├── public/
│   │   └── index.html    # HTML template
│   └── src/
│       ├── App.js        # Main React component
│       ├── App.css       # Styling
│       ├── index.js      # React entry point
│       └── index.css     # Global styles
└── Sample Trip Data _ Trip Tracker - Sheet1.csv # Example data
``` 