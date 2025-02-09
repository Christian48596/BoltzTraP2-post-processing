#!/bin/bash

# ----------------------------------------
# install.sh
# This script sets up the environment for the BTP2-extract Python script.
# It checks for Python, pip, necessary Python packages, and PyInstaller.
# If any are missing, it prompts the user to install them.
# Finally, it uses PyInstaller to create an executable of the Python script.
# It also provides instructions to add the executable to the system PATH.
# ----------------------------------------

# Define color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Function to print messages in different colors
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_prompt() {
    echo -e "${CYAN}$1${NC}"
}

# Function to prompt user for yes/no and return 0 for yes, 1 for no
ask_install() {
    while true; do
        read -p "$(echo -e "${CYAN}$1 [y/n]: ${NC}")" yn
        case $yn in
            [Yy]* ) return 0 ;;
            [Nn]* ) return 1 ;;
            * ) print_warning "Please answer yes or no." ;;
        esac
    done
}

# Function to determine the package manager (for installing Python if needed)
get_package_manager() {
    if command -v apt-get &>/dev/null; then
        echo "apt-get"
    elif command -v brew &>/dev/null; then
        echo "brew"
    else
        echo "unknown"
    fi
}

# -------------------------------
# 1. Check for Python Installation
# -------------------------------
print_info "Checking for Python installation..."
if command -v python3 &>/dev/null; then
    print_success "Python3 is already installed."
    PYTHON_CMD=python3
elif command -v python &>/dev/null; then
    print_success "Python is already installed."
    PYTHON_CMD=python
else
    print_warning "Python is not installed."
    if ask_install "Do you want to install Python?"; then
        PM=$(get_package_manager)
        if [ "$PM" == "apt-get" ]; then
            print_info "Updating package list..."
            sudo apt-get update
            print_info "Installing Python3..."
            sudo apt-get install -y python3
            if command -v python3 &>/dev/null; then
                PYTHON_CMD=python3
                print_success "Python3 installed successfully."
            else
                print_error "Python installation failed."
                exit 1
            fi
        elif [ "$PM" == "brew" ]; then
            print_info "Installing Python using Homebrew..."
            brew install python
            if command -v python3 &>/dev/null; then
                PYTHON_CMD=python3
                print_success "Python installed successfully via Homebrew."
            else
                print_error "Python installation failed via Homebrew."
                exit 1
            fi
        else
            print_error "Unsupported package manager. Please install Python manually."
            exit 1
        fi
    else
        print_error "Python is required. Please install Python before continuing."
        exit 1
    fi
fi

echo -e "${YELLOW}----------------------------------------${NC}"

# -------------------------------
# 2. Check for pip Installation Using the Python Interpreter
# -------------------------------
# Use the pip module from the detected Python interpreter.
PIP_CMD="$PYTHON_CMD -m pip"

print_info "Checking for pip installation..."
$PIP_CMD --version &>/dev/null
if [ $? -eq 0 ]; then
    print_success "pip is available."
else
    print_warning "pip is not installed."
    if ask_install "Do you want to install pip?"; then
        print_info "Downloading get-pip.py..."
        curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
        if [ $? -ne 0 ]; then
            print_error "Failed to download get-pip.py."
            exit 1
        fi
        print_info "Installing pip..."
        $PYTHON_CMD get-pip.py
        if [ $? -ne 0 ]; then
            print_error "pip installation failed."
            rm get-pip.py
            exit 1
        fi
        rm get-pip.py
        print_success "pip installed successfully."
    else
        print_error "pip is required. Please install pip before continuing."
        exit 1
    fi
fi

echo -e "${YELLOW}----------------------------------------${NC}"

# -------------------------------
# 2.1 Detect Conda Environment & Set Extra Pip Flags
# -------------------------------
if [ -n "$CONDA_DEFAULT_ENV" ]; then
    print_info "Conda environment detected: $CONDA_DEFAULT_ENV"
    # When in a Conda (or other externally managed) environment, pip may refuse
    # to install packages unless overridden. The flag below will allow installations.
    PIP_EXTRA="--break-system-packages"
else
    PIP_EXTRA=""
fi

# -------------------------------
# 3. Upgrade pip (Skip in Conda)
# -------------------------------
if [ -n "$CONDA_DEFAULT_ENV" ]; then
    print_warning "Conda environment detected. Skipping pip upgrade to avoid externally-managed-environment issues."
else
    print_info "Upgrading pip..."
    $PIP_CMD install --upgrade pip $PIP_EXTRA
    if [ $? -eq 0 ]; then
        print_success "pip upgraded successfully."
    else
        print_warning "pip upgrade failed. Continuing with existing pip version."
    fi
fi

echo -e "${YELLOW}----------------------------------------${NC}"

# -------------------------------
# 4. Check and Install Required Python Packages
# -------------------------------
REQUIRED_PACKAGES=(pandas matplotlib seaborn numpy)

# Function to check installed packages using pip
check_installed_packages() {
    MISSING=()
    for pkg in "${REQUIRED_PACKAGES[@]}"; do
        $PIP_CMD show "$pkg" &>/dev/null
        if [ $? -ne 0 ]; then
            MISSING+=("$pkg")
        fi
    done
    echo "${MISSING[@]}"
}

print_info "Checking for required Python packages: ${REQUIRED_PACKAGES[*]}..."
MISSING_PACKAGES=$(check_installed_packages)

if [ -n "$MISSING_PACKAGES" ]; then
    print_warning "The following packages are missing: $MISSING_PACKAGES"
    if ask_install "Do you want to install the missing packages?"; then
        print_info "Installing missing packages..."
        $PIP_CMD install $PIP_EXTRA $MISSING_PACKAGES
        if [ $? -eq 0 ]; then
            print_success "Missing packages installed successfully."
        else
            print_error "Failed to install some packages. Please check the errors above."
            exit 1
        fi
    else
        print_error "Cannot proceed without installing the required Python packages."
        exit 1
    fi
else
    print_success "All required Python packages are already installed."
fi

echo -e "${YELLOW}----------------------------------------${NC}"

# -------------------------------
# 5. Check and Install PyInstaller
# -------------------------------
print_info "Checking for PyInstaller installation..."
$PIP_CMD show pyinstaller &>/dev/null
if [ $? -ne 0 ]; then
    print_warning "PyInstaller is not installed."
    if ask_install "Do you want to install PyInstaller?"; then
        print_info "Installing PyInstaller..."
        $PIP_CMD install $PIP_EXTRA pyinstaller
        if [ $? -eq 0 ]; then
            print_success "PyInstaller installed successfully."
        else
            print_error "PyInstaller installation failed."
            exit 1
        fi
    else
        print_error "PyInstaller is required to create the executable. Please install it before continuing."
        exit 1
    fi
else
    print_success "PyInstaller is already installed."
fi

echo -e "${YELLOW}----------------------------------------${NC}"

# -------------------------------
# 6. Build the Executable Using PyInstaller
# -------------------------------
# Define the Python script to be packaged
SCRIPT_NAME="BTP2-extract.py"

print_info "Checking for the Python script '$SCRIPT_NAME'..."
if [ ! -f "$SCRIPT_NAME" ]; then
    print_error "The script '$SCRIPT_NAME' was not found in the current directory."
    exit 1
else
    print_success "Found the script '$SCRIPT_NAME'."
fi

print_info "Creating executable with PyInstaller..."
$PYTHON_CMD -m PyInstaller --onefile "$SCRIPT_NAME"
if [ $? -eq 0 ]; then
    print_success "Executable created successfully."
    print_info "You can find the executable in the 'dist' directory."
else
    print_error "There was an error creating the executable."
    exit 1
fi

echo -e "${YELLOW}----------------------------------------${NC}"

# -------------------------------
# 7. Provide PATH Update Instructions
# -------------------------------
EXECUTABLE_NAME=$(basename "$SCRIPT_NAME" .py)
EXECUTABLE_PATH="$(pwd)/dist/$EXECUTABLE_NAME"

if [ ! -f "$EXECUTABLE_PATH" ]; then
    print_error "Executable '$EXECUTABLE_PATH' not found."
    exit 1
fi

print_success "Executable is located at: $EXECUTABLE_PATH"

DIST_DIR="$(pwd)/dist"
print_info "To run the executable from anywhere, add the 'dist' directory to your system PATH."
print_info "Add the following line to your shell configuration file (.bashrc or .zshrc):"
echo ""
echo -e "${CYAN}export PATH=\"\$PATH:$DIST_DIR\"${NC}"
echo ""
print_info "Or add it automatically using:"
echo ""
echo -e "${CYAN}echo 'export PATH=\"\$PATH:$DIST_DIR\"' >> ~/.bashrc${NC}"
echo -e "${CYAN}# or for Zsh users:${NC}"
echo -e "${CYAN}echo 'export PATH=\"\$PATH:$DIST_DIR\"' >> ~/.zshrc${NC}"
echo ""
print_info "Then reload your shell configuration with:"
echo -e "${CYAN}source ~/.bashrc${NC}  or  ${CYAN}source ~/.zshrc${NC}"
echo ""
print_success "Installation and packaging complete. You can now run the executable from anywhere on your system."

echo -e "${YELLOW}----------------------------------------${NC}"