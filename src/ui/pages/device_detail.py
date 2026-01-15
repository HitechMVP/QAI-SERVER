from nicegui import ui, context, app
from src.core.device_socket_manager import device_socket_manager
import asyncio
import time

async def send_command(device_id, cmd, payload=None, target_client=None):
    client = target_client
    if client is None:
        try:
            client = context.client
        except RuntimeError:
            client = None

    success = await device_socket_manager.send_command(device_id, cmd, payload)
    
    if client:
        with client: 
            if success:
                if cmd != 'get_config':
                    ui.notify(f"Đã gửi: {cmd}", type='positive', position='top')
            else:
                ui.notify(f"Thiết bị {device_id} đang Offline!", type='negative', position='top')
    
    return success

ui.add_head_html('''
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        
        body { 
            font-family: 'Inter', sans-serif; 
            background-color: #f8fafc;
            touch-action: manipulation; 
            -webkit-tap-highlight-color: transparent; 
            user-select: none;
            -webkit-user-select: none; 
        }
        
        ::-webkit-scrollbar { width: 4px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 2px; }
    </style>
''')

async def check_and_open_config(device_id):
    device_data = device_socket_manager.device_data.get(device_id, {})
    if device_data.get('status') != 'online':
        ui.notify(f"⚠️ Thiết bị {device_id} đang OFFLINE!", type='negative', position='top')
        return

    current_client = context.client
    
    fetch_task = asyncio.create_task(
        send_command(device_id, cmd='get_config', target_client=current_client)
    )
    
    with ui.dialog() as pwd_dialog, ui.card().classes('w-80 p-6 rounded-xl shadow-xl'):
        ui.label('Xác thực quyền truy cập').classes('text-lg font-bold text-slate-800 mb-1')
        
        pwd_input = ui.input('Mật khẩu', password=True) \
        .classes('w-full') \
        .props('outlined dense input-class="text-[16px]"')
        
        async def on_submit():
            val = pwd_input.value
            
            if val == '1' or val == 'admin':
                pwd_dialog.close()
                
                is_admin_mode = (val == 'admin')
                
                n = ui.notification('Đang đồng bộ dữ liệu...', spinner=True, timeout=None)
                try:
                    await fetch_task 
                    render_config_modal(device_id, current_client, is_admin=is_admin_mode)
                    
                finally:
                    n.dismiss()
            else:
                ui.notify('Mật khẩu không đúng!', type='negative')
                pwd_input.value = ""

        pwd_input.on('keydown.enter', on_submit)

        with ui.row().classes('w-full justify-end gap-2 mt-4'):
            ui.button('Hủy', on_click=pwd_dialog.close).props('flat color=slate-500 dense')
            ui.button('Xác nhận', on_click=on_submit).props('unelevated color=primary dense')
            
    pwd_dialog.open()

def render_config_modal(device_id, client, is_admin=False):

    device_info = device_socket_manager.device_data.get(device_id, {})
    conf = device_info.get('configs', {}) 
    
    max_w = int(conf.get('frame_width', 640))
    max_h = int(conf.get('frame_height', 480))
    
    with client:
        with ui.dialog().classes('z-50') as dialog:
            with ui.card().classes('bg-white text-slate-800 p-0 shadow-2xl flex flex-col w-full h-[100dvh] md:w-[450px] md:h-auto md:max-h-[90vh] md:rounded-2xl overflow-hidden'):
                
                # HEADER
                with ui.row().classes('w-full items-center justify-between p-4 border-b bg-slate-50'):
                    with ui.row().classes('items-center gap-2'):
                        header_color = 'red' if is_admin else 'primary'
                        role_text = 'ADMIN' if is_admin else 'USER'
                        
                        ui.icon('tune', color=header_color).classes('text-lg')
                        with ui.column().classes('gap-0'):
                            ui.label('Cấu hình thiết bị').classes('font-bold text-base leading-tight')
                            ui.label(f'Quyền: {role_text}').classes('text-[10px] text-slate-400 font-bold')
                            
                    ui.button(icon='close', on_click=dialog.close).props('flat round dense color=slate-400')

                # TABS
                with ui.tabs().classes('w-full border-b bg-white') as tabs:
                    ui.tab('MAIN', label='Cài đặt')
                    
                    if is_admin:
                        ui.tab('CROP', label='Vùng')
                        ui.tab('SYS', label='Hệ thống')
                        ui.tab('DATA', label='Dữ liệu')
                        ui.tab('ALL', label='Toàn bộ')
                

                # CONTENT
                with ui.scroll_area().classes('flex-grow w-full bg-slate-50 p-4'):
                    with ui.tab_panels(tabs, value='MAIN').classes('w-full bg-transparent'):
                        
                        with ui.tab_panel('MAIN').classes('p-0 flex flex-col gap-4'):
                            with ui.column().classes('w-full bg-white p-4 rounded-xl border shadow-sm gap-1'):
                                with ui.row().classes('w-full justify-between items-center'):
                                    ui.label('Thời gian nhắm mắt').classes('text-xs font-bold text-slate-500 uppercase')
                                    drowsy_label = ui.label().classes('text-sm font-bold text-green-600')
                                s_drowsy = ui.slider(min=0.5, max=5.0, step=0.1, value=conf.get('drowsy_time_threshold', 1.5)) \
                                    .on('update:model-value', lambda e: send_command(device_id, 'update_config', {'drowsy_time_threshold': e.args}))
                                drowsy_label.bind_text_from(s_drowsy, 'value', backward=lambda v: f'{v:.1f}s')
                            
                            with ui.column().classes('w-full bg-white p-4 rounded-xl border shadow-sm gap-4'):
                                
                                with ui.column().classes('w-full gap-1'):
                                    ui.label('Chế độ ngắt còi (Relay)').classes('text-xs font-bold text-slate-500 uppercase')
                                    
                                    select_mode = ui.select(
                                        {
                                            0: 'Tắt tự động (Timer)', 
                                            1: 'Tắt thủ công'
                                        }, 
                                        value=conf.get('alert_mode', 0),
                                        on_change=lambda e: send_command(device_id, 'update_config', {'alert_mode': e.value})
                                    ).props('outlined bg-white dense behavior=menu').classes('w-full')

                                ui.separator()

                                with ui.column().classes('w-full gap-0'):
                                    with ui.row().classes('w-full justify-between items-center'):
                                        ui.label('Thời gian hú còi (Timer)').classes('text-xs font-bold text-slate-500 uppercase')
                                        alert_label = ui.label().classes('text-sm font-bold text-orange-600')
                                    
                                    s_alert = ui.slider(min=1.0, max=15.0, step=0.5, value=conf.get('alert_time', 3.0)) \
                                        .on('update:model-value', lambda e: send_command(device_id, 'update_config', {'alert_time': e.args}))
                                    
                                    alert_label.bind_text_from(s_alert, 'value', backward=lambda v: f'{v:.1f}s')

                                    s_alert.bind_enabled_from(select_mode, 'value', backward=lambda v: v == 0)
                                    alert_label.bind_visibility_from(select_mode, 'value', backward=lambda v: v == 0)

                        if is_admin:
                            
                            # TAB CROP
                            with ui.tab_panel('CROP').classes('p-0 flex flex-col gap-4'):
                                with ui.row().classes('w-full justify-between items-center bg-white p-4 rounded-xl border shadow-sm'):
                                    with ui.column().classes('gap-0'):
                                        ui.label('Sử dụng vùng cắt (Crop)').classes('text-sm font-bold text-slate-700')
                                        ui.label(f'Res: {max_w}x{max_h}').classes('text-[10px] text-slate-400')
                                    ui.switch(value=conf.get('crop_enabled', True),
                                            on_change=lambda e: send_command(device_id, 'update_config', {'crop_enabled': e.value}))
                                
                                with ui.column().classes('w-full bg-white p-4 rounded-xl border shadow-sm gap-4'):
                                    def crop_slider(label, key, max_val, color):
                                        with ui.column().classes('w-full gap-0'):
                                            with ui.row().classes('w-full justify-between items-center'):
                                                ui.label(label).classes('text-xs font-bold text-slate-500')
                                                val_lbl = ui.label().classes(f'text-xs font-bold text-{color}-600')
                                            sl = ui.slider(min=0, max=max_val, step=10, value=conf.get(key, 0)) \
                                                .props(f'color={color}') \
                                                .on('update:model-value', lambda e, k=key: send_command(device_id, 'update_config', {k: int(e.args)}))
                                            val_lbl.bind_text_from(sl, 'value', backward=lambda v: f'{int(v)} px')

                                    crop_slider('Tọa độ X', 'crop_x', max_w, 'blue')
                                    crop_slider('Tọa độ Y', 'crop_y', max_h, 'blue')
                                    ui.separator()
                                    crop_slider('Chiều rộng', 'crop_w', max_w, 'purple')
                                    crop_slider('Chiều cao', 'crop_h', max_h, 'purple')

                            # TAB SYS
                            with ui.tab_panel('SYS').classes('p-0 flex flex-col gap-4'):
                                with ui.column().classes('w-full bg-white p-4 rounded-xl border shadow-sm gap-1'):
                                    ui.label('Tham số AI').classes('text-sm font-bold text-slate-700 mb-2')
                                    
                                    with ui.row().classes('w-full justify-between items-center'):
                                        ui.label('Ngưỡng YOLO').classes('text-xs font-medium text-slate-500')
                                        det_lbl = ui.label().classes('text-xs font-bold text-blue-600')
                                    s_det = ui.slider(min=0.1, max=1.0, step=0.01, value=conf.get('det_conf_threshold', 0.5)) \
                                        .on('update:model-value', lambda e: send_command(device_id, 'update_config', {'det_conf_threshold': e.args}))
                                    det_lbl.bind_text_from(s_det, 'value', backward=lambda v: f'{int(v*100)}%')

                                    with ui.row().classes('w-full justify-between items-center mt-2'):
                                        ui.label('Độ nhạy mắt').classes('text-xs font-medium text-slate-500')
                                        cls_lbl = ui.label().classes('text-xs font-bold text-orange-600')
                                    s_cls = ui.slider(min=0.01, max=1.0, step=0.01, value=conf.get('cls_threshold', 0.2)) \
                                        .props('color=orange') \
                                        .on('update:model-value', lambda e: send_command(device_id, 'update_config', {'cls_threshold': e.args}))
                                    cls_lbl.bind_text_from(s_cls, 'value', backward=lambda v: f'{int(v*100)}%')

                                    with ui.row().classes('w-full justify-between items-center mt-2'):
                                        ui.label('Tốc độ (FPS)').classes('text-xs font-medium text-slate-500')
                                        fps_lbl = ui.label().classes('text-xs font-bold text-purple-600')
                                    s_fps = ui.slider(min=5, max=30, step=1, value=conf.get('frame_rate', 15)) \
                                        .props('color=purple') \
                                        .on('update:model-value', lambda e: send_command(device_id, 'update_config', {'frame_rate': int(e.args)}))
                                    fps_lbl.bind_text_from(s_fps, 'value', backward=lambda v: f'{int(v)} FPS')

                                with ui.column().classes('w-full bg-white p-4 rounded-xl border shadow-sm gap-2'):
                                    ui.label('Logic cảnh báo').classes('text-sm font-bold text-slate-700')
                                    ui.select({0: 'Cả 2 mắt cùng đóng', 1: 'Chỉ cần 1 mắt đóng'}, 
                                        value=conf.get('logic_mode', 0), 
                                        on_change=lambda e: send_command(device_id, 'update_config', {'logic_mode': e.value})) \
                                    .props('outlined bg-white dense behavior=menu').classes('w-full')
                                
                            # TAB DATA
                            with ui.tab_panel('DATA').classes('p-0 flex flex-col gap-4'):

                                # Enable data collection
                                with ui.column().classes('w-full bg-white p-4 rounded-xl border shadow-sm gap-2'):
                                    ui.label('Thu thập dữ liệu').classes('text-sm font-bold text-slate-700')

                                    ui.switch(
                                        value=conf.get('data_collection_enabled', True),
                                        on_change=lambda e: send_command(
                                            device_id,
                                            'update_config',
                                            {'data_collection_enabled': e.value}
                                        )
                                    ).props('color=green')

                                    ui.label('Bật / tắt chế độ thu thập dữ liệu').classes('text-xs text-slate-500')

                                # Data collection interval
                                with ui.column().classes('w-full bg-white p-4 rounded-xl border shadow-sm gap-2'):
                                    with ui.row().classes('w-full justify-between items-center'):
                                        ui.label('Chu kỳ thu thập').classes('text-xs font-bold text-slate-500')
                                        interval_lbl = ui.label().classes('text-xs font-bold text-blue-600')

                                    s_interval = ui.slider(
                                        min=1,
                                        max=60,
                                        step=1,
                                        value=conf.get('data_collection_interval', 5)
                                    ).props('color=blue') \
                                    .on(
                                        'update:model-value',
                                        lambda e: send_command(
                                            device_id,
                                            'update_config',
                                            {'data_collection_interval': int(e.args)}
                                        )
                                    )

                                    interval_lbl.bind_text_from(
                                        s_interval, 'value',
                                        backward=lambda v: f'{int(v)} s'
                                    )

                                # Upload dataset button
                                with ui.column().classes('w-full bg-white p-4 rounded-xl border shadow-sm gap-2'):
                                    ui.label('Dataset').classes('text-sm font-bold text-slate-700')

                                    ui.button(
                                        'UPLOAD DATASET',
                                        icon='cloud_upload',
                                        on_click=lambda: send_command(device_id, 'upload_dataset')
                                    ).props('unelevated color=primary') \
                                    .classes('w-full py-2 font-bold')
                                    
                            # TAB ALL CONFIG
                            with ui.tab_panel('ALL').classes('p-0 flex flex-col gap-4'):

                                edited_conf = {}

                                def update_value(k, v):
                                    edited_conf[k] = v

                                with ui.column().classes('w-full bg-white p-4 rounded-xl border shadow-sm gap-3'):
                                    ui.label('Toàn bộ cấu hình').classes('text-sm font-bold text-slate-700')

                                    for key, value in conf.items():

                                        with ui.row().classes('w-full items-center gap-2'):
                                            ui.label(key).classes('text-xs font-mono text-slate-600 w-[45%] break-all')

                                            # BOOL
                                            if isinstance(value, bool):
                                                ui.switch(
                                                    value=value,
                                                    on_change=lambda e, k=key: update_value(k, e.value)
                                                )

                                            # NUMBER
                                            elif isinstance(value, (int, float)):
                                                ui.input(
                                                    value=str(value),
                                                    on_change=lambda e, k=key: update_value(k, float(e.value) if '.' in e.value else int(e.value))
                                                ).props('outlined dense type=number').classes('w-full')

                                            # STRING / OTHER
                                            else:
                                                ui.input(
                                                    value=str(value),
                                                    on_change=lambda e, k=key: update_value(k, e.value)
                                                ).props('outlined dense').classes('w-full')

                                # SAVE BUTTON
                                with ui.column().classes('w-full bg-white p-4 rounded-xl border shadow-sm'):
                                    ui.button(
                                        'LƯU TOÀN BỘ CẤU HÌNH',
                                        icon='save',
                                        on_click=lambda: send_command(
                                            device_id,
                                            'update_config',
                                            edited_conf
                                        )
                                    ).props('unelevated color=primary') \
                                    .classes('w-full py-2 font-bold')

                with ui.row().classes('w-full p-4 border-t bg-white shadow-inner'):
                    ui.button('HOÀN TẤT', on_click=dialog.close).props('unelevated color=primary').classes('w-full py-2 font-bold')
        
        dialog.open()

async def check_and_reboot(device_id):
    device_data = device_socket_manager.device_data.get(device_id, {})
    if device_data.get('status') != 'online':
        ui.notify(f"⚠️ Thiết bị {device_id} đang OFFLINE. Không thể khởi động lại!", type='negative', position='top')
        return

    with ui.dialog() as pwd_dialog, ui.card().classes('w-[360px] p-0 gap-0 rounded-2xl shadow-2xl bg-white overflow-hidden'):
        
        with ui.column().classes('w-full p-6 items-center gap-3 text-center'):
            with ui.element('div').classes('w-16 h-16 bg-red-50 rounded-full flex items-center justify-center mb-1'):
                ui.icon('restart_alt').classes('text-3xl text-red-500')
            
            with ui.column().classes('gap-1'):
                ui.label('Khởi động lại?').classes('text-xl font-bold text-slate-800')
                ui.label(f'Thiết bị {device_id} sẽ mất kết nối trong giây lát.') \
                    .classes('text-xs text-slate-500 font-medium leading-relaxed px-2')

        with ui.column().classes('w-full px-6 pb-2'):
            ui.label('XÁC THỰC ADMIN').classes('text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1 ml-1')

            pwd_input = ui.input(password=True, placeholder='Nhập mật khẩu...') \
        .classes('w-full') \
        .props('outlined dense color=red rounded input-class="text-[16px] font-medium"')
            
        with ui.row().classes('w-full bg-slate-50 p-4 justify-between items-center border-t border-slate-100 mt-4'):
            
            async def on_submit():
                if pwd_input.value == 'admin': 
                    pwd_dialog.close()
                    ui.notify(f'🚀 Đang gửi lệnh REBOOT tới {device_id}...', type='warning', position='top')
                    await send_command(device_id, cmd='reboot')
                else:
                    ui.notify('Sai mật khẩu!', type='negative')
                    pwd_input.value = ""
                    pwd_input.run_method('focus')
            
            pwd_input.on('keydown.enter', on_submit)

            ui.button('Hủy bỏ', on_click=pwd_dialog.close) \
                .props('flat dense no-caps text-color=slate-500') \
                .classes('font-semibold hover:bg-slate-200 px-3')

            ui.button('Xác nhận', on_click=on_submit) \
                .props('unelevated dense color=red-600 no-caps icon-right=arrow_forward') \
                .classes('px-4 rounded-lg shadow-sm shadow-red-200 font-bold')
            
    pwd_dialog.open()


@ui.page('/device/{device_id}')
def device_detail_page(device_id: str):
    ui.colors(primary='#3b82f6', secondary='#64748b', accent='#f59e0b', positive='#10b981')
    
    device_data = device_socket_manager.device_data.get(device_id, {})
    is_online = device_data.get('status') == 'online'

    with ui.column().classes('w-full h-[100dvh] bg-slate-50 overflow-hidden gap-0 relative'):

        with ui.row().classes('w-full h-14 px-4 flex items-center justify-between shrink-0 bg-white border-b border-slate-200 z-20'):
            with ui.row().classes('items-center gap-3'):
                ui.button(icon='arrow_back_ios_new', on_click=lambda: ui.navigate.to('/')) \
                    .props('flat round dense color=slate-600') \
                    .classes('active:bg-slate-100 transition-colors duration-100') 
                
                with ui.column().classes('gap-0'):
                    ui.label(device_id).classes('text-sm font-bold text-slate-800 leading-tight')
                    with ui.row().classes('items-center gap-1'):
                        ui.element('div').classes(f'w-1.5 h-1.5 rounded-full {"bg-green-500" if is_online else "bg-red-500"}')
                        ui.label('TRỰC TUYẾN' if is_online else 'MẤT KẾT NỐI').classes('text-[10px] font-bold text-slate-500')
            
            ui.button(icon='more_vert').props('flat round color=slate-400 dense')

        video_container = ui.column().classes('w-full flex-grow items-center justify-center bg-black relative overflow-hidden')
        
        def render_video_stream():
            video_container.clear()
            with video_container:
                ui.html(f'<img id="video"  style="width:100%; height:100%; object-fit:contain; pointer-events:none;"/>', sanitize=False) \
                    .classes('w-full h-full select-none')

                ui.run_javascript(f"""
                    const socket = io("/", {{ 
                        path: "/socket.io/user",
                        transports: ['websocket', 'polling']
                    }});

                    socket.emit("join_device", "{device_id}");

                    socket.on("video_frame", (data) => {{
                        if (data.device_id !== "{device_id}") return;

                        const imgElement = document.getElementById("video");
                        if (imgElement) {{
                            // 1. Dọn dẹp bộ nhớ RAM của frame cũ (QUAN TRỌNG NHẤT)
                            if (imgElement.src.startsWith("blob:")) {{
                                URL.revokeObjectURL(imgElement.src);
                            }}

                            // 2. data.image bây giờ là ArrayBuffer.
                            // Tạo Blob từ dữ liệu nhị phân.
                            // Lưu ý: Nếu cam bạn là PNG thì đổi 'image/jpeg' thành 'image/png'
                            const blob = new Blob([data.image], {{ type: 'image/jpeg' }});

                            // 3. Tạo đường dẫn ảo và gán vào ảnh
                            const url = URL.createObjectURL(blob);
                            imgElement.src = url;
                        }}
                    }});

                    socket.on("connect", () => {{
                        console.log("JS: Connected to User Socket");
                    }});
                """)
                            
                ui.button(icon='refresh', on_click=render_video_stream) \
                    .props('round flat dense text-color=white') \
                    .classes('absolute top-2 right-2 bg-white/10 backdrop-blur-sm active:bg-white/20')

        render_video_stream()

        with ui.column().classes('w-full shrink-0 bg-white border-t border-slate-200 p-4 pb-8 z-20'):
            
            with ui.grid(columns=4).classes('w-full max-w-md mx-auto gap-4'):
                
                def control_btn(icon, label, theme, callback):
                    themes = {
                        'blue':   ('bg-blue-50',   'text-blue-600',   'border-blue-100',   'active:bg-blue-100'),
                        'purple': ('bg-purple-50', 'text-purple-600', 'border-purple-100', 'active:bg-purple-100'),
                        'red':    ('bg-red-50',    'text-red-600',    'border-red-100',    'active:bg-red-100')
                    }
                    bg, text, border, active = themes.get(theme, themes['blue'])

                    with ui.column().classes('items-center gap-2 w-full cursor-pointer group'):
                        with ui.button(icon=icon, on_click=callback) \
                                .props('round unelevated size=md') \
                                .classes(f"w-12 h-12 md:w-14 md:h-14 {bg} {text} border {border} "
                                         f"{active} transition-transform duration-75 ease-out active:scale-[0.96]"):
                            pass 
                        
                        ui.label(label).classes('text-[10px] font-bold text-slate-500 uppercase tracking-wide select-none')

                control_btn('tune', 'Cấu hình', 'blue', lambda: check_and_open_config(device_id))
                control_btn('history', 'Lịch sử', 'purple', lambda: ui.navigate.to(f'{device_id}/history'))
                control_btn('notifications_off', 'Tắt Còi', 'red', 
                            lambda: send_command(device_id, 'update_config', {'alarm_status': False}))
                control_btn('power_settings_new', 'Hệ thống', 'red', lambda: check_and_reboot(device_id))