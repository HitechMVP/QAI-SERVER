import os
import glob
from datetime import datetime
from nicegui import ui

STORAGE_ROOT = 'server_storage'

vn_locale = {
    'days': 'Chủ nhật_Thứ hai_Thứ ba_Thứ tư_Thứ năm_Thứ sáu_Thứ bảy'.split('_'),
    'daysShort': 'CN_T2_T3_T4_T5_T6_T7'.split('_'),
    'months': 'Tháng 1_Tháng 2_Tháng 3_Tháng 4_Tháng 5_Tháng 6_Tháng 7_Tháng 8_Tháng 9_Tháng 10_Tháng 11_Tháng 12'.split('_'),
    'monthsShort': 'Th1_Th2_Th3_Th4_Th5_Th6_Th7_Th8_Th9_Th10_Th11_Th12'.split('_'),
    'firstDayOfWeek': 1, 
    'format24h': True,
    'pluralDay': 'ngày'
}

def get_available_dates(device_id):
    img_dir = os.path.join(STORAGE_ROOT, device_id, 'images')
    if not os.path.exists(img_dir): return []
    found_dates = set()
    files = glob.glob(os.path.join(img_dir, "img_*.jpg"))
    for f_path in files:
        try:
            fname = os.path.basename(f_path)
            parts = fname.split('_') 
            if len(parts) >= 2:
                date_str = parts[1] 
                fmt_date = f"{date_str[:4]}/{date_str[4:6]}/{date_str[6:]}"
                found_dates.add(fmt_date)
        except: continue
    return list(found_dates)

def get_data_for_date(device_id, date_obj):
    date_str_compact = date_obj.strftime("%Y%m%d")
    img_dir = os.path.join(STORAGE_ROOT, device_id, 'images')
    vid_dir = os.path.join(STORAGE_ROOT, device_id, 'videos')

    # 1. Load toàn bộ Video trong ngày vào dict
    video_map = {} 
    vid_pattern = os.path.join(vid_dir, f"evidence_{date_str_compact}_*.mp4")
    for v_path in glob.glob(vid_pattern):
        try:
            fname = os.path.basename(v_path)
            parts = fname.split('_')
            if len(parts) >= 3:
                time_str = parts[2].split('.')[0]
                dt_vid = datetime.strptime(f"{date_str_compact}_{time_str}", "%Y%m%d_%H%M%S")
                video_map[dt_vid] = f"/media/{device_id}/videos/{fname}"
        except: continue

    # 2. Logic tìm Video khớp với Ảnh
    def find_matching_video(img_dt):
        best_url = None
        # Chỉ tìm video trong khoảng 30s SAU KHI chụp ảnh
        # Bạn có thể tăng số này lên nếu thời gian lưu video lâu hơn
        min_diff = 30.0 
        
        for vid_dt, url in video_map.items():
            # Tính khoảng cách: Video - Ảnh
            diff = (vid_dt - img_dt).total_seconds()
            
            # ĐIỀU KIỆN QUAN TRỌNG:
            # 1. diff >= 0: Video phải diễn ra SAU hoặc CÙNG LÚC với ảnh
            # 2. diff < min_diff: Lấy video gần nhất trong khoảng cho phép
            if 0 <= diff < min_diff:
                min_diff = diff
                best_url = url
                
        return best_url

    # 3. Gom nhóm dữ liệu
    grouped_slots = {i: [] for i in range(12)}
    img_pattern = os.path.join(img_dir, f"img_{date_str_compact}_*.jpg")
    img_files = sorted(glob.glob(img_pattern)) 

    for f_path in img_files:
        try:
            fname = os.path.basename(f_path)
            parts = fname.split('_')
            if len(parts) < 3: continue
            time_part = parts[2]
            # Parse thời gian ảnh
            dt = datetime.strptime(f"{date_str_compact}_{time_part}", "%Y%m%d_%H%M%S")
            
            slot_idx = dt.hour // 2
            
            grouped_slots[slot_idx].append({
                'image_url': f"/media/{device_id}/images/{fname}",
                'video_url': find_matching_video(dt), # Gọi hàm tìm kiếm mới
                'display_time': dt.strftime("%H:%M:%S"),
                'raw_dt': dt
            })
        except: continue
        
    return grouped_slots



@ui.page('/device/{device_id}/history')
def history_page(device_id: str):
    ui.add_head_html('''
        <style>
            body { background-color: #0f172a; color: #f1f5f9; margin: 0; padding: 0; }
            .q-date { background: #1e293b; color: white; width: 100% !important; }
            /* Card ảnh */
            .history-card { 
                border: 1px solid #334155; border-radius: 8px; overflow: hidden; position: relative; 
                background: #1e293b;
            }
            /* Hiệu ứng active cho biểu đồ */
            .bar-active { background-color: #eab308 !important; box-shadow: 0 0 10px rgba(234, 179, 8, 0.5); }
        </style>
    ''')

    state = {
        'data': {},
        'current_date': datetime.now().strftime("%Y/%m/%d")
    }
    available_dates = get_available_dates(device_id)

    # --- LAYOUT CHÍNH (Mobile: Cột dọc, PC: Hàng ngang) ---
    # flex-col: Xếp dọc (mặc định cho mobile)
    # md:flex-row: Xếp ngang (từ màn hình trung bình trở lên)
    with ui.element('div').classes('w-full min-h-screen flex flex-col md:flex-row bg-slate-900'):
        
        # --- 1. SIDEBAR (Lịch & Thông tin) ---
        # Mobile: w-full (full màn hình), PC: w-[320px] cố định
        with ui.column().classes('w-full md:w-[320px] bg-slate-900 border-b md:border-b-0 md:border-r border-slate-700 p-4 gap-4 flex-shrink-0 z-20'):
            
            # Header Sidebar
            with ui.row().classes('w-full justify-between items-center'):
                ui.button(icon='arrow_back', on_click=lambda: ui.navigate.to(f'/device/{device_id}')) \
                    .props('flat round color=slate-400')
                ui.label('LỊCH SỬ').classes('font-bold text-lg text-white')
                ui.element('div').classes('w-8') # Spacer ảo để cân giữa chữ

            # Calendar (Tự co giãn theo chiều rộng cha)
            with ui.card().classes('w-full p-0 bg-transparent shadow-none'):
                date_picker = ui.date(value=state['current_date'], on_change=lambda e: load_day_data(e.value)) \
                    .props(f'today-btn event-color="green" :events="{available_dates}" minimal flat square dark :locale={vn_locale}') \
                    .classes('w-full text-white')

            # Info Box
            with ui.row().classes('w-full justify-between items-center bg-slate-800 p-3 rounded-lg border border-slate-700'):
                lbl_date_display = ui.label('...').classes('text-base font-bold text-blue-400')
                lbl_total_events = ui.label('Loading...').classes('text-xs text-slate-400')

        # --- 2. CONTENT AREA (Biểu đồ & Danh sách ảnh) ---
        # flex-1: Chiếm hết phần còn lại
        with ui.column().classes('flex-1 w-full h-[calc(100vh-80px)] md:h-screen overflow-hidden relative'):
            
            # A. Biểu đồ (Cố định ở trên cùng của vùng Content)
            # Mobile: Cao 100px, PC: Cao 128px (h-32)
            with ui.column().classes('w-full p-2 md:p-4 bg-slate-900/90 z-10 shrink-0 border-b border-slate-800'):
                ui.label('Thống kê sự kiện (24h)').classes('text-xs text-slate-500 font-bold uppercase mb-1')
                chart_container = ui.row().classes('w-full h-24 md:h-32 items-end gap-1 md:gap-2 justify-between')

            # B. Gallery (Cuộn độc lập bên dưới biểu đồ)
            scroll_area = ui.column().classes('w-full flex-grow overflow-y-auto p-2 md:p-4 pb-20')
            with scroll_area:
                lbl_gallery_title = ui.label('Chi tiết').classes('text-lg font-bold text-white mb-2 sticky top-0 bg-slate-900/80 backdrop-blur py-2 z-10 w-full')
                
                # Grid System Responsive:
                # grid-cols-2: Mobile (2 cột)
                # md:grid-cols-4: Tablet/PC nhỏ (4 cột)
                # xl:grid-cols-5: PC to (5 cột)
                gallery_grid = ui.element('div').classes('w-full grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-2 md:gap-4')

    # --- DIALOG (POPUP) ---
    with ui.dialog().classes('z-50') as dialog:
        # Mobile: w-full h-full (full màn hình), PC: có border radius
        with ui.card().classes('w-full h-full md:w-[90vw] md:h-[85vh] md:max-w-6xl p-0 bg-black flex flex-col gap-0 md:rounded-xl md:border md:border-gray-700'):
            
            # Toolbar
            with ui.row().classes('w-full bg-slate-900 p-2 justify-between items-center shrink-0'):
                ui.label('Media Player').classes('text-gray-400 text-xs font-bold ml-2')
                ui.button(icon='close', on_click=dialog.close).props('flat round color=white dense')

            # Media Container
            media_view = ui.element('div').classes('flex-grow w-full flex items-center justify-center bg-black overflow-hidden relative')

    def show_media(item, type='image'):
        media_view.clear()
        with media_view:
            if type == 'video' and item['video_url']:
                # FIX: 
                # 1. Thay đổi style thành width: 100%; height: 100%; object-fit: contain;
                # 2. Điều này buộc video nằm gọn trong khung đen đã định sẵn kích thước
                ui.html(f'''
                    <video autoplay controls playsinline 
                           style="width: 100%; height: 100%; object-fit: contain; outline: none;">
                        <source src="{item['video_url']}" type="video/mp4">
                        Trình duyệt của bạn không hỗ trợ thẻ video.
                    </video>
                ''')
            else:
                # Ảnh thì dùng NiceGUI component đã ổn rồi, nhưng thêm w-full h-full cho chắc chắn
                ui.image(item['image_url']).classes('w-full h-full object-contain')
        
        dialog.open()

    # --- LOGIC RENDER (KHÔNG ĐỔI LOGIC, CHỈ CHỈNH CLASS) ---

    def render_gallery(items, slot_idx):
        gallery_grid.clear()
        start_h = slot_idx * 2
        lbl_gallery_title.set_text(f'{start_h:02d}:00 - {start_h+2:02d}:00 ({len(items)} ảnh)')

        if not items:
            with gallery_grid:
                ui.label('Không có dữ liệu.').classes('col-span-full text-center text-slate-500 italic py-10')
            return

        with gallery_grid:
            for item in items:
                # Card Wrapper
                with ui.element('div').classes('history-card group cursor-pointer aspect-video relative hover:ring-2 ring-blue-500 transition-all'):
                    
                    # Ảnh nền
                    img = ui.image(item['image_url']).classes('w-full h-full object-cover')
                    img.on('click', lambda _, i=item: show_media(i, 'image'))

                    # Nếu có Video
                    if item['video_url']:
                        # Nút Play overlay ở giữa
                        # with ui.element('div').classes('absolute inset-0 flex items-center justify-center pointer-events-none bg-black/10 group-hover:bg-black/30 transition-colors'):
                        #     ui.icon('play_circle', color='white').classes('text-3xl md:text-5xl opacity-80 drop-shadow-lg')
                        
                        # Nút mở Video riêng (góc phải dưới)
                        with ui.element('div').classes('absolute bottom-6 right-1 z-10'):
                             ui.button(icon='smart_display', on_click=lambda _, i=item: show_media(i, 'video')) \
                                .props('round dense color=green-600 size=sm')

                    # Footer thông tin (Time)
                    with ui.element('div').classes('absolute bottom-0 left-0 w-full bg-black/70 p-1 flex justify-between items-center backdrop-blur-[2px]'):
                        ui.label(item['display_time']).classes('text-[10px] md:text-xs font-mono font-bold text-white')
                        if item['video_url']:
                             ui.icon('videocam', size='12px', color='lightgreen')

    def render_chart(grouped_data, selected_slot):
        chart_container.clear()
        counts = [len(grouped_data.get(s, [])) for s in range(12)]
        max_val = max(counts) if counts and max(counts) > 0 else 1

        with chart_container:
            for s in range(12):
                count = counts[s]
                h_pct = max((count / max_val) * 100, 15) # Min height 15% để dễ ấn
                
                # Logic màu sắc
                bg_color = 'bg-blue-600' if count > 0 else 'bg-slate-700'
                active_class = 'bar-active' if s == selected_slot else ''
                
                # Cột Bar (Container)
                with ui.column().classes('flex-1 h-full justify-end items-center gap-0 cursor-pointer group relative touch-manipulation') as col:
                    # Số lượng (chỉ hiện nếu > 0)
                    if count > 0:
                        ui.label(str(count)).classes('text-[9px] font-bold text-white mb-0.5')
                    
                    # Thanh Bar thực tế
                    bar = ui.element('div').classes(f'w-full rounded-t-sm {bg_color} {active_class} transition-all duration-300 opacity-80 group-hover:opacity-100')
                    bar.style(f'height: {h_pct}%;')
                    
                    # Label giờ
                    ui.label(f'{s*2}h').classes('text-[8px] md:text-[10px] text-slate-400 mt-1')
                    
                    # Click event
                    col.on('click', lambda _, idx=s: select_slot(idx))

    def select_slot(slot_idx):
        current_data = state['data']
        render_chart(current_data, slot_idx)
        items = current_data.get(slot_idx, [])
        render_gallery(items, slot_idx)

    def load_day_data(date_val):
        if not date_val: return
        try:
            if isinstance(date_val, list): date_val = date_val[0]
            date_val = date_val.replace('-', '/')
            d_obj = datetime.strptime(date_val, "%Y/%m/%d")
            
            lbl_date_display.set_text(d_obj.strftime("%d/%m/%Y"))
            
            data = get_data_for_date(device_id, d_obj)
            state['data'] = data
            
            total = sum(len(items) for items in data.values())
            lbl_total_events.set_text(f"Tổng: {total} khoảnh khắc")
            
            default_slot = 0
            if d_obj.date() == datetime.now().date():
                 default_slot = datetime.now().hour // 2
            else:
                for s in range(12):
                    if len(data.get(s, [])) > 0:
                        default_slot = s
                        break
            select_slot(default_slot)
        except Exception as e:
            ui.notify(f'Lỗi: {str(e)}', type='negative')

    load_day_data(state['current_date'])