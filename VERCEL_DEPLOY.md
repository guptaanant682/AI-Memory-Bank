# Deploy AI Memory Bank to Vercel

## Quick Deploy (Frontend Only)

1. **Fork/Import Repository**:
   - Go to [vercel.com](https://vercel.com)
   - Click "New Project"
   - Import from GitHub: `https://github.com/guptaanant682/AI-Memory-Bank`

2. **Configure Build Settings**:
   - Framework Preset: `Next.js`
   - Build Command: `cd frontend && npm run build`
   - Output Directory: `frontend/.next`
   - Install Command: `cd frontend && npm install`

3. **Deploy**:
   - Click "Deploy"
   - Wait for build to complete
   - Your site will be live at: `https://your-project.vercel.app`

## With Backend (Serverless Functions)

1. **Environment Variables** (Optional):
   ```
   NEXT_PUBLIC_API_URL=/api
   ```

2. **Project Structure**:
   ```
   /
   ├── frontend/          # Next.js app
   ├── api/              # Serverless functions
   ├── vercel.json       # Deployment config
   └── ...
   ```

3. **Deploy**:
   - Same steps as above
   - Vercel will automatically detect and deploy serverless functions

## Live Demo

Your AI Memory Bank will be available at:
- **Frontend**: https://your-project.vercel.app
- **API**: https://your-project.vercel.app/api

## Features Available

✅ Document upload and storage
✅ AI-powered question answering  
✅ Search functionality
✅ Responsive UI
✅ Real-time processing

## Troubleshooting

If deployment fails:
1. Check build logs in Vercel dashboard
2. Ensure all dependencies are in package.json
3. Verify file paths are correct
4. Contact support if needed

---
Generated with Claude Code