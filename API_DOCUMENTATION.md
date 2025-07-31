# SeedVR2 Video Enhancement API Documentation

## Overview

SeedVR2 is an AI-powered video super-resolution service that enhances video quality and resolution using a 3B parameter diffusion transformer model. The API provides asynchronous video processing with job-based tracking.

## Base URL

```
https://4g871oyazjkpf2-8000.proxy.runpod.net
```

## Authentication

No authentication required (currently).

## Endpoints

### 1. Health Check

Check if the service is running.

**Endpoint:** `GET /health`

**Response:**
```json
{
  "ok": true
}
```

---

### 2. Submit Video for Enhancement

Submit a video file for AI-powered enhancement and super-resolution processing.

**Endpoint:** `POST /submit`

**Content-Type:** `multipart/form-data`

**Parameters:**

| Parameter | Type | Required | Description | Default |
|-----------|------|----------|-------------|---------|
| `video` | file | Yes | Video file to process (supported: .mp4, .mov, .mkv, .webm, .avi, .gif) | - |
| `res_h` | string | No | Output height in pixels | "2160" |
| `res_w` | string | No | Output width in pixels | "3840" |

**Example Request:**
```bash
# Basic submission (uses default 4K resolution)
JOB=$(curl -sS -F "video=@/path/to/video.mp4" \
  https://4g871oyazjkpf2-8000.proxy.runpod.net/submit | jq -r .job_id)

# Custom resolution (HD 720p)
JOB=$(curl -sS -F "video=@/path/to/video.mp4" \
  -F "res_h=720" -F "res_w=1280" \
  https://4g871oyazjkpf2-8000.proxy.runpod.net/submit | jq -r .job_id)

# Full HD (1080p)
JOB=$(curl -sS -F "video=@/path/to/video.mp4" \
  -F "res_h=1080" -F "res_w=1920" \
  https://4g871oyazjkpf2-8000.proxy.runpod.net/submit | jq -r .job_id)

# 4K Ultra HD
JOB=$(curl -sS -F "video=@/path/to/video.mp4" \
  -F "res_h=2160" -F "res_w=3840" \
  https://4g871oyazjkpf2-8000.proxy.runpod.net/submit | jq -r .job_id)
```

**Success Response:** `200 OK`
```json
{
  "job_id": "356b18eb-6812-4ed0-b339-e80c89ae7635"
}
```

---

### 3. Check Job Status

Poll the status of a submitted video processing job.

**Endpoint:** `GET /status/{job_id}`

**Path Parameters:**
- `job_id` - The UUID returned from the submit endpoint

**Example Request:**
```bash
curl -s https://4g871oyazjkpf2-8000.proxy.runpod.net/status/356b18eb-6812-4ed0-b339-e80c89ae7635
```

**Response Examples:**

**Queued:**
```json
{
  "status": "queued",
  "in_path": "/workspace/SeedVR/srv_inputs/356b18eb-6812-4ed0-b339-e80c89ae7635/test.mp4",
  "out_path": null,
  "error": null,
  "started": 1753930198.0936694
}
```

**Running:**
```json
{
  "status": "running",
  "in_path": "/workspace/SeedVR/srv_inputs/356b18eb-6812-4ed0-b339-e80c89ae7635/test.mp4",
  "out_path": null,
  "error": null,
  "started": 1753930198.0936694
}
```

**Completed:**
```json
{
  "status": "done",
  "in_path": "/workspace/SeedVR/srv_inputs/356b18eb-6812-4ed0-b339-e80c89ae7635/test.mp4",
  "out_path": "/workspace/SeedVR/srv_outputs/356b18eb-6812-4ed0-b339-e80c89ae7635/test.mp4",
  "error": null,
  "started": 1753930198.0936694,
  "ended": 1753930320.04226
}
```

**Error:**
```json
{
  "status": "error",
  "in_path": "/workspace/SeedVR/srv_inputs/356b18eb-6812-4ed0-b339-e80c89ae7635/test.mp4",
  "out_path": null,
  "error": "CUDA out of memory. Tried to allocate 3.85 GiB",
  "started": 1753930198.0936694,
  "ended": 1753930350.12345
}
```

**Status Codes:**
- `200 OK` - Job found
- `404 Not Found` - Job ID does not exist

---

### 4. Download Enhanced Video

Download the processed video once the job status is "done".

**Endpoint:** `GET /result/{job_id}`

**Path Parameters:**
- `job_id` - The UUID returned from the submit endpoint

**Example Request:**
```bash
# Download with original filename
curl -OJ https://4g871oyazjkpf2-8000.proxy.runpod.net/result/356b18eb-6812-4ed0-b339-e80c89ae7635

# Download with custom filename
curl -o enhanced_video.mp4 https://4g871oyazjkpf2-8000.proxy.runpod.net/result/356b18eb-6812-4ed0-b339-e80c89ae7635
```

**Response:**
- `200 OK` - Returns the video file with `Content-Type: application/octet-stream`
- `404 Not Found` - Job ID does not exist
- `425 Too Early` - Job is not ready (still processing)
- `500 Internal Server Error` - Job failed with error (returns JSON with error details)

---

## Complete Workflow Example

```bash
# 1. Submit video for enhancement
JOB=$(curl -sS -F "video=@$HOME/Downloads/test.mp4" \
  -F "res_h=720" -F "res_w=1280" \
  https://4g871oyazjkpf2-8000.proxy.runpod.net/submit | jq -r .job_id)

echo "Job ID: $JOB"

# 2. Poll status until complete
while true; do
  STATUS=$(curl -s https://4g871oyazjkpf2-8000.proxy.runpod.net/status/$JOB | jq -r .status)
  echo "Status: $STATUS"
  
  if [ "$STATUS" = "done" ]; then
    break
  elif [ "$STATUS" = "error" ]; then
    echo "Job failed!"
    curl -s https://4g871oyazjkpf2-8000.proxy.runpod.net/status/$JOB | jq .error
    exit 1
  fi
  
  sleep 5
done

# 3. Download enhanced video
curl -OJ https://4g871oyazjkpf2-8000.proxy.runpod.net/result/$JOB
echo "Download complete!"
```

## Resolution Guidelines

| Resolution | Width × Height | Use Case | GPU Memory | Processing Time |
|------------|---------------|----------|------------|-----------------|
| HD (720p) | 1280 × 720 | Fast processing, lower quality | ~8GB | ~1-2 min |
| Full HD (1080p) | 1920 × 1080 | Balanced quality/speed | ~16GB | ~2-5 min |
| 2K (1440p) | 2560 × 1440 | High quality | ~24GB | ~5-10 min |
| 4K (2160p) | 3840 × 2160 | Maximum quality | ~40GB+ | ~10-20 min |

**Note:** Processing times vary based on video length and GPU capabilities.

## Error Handling

Common errors and solutions:

1. **CUDA Out of Memory**
   - Reduce resolution
   - Process shorter video clips
   - Wait for GPU resources to free up

2. **File Not Found**
   - Ensure video file path is correct
   - Check file permissions

3. **Job Not Found**
   - Verify job_id is correct
   - Job may have expired (jobs are stored in memory)

## Limitations

- Maximum file size: Limited by available disk space
- Supported formats: .mp4, .mov, .mkv, .webm, .avi, .gif
- Jobs are stored in memory (lost on server restart)
- Processing is sequential (one job at a time per worker)

## Technical Details

- **Model**: SeedVR2 3B parameter diffusion transformer
- **Task**: Video super-resolution with cinematic enhancement
- **Framework**: PyTorch with CUDA acceleration
- **API Framework**: FastAPI with async support 