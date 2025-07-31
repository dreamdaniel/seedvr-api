# /workspace/SeedVR/app_queue.py
import os, uuid, shutil, subprocess, sys, threading, time
from typing import Dict
from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.responses import FileResponse, JSONResponse

REPO = "/workspace/SeedVR"
sys.path.append(REPO)

# Config via env (portable across clouds)
CKPT_DIR = os.environ.get("MODEL_DIR", "/workspace/models/SeedVR2-3B")
APP_IN   = os.environ.get("APP_IN",  f"{REPO}/srv_inputs")
APP_OUT  = os.environ.get("APP_OUT", f"{REPO}/srv_outputs")
RES_H    = os.environ.get("RES_H", "2160")
RES_W    = os.environ.get("RES_W", "3840")
SP_SIZE  = os.environ.get("SP_SIZE", "1")

os.makedirs(APP_IN, exist_ok=True)
os.makedirs(APP_OUT, exist_ok=True)
os.makedirs(f"{REPO}/ckpts", exist_ok=True)

# Ensure expected checkpoint links exist inside repo/ckpts
for name in ["seedvr2_ema_3b.pth","ema_vae.pth","pos_emb.pt","neg_emb.pt"]:
    s = os.path.join(CKPT_DIR, name)
    d = os.path.join(REPO, "ckpts", name)
    if os.path.isfile(s) and not os.path.exists(d):
        os.symlink(s, d)

def run_seedvr2(in_dir: str, out_dir: str, res_h: str = None, res_w: str = None):
    env = os.environ.copy()
    env["PYTHONPATH"] = REPO + ":" + env.get("PYTHONPATH","")
    
    # Use provided resolution or fall back to defaults
    height = res_h if res_h else RES_H
    width = res_w if res_w else RES_W
    
    cmd = [
        "torchrun","--nproc-per-node=1", f"{REPO}/projects/inference_seedvr2_3b.py",
        "--video_path", in_dir, "--output_dir", out_dir,
        "--seed","123","--res_h",str(height),"--res_w",str(width),"--sp_size",str(SP_SIZE)
    ]
    subprocess.check_call(cmd, env=env)

VIDEO_EXTS = {".mp4",".mov",".mkv",".webm",".avi",".gif"}
def pick_output_file(out_dir: str) -> str:
    paths = []
    for root, _, files in os.walk(out_dir):
        for f in files:
            paths.append(os.path.join(root, f))
    if not paths:
        raise FileNotFoundError("No files produced in output_dir")
    vids = [p for p in paths if os.path.splitext(p)[1].lower() in VIDEO_EXTS]
    return max(vids, key=os.path.getmtime) if vids else max(paths, key=os.path.getsize)

# In-memory job store
JOBS: Dict[str, Dict] = {}
LOCK = threading.Lock()

def worker(job_id: str, in_dir: str, out_dir: str, res_h: str = None, res_w: str = None):
    with LOCK:
        JOBS[job_id]["status"] = "running"
    try:
        run_seedvr2(in_dir, out_dir, res_h, res_w)
        out_path = pick_output_file(out_dir)
        with LOCK:
            JOBS[job_id].update(status="done", out_path=out_path, error=None, ended=time.time())
    except Exception as e:
        with LOCK:
            JOBS[job_id].update(status="error", error=str(e), ended=time.time())

app = FastAPI()

@app.get("/health")
def health(): return {"ok": True}

@app.post("/submit")
async def submit(video: UploadFile = File(...), res_h: str = Form(default=None), res_w: str = Form(default=None)):
    job = str(uuid.uuid4())
    in_dir  = os.path.join(APP_IN, job)
    out_dir = os.path.join(APP_OUT, job)
    os.makedirs(in_dir); os.makedirs(out_dir)
    in_path = os.path.join(in_dir, video.filename)
    with open(in_path, "wb") as f:
        shutil.copyfileobj(video.file, f)
    with LOCK:
        JOBS[job] = {"status":"queued","in_path":in_path,"out_path":None,"error":None,"started":time.time()}
    threading.Thread(target=worker, args=(job, in_dir, out_dir, res_h, res_w), daemon=True).start()
    return {"job_id": job}

@app.get("/status/{job_id}")
def status(job_id: str):
    with LOCK:
        j = JOBS.get(job_id)
        if not j: raise HTTPException(status_code=404, detail="job not found")
        return j

@app.get("/result/{job_id}")
def result(job_id: str):
    with LOCK:
        j = JOBS.get(job_id)
        if not j: raise HTTPException(status_code=404, detail="job not found")
        if j["status"] == "done" and j.get("out_path") and os.path.isfile(j["out_path"]):
            fname = os.path.basename(j["out_path"])
            return FileResponse(j["out_path"], filename=fname, media_type="application/octet-stream")
        if j["status"] == "error":
            return JSONResponse({"error": j["error"]}, status_code=500)
    raise HTTPException(status_code=425, detail="job not ready")
