#!/bin/bash
source /workspace/miniforge/etc/profile.d/conda.sh
conda activate seedvr310
cd /workspace/SeedVR
export PYTHONPATH=$PWD:$PYTHONPATH
uvicorn app_queue:app --host 0.0.0.0 --port 8000
