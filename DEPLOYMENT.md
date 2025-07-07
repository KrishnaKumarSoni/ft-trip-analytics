# Render Deployment Guide

## Prerequisites
- GitHub account with the ft-trip-analytics repository
- Render account (free tier available)

## Deployment Steps

### 1. Create Render Account
1. Go to [render.com](https://render.com) and sign up
2. Connect your GitHub account

### 2. Deploy the Application
1. Click "New" -> "Web Service"
2. Select "Connect a repository"
3. Choose your GitHub account and select `ft-trip-analytics`
4. Configure the deployment:
   - **Name**: `ft-trip-analytics` (or your preferred name)
   - **Environment**: `Python`
   - **Build Command**: `./build.sh`
   - **Start Command**: `python app.py`
   - **Plan**: `Free` (or upgrade as needed)

### 3. Environment Configuration
The app will automatically detect the PORT environment variable from Render.

### 4. Deploy
1. Click "Create Web Service"
2. Render will automatically build and deploy your application
3. The build process will:
   - Install Python dependencies
   - Build React frontend
   - Start the Flask server

### 5. Access Your Application
- Your app will be available at: `https://your-app-name.onrender.com`
- The React frontend will be served at the root URL
- API endpoints will be available at `/upload`, `/generate-batch-reports`, etc.

## Features Available After Deployment

✅ **Full Stack Application**: React frontend + Flask backend
✅ **File Upload**: CSV and Excel file support
✅ **Batch Processing**: Background PDF generation
✅ **Progress Tracking**: Real-time progress updates
✅ **PDF Downloads**: Individual PDF downloads
✅ **Temporary Storage**: PDFs stored temporarily (auto-cleanup after 1 hour)

**Note**: On Render's free tier, PDFs are stored temporarily and automatically cleaned up after 1 hour. Download your files promptly after generation.

## Troubleshooting

### Build Issues
- Check the build logs in Render dashboard
- Ensure all dependencies are listed in `requirements.txt`
- Verify `build.sh` script has execute permissions

### Runtime Issues
- Check the runtime logs in Render dashboard
- Monitor memory usage (free tier has 512MB limit)
- Verify disk storage is properly mounted

### Performance
- Free tier has limitations: 
  - 512MB RAM
  - CPU throttling after 750 hours/month
  - Temporary storage only (files auto-deleted after 1 hour)
- Consider upgrading to paid plans for production use with persistent storage

## Monitoring
- Access logs and metrics in Render dashboard
- Set up alerts for downtime or errors
- Monitor memory usage and processing times

## Updates
To update the application:
1. Push changes to GitHub
2. Render will automatically redeploy
3. Or manually trigger deployment from dashboard 