# DEPRECATED: This configuration template is no longer used
# The application now uses .env files for configuration
#
# =============================================================================
# MIGRATION NOTICE
# =============================================================================
# This file is kept for reference only. The application now uses environment
# variables loaded from a .env file for better security and flexibility.
#
# To configure the application:
# 1. Copy .env.example to .env
# 2. Edit .env with your actual values
# 3. Run the application - it will automatically load your configuration
#
# =============================================================================
# ENVIRONMENT VARIABLES REFERENCE
# =============================================================================
# The following environment variables are supported in your .env file:
#
# # Azure Computer Vision API
# AZURE_API_KEY=your_actual_api_key_here
# AZURE_ENDPOINT=https://your-resource-name.cognitiveservices.azure.com/
#
# # Application Settings
# DEFAULT_CAPTURE_INTERVAL=60
# SCREENSHOTS_FOLDER=screenshots
#
# # OCR Settings
# OCR_LANGUAGE=en
# DETECT_ORIENTATION=true
#
# # Window Detection
# SCRCPY_WINDOW_TITLES=scrcpy,Mi Band,Android,Xiaomi
#
# =============================================================================
# SETUP INSTRUCTIONS
# =============================================================================
# 1. Copy .env.example to .env:
#    copy .env.example .env
#
# 2. Edit .env file with your actual Azure credentials
#
# 3. Run the application:
#    python main.py
#
# For help getting Azure credentials:
# https://docs.microsoft.com/en-us/azure/cognitive-services/computer-vision/