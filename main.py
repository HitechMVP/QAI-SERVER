import logging
import os
import shutil
import uvicorn
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles 
from fastapi.responses import StreamingResponse
from nicegui import ui

from src.utils.logger import setup_logger
from src.core.device_socket_manager import device_socket_manager
from src.core.user_socket_manager import user_socket_manager
from src.ui.pages import dashboard, device_detail, history, admin_history

setup_logger(level=logging.INFO)
logger = logging.getLogger("ServerMain")

app = FastAPI()

device_socket_manager.bind_user_socket(user_socket_manager)

app.mount("/socket.io/device", device_socket_manager.app)
app.mount("/socket.io/user", user_socket_manager.app)

if not os.path.exists('server_storage'):
    os.makedirs('server_storage')

app.mount("/media", StaticFiles(directory="server_storage"), name="media")
app.mount("/assets", StaticFiles(directory="assets"), name="assets")

@app.get("/api/video_feed/{device_id}")
async def video_feed(device_id: str):
    return StreamingResponse(
        device_socket_manager.get_stream_generator(device_id),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

@app.post("/upload")
async def receive_file(
    file: UploadFile = File(...),
    device_id: str = Form(...),
    file_type: str = Form(...),  
    filename: str = Form(...)    
):
    base_dir = f"server_storage/{device_id}"
    
    if file_type == "video":
        if "_ANN_" in filename:
            sub_folder = "annotated_videos"
        else:
            sub_folder = "videos"
    elif file_type == "image":
        sub_folder = "images"
    else:
        sub_folder = f"{file_type}s"

    save_dir = os.path.join(base_dir, sub_folder)
    os.makedirs(save_dir, exist_ok=True)
    
    file_path = os.path.join(save_dir, filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    return {"status": "success", "path": file_path, "folder": sub_folder}

UPLOAD_ROOT = "received_dataset"
@app.post("/dataset_upload")
async def upload_file(
    file: UploadFile = File(...),
    sub_folder: str = Form(...)  
):
    try:
        save_dir = os.path.join(UPLOAD_ROOT, sub_folder)
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        
        file_location = os.path.join(save_dir, file.filename)
        
        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        logger.info(f"Received: {sub_folder}/{file.filename}")
        return {"status": "success", "filename": file.filename}
    
    except Exception as e:
        logger.error(f"Error: {e}")
        return {"status": "error", "message": str(e)}

ui.run_with(
    app, 
    title="ORO Dashboard", 
    favicon="assets/oro.png"
)

if __name__ == '__main__':
    logger.info("🚀 Server starting on http://0.0.0.0:80")
    uvicorn.run(app, host='0.0.0.0', port=80, log_level="warning")