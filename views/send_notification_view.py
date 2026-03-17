"""
Send Notification View
Allows operators to send push notifications to individual passes or template holders.
"""

import flet as ft
import configs

def build_send_notification_view(page: ft.Page, state, api_client) -> ft.Container:
    """
    Build the Send Notification tab content.
    """
    ns = state.notification_state  # shorthand
    
    # ── UI Controls ──
    mode_radio = ft.RadioGroup(
        content=ft.Row([
            ft.Radio(value="single", label=state.t("mode.single")),
            ft.Radio(value="template", label=state.t("mode.template")),
        ], spacing=20),
        value=ns.get("mode"),
    )

    class_dropdown = ft.Dropdown(
        label=state.t("label.select_template"),
        hint_text=state.t("label.select_template"),
        width=400,
        options=[],
        visible=False,
    )

    email_field = ft.TextField(
        label=state.t("label.customer_email"),
        hint_text=state.t("label.customer_email"),
        width=400,
        visible=True,
    )

    find_passes_btn = ft.ElevatedButton(
        state.t("btn.find_passes"),
        icon="search",
        width=400,
        visible=True,
    )

    pass_dropdown = ft.Dropdown(
        label=state.t("label.select_pass"),
        hint_text=state.t("label.select_pass"),
        width=400,
        visible=True,
        options=[],
    )

    message_field = ft.TextField(
        label=state.t("label.message"),
        hint_text=state.t("label.message"),
        multiline=True,
        min_lines=3,
        max_lines=5,
        width=400,
    )

    status_text = ft.Text(ns.get("status_message"), color=ns.get("status_color"), size=12)
    loading_indicator = ft.ProgressBar(width=400, visible=ns.get("is_loading"), color="blue")

    send_btn = ft.ElevatedButton(
        state.t("btn.send_notification"),
        icon="send",
        width=400,
        style=ft.ButtonStyle(bgcolor="blue", color="white"),
    )

    # ── Helpers ──
    def _set_status(msg, color="green"):
        ns.update_multiple({
            "status_message": msg,
            "status_color": color,
            "is_loading": False
        })

    def load_classes():
        try:
            classes = api_client.get_classes()
            class_dropdown.options = [
                ft.dropdown.Option(key=cls["class_id"], text=f"{cls['class_id']} ({cls.get('class_type', 'Unknown')})")
                for cls in classes
            ]
            page.update()
        except Exception as e:
            _set_status(state.t("msg.error_syncing", error=str(e)), "red")

    # ── Event Handlers ──
    def on_mode_change(e):
        mode = mode_radio.value
        ns.update("mode", mode)
        
        is_single = mode == "single"
        email_field.visible = is_single
        find_passes_btn.visible = is_single
        pass_dropdown.visible = is_single
        class_dropdown.visible = not is_single
        
        if not is_single and not class_dropdown.options:
            load_classes()
            
        page.update()

    mode_radio.on_change = on_mode_change

    def on_find_passes(e):
        email = email_field.value.strip()
        if not email:
            _set_status(state.t("msg.enter_email"), "red")
            return

        ns.update("is_loading", True)
        page.update()

        try:
            passes = api_client.get_passes_by_email(email)
            if not passes:
                _set_status(state.t("msg.no_passes_found"), "orange")
                pass_dropdown.options = []
            else:
                pass_dropdown.options = [
                    ft.dropdown.Option(key=p["object_id"], text=f"{p['object_id']} ({p.get('class_id')})")
                    for p in passes
                ]
                _set_status(state.t("msg.found_passes", count=len(passes)), "green")
            
            ns.update_multiple({
                "passes_found": passes,
                "is_loading": False
            })
        except Exception as ex:
            _set_status(f"Error finding passes: {ex}", "red")
        
        page.update()

    find_passes_btn.on_click = on_find_passes

    def on_send(e):
        mode = ns.get("mode")
        message = message_field.value.strip()
        
        if not message:
            _set_status(state.t("msg.enter_message"), "red")
            return

        ns.update("is_loading", True)
        page.update()

        try:
            if mode == "single":
                pass_id = pass_dropdown.value
                if not pass_id:
                    _set_status(state.t("msg.select_pass_err"), "red")
                    return
                
                result = api_client.send_pass_notification(pass_id, message)
                _set_status(state.t("msg.notification_sent"), "green")
            else:
                class_id = class_dropdown.value
                if not class_id:
                    _set_status(state.t("msg.select_template_err"), "red")
                    return
                
                result = api_client.send_class_notification(class_id, message)
                _set_status(state.t("msg.bulk_notification"), "green")
        except Exception as ex:
            _set_status(f"Error sending notification: {ex}", "red")
        
        page.update()

    send_btn.on_click = on_send

    # ── State Sync ──
    def on_state_change(data):
        status_text.value = data.get("status_message", "")
        status_text.color = data.get("status_color", "grey")
        loading_indicator.visible = data.get("is_loading", False)
        page.update()

    ns.subscribe(on_state_change)

    # ── Initial Load ──
    load_classes()

    # ── Layout ──
    left_panel = ft.Container(
        width=450,
        content=ft.Column([
            ft.Text(state.t("header.send_notification"), size=22, weight=ft.FontWeight.BOLD),
            ft.Text(state.t("subtitle.send_notification"), size=11, color="grey"),
            ft.Divider(),
            
            ft.Text(state.t("label.mode"), size=14, weight=ft.FontWeight.W_500),
            mode_radio,
            ft.Divider(height=10, color="transparent"),
            
            ft.Text(state.t("label.target"), size=14, weight=ft.FontWeight.W_500),
            email_field,
            find_passes_btn,
            pass_dropdown,
            class_dropdown,
            ft.Divider(height=10, color="transparent"),
            
            ft.Text(state.t("label.step_message"), size=14, weight=ft.FontWeight.W_500),
            message_field,
            ft.Divider(height=10, color="transparent"),
            
            send_btn,
            ft.Container(height=10),
            loading_indicator,
            status_text,
            
        ], spacing=10, scroll="auto"),
        padding=20,
        bgcolor="white",
        border_radius=10,
        shadow=ft.BoxShadow(blur_radius=10, color="black12"),
    )

    return ft.Container(
        content=ft.Row([
            ft.VerticalDivider(width=1, color="transparent"),
            left_panel,
            ft.Container(
                expand=True,
                content=ft.Column([
                    ft.Icon("notifications_active", size=100, color="blue100"),
                    ft.Text("Notification Center", size=20, color="grey400", weight=ft.FontWeight.BOLD),
                    ft.Text("Fill in the form on the left to broadcast messages", size=12, color="grey400"),
                ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            )
        ], expand=True),
        expand=True,
        padding=20,
        bgcolor="grey50",
    )
