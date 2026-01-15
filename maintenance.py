import uvicorn
import sys
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse


CONTACT_NAME = "Mr Hậu"
CONTACT_DEPT = "PE Dept"
CONTACT_PHONE = "0898088264"

NOTICE = "Các thiết bị ở chế độ tắt còi thủ công sẽ tạm chuyển về chế độ tắt còi tự động sau 2s. Xin chân thành cảm ơn."

if len(sys.argv) > 1:
    EXPECTED_TIME = sys.argv[1]
else:
    EXPECTED_TIME = "Sớm nhất có thể"

app = FastAPI()

html_content = f"""
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bảo trì hệ thống | Q-AEye</title>
    <style>
        :root {{
            --primary-color: #2c3e50;
            --accent-color: #c0392b;
            --bg-color: #f8f9fa;
            --text-color: #2c3e50;
        }}
        body {{
            font-family: "Hiragino Sans", "Meiryo", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background-color: var(--bg-color);
            display: flex;
            justify_content: center;
            align_items: center;
            min-height: 100vh;
            margin: 0;
            padding: 20px;
            color: var(--text-color);
        }}
        .container {{
            background: white;
            padding: 3rem 2rem;
            border-radius: 8px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
            max_width: 600px; /* Tăng chiều rộng tổng thể để chứa chữ to */
            width: 100%;
            text-align: center;
            border-top: 6px solid var(--accent-color);
        }}
        
        .bowing-icon {{
            font-size: 5rem;
            margin-bottom: 1rem;
            display: inline-block;
        }}
        
        h1 {{
            font-size: 1.6rem;
            margin: 0.5rem 0;
            font-weight: 800;
        }}
        
        .jp-text {{
            font-size: 0.9rem;
            color: #7f8c8d;
            margin-bottom: 2rem;
        }}

        .message {{
            font-size: 1.1rem;
            line-height: 1.6;
            color: #34495e;
            margin-bottom: 2.5rem;
        }}
        
        /* --- PHẦN CHỈNH SỬA TO BỰ --- */
        .highlight-box {{
            background-color: #fff8e1; /* Nền vàng nhạt */
            border: 2px solid #ffc107; /* Viền vàng đậm */
            color: #5d4037;
            padding: 2rem;             /* Khoảng cách rộng */
            border-radius: 8px;
            margin-bottom: 2.5rem;
            text-align: left;
            box-shadow: 0 4px 15px rgba(255, 193, 7, 0.2); /* Bóng đổ vàng */
        }}
        
        .highlight-title {{
            font-size: 1.5rem; /* Tiêu đề "LƯU Ý" rất to */
            font-weight: 900;
            color: #d35400;
            margin-bottom: 0.8rem;
            display: flex;
            align-items: center;
            text-transform: uppercase;
        }}

        .highlight-content {{
            font-size: 1.3rem; /* Nội dung thông báo to, dễ đọc */
            line-height: 1.5;
            font-weight: 600;
        }}
        /* --------------------------- */
        
        .time-info {{
            font-weight: bold;
            color: var(--accent-color);
            font-size: 1.2rem;
        }}

        .contact-section {{
            border-top: 1px solid #eee;
            padding-top: 2rem;
        }}

        .btn {{
            display: inline-block;
            background-color: var(--primary-color);
            color: white;
            text-decoration: none;
            padding: 1rem 2.5rem;
            border-radius: 6px;
            font-weight: 600;
            transition: all 0.3s;
            font-size: 1.1rem;
        }}
        .btn:hover {{
            background-color: #1a252f;
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.15);
        }}
        .contact-label {{
            display: block;
            font-size: 0.85rem;
            opacity: 0.8;
            margin-bottom: 5px;
            font-weight: normal;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="bowing-icon">🙇‍♂️</div>
        
        <h1>THÀNH THẬT XIN LỖI</h1>
        <div class="jp-text">ご迷惑をおかけして申し訳ございません</div>

        <div class="message">
            Kính gửi Quý đồng nghiệp,<br>
            Hệ thống đang được bảo trì để nâng cao chất lượng phục vụ.<br>
            Dự kiến hoàn thành lúc: <span class="time-info">{EXPECTED_TIME}</span>
        </div>

        <div class="highlight-box">
            <div class="highlight-title">⚠️ LƯU Ý / 注意 </div>
            <div class="highlight-content">
                {NOTICE}
            </div>
        </div>

        <div class="contact-section">
            <a href="tel:{CONTACT_PHONE}" class="btn">
                <span class="contact-label">Hỗ trợ khẩn cấp / 緊急連絡先 ({CONTACT_NAME} - {CONTACT_DEPT})</span>
                📞 {CONTACT_PHONE}
            </a>
        </div>
    </div>
</body>
</html>
"""

@app.get("/{full_path:path}")
async def catch_all(request: Request, full_path: str):
    return HTMLResponse(content=html_content, status_code=503)

if __name__ == "__main__":
    print(f"Server bảo trì đang chạy. Dự kiến xong: {EXPECTED_TIME}")
    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="warning")