# 🚀 Pathavana Startup Scripts

## Quick Start Commands

I've created comprehensive startup scripts that handle everything for you - **no need to manually activate virtual environments or navigate directories!**

### **🎯 Single Command to Start Backend**
```bash
/Users/jianphua/projects/pathavana/start_backend.sh
```

### **🎯 Single Command to Start Frontend**
```bash
/Users/jianphua/projects/pathavana/start_frontend.sh
```

### **🎯 Master Script (Interactive)**
```bash
/Users/jianphua/projects/pathavana/start_pathavana.sh
```

---

## 📋 What Each Script Does

### **`start_backend.sh`** 
✅ **Automatically activates virtual environment**  
✅ **Creates .env file if missing**  
✅ **Tests configuration loading**  
✅ **Attempts to install FastAPI if missing**  
✅ **Starts the backend server**  
✅ **Shows all access URLs**  

**What it handles:**
- Virtual environment activation
- Directory navigation  
- Dependency checking and installation
- Configuration validation
- Server startup with proper logging

### **`start_frontend.sh`**
✅ **Checks Node.js and npm**  
✅ **Creates .env file if missing**  
✅ **Installs npm dependencies if needed**  
✅ **Verifies React app structure**  
✅ **Checks backend connection**  
✅ **Starts React development server**  

**What it handles:**
- Node.js environment verification
- Dependency management
- Environment configuration
- Backend connectivity check
- Development server startup

### **`start_pathavana.sh`** (Master Script)
✅ **Interactive menu for service selection**  
✅ **Can start backend only, frontend only, or both**  
✅ **Opens multiple terminals on macOS**  
✅ **Provides clear instructions for manual setup**  

**Options:**
```bash
./start_pathavana.sh backend     # Backend only
./start_pathavana.sh frontend    # Frontend only  
./start_pathavana.sh both        # Both services
./start_pathavana.sh help        # Show help
./start_pathavana.sh             # Interactive mode
```

---

## 🌐 Access URLs (After Starting)

| Service | URL | Description |
|---------|-----|-------------|
| **Frontend** | http://localhost:3000 | React application |
| **Backend API** | http://localhost:8000 | REST API server |
| **API Docs** | http://localhost:8000/api/docs | Interactive API documentation |
| **Health Check** | http://localhost:8000/api/health | Service status |

---

## 🔧 What the Scripts Handle Automatically

### **Environment Setup**
- ✅ Virtual environment creation and activation
- ✅ Environment variable configuration
- ✅ Directory navigation and path management

### **Dependency Management**
- ✅ Python package installation (FastAPI, uvicorn, etc.)
- ✅ Node.js dependency installation
- ✅ Version compatibility checking

### **Configuration**
- ✅ .env file creation from templates
- ✅ Configuration validation and testing
- ✅ Error handling and fallback modes

### **Service Management**
- ✅ Server startup with proper logging
- ✅ Port availability checking
- ✅ Service connectivity verification
- ✅ Graceful error handling

---

## 🛟 Troubleshooting

### **If Backend Script Fails**
The script includes comprehensive error checking and will show exactly what went wrong:
- Virtual environment issues
- Configuration problems
- Missing dependencies
- Port conflicts

### **If Frontend Script Fails**
The script checks for:
- Node.js installation
- npm availability
- Package dependencies
- Backend connectivity

### **Common Solutions**
All scripts include automatic fixes for common issues:
- Missing virtual environment → Creates new one
- Missing .env file → Creates from template
- Missing dependencies → Attempts installation
- Configuration errors → Shows specific error messages

---

## 🎉 **Recommended Usage**

### **For Development (Most Common)**
```bash
# Option 1: Use the master script
/Users/jianphua/projects/pathavana/start_pathavana.sh both

# Option 2: Start manually in separate terminals
# Terminal 1:
/Users/jianphua/projects/pathavana/start_backend.sh

# Terminal 2:  
/Users/jianphua/projects/pathavana/start_frontend.sh
```

### **For Backend Development Only**
```bash
/Users/jianphua/projects/pathavana/start_backend.sh
```

### **For Frontend Development Only**
```bash
/Users/jianphua/projects/pathavana/start_frontend.sh
```

---

## ✅ **Success Indicators**

### **Backend Started Successfully**
```
🎉 Starting FastAPI Production Server
📍 Frontend: http://localhost:3000
📍 Backend API: http://localhost:8000
📍 API Documentation: http://localhost:8000/api/docs
📍 Health Check: http://localhost:8000/api/health
```

### **Frontend Started Successfully**  
```
🎉 Starting React Development Server
📍 Frontend Application: http://localhost:3000
📍 Backend API: http://localhost:8000
🔄 Hot reload enabled - changes will update automatically
```

---

**🚀 Just run the scripts and you're ready to develop!**