#!/bin/bash
# Linux Installation Script for Biosensor Data Capture Tool
# Handles virtual environment and externally-managed-environment issues

echo "🐧 Installing Linux dependencies for Biosensor Data Capture Tool..."
echo "================================================"

# Install system packages
echo "📦 Installing system packages..."
sudo apt install python3-tk xdotool wmctrl scrot python3-full python3-venv

if [ $? -eq 0 ]; then
    echo "✅ System packages installed successfully"
else
    echo "❌ Failed to install system packages"
    echo "Please run manually: sudo apt install python3-tk xdotool wmctrl scrot python3-full python3-venv"
    exit 1
fi

# Function to check if we're in a virtual environment
check_virtual_env() {
    if [[ "$VIRTUAL_ENV" != "" ]]; then
        return 0  # In virtual environment
    else
        return 1  # Not in virtual environment
    fi
}

# Function to install with virtual environment
install_with_venv() {
    echo "🔧 Creating virtual environment..."
    python3 -m venv grace_env
    
    if [ $? -eq 0 ]; then
        echo "✅ Virtual environment created successfully"
        echo "🐍 Activating virtual environment and installing packages..."
        source grace_env/bin/activate
        pip install -r linux_requirements.txt
        
        if [ $? -eq 0 ]; then
            echo "✅ Python packages installed successfully in virtual environment"
            echo "🎉 Installation complete!"
            echo ""
            echo "📋 To run the application:"
            echo "   1. Activate virtual environment: source grace_env/bin/activate"
            echo "   2. Run application: python main.py"
            echo "   3. Deactivate when done: deactivate"
            return 0
        else
            echo "❌ Failed to install Python packages in virtual environment"
            return 1
        fi
    else
        echo "❌ Failed to create virtual environment"
        return 1
    fi
}

# Function to install system-wide (with --break-system-packages)
install_system_wide() {
    echo "⚠️  Installing system-wide (not recommended)..."
    pip install -r linux_requirements.txt --break-system-packages
    
    if [ $? -eq 0 ]; then
        echo "✅ Python packages installed system-wide"
        echo "🎉 Installation complete! You can now run: python main.py"
        return 0
    else
        echo "❌ Failed to install Python packages system-wide"
        return 1
    fi
}

# Check virtual environment status and install accordingly
echo "🔍 Checking Python environment..."

if check_virtual_env; then
    echo "✅ Virtual environment detected: $VIRTUAL_ENV"
    echo "🐍 Installing Python packages in virtual environment..."
    pip install -r linux_requirements.txt
    
    if [ $? -eq 0 ]; then
        echo "✅ Python packages installed successfully"
        echo "🎉 Installation complete! You can now run: python main.py"
    else
        echo "❌ Failed to install Python packages in virtual environment"
        exit 1
    fi
else
    echo "⚠️  No virtual environment detected"
    echo "🔒 Modern Linux systems use externally-managed environments"
    echo ""
    echo "📋 Choose installation method:"
    echo "   1. 🌟 RECOMMENDED: Create virtual environment (safer)"
    echo "   2. ⚠️  Install system-wide (may break system packages)"
    echo ""
    read -p "Enter your choice (1 or 2): " choice
    
    case $choice in
        1)
            install_with_venv
            ;;
        2)
            echo "⚠️  WARNING: Installing system-wide may interfere with system packages!"
            read -p "Are you sure? (y/N): " confirm
            if [[ $confirm =~ ^[Yy]$ ]]; then
                install_system_wide
            else
                echo "❌ Installation cancelled"
                echo "💡 Tip: Use option 1 (virtual environment) for safer installation"
                exit 1
            fi
            ;;
        *)
            echo "❌ Invalid choice. Please run the script again and choose 1 or 2"
            exit 1
            ;;
    esac
fi

echo "================================================"
echo "🚀 Installation complete!"