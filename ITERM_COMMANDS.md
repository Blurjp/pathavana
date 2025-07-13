# 🚀 Pathavana iTerm Commands

## 🎯 **Best Option: iTerm with Separate Tabs**

### **Single Command to Start Both Services in iTerm Tabs:**
```bash
/Users/jianphua/projects/pathavana/start_both_iterm.sh
```

**What this does:**
- ✅ **Opens iTerm2** (or creates new window if already open)
- ✅ **Creates Tab 1**: "Pathavana Backend" - runs the backend server
- ✅ **Creates Tab 2**: "Pathavana Frontend" - waits 5 seconds, then runs frontend
- ✅ **Names the tabs** so you can easily identify them
- ✅ **Shows console output** from both services in real-time

---

## 🎛️ **Alternative Options**

### **Master Script with iTerm Option:**
```bash
# Interactive menu (choose option 3)
/Users/jianphua/projects/pathavana/start_pathavana.sh

# Direct iTerm command
/Users/jianphua/projects/pathavana/start_pathavana.sh iterm
```

### **Terminal App Alternative:**
```bash
# For regular Terminal app instead of iTerm
/Users/jianphua/projects/pathavana/start_both_terminal.sh

# Or via master script
/Users/jianphua/projects/pathavana/start_pathavana.sh terminal
```

### **Individual Services:**
```bash
# Backend only
/Users/jianphua/projects/pathavana/start_backend.sh

# Frontend only  
/Users/jianphua/projects/pathavana/start_frontend.sh
```

---

## 🖥️ **What You'll See in iTerm**

### **Tab 1: Pathavana Backend**
```
🚀 Pathavana Backend Starting...
================================
📁 Project directory: /Users/jianphua/projects/pathavana
📁 Backend directory: /Users/jianphua/projects/pathavana/backend
🔧 Activating virtual environment...
✅ Configuration loaded: Pathavana Travel Planning API
🎉 Starting FastAPI Production Server
📍 Backend API: http://localhost:8000
📍 API Documentation: http://localhost:8000/api/docs
```

### **Tab 2: Pathavana Frontend**
```
🚀 Pathavana Frontend Starting...
=================================
📁 Frontend directory: /Users/jianphua/projects/pathavana/frontend
✅ Node.js version: v20.19.2
✅ npm version: 10.8.2
🎉 Starting React Development Server
📍 Frontend Application: http://localhost:3000
```

---

## 🔄 **Console Output Benefits**

### **Backend Tab Shows:**
- ✅ **API requests** in real-time
- ✅ **Database operations** and queries
- ✅ **Error messages** and stack traces
- ✅ **Service startup** progress
- ✅ **Configuration loading** status

### **Frontend Tab Shows:**
- ✅ **React compilation** progress
- ✅ **Hot reload** notifications
- ✅ **TypeScript errors** and warnings
- ✅ **Build status** and bundle info
- ✅ **Development server** logs

---

## 💡 **iTerm Tips**

### **Navigation:**
- **Switch tabs**: `Cmd + 1` (backend), `Cmd + 2` (frontend)
- **New tab**: `Cmd + T`
- **Close tab**: `Cmd + W`
- **Split pane**: `Cmd + D` (horizontal), `Cmd + Shift + D` (vertical)

### **Monitoring:**
- **Stop service**: `Ctrl + C` in the respective tab
- **Restart service**: Re-run the startup script in that tab
- **View logs**: Scroll up in the tab to see previous output

### **Useful Commands in Each Tab:**
```bash
# In backend tab (after stopping with Ctrl+C):
./start_backend.sh                    # Restart backend
curl http://localhost:8000/api/health # Test backend

# In frontend tab (after stopping with Ctrl+C):
./start_frontend.sh                   # Restart frontend
npm test                             # Run tests
npm run build                        # Create production build
```

---

## 🌐 **Access URLs**

Once both services are running in iTerm tabs:

| Service | URL | Description |
|---------|-----|-------------|
| **Frontend** | http://localhost:3000 | Main React application |
| **Backend API** | http://localhost:8000 | REST API server |
| **API Documentation** | http://localhost:8000/api/docs | Interactive Swagger docs |
| **Health Check** | http://localhost:8000/api/health | Service status |
| **API Info** | http://localhost:8000/api/info | Application information |

---

## 🎉 **Recommended Workflow**

1. **Start both services**: `/Users/jianphua/projects/pathavana/start_both_iterm.sh`
2. **Wait for startup**: Both tabs will show when services are ready
3. **Open browser**: Navigate to http://localhost:3000
4. **Monitor logs**: Switch between tabs to see real-time console output
5. **Develop**: Make changes and see hot reload in frontend tab
6. **API testing**: Check backend tab for API request logs
7. **Stop services**: `Ctrl + C` in each tab when done

**Perfect for development - you get full visibility into both services! 🚀**