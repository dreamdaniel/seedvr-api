# SeedVR2 API

An AI-powered video super-resolution API service built with FastAPI and the SeedVR2 3B parameter diffusion transformer model.

## Features

- 🎬 Video super-resolution and enhancement
- 🚀 Async job-based processing
- 📊 Real-time status tracking
- 🎯 Configurable output resolutions (720p to 4K)
- 📡 RESTful API interface

## Quick Start

1. Start the API server:
   ```bash
   python app_queue.py
   ```

2. Submit a video for enhancement:
   ```bash
   curl -F "video=@input.mp4" -F "res_h=1080" -F "res_w=1920" \
     http://localhost:8000/submit
   ```

3. Check status and download results:
   ```bash
   curl http://localhost:8000/status/{job_id}
   curl -OJ http://localhost:8000/result/{job_id}
   ```

## Documentation

See [API_DOCUMENTATION.md](./API_DOCUMENTATION.md) for complete API reference including:
- Endpoint details
- Request/response formats  
- Resolution guidelines
- Error handling
- Complete workflow examples

## Files

- `app_queue.py` - FastAPI server with queue-based job processing
- `API_DOCUMENTATION.md` - Complete API documentation

## Model

Built on SeedVR2, a 3B parameter diffusion transformer model for cinematic video enhancement.
