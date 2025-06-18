# WSL Development Environment Setup Guide

## Overview
This guide covers setting up a Python development environment on WSL (Windows Subsystem for Linux) for the OMI project, including handling Python version compatibility issues and dependency conflicts.

## Prerequisites
- WSL Ubuntu 24.04 installed
- Git configured with your GitHub credentials

## Initial Setup

### 1. Fork and Clone Repository
```bash
# Navigate to GitHub and fork the original repository
# Clone your fork (not the original)
git clone https://github.com/userXXX/omi.git
cd omi
```

### 2. Check Git Branch Status
```bash
# Check current branch
git branch

# Check all branches including remotes
git branch -a

# Verify you're working on your fork
git remote -v
```

## Environment Setup

### 3. Install System Dependencies
```bash
# Update system packages
sudo apt-get update

# Install build dependencies for Python packages
sudo apt-get install libopenblas-dev liblapack-dev gfortran cmake
sudo apt-get install build-essential python3-dev
sudo apt-get install portaudio19-dev python3-pyaudio

# Check available Python versions
python3.11 --version
```

### 4. Install uv (Fast Python Package Manager)
```bash
# Install uv - much faster than pip
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or alternative method
pip install uv
```

## Python Environment Configuration

### 5. Create Virtual Environment with Python 3.11
```bash
# Remove any existing environment
rm -rf .venv

# Create new environment with Python 3.11 using uv
uv venv --python 3.11

# Activate environment
source .venv/bin/activate

# Verify Python version
python --version
```

### 6. Fix Requirements Dependencies
```bash
# Copy and update requirements.txt to fix version conflicts
cp requirements.txt requirements_updated.txt

# Fix torch version compatibility
sed -i 's/torch==2.4.0/torch>=2.5.0/' requirements_updated.txt
sed -i 's/torchaudio==2.4.0/torchaudio>=2.6.0/' requirements_updated.txt
sed -i 's/torchvision==0.19.0/torchvision>=0.19.0/' requirements_updated.txt

# Fix proto-plus conflict for Python 3.13+ compatibility
sed -i 's/proto-plus==1.24.0/proto-plus>=1.25.0/' requirements_updated.txt
```

### 7. Install Dependencies
```bash
# Install all requirements (much faster with uv)
uv pip install -r requirements_updated.txt
```

## Common Issues and Solutions

### Python Version Compatibility
- **Problem**: numba doesn't support Python 3.13
- **Solution**: Use Python 3.11 or 3.12 instead

### PyTorch Version Conflicts
- **Problem**: requirements.txt specifies outdated torch versions
- **Solution**: Update to use `>=` instead of `==` for flexibility

### Proto-plus Dependency Conflicts
- **Problem**: Google Cloud packages need newer proto-plus versions
- **Solution**: Update proto-plus constraint to `>=1.25.0`

### Missing System Libraries
- **Problem**: scipy compilation fails without OpenBLAS
- **Solution**: Install system development packages first

## Git Workflow Setup

### 8. Configure Remote Repositories
```bash
# Add your fork as remote (if not already set)
git remote add fork https://github.com/userXXX/omi.git

# Add original repository as upstream
git remote add upstream https://github.com/BasedHardware/omi.git

# Verify remotes
git remote -v
```

### 9. Working with Branches
```bash
# Create feature branch
git checkout -b feature-branch-name

# Push to your fork
git push fork feature-branch-name

# Keep fork updated with upstream
git fetch upstream
git merge upstream/main
```

## Verification

### 10. Test Installation
```bash
# Activate environment
source .venv/bin/activate

# Check if ML dependencies are available
python -c "
try:
    import torch
    import pyaudio
    print('✅ ML dependencies available')
except ImportError as e:
    print(f'❌ Missing dependency: {e}')
"

# Run basic tests
python -m pytest --version
```

## Performance Notes

### CPU vs GPU Considerations
- **CPU Mode**: Most functionality works but ML operations are slower
- **Real-time features**: May struggle with latency on CPU
- **Speech processing**: Significantly slower without GPU
- **Development**: CPU is sufficient for coding and testing

### uv Benefits
- 10-100x faster package installation than pip
- Automatic Python version management
- Better dependency resolution
- Built-in virtual environment handling

## Environment Activation
```bash
# Always activate before working
source /home/userXXX/omi/.venv/bin/activate

# Or create an alias in ~/.bashrc
echo "alias omi-env='source /home/userXXX/omi/.venv/bin/activate'" >> ~/.bashrc
source ~/.bashrc
```

## Troubleshooting

### If packages fail to install:
1. Check Python version compatibility
2. Install missing system dependencies
3. Use conda for problematic packages
4. Skip ML dependencies for basic functionality

### If git push fails:
1. Ensure you're pushing to your fork, not upstream
2. Use `git push fork branch-name --force` if needed (carefully)
3. Keep fork relationship for easy upstream syncing

## Next Steps
1. Configure your IDE/editor to use the virtual environment
2. Set up pre-commit hooks for code quality
3. Review project documentation for development workflow
4. Test core functionality before making changes