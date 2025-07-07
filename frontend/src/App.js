import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

function App() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploadStatus, setUploadStatus] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [batchId, setBatchId] = useState(null);
  const [batchStatus, setBatchStatus] = useState(null);
  const [progress, setProgress] = useState(0);
  const [completedPdfs, setCompletedPdfs] = useState([]);
  const [worksheets, setWorksheets] = useState([]);
  const [selectedWorksheet, setSelectedWorksheet] = useState('');
  const [showWorksheetSelection, setShowWorksheetSelection] = useState(false);

  const handleFileSelect = async (event) => {
    const file = event.target.files[0];
    if (file) {
      setSelectedFile(file);
      setUploadStatus('');
      setError('');
      setBatchId(null);
      setBatchStatus(null);
      setProgress(0);
      setCompletedPdfs([]);
      setWorksheets([]);
      setSelectedWorksheet('');
      setShowWorksheetSelection(false);

      // If it's an Excel file, get worksheets
      if (file.name.endsWith('.xlsx')) {
        try {
          setLoading(true);
          const formData = new FormData();
          formData.append('file', file);

          const response = await axios.post('/list-worksheets', formData, {
            headers: {
              'Content-Type': 'multipart/form-data',
            },
          });

          setWorksheets(response.data.worksheets);
          setShowWorksheetSelection(true);
          setSelectedWorksheet(response.data.worksheets[0]); // Default to first worksheet
          setLoading(false);
        } catch (err) {
          setError(err.response?.data?.error || 'Error reading Excel file');
          setLoading(false);
        }
      }
    }
  };

  const handleFileUpload = async () => {
    if (!selectedFile) {
      setError('Please select a CSV or Excel file first');
      return;
    }

    if (selectedFile.name.endsWith('.xlsx') && !selectedWorksheet) {
      setError('Please select a worksheet');
      return;
    }

    setLoading(true);
    setError('');

    const formData = new FormData();
    formData.append('file', selectedFile);
    
    // Add worksheet name for Excel files
    if (selectedFile.name.endsWith('.xlsx') && selectedWorksheet) {
      formData.append('worksheet_name', selectedWorksheet);
    }

    try {
      const response = await axios.post('/generate-batch-reports', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      setBatchId(response.data.batch_id);
      setUploadStatus(response.data.message);
      
    } catch (err) {
      setError(err.response?.data?.error || 'Error uploading file');
      setLoading(false);
    }
  };

  const handleDownloadReport = async (filename) => {
    try {
      const response = await axios.get(`/download-pdf/${filename}`, {
        responseType: 'blob',
      });

      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);

    } catch (err) {
      setError(err.response?.data?.error || 'Error downloading PDF');
    }
  };

  // Poll batch status when batch processing starts
  useEffect(() => {
    let interval;
    
    if (batchId && batchStatus !== 'completed' && batchStatus !== 'error') {
      interval = setInterval(async () => {
        try {
          const response = await axios.get(`/batch-status/${batchId}`);
          const data = response.data;
          
          setBatchStatus(data.status);
          setProgress(data.progress);
          setCompletedPdfs(data.pdfs);
          
          if (data.status === 'completed') {
            setLoading(false);
            setUploadStatus('All PDF reports generated successfully!');
          } else if (data.status === 'error') {
            setLoading(false);
            setError(data.error || 'Error generating reports');
          }
          
        } catch (err) {
          setError('Error checking batch status');
          setLoading(false);
        }
      }, 1000); // Poll every second
    }
    
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [batchId, batchStatus]);

  return (
    <div className="App">
      <header className="App-header">
        <h1>Trip Analytics Tool</h1>
        <p>Upload your CSV file with trip data to generate detailed analytics reports</p>
      </header>

      <main className="App-main">
        <div className="upload-section">
          <h2>Upload Trip Data</h2>
          <p className="requirements">
            <strong>Supported files:</strong> CSV (.csv) or Excel (.xlsx)<br/>
            <strong>Required columns:</strong> latitude, longitude, device_timestamp
          </p>
          
          <div className="file-input-container">
            <input
              type="file"
              accept=".csv,.xlsx"
              onChange={handleFileSelect}
              className="file-input"
              id="file-upload"
            />
            <label htmlFor="file-upload" className="file-label">
              {selectedFile ? selectedFile.name : 'Choose CSV or Excel File'}
            </label>
          </div>

          {showWorksheetSelection && (
            <div className="worksheet-selection">
              <h3>Select Worksheet</h3>
              <select
                value={selectedWorksheet}
                onChange={(e) => setSelectedWorksheet(e.target.value)}
              >
                {worksheets.map((worksheet, index) => (
                  <option key={index} value={worksheet}>{worksheet}</option>
                ))}
              </select>
            </div>
          )}

          <button 
            onClick={handleFileUpload}
            disabled={!selectedFile || loading}
            className="upload-button"
          >
            {loading ? 'Processing...' : 'Generate Reports'}
          </button>
        </div>

        {error && (
          <div className="error-message">
            <strong>Error:</strong> {error}
          </div>
        )}

        {uploadStatus && (
          <div className="success-message">
            <strong>Success:</strong> {uploadStatus}
          </div>
        )}

        {batchId && (
          <div className="processing-section">
            <h2>Processing Trip Reports</h2>
            
            {loading && (
              <div className="progress-container">
                <div className="progress-bar">
                  <div 
                    className="progress-fill" 
                    style={{ width: `${progress}%` }}
                  ></div>
                </div>
                <p className="progress-text">
                  {progress.toFixed(1)}% Complete
                  {batchStatus === 'processing' && ` (${completedPdfs.length} reports generated)`}
                </p>
              </div>
            )}
            
            {completedPdfs.length > 0 && (
              <div className="completed-reports">
                <h3>Generated Reports ({completedPdfs.length})</h3>
                <div className="reports-grid">
                  {completedPdfs.map((report, index) => (
                    <div key={index} className="report-card">
                      <h3>Trip ID: {report.trip_id}</h3>
                      <div className="report-stats">
                        <p><strong>Ping Count:</strong> {report.ping_count}</p>
                        <p><strong>Total Distance:</strong> {report.total_distance.toFixed(2)} KM</p>
                        <p><strong>Average Speed:</strong> {report.avg_speed.toFixed(2)} KM/Hr</p>
                      </div>
                      <button 
                        onClick={() => handleDownloadReport(report.filename)}
                        className="download-button"
                      >
                        Download PDF Report
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}

export default App; 