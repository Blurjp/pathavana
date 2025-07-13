# Pathavana Production Setup Guide

## 🚀 Quick Start Commands

### **Step 1: Activate Virtual Environment**
```bash
cd /Users/jianphua/projects/pathavana/backend
source venv/bin/activate
```

### **Step 2: Start Backend Service**
```bash
# Option A: Use the production startup script (recommended)
./start_production.sh

# Option B: Manual start
python3 app/main_production.py
```

### **Step 3: Start Frontend Service** (in new terminal)
```bash
cd /Users/jianphua/projects/pathavana/frontend
./start_frontend.sh

# Or manually:
npm start
```

## 🌐 Access URLs

Once both services are running:
- **Frontend Application**: http://localhost:3000
- **Backend API Documentation**: http://localhost:8000/api/docs
- **Backend Health Check**: http://localhost:8000/api/health
- **Backend API Info**: http://localhost:8000/api/info

## 🔧 Environment Configuration

### **Backend Environment (.env)**
Location: `/Users/jianphua/projects/pathavana/backend/.env`

Contains your actual configuration:
- ✅ Azure OpenAI API credentials
- ✅ Amadeus API credentials (test environment)
- ✅ Google OAuth client ID
- ✅ Database configuration (SQLite for development)
- ✅ CORS settings for frontend communication

### **Frontend Environment (.env)**
Location: `/Users/jianphua/projects/pathavana/frontend/.env`

Contains:
- Backend API URL: `http://localhost:8000`
- Google OAuth client ID
- Development environment flags

## 📦 Dependency Management

### **Backend Dependencies**
The startup script automatically handles dependencies:

1. **Production Mode**: If FastAPI and uvicorn are available
   - Full functionality with all features
   - Interactive API documentation
   - Production-ready server

2. **Fallback Mode**: If dependencies are missing
   - Basic HTTP server with same endpoints
   - Graceful degradation
   - Still functional for development

### **Frontend Dependencies**
- ✅ React 18 with TypeScript
- ✅ All required packages already installed
- ✅ Production-ready build system

## 🏗️ Architecture Features

### **Backend Capabilities**
- ✅ **FastAPI** application with automatic OpenAPI documentation
- ✅ **SQLAlchemy** database models with unified session architecture
- ✅ **Configuration management** with .env file loading
- ✅ **CORS middleware** for frontend communication
- ✅ **Error handling** and graceful degradation
- ✅ **Health checks** and monitoring endpoints

### **Frontend Capabilities**
- ✅ **React 18** with TypeScript
- ✅ **Real-time chat interface** components
- ✅ **Session management** with UUID-based routing
- ✅ **Travel components** (flights, hotels, activities)
- ✅ **Google Maps integration** ready
- ✅ **Responsive design** for all devices

## 🔄 Development Workflow

### **Backend Development**
```bash
# Activate environment
cd backend
source venv/bin/activate

# Start development server
./start_production.sh

# The server will auto-reload on file changes if FastAPI is available
```

### **Frontend Development**
```bash
# Start development server
cd frontend
./start_frontend.sh

# Hot reload enabled - changes reflect immediately
```

### **Database Operations**
```bash
# From backend directory with venv activated
cd backend
source venv/bin/activate

# Run database migrations (when ready)
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "Description"
```

## 🧪 Testing the Setup

### **Backend Health Check**
```bash
curl http://localhost:8000/api/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "pathavana-backend",
  "version": "1.0.0"
}
```

### **Frontend Verification**
1. Open http://localhost:3000
2. Should see the Pathavana React application
3. Check browser console for any errors

### **API Integration Test**
```bash
curl -X POST http://localhost:8000/api/travel/sessions \\
  -H "Content-Type: application/json" \\
  -d '{"message": "I want to visit Paris"}'
```

## 🚨 Troubleshooting

### **Backend Issues**

1. **Virtual environment not found**:
   ```bash
   cd backend
   python3 -m venv venv
   source venv/bin/activate
   ```

2. **Configuration errors**:
   - Check that `.env` file exists in backend directory
   - Verify all required environment variables are set

3. **Import errors**:
   - The system gracefully falls back to basic HTTP server
   - Check console output for specific error messages

### **Frontend Issues**

1. **npm errors**:
   ```bash
   cd frontend
   rm -rf node_modules package-lock.json
   npm install
   ```

2. **Port conflicts**:
   - Backend uses port 8000
   - Frontend uses port 3000
   - Make sure these ports are free

### **Network Issues**

If you can't install Python packages due to network restrictions:
- The backend will run in fallback mode
- All endpoints will work with demo responses
- Structure and configuration are fully functional

## 🔐 Security Notes

### **Development Mode**
- CORS is configured for localhost origins
- Debug mode enabled for development
- SQLite database for local development

### **Production Deployment**
- Update CORS origins for production domains
- Use PostgreSQL for production database
- Set DEBUG=False in production
- Use proper secret keys and API credentials

## 🎯 Next Steps

### **Immediate Development**
1. ✅ Backend server running
2. ✅ Frontend application running
3. ✅ API communication working
4. Start implementing specific features

### **Production Deployment**
1. Install production dependencies
2. Configure PostgreSQL database
3. Set up proper environment variables
4. Deploy using Docker/Kubernetes configurations

### **Feature Development**
1. Implement AI agent functionality (requires OpenAI API)
2. Add external API integrations (Amadeus, Google Maps)
3. Implement authentication flows
4. Add real-time features

---

## ✅ Success Checklist

After running the setup commands, verify:

- [ ] Backend server starts without errors
- [ ] Frontend application loads at http://localhost:3000
- [ ] API health check returns success
- [ ] No CORS errors in browser console
- [ ] Environment variables loaded correctly
- [ ] Database connection working (SQLite)

**🎉 You're ready for development!**