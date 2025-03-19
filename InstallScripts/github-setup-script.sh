#!/bin/bash
# File: github-setup.sh
# Path: AIDEV-Hub/Scripts/github-setup.sh
# Standard: AIDEV-PascalCase-1.6
# Created: 2025-03-18
# Last Modified: 2025-03-18  2:30PM
# Description: Sets up the GitHub repository for AIDEV-Hub project

echo "Setting up AIDEV-Hub GitHub repository..."
echo "----------------------------------------"

# Check if GitHub CLI is installed
if ! command -v gh &> /dev/null; then
    echo "GitHub CLI not found. Installing..."
    # Check the OS and install gh accordingly
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # For Ubuntu/Debian
        sudo apt update
        sudo apt install gh -y
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        # For macOS
        brew install gh
    else
        echo "Your OS isn't directly supported by this script. Please install GitHub CLI manually:"
        echo "https://github.com/cli/cli#installation"
        exit 1
    fi
fi

# Check if logged in to GitHub
if ! gh auth status &> /dev/null; then
    echo "Please log in to GitHub:"
    gh auth login
fi

# Create README.md file
cat > ~/Desktop/AIDEV-Hub/README.md << 'EOF'
# AI Collaboration Hub (AIDEV-Hub)

A central hub for AI-assisted development that intelligently routes tasks between web-based AI services and local AI models, while maintaining session continuity and context.

## Project Vision

AI Collaboration Hub aims to create an integrated development environment that bridges multiple AI capabilities with human-directed development processes. The system optimizes the use of AI resources by intelligently routing tasks between web-based AI services and local AI models, while maintaining session continuity and context.

This tool serves as a central hub for AI-assisted development, allowing developers to leverage the right AI tool for each task while maintaining a coherent workflow and development history.

## Key Features

- **Intelligent Task Routing**: Automatically selects the best AI model for each task
- **Session Continuity**: Maintains context across sessions and recovers from crashes
- **Resource Optimization**: Reduces costs by using local models when appropriate
- **Seamless Integration**: Works with your existing development workflow
- **User Control**: Customize how tasks are routed to different AI models

## Project Status

This project is in early development. Contributions are welcome!

## Getting Started

See the [Setup Instructions](Docs/AI%20Collaboration%20Hub%20Setup%20Instructions.md) for details on installing and configuring the project.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

*"Code is not merely functional—it is a visual medium that developers interact with for extended periods. The choices made in these standards prioritize the axis of symmetry, character distinction, readability at scale, and visual hierarchy."*

— Herbert J. Bowers
EOF

# Create LICENSE file (MIT License)
cat > ~/Desktop/AIDEV-Hub/LICENSE << 'EOF'
MIT License

Copyright (c) 2025 Herbert J. Bowers

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
EOF

# Create .gitignore file
cat > ~/Desktop/AIDEV-Hub/.gitignore << 'EOF'
# Python virtual environment
.venv/
venv/
ENV/

# Python compiled files
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# State database files
State/AIDevHub.db-journal

# Session files that shouldn't be committed
Session/Temp/

# IDE specific files
.idea/
.vscode/
*.swp
*.swo

# OS specific files
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db
EOF

# Create a Python requirements.txt file 
cat > ~/Desktop/AIDEV-Hub/requirements.txt << 'EOF'
requests>=2.28.1
pysqlite3>=0.5.0
websockets>=10.4
EOF

# Initialize git repository if not already initialized
if [ ! -d ~/Desktop/AIDEV-Hub/.git ]; then
    cd ~/Desktop/AIDEV-Hub
    git init
    git add .
    git commit -m "Initial commit: Set up AIDEV-Hub project structure"
fi

# Create GitHub repository
echo "Creating GitHub repository 'AIDEV-Hub' under username 'CallMeChewy'..."
cd ~/Desktop/AIDEV-Hub
gh repo create CallMeChewy/AIDEV-Hub --public --source=. --push --description "A central hub for AI-assisted development that intelligently routes tasks between web-based and local AI services while maintaining session continuity."

echo ""
echo "GitHub repository setup completed successfully!"
echo "Repository URL: https://github.com/CallMeChewy/AIDEV-Hub"
echo ""
echo "AIDEV-Hub has been initialized with README.md, LICENSE, and initial project structure."
