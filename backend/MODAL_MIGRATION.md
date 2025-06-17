# Modal to Unified FastAPI Migration Guide

This guide details the complete migration from Modal to a unified local FastAPI application for the Omi backend.

## What Changed

### ✅ Completed Migration

1. **Dependencies Updated**
   - Removed `modal==1.0.4` dependency
   - All required packages already present: `apscheduler`, `uvicorn`, `python-multipart`

2. **Modal Services Migrated**
   - `/v1/speaker-identification` - Speaker identification using SpeechBrain
   - `/v1/vad` - Voice Activity Detection using PyAnnote
   - Cron jobs using APScheduler instead of Modal Cron

3. **Architecture Changes**
   - Single unified FastAPI application in `main.py`
   - Lazy-loading ML models for fast startup
   - Local environment variables replace Modal Secrets
   - Standard FastAPI routers replace Modal endpoints

### 🔄 Service Mapping

| Modal Service | New Location | Description |
|---------------|--------------|-------------|
| `modal/speech_profile_modal.py` | `routers/modal_services.py` `/v1/speaker-identification` | Speaker identification |
| `modal/vad_modal.py` | `routers/modal_services.py` `/v1/vad` | Voice activity detection |
| `modal/job_modal.py` | `main.py` APScheduler | Cron jobs for notifications |
| `pusher/main.py` | `main.py` | Integrated into main app |

## Running the Unified Backend

### Quick Start

1. **Run the setup script:**
   ```bash
   cd backend
   ./setup_unified_backend.sh
   ```

2. **Configure environment:**
   ```bash
   cp .env.template .env
   # Edit .env with your configuration
   ```

3. **Run for development:**
   ```bash
   source venv/bin/activate
   uvicorn main:app --reload
   ```

### Docker Production Deployment

1. **Build the unified container:**
   ```bash
   docker build -f Dockerfile.unified -t omi-backend .
   ```

2. **Run with GPU support:**
   ```bash
   docker run -p 8080:8080 --env-file .env --gpus all omi-backend
   ```

### Environment Configuration

Key environment variables for the unified backend:

```env
# Database
DATABASE_CHOICE=postgres
POSTGRES_URL=postgresql://user:pass@localhost:5432/omi_db

# STT (kept as requested)
DEEPGRAM_API_KEY=your_key

# ML Models
HUGGINGFACE_TOKEN=your_token

# Optional: HTTP timeouts
HTTP_GET_TIMEOUT=30
HTTP_PUT_TIMEOUT=60
```

## API Endpoints

### Migrated Modal Endpoints

- `POST /v1/speaker-identification` - Speaker identification
- `POST /v1/vad` - Voice activity detection
- `GET /health` - Health check

### Existing Endpoints

All existing FastAPI endpoints remain unchanged and continue to work.

## Performance Considerations

### ML Model Loading

The unified backend implements lazy loading for heavy ML models:

- **SpeechBrain ECAPA-VOXCELEB**: ~500MB, loads on first speaker identification request
- **PyAnnote VAD**: ~300MB, loads on first VAD request
- **GPU Support**: Models automatically use CUDA if available

### Memory Usage

- **Startup**: ~200MB (without ML models)
- **With Models**: ~2GB+ (depending on GPU memory)
- **Concurrent Requests**: Models are shared across requests

## Cleanup

After successful migration, you can remove these directories:

```bash
# Remove Modal files
rm -rf modal/

# Remove separate pusher deployment
rm -rf pusher/
```

## Troubleshooting

### Common Issues

1. **Import Errors for ML Libraries**
   - Expected during development
   - Install with: `pip install torch speechbrain pyannote.audio`

2. **GPU Not Detected**
   - Check CUDA installation: `nvidia-smi`
   - Models will fallback to CPU automatically

3. **Model Download Issues**
   - Ensure `HUGGINGFACE_TOKEN` is set
   - Models download to `./pretrained_models/`

4. **Port Conflicts**
   - Default port is 8080
   - Change with: `uvicorn main:app --port 8000`

### Logs and Monitoring

- Application logs show model loading progress
- Health endpoint: `GET /health`
- API documentation: `http://localhost:8080/docs`

## Migration Benefits

1. **Simplified Deployment**: Single container instead of multiple Modal functions
2. **Cost Control**: No Modal compute charges
3. **Local Development**: Full stack runs locally
4. **GPU Flexibility**: Use your own GPU resources
5. **Standard FastAPI**: Easier debugging and development

## Database Requirements

The unified backend supports both database options:

- **Firestore**: Original Firebase setup (requires `SERVICE_ACCOUNT_JSON`)
- **PostgreSQL**: Recommended for production (requires `POSTGRES_URL`)

Set `DATABASE_CHOICE=postgres` for PostgreSQL or `DATABASE_CHOICE=firestore` for Firestore.
