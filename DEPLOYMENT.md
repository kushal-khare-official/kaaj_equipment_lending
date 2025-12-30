# Deployment Guide

This guide covers deploying the Lender Matching Platform with:
- **Frontend**: Vercel (React/Vite)
- **Backend**: Render (FastAPI/Python)
- **Database**: Render PostgreSQL

## ✅ Completed Steps

### 1. PostgreSQL Database (Render)
The database has been created successfully:
- **Name**: `lender-matching-db`
- **Host**: `dpg-d59q94ogjchc73at25o0-a.oregon-postgres.render.com`
- **Database**: `lender_matching_db`
- **User**: `lender_matching_db_user`
- **Region**: Oregon
- **Dashboard**: https://dashboard.render.com/d/dpg-d59q94ogjchc73at25o0-a

> ⚠️ Get the password from the Render dashboard under "Connections"

### 2. Configuration Files Created
- `backend/render.yaml` - Render deployment configuration
- `frontend/vercel.json` - Vercel deployment configuration

---

## 🔧 Manual Steps Required

### Step 1: Deploy Backend to Render

1. Go to https://dashboard.render.com/web/new
2. Connect your GitHub repository: `kushal-khare-official/kaaj_equipment_lending`
3. Configure the service:
   - **Name**: `lender-matching-api`
   - **Region**: Oregon
   - **Branch**: `main`
   - **Root Directory**: `backend`
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

4. Add Environment Variables:
   ```
   DATABASE_URL=postgresql://lender_matching_db_user:<PASSWORD>@dpg-d59q94ogjchc73at25o0-a.oregon-postgres.render.com/lender_matching_db
   ENVIRONMENT=production
   SECRET_KEY=<generate-a-secure-random-string>
   ```
   > Replace `<PASSWORD>` with the password from your Render PostgreSQL dashboard

5. Click "Create Web Service"

6. After deployment, run database migrations:
   - Go to the Shell tab in your Render service
   - Run: `alembic upgrade head`

### Step 2: Deploy Frontend to Vercel

**Option A: Via Vercel Dashboard**
1. Go to https://vercel.com/new
2. Import your GitHub repository: `kushal-khare-official/kaaj_equipment_lending`
3. Configure the project:
   - **Framework Preset**: Vite
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`

4. Add Environment Variable:
   ```
   VITE_API_BASE=https://lender-matching-api.onrender.com
   ```
   > Replace with your actual Render backend URL

5. Click "Deploy"

**Option B: Via Vercel CLI**
```bash
cd frontend
npx vercel login
npx vercel deploy --prod
```

---

## 🔗 Post-Deployment

### Update CORS (if needed)
If you encounter CORS issues, update `backend/app/main.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://your-frontend.vercel.app",
        "http://localhost:5173",  # Keep for local dev
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Seed the Database
After the backend is deployed, you may want to seed initial lender data:
1. Go to Render Shell
2. Run: `python scripts/seed_lenders.py`

---

## 📝 URLs After Deployment

| Service | URL |
|---------|-----|
| Frontend | `https://your-project.vercel.app` |
| Backend API | `https://lender-matching-api.onrender.com` |
| API Health | `https://lender-matching-api.onrender.com/health` |
| Render Dashboard | https://dashboard.render.com |
| Vercel Dashboard | https://vercel.com/dashboard |

---

## 🔒 Security Notes

1. Never commit secrets to git
2. Use Render's environment variable system for sensitive data
3. Generate a strong `SECRET_KEY` for production
4. Consider enabling Render's IP allowlist for the database
5. Enable Vercel's deployment protection for preview deployments

