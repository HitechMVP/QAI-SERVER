from nicegui import ui, app
from datetime import datetime

from src.core.factory_manager import factory_manager
from src.core.device_socket_manager import device_socket_manager

def format_last_seen(timestamp):
    if not timestamp:
        return "N/A"
    try:
        dt = datetime.fromtimestamp(float(timestamp))
        return dt.strftime("%Y-%m-%d %H:%M")
    except:
        return "Invalid"


def render_device_card(device_id):
    data = device_socket_manager.device_data.get(device_id, {})
    raw_status = data.get('status', 'offline')
    last_seen = data.get('last_seen', 0)
    ip = data.get('configs', {}).get('ip', 'N/A') 
    is_online = (raw_status == 'online')

    if is_online:
        status_label = "ONLINE"
        badge_class = "bg-teal-100 text-teal-800 border border-teal-200"
        icon_bg = "bg-teal-100 text-teal-700"
        icon_name = "videocam"
        dot_class = "bg-teal-500 shadow-[0_0_10px_rgba(20,184,166,0.6)]"
        border_class = "border-slate-200 hover:border-teal-400"
    else:
        status_label = "OFFLINE"
        badge_class = "bg-red-100 text-red-700 border border-red-200"
        icon_bg = "bg-red-100 text-red-600"
        icon_name = "videocam_off"
        dot_class = "bg-red-500"
        border_class = "border-slate-200 hover:border-red-400"

    with ui.card().classes(
        f'''
        w-full p-3 sm:p-4 rounded-xl border {border_class}
        bg-white shadow-md hover:shadow-lg
        hover:-translate-y-0.5 transition-all duration-300
        cursor-pointer group
        '''
    ).on('click', lambda: ui.navigate.to(f'/device/{device_id}')):

        with ui.row().classes('w-full items-center justify-between no-wrap gap-3'):

            with ui.row().classes('items-center gap-3 flex-1 overflow-hidden'):
                with ui.element('div').classes(
                    f'''
                    w-10 h-10 sm:w-12 sm:h-12 rounded-xl {icon_bg}
                    flex items-center justify-center border border-black/5 shrink-0
                    '''
                ):
                    ui.icon(icon_name).classes('text-[22px]')

                with ui.column().classes('gap-1 min-w-0'):
                    ui.label(device_id).classes(
                        '''
                        text-xs sm:text-sm font-bold text-slate-900
                        truncate group-hover:text-blue-700 transition-colors leading-tight
                        '''
                    )
                    
                    with ui.row().classes('items-center gap-1.5'):
                        ui.icon('hub').classes('text-[10px] text-slate-400') 
                        ui.label(ip).classes('text-[11px] text-slate-500 font-mono leading-none')

                    with ui.element('div').classes(
                        f'''
                        px-2 py-0.5 rounded-md text-[10px] mt-0.5
                        font-bold uppercase tracking-wider w-fit {badge_class}
                        '''
                    ):
                        ui.label(status_label)

            with ui.row().classes('items-center gap-2 shrink-0'):
                if not is_online:
                    ui.label(format_last_seen(last_seen)).classes(
                        'text-[11px] font-mono font-medium text-slate-500'
                    )

                ui.element('div').classes(
                    f'w-2.5 h-2.5 rounded-full ring-2 ring-white {dot_class}'
                )
@ui.page('/')
def dashboard():
    app.add_static_files('/assets', 'assets')

    ui.add_head_html(
        '<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">'
    )
    
    ui.add_head_html(
        '''
        <style>
            body { 
                font-family: "Inter", sans-serif; 
                background-image: url('/assets/bg.jpg'); 
                background-size: cover;
                background-position: center;
                background-repeat: no-repeat;
                background-attachment: fixed;
            }
        </style>
        '''
    )

    ui.colors(primary='#2563EB', dark='#020617')

    with ui.header().classes(
        '''
        bg-slate-900/80 backdrop-blur-md text-white h-16 
        border-b border-white/10
        px-4 sm:px-8 flex items-center justify-between
        sticky top-0 z-50 shadow-lg
        '''
    ):
        with ui.row().classes('items-center gap-3'):
            with ui.element('div').classes(
                'bg-blue-600 p-1.5 rounded-lg shadow-lg shadow-blue-600/40'
            ):
                ui.icon('domain', color='white').classes('text-[20px]')
            with ui.column().classes('gap-0'):
                ui.label('ORO MONITOR').classes(
                    'text-sm font-extrabold tracking-tight leading-none'
                )
                ui.label('Real-time Dashboard').classes(
                    'text-[10px] font-bold text-slate-400 uppercase tracking-widest'
                )

    # CONTENT
    with ui.column().classes(
        'w-full max-w-7xl mx-auto px-3 sm:px-6 pt-3 pb-6 gap-6'
    ):
        lines = factory_manager.get_all_lines()

        if not lines:
            with ui.column().classes(
                'w-full items-center justify-center py-20 opacity-60'
            ):
                ui.icon('dns', size='xl', color='slate-400')
                ui.label('No factory configuration found').classes(
                    'text-slate-500 font-medium'
                )

        for i, (line_id, info) in enumerate(lines.items()):
            devices = info.get('devices', [])

            if i % 2 == 0:
                container_cls = "bg-white/90 backdrop-blur-sm border border-white/50 shadow-sm"
                header_bg = "bg-slate-50/50 border-b border-slate-200/50"
                text_main = "text-slate-900"
                text_sub = "text-slate-500"
                icon_color = "text-slate-600"
            else:
                container_cls = "bg-indigo-50/90 backdrop-blur-sm border border-indigo-100/50 shadow-sm"
                header_bg = "bg-indigo-100/50 border-b border-indigo-200/50"
                text_main = "text-indigo-900"
                text_sub = "text-indigo-500"
                icon_color = "text-indigo-700"

            with ui.column().classes(
                f'''
                w-full {container_cls}
                rounded-xl overflow-hidden gap-0
                transition-all hover:shadow-lg duration-300
                '''
            ):
                with ui.row().classes(
                    f'w-full items-center justify-between px-4 py-3 sm:px-6 {header_bg}'
                ):
                    with ui.row().classes('items-center gap-3'):
                        ui.icon('hub').classes(f'{icon_color} text-xl')
                        with ui.column().classes('gap-0'):
                            ui.label(info.get('name', line_id)).classes(
                                f'text-sm sm:text-base font-bold {text_main} uppercase tracking-wide'
                            )
                            ui.label(f"ID: {line_id}").classes(
                                f'text-[10px] font-mono font-bold {text_sub}'
                            )

                    ui.label(f"{len(devices)} CAMS").classes(
                        'text-[10px] font-bold text-white bg-slate-800 px-2 py-1 rounded-md'
                    )

                with ui.element('div').classes('w-full p-4 sm:p-6'):
                    if not devices:
                        with ui.row().classes(
                            'w-full justify-center py-6 border-2 border-dashed border-slate-300/50 rounded-lg bg-white/40'
                        ):
                            ui.label('No devices assigned').classes(
                                'text-xs text-slate-500 italic'
                            )
                    else:
                        with ui.grid().classes(
                            'w-full grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4'
                        ):
                            for dev_id in devices:
                                render_device_card(dev_id)
        

    with ui.footer().classes(
        'bg-[#0B1120]/80 backdrop-blur-md h-10 w-full flex items-center justify-center border-t border-white/5'
    ):
        with ui.row().classes('items-center gap-3'):
            ui.label('ORO INTELLIGENCE').classes('text-[10px] font-bold text-slate-400 tracking-wider leading-none')
            
            ui.element('div').classes('w-1 h-1 rounded-full bg-slate-600')
            
            with ui.row().classes('items-center gap-1.5'):
                ui.label('KOUKI BUILD').classes('text-[10px] font-bold text-slate-500 leading-none')

        
