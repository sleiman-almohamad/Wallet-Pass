"""
Send Notification View
Allows operators to send push notifications to individual passes or template holders.
Supports both Google Wallet (via Google API) and Apple Wallet (via APNs).
"""

import flet as ft
from datetime import datetime
import configs


def build_send_notification_view(page: ft.Page, state, api_client) -> ft.Container:
    """
    Build the Send Notification tab content.
    """
    ns = state.notification_state  # shorthand

    # =======================================================
    # Notification History (shared across tabs)
    # =======================================================
    notification_history = []  # List of dicts: {platform, target, message, result, timestamp, color}
    history_column = ft.Column(spacing=8, scroll=ft.ScrollMode.AUTO, expand=True)

    def _add_history_entry(platform: str, target: str, message: str, result: str, color: str):
        ts = datetime.now().strftime("%H:%M:%S")
        notification_history.insert(0, {
            "platform": platform, "target": target,
            "message": message, "result": result,
            "timestamp": ts, "color": color,
        })
        # Keep only last 50
        if len(notification_history) > 50:
            notification_history.pop()
        _rebuild_history()

    def _rebuild_history():
        history_column.controls.clear()
        if not notification_history:
            history_column.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Icon("notifications_none", size=48, color="#d1d5db"),
                        ft.Text(state.t("msg.no_notifications"), size=13, color="#9ca3af", text_align=ft.TextAlign.CENTER),
                        ft.Text(state.t("msg.send_notification_history_hint"), size=11, color="#d1d5db", text_align=ft.TextAlign.CENTER),
                    ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8),
                    expand=True, alignment=ft.alignment.center,
                )
            )
        else:
            for entry in notification_history:
                platform_icon = ft.Icons.ANDROID if entry["platform"] == "Google" else ft.Icons.APPLE
                platform_color = "#34a853" if entry["platform"] == "Google" else "#1a1a2e"
                
                card = ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Container(
                                content=ft.Icon(platform_icon, size=14, color="white"),
                                width=24, height=24, border_radius=12,
                                bgcolor=platform_color, alignment=ft.alignment.center,
                            ),
                            ft.Text(entry["platform"], size=11, weight=ft.FontWeight.W_600, color="#374151"),
                            ft.Container(expand=True),
                            ft.Text(entry["timestamp"], size=10, color="#9ca3af"),
                        ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                        ft.Text(f"To: {entry['target']}", size=11, color="#6b7280", max_lines=1),
                        ft.Container(
                            content=ft.Text(entry["result"], size=11, color=entry["color"], weight=ft.FontWeight.W_500),
                            padding=ft.padding.symmetric(horizontal=8, vertical=4),
                            border_radius=6,
                            bgcolor="#f0fdf4" if entry["color"] == "#16a34a" else "#fef2f2",
                        ),
                    ], spacing=6),
                    padding=12, border_radius=10,
                    border=ft.border.all(1, "#e5e7eb"),
                    bgcolor="white",
                )
                history_column.controls.append(card)
        
        if page:
            page.update()

    _rebuild_history()  # Initialize empty state

    # =======================================================
    # Shared / Common Status Helpers
    # =======================================================
    status_text = ft.Text(ns.get("status_message"), color=ns.get("status_color"), size=12)
    loading_indicator = ft.ProgressBar(width=400, visible=ns.get("is_loading"), color="#0052FF")

    def _set_status(msg, color="green"):
        ns.update_multiple({
            "status_message": msg,
            "status_color": color,
            "is_loading": False
        })

    def on_state_change(data):
        status_text.value = data.get("status_message", "")
        status_text.color = data.get("status_color", "grey")
        loading_indicator.visible = data.get("is_loading", False)
        page.update()

    ns.subscribe(on_state_change)


    # =======================================================
    # GOOGLE WALLET TAB
    # =======================================================
    mode_radio = ft.RadioGroup(
        content=ft.Row([
            ft.Radio(value="single", label=state.t("mode.single")),
            ft.Radio(value="template", label=state.t("mode.template")),
        ], spacing=20),
        value=ns.get("mode") or "single",
    )

    class_dropdown = ft.Dropdown(
        label=state.t("label.select_template"),
        hint_text=state.t("placeholder.choose_template"),
        width=400, border_radius=8, text_size=13,
        options=[],
        visible=False,
    )

    search_holder_field = ft.TextField(
        label=state.t("label.search_holder"),
        hint_text="",
        width=400, border_radius=8, text_size=13,
        visible=True,
        prefix_icon="search",
    )

    find_passes_btn = ft.ElevatedButton(
        state.t("btn.find_passes"),
        icon="search",
        width=400,
        visible=True,
        style=ft.ButtonStyle(
            bgcolor="#f3f4f6", color="#374151",
            shape=ft.RoundedRectangleBorder(radius=8),
        ),
    )

    pass_dropdown = ft.Dropdown(
        label=state.t("label.select_pass"),
        hint_text=state.t("placeholder.choose_pass"),
        width=400, border_radius=8, text_size=13,
        visible=True,
        options=[],
    )

    message_field = ft.TextField(
        label=state.t("label.message"),
        hint_text="",
        multiline=True,
        min_lines=3,
        max_lines=5,
        width=400, border_radius=8, text_size=13,
    )

    send_btn = ft.ElevatedButton(
        state.t("btn.send_notification"),
        icon="send",
        width=400, height=44,
        style=ft.ButtonStyle(
            bgcolor="#0052FF", color="white",
            shape=ft.RoundedRectangleBorder(radius=8),
        ),
    )

    def load_classes():
        try:
            classes = api_client.get_classes()
            current_val = class_dropdown.value
            
            class_dropdown.options = [
                ft.dropdown.Option(
                    key=str(cls.get("class_id", "")), 
                    text=f"{str(cls.get('class_id', '')).split('.')[-1]} ({cls.get('class_type', 'Unknown')})"
                )
                for cls in classes if cls.get("class_id")
            ]
            
            if current_val and any(c.get("class_id") == current_val for c in classes):
                class_dropdown.value = current_val
                
            page.update()
        except Exception as e:
            _set_status(f"❌ {state.t('msg.api_error', detail=str(e))}", "red")

    def on_mode_change(e):
        mode = mode_radio.value
        ns.update("mode", mode)
        
        is_single = mode == "single"
        search_holder_field.visible = is_single
        find_passes_btn.visible = is_single
        pass_dropdown.visible = is_single
        class_dropdown.visible = not is_single
        
        if not is_single and not class_dropdown.options:
            load_classes()
            
        page.update()

    mode_radio.on_change = on_mode_change

    def on_find_passes(e):
        search_query = search_holder_field.value.strip().lower()
        if not search_query:
            _set_status(state.t("msg.enter_search_query"), "orange")
            page.update()
            return

        ns.update("is_loading", True)
        page.update()

        try:
            all_passes = api_client.get_passes() if api_client else []
            matching_passes = [
                p for p in all_passes 
                if search_query in str(p.get("holder_name", "")).lower()
            ]

            if not matching_passes:
                _set_status(f"❌ {state.t('msg.no_passes_found')}", "orange")
                pass_dropdown.options = []
                pass_dropdown.value = None
            else:
                pass_dropdown.options = [
                    ft.dropdown.Option(
                        key=str(p.get("object_id", "")), 
                        text=f"{p.get('holder_name', 'Unknown')} ({str(p.get('class_id', 'Unknown Template')).split('.')[-1]})"
                    )
                    for p in matching_passes if p.get("object_id")
                ]
                pass_dropdown.value = str(matching_passes[0].get("object_id", ""))
                _set_status(state.t("msg.found_passes_count", count=len(matching_passes)), "green")
            
            ns.update_multiple({
                "passes_found": matching_passes,
                "is_loading": False
            })
        except Exception as ex:
            import traceback; traceback.print_exc()
            _set_status(f"❌ {state.t('msg.api_error', detail=str(ex))}", "red")
        
        page.update()

    search_holder_field.on_submit = on_find_passes
    find_passes_btn.on_click = on_find_passes

    def on_send(e):
        mode = ns.get("mode")
        message = message_field.value.strip()
        
        if not message:
            _set_status(state.t("msg.enter_message_err"), "red")
            return

        ns.update("is_loading", True)
        page.update()

        try:
            if mode == "single":
                pass_id = pass_dropdown.value
                if not pass_id:
                    _set_status(state.t("msg.select_pass_err"), "red")
                    ns.update("is_loading", False)
                    page.update()
                    return
                
                result = api_client.send_pass_notification(pass_id, message)
                result_msg = result.get("message", "Notification sent")
                _set_status(f"✅ {result_msg}", "green")
                _add_history_entry("Google", f"Pass: {pass_id.split('.')[-1]}", message, result_msg, "#16a34a")
            else:
                class_id = class_dropdown.value
                if not class_id:
                    _set_status(state.t("msg.select_template_err"), "red")
                    ns.update("is_loading", False)
                    page.update()
                    return
                
                result = api_client.send_class_notification(class_id, message)
                result_msg = result.get("message", "Bulk notification sent")
                _set_status(f"✅ {result_msg}", "green")
                _add_history_entry("Google", f"Template: {class_id.split('.')[-1]}", message, result_msg, "#16a34a")
        except Exception as ex:
            error_msg = str(ex)
            _set_status(f"❌ {state.t('msg.api_error', detail=error_msg)}", "red")
            target = pass_dropdown.value or class_dropdown.value or "Unknown"
            _add_history_entry("Google", target, message, f"Failed: {error_msg}", "#dc2626")
        
        page.update()

    send_btn.on_click = on_send

    google_tab_content = ft.Column([
        ft.Container(
            content=ft.Column([
                ft.Text(state.t("header.select_mode"), size=13, weight=ft.FontWeight.W_600, color="#374151"),
                mode_radio,
            ], spacing=6),
            padding=ft.padding.only(bottom=10),
        ),
        ft.Divider(height=1, color="#e5e7eb"),
        ft.Container(height=6),
        
        ft.Text(state.t("header.select_target"), size=13, weight=ft.FontWeight.W_600, color="#374151"),
        search_holder_field,
        find_passes_btn,
        pass_dropdown,
        class_dropdown,
        ft.Divider(height=1, color="#e5e7eb"),
        ft.Container(height=6),
        
        ft.Text(state.t("header.compose_message"), size=13, weight=ft.FontWeight.W_600, color="#374151"),
        message_field,
        ft.Container(height=6),
        
        send_btn,
    ], spacing=10, scroll="auto")


    # =======================================================
    # APPLE WALLET TAB
    # =======================================================
    
    apple_mode_radio = ft.RadioGroup(
        content=ft.Row([
            ft.Radio(value="single", label=state.t("mode.single")),
            ft.Radio(value="template", label=state.t("mode.template")),
        ], spacing=20),
        value="single",
    )

    apple_search_field = ft.TextField(
        label=state.t("label.search_holder"),
        hint_text="",
        width=400, border_radius=8, text_size=13,
        prefix_icon="search",
        visible=True,
    )

    apple_find_btn = ft.ElevatedButton(
        state.t("btn.find_passes"),
        icon="search",
        width=400,
        visible=True,
        style=ft.ButtonStyle(
            bgcolor="#f3f4f6", color="#374151",
            shape=ft.RoundedRectangleBorder(radius=8),
        ),
    )

    apple_pass_dropdown = ft.Dropdown(
        label=state.t("label.select_pass"),
        hint_text=state.t("placeholder.choose_pass"),
        width=400, border_radius=8, text_size=13,
        options=[],
        visible=True,
    )

    apple_template_dropdown = ft.Dropdown(
        label=state.t("label.select_template"),
        hint_text=state.t("placeholder.choose_template"),
        width=400, border_radius=8, text_size=13,
        options=[],
        visible=False,
    )

    apple_device_count_text = ft.Container(
        content=ft.Row([
            ft.Icon("devices", size=14, color="#6b7280"),
            ft.Text(state.t("label.registered_devices", count="—"), size=11, color="#6b7280"),
        ], spacing=6),
        padding=ft.padding.symmetric(horizontal=12, vertical=6),
        border_radius=6,
        bgcolor="#f9fafb",
        visible=True,
    )
    apple_device_label = apple_device_count_text.content.controls[1]  # reference to the Text

    apple_info_banner = ft.Container(
        content=ft.Row([
            ft.Icon("info_outline", size=14, color="#3b82f6"),
            ft.Text(
                state.t("msg.apple_silent_push_hint"),
                size=11, color="#3b82f6", expand=True,
            ),
        ], spacing=8),
        padding=ft.padding.symmetric(horizontal=12, vertical=8),
        border_radius=8,
        bgcolor="#eff6ff",
        border=ft.border.all(1, "#bfdbfe"),
    )

    apple_message_field = ft.TextField(
        label=state.t("header.compose_notification"),
        hint_text=state.t("placeholder.apple_notification_hint"),
        width=400, border_radius=8, text_size=13,
        multiline=True, min_lines=2, max_lines=4,
    )

    apple_send_btn = ft.ElevatedButton(
        state.t("btn.send_lock_screen_notification"),
        icon=ft.Icons.NOTIFICATIONS_ACTIVE,
        width=400, height=44,
        style=ft.ButtonStyle(
            bgcolor="#1a1a2e", color="white",
            shape=ft.RoundedRectangleBorder(radius=8),
        ),
    )

    def load_apple_passes():
        try:
            passes = api_client.get_all_apple_passes()
            current_val = apple_pass_dropdown.value
            
            apple_pass_dropdown.options = [
                ft.dropdown.Option(
                    key=str(p.get("serial_number", "")), 
                    text=f"{p.get('holder_name', 'Unknown')} ({p.get('serial_number', '')})"
                )
                for p in passes if p.get("serial_number")
            ]
            
            if current_val and any(p.get("serial_number") == current_val for p in passes):
                apple_pass_dropdown.value = current_val
                
            page.update()
        except Exception as e:
            _set_status(f"❌ {state.t('msg.api_error', detail=str(e))}", "red")

    def load_apple_templates():
        try:
            templates = api_client.get_apple_templates() if hasattr(api_client, "get_apple_templates") else []
            current_val = apple_template_dropdown.value
            
            apple_template_dropdown.options = [
                ft.dropdown.Option(
                    key=str(t.get("template_id", "")),
                    text=f"{t.get('template_name', 'Unnamed')} ({t.get('pass_style', 'unknown')})"
                )
                for t in templates if t.get("template_id")
            ]
            
            if current_val and any(t.get("template_id") == current_val for t in templates):
                apple_template_dropdown.value = current_val

            page.update()
        except Exception as e:
            _set_status(f"❌ {state.t('msg.api_error', detail=str(e))}", "red")

    def on_apple_mode_change(e):
        mode = apple_mode_radio.value
        is_single = mode == "single"

        apple_search_field.visible = is_single
        apple_find_btn.visible = is_single
        apple_pass_dropdown.visible = is_single
        apple_device_count_text.visible = is_single
        apple_template_dropdown.visible = not is_single

        if not is_single and not apple_template_dropdown.options:
            load_apple_templates()

        page.update()

    apple_mode_radio.on_change = on_apple_mode_change

    def on_apple_find(e):
        search_query = apple_search_field.value.strip().lower()
        if not search_query:
            _set_status(state.t("msg.enter_search_query"), "orange")
            page.update()
            return

        ns.update("is_loading", True)
        page.update()

        try:
            all_passes = api_client.get_all_apple_passes()
            matching = [
                p for p in all_passes
                if search_query in str(p.get("holder_name", "")).lower()
            ]

            if not matching:
                _set_status(f"❌ {state.t('msg.no_passes_found')}", "orange")
                apple_pass_dropdown.options = []
                apple_pass_dropdown.value = None
            else:
                apple_pass_dropdown.options = [
                    ft.dropdown.Option(
                        key=str(p.get("serial_number", "")),
                        text=f"{p.get('holder_name', 'Unknown')} ({p.get('serial_number', '')})"
                    )
                    for p in matching if p.get("serial_number")
                ]
                apple_pass_dropdown.value = str(matching[0].get("serial_number", ""))
                _set_status(state.t("msg.found_passes_count", count=len(matching)), "green")
                # Trigger device count for auto-selected pass
                _update_device_count(apple_pass_dropdown.value)

            ns.update("is_loading", False)
        except Exception as ex:
            _set_status(f"❌ {state.t('msg.api_error', detail=str(ex))}", "red")

        page.update()

    apple_search_field.on_submit = on_apple_find
    apple_find_btn.on_click = on_apple_find

    def _update_device_count(serial):
        if not serial:
            apple_device_label.value = state.t("label.registered_devices", count="—")
            apple_device_label.color = "#6b7280"
            return
        try:
            count = api_client.get_apple_pass_devices_count(serial)
            apple_device_label.value = state.t("label.registered_devices", count=count)
            apple_device_label.color = "#16a34a" if count > 0 else "#ea580c"
        except Exception:
            apple_device_label.value = state.t("label.registered_devices", count="Error")
            apple_device_label.color = "#dc2626"

    def on_apple_pass_change(e):
        serial = apple_pass_dropdown.value
        _update_device_count(serial)
        page.update()

    apple_pass_dropdown.on_change = on_apple_pass_change

    def on_apple_send(e):
        mode = apple_mode_radio.value
        msg = apple_message_field.value.strip()
        
        if not msg:
            _set_status(state.t("msg.enter_message_err"), "orange")
            page.update()
            return

        ns.update("is_loading", True)
        page.update()

        try:
            if mode == "single":
                serial = apple_pass_dropdown.value
                if not serial:
                    _set_status(state.t("msg.select_pass_err"), "red")
                    ns.update("is_loading", False)
                    page.update()
                    return

                result = api_client.send_apple_pass_notification(serial, msg)
                result_msg = result.get("message", "APNs push sent")
                _set_status(f"✅ {result_msg}", "green")
                _add_history_entry("Apple", f"Pass: {serial}", f"Msg: {msg[:20]}...", result_msg, "#16a34a")
            else:
                template_id = apple_template_dropdown.value
                if not template_id:
                    _set_status(state.t("msg.select_template_err"), "red")
                    ns.update("is_loading", False)
                    page.update()
                    return

                result = api_client.send_apple_template_notification(template_id, msg)
                result_msg = result.get("message", "Bulk APNs sent")
                _set_status(f"✅ {result_msg}", "green")
                _add_history_entry("Apple", f"Template: {template_id}", f"Bulk Msg: {msg[:20]}...", result_msg, "#16a34a")
            
            # Clear field on success
            apple_message_field.value = ""
        except Exception as ex:
            error_msg = str(ex)
            _set_status(f"❌ {state.t('msg.api_error', detail=error_msg)}", "red")
            target = apple_pass_dropdown.value or apple_template_dropdown.value or "Unknown"
            _add_history_entry("Apple", target, "Push update", f"Failed: {error_msg}", "#dc2626")
        
        page.update()

    apple_send_btn.on_click = on_apple_send

    apple_tab_content = ft.Column([
        ft.Container(
            content=ft.Column([
                ft.Text(state.t("header.select_mode"), size=13, weight=ft.FontWeight.W_600, color="#374151"),
                apple_mode_radio,
            ], spacing=6),
            padding=ft.padding.only(bottom=10),
        ),
        ft.Divider(height=1, color="#e5e7eb"),
        ft.Container(height=6),

        ft.Text(state.t("header.select_target"), size=13, weight=ft.FontWeight.W_600, color="#374151"),
        apple_search_field,
        apple_find_btn,
        apple_pass_dropdown,
        apple_device_count_text,
        apple_template_dropdown,
        ft.Divider(height=1, color="#e5e7eb"),
        ft.Container(height=6),
        
        ft.Text(state.t("header.compose_notification"), size=13, weight=ft.FontWeight.W_600, color="#374151"),
        apple_message_field,
        ft.Container(height=6),
        
        apple_info_banner,
        ft.Container(height=6),

        apple_send_btn,
    ], spacing=10, scroll="auto")


    # =======================================================
    # Main Layout Assembly
    # =======================================================

    tabs = ft.Tabs(
        selected_index=0,
        animation_duration=200,
        label_padding=ft.padding.symmetric(horizontal=16),
        tabs=[
            ft.Tab(
                text=state.t("label.google_wallet"),
                content=ft.Container(content=google_tab_content, padding=ft.padding.only(top=15)),
                icon=ft.Icons.ANDROID
            ),
            ft.Tab(
                text=state.t("label.apple_wallet"),
                content=ft.Container(content=apple_tab_content, padding=ft.padding.only(top=15)),
                icon=ft.Icons.APPLE
            ),
        ],
        expand=True
    )

    left_panel = ft.Container(
        width=460,
        content=ft.Column([
            ft.Row([
                ft.Icon("notifications_active", size=24, color="#0052FF"),
                ft.Text(
                    state.t("header.send_notification"),
                    size=22, weight=ft.FontWeight.BOLD, color="#1a1a2e",
                ),
            ], spacing=10),
            ft.Text(
                state.t("subtitle.send_notification"),
                size=12, color="#9ca3af",
            ),
            ft.Divider(height=1, color="#e5e7eb"),
            
            ft.Container(content=tabs, expand=True, height=520),
            
            ft.Container(height=4),
            loading_indicator,
            status_text,
            
        ], spacing=8),
        padding=24,
        bgcolor="white",
        border_radius=12,
        shadow=ft.BoxShadow(blur_radius=12, color="#0000000d"),
    )

    # Right panel — Notification History
    right_panel = ft.Container(
        expand=True,
        content=ft.Column([
            ft.Row([
                ft.Icon("history", size=20, color="#0052FF"),
                ft.Text(state.t("header.notification_history"), size=16, weight=ft.FontWeight.W_700, color="#1a1a2e"),
            ], spacing=8),
            ft.Text(state.t("subtitle.notification_history"), size=11, color="#9ca3af"),
            ft.Divider(height=1, color="#e5e7eb"),
            ft.Container(height=4),
            history_column,
        ], spacing=8),
        padding=24,
        bgcolor="white",
        border_radius=12,
        shadow=ft.BoxShadow(blur_radius=12, color="#0000000d"),
    )

    def refresh_send_notification():
        load_classes()
        load_apple_passes()
        load_apple_templates()
        if mode_radio.value == "single" and search_holder_field.value and search_holder_field.value.strip():
            on_find_passes(None)

    state.register_refresh_callback("send_notification_list", refresh_send_notification)

    # ── Initial Load ──
    load_classes()
    load_apple_passes()
    load_apple_templates()

    return ft.Container(
        content=ft.Row([
            ft.Container(width=8),
            left_panel,
            ft.Container(width=16),
            right_panel,
            ft.Container(width=8),
        ], expand=True, vertical_alignment=ft.CrossAxisAlignment.START),
        expand=True,
        padding=20,
        bgcolor="#f5f5f7",
    )