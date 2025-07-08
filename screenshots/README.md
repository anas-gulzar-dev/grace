# Grace Biosensor Data Capture - File Organization

This directory contains all captured data organized in a structured manner to prevent file conflicts and make data management easier.

## Directory Structure

```
screenshots/
├── images/                    # All screenshot images
│   ├── auto_captures/        # Images from auto-capture mode
│   └── manual_captures/      # Images from manual capture mode
├── json/                     # All JSON export files
│   ├── auto_capture_*.json   # JSON files from auto-capture
│   └── manual_captures/      # JSON files from manual captures
├── csv/                      # All CSV export files
│   ├── auto_data.csv         # Main CSV for auto-capture data
│   └── manual_captures/      # CSV files from manual captures
└── README.md                 # This file
```

## File Naming Convention

### Images
- **Auto-capture**: `auto_background_YYYYMMDD_HHMMSS_XXXX.png`
- **Manual capture**: `manual_background_YYYYMMDD_HHMMSS_XXXX.png`

### JSON Files
- **Auto-capture**: `auto_capture_YYYY-MM-DD_HH-MM-SS.json`
- **Manual capture**: `manual_capture_YYYY-MM-DD_HH-MM-SS.json`

### CSV Files
- **Auto-capture**: `auto_data.csv` (single file, appended)
- **Manual capture**: `manual_capture_YYYY-MM-DD_HH-MM-SS.csv`

## Data Management

### Auto-Capture Mode
- Images are stored in `images/auto_captures/`
- JSON files are stored in `json/` root directory
- CSV data is appended to `csv/auto_data.csv`
- Auto-deletion can be configured in the application

### Manual Capture Mode
- Images are stored in `images/manual_captures/`
- JSON files are stored in `json/manual_captures/`
- Each capture creates a new CSV file in `csv/manual_captures/`
- Screenshots are preserved by default (not auto-deleted)

## Cleanup Policy

The application includes an automatic cleanup feature that can be configured to:
1. Delete files older than a specified time (in minutes)
2. Keep only the last N files

This helps manage disk space while preserving important data.

## Tips for Data Management

1. **Regular Backups**: Consider backing up the `csv/` and `json/` directories regularly
2. **Archive Old Data**: Move old files to an archive directory periodically
3. **Monitor Disk Space**: The auto-cleanup feature helps, but monitor available space
4. **Export Important Data**: Use the export features to save important captures

## File Access

All files are saved with UTF-8 encoding and can be opened with:
- **Images**: Any image viewer
- **JSON**: Any text editor or JSON viewer
- **CSV**: Excel, Google Sheets, or any spreadsheet application
