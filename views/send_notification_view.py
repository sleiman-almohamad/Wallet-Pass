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
            ft.Radio(value="single", label=state.t("mode.single") if hasattr(state, "t") else "Single Pass"),
            ft.Radio(value="template", label=state.t("mode.template") if hasattr(state, "t") else "Template/Class"),
        ], spacing=20),
        value=ns.get("mode") or "single",
    )

    class_dropdown = ft.Dropdown(
        label=state.t("label.select_template") if hasattr(state, "t") else "Select Template",
        hint_text="Choose a template",
        width=400,
        options=[],
        visible=False,
    )

    # ✅ التعديل الأول: تغيير حقل الإيميل ليصبح حقل بحث بالاسم
    search_holder_field = ft.TextField(
        label=state.t("label.search_holder") if hasattr(state, "t") else "Search by Holder Name",
        hint_text="e.g., Sleiman",
        width=400,
        visible=True,
        prefix_icon="search",
        on_submit=lambda e: on_find_passes(e) # للبحث عند ضغط Enter
    )

    find_passes_btn = ft.ElevatedButton(
        state.t("btn.find_passes") if hasattr(state, "t") else "Find Passes",
        icon="search",
        width=400,
        visible=True,
    )

    pass_dropdown = ft.Dropdown(
        label=state.t("label.select_pass") if hasattr(state, "t") else "Select Pass",
        hint_text="Choose a pass",
        width=400,
        visible=True,
        options=[],
    )

    message_field = ft.TextField(
        label=state.t("label.message") if hasattr(state, "t") else "Notification Message",
        hint_text="Enter your message here...",
        multiline=True,
        min_lines=3,
        max_lines=5,
        width=400,
    )

    status_text = ft.Text(ns.get("status_message"), color=ns.get("status_color"), size=12)
    loading_indicator = ft.ProgressBar(width=400, visible=ns.get("is_loading"), color="blue")

    send_btn = ft.ElevatedButton(
        state.t("btn.send_notification") if hasattr(state, "t") else "Send Notification",
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
            current_val = class_dropdown.value
            
            # ✅ تطبيق الخدعة لإخفاء الـ Prefix من اسم الكلاس
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
            _set_status(f"Error loading templates: {e}", "red")

    # ── Event Handlers ──
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

    # ✅ التعديل الثاني: تابع البحث الذكي بالاسم (Holder Name)
    def on_find_passes(e):
        search_query = search_holder_field.value.strip().lower()
        if not search_query:
            _set_status("⚠️ Please enter a name to search", "orange")
            page.update()
            return

        ns.update("is_loading", True)
        page.update()

        try:
            # جلب كل البطاقات وفلترتها محلياً لتسريع العملية
            all_passes = api_client.get_passes() if api_client else []
            matching_passes = [
                p for p in all_passes 
                if search_query in str(p.get("holder_name", "")).lower()
            ]

            if not matching_passes:
                _set_status(f"❌ No passes found matching '{search_query}'.", "orange")
                pass_dropdown.options = []
                pass_dropdown.value = None
            else:
                # عرض الأسماء بوضوح بدون الـ Prefix المعقد
                pass_dropdown.options = [
                    ft.dropdown.Option(
                        key=str(p.get("object_id", "")), 
                        text=f"{p.get('holder_name', 'Unknown')} ({str(p.get('class_id', 'Unknown Template')).split('.')[-1]})"
                    )
                    for p in matching_passes if p.get("object_id")
                ]
                # اختيار أول نتيجة تلقائياً
                pass_dropdown.value = str(matching_passes[0].get("object_id", ""))
                _set_status(f"✅ Found {len(matching_passes)} pass(es).", "green")
            
            ns.update_multiple({
                "passes_found": matching_passes,
                "is_loading": False
            })
        except Exception as ex:
            import traceback; traceback.print_exc()
            _set_status(f"❌ Error finding passes: {ex}", "red")
        
        page.update()

    find_passes_btn.on_click = on_find_passes

    def on_send(e):
        mode = ns.get("mode")
        message = message_field.value.strip()
        
        if not message:
            _set_status("⚠️ Please enter a message to send", "red")
            return

        ns.update("is_loading", True)
        page.update()

        try:
            if mode == "single":
                pass_id = pass_dropdown.value
                if not pass_id:
                    _set_status("❌ Please select a pass first", "red")
                    return
                
                result = api_client.send_pass_notification(pass_id, message)
                _set_status("✅ Notification sent successfully to the pass!", "green")
            else:
                class_id = class_dropdown.value
                if not class_id:
                    _set_status("❌ Please select a template first", "red")
                    return
                
                result = api_client.send_class_notification(class_id, message)
                _set_status("✅ Bulk notification sent successfully to all template holders!", "green")
        except Exception as ex:
            _set_status(f"❌ Error sending notification: {ex}", "red")
        
        page.update()

    send_btn.on_click = on_send

    # ── State Sync ──
    def on_state_change(data):
        status_text.value = data.get("status_message", "")
        status_text.color = data.get("status_color", "grey")
        loading_indicator.visible = data.get("is_loading", False)
        page.update()

    ns.subscribe(on_state_change)

    def refresh_send_notification():
        load_classes()
        if mode_radio.value == "single" and search_holder_field.value and search_holder_field.value.strip():
            on_find_passes(None)

    state.register_refresh_callback("send_notification_list", refresh_send_notification)

    # ── Initial Load ──
    load_classes()

    # ── Layout ──
    left_panel = ft.Container(
        width=450,
        content=ft.Column([
            ft.Text(state.t("header.send_notification") if hasattr(state, "t") else "Send Notification", size=22, weight=ft.FontWeight.BOLD),
            ft.Text(state.t("subtitle.send_notification") if hasattr(state, "t") else "Broadcast messages to users", size=11, color="grey"),
            ft.Divider(),
            
            ft.Text(state.t("label.mode") if hasattr(state, "t") else "Select Mode:", size=14, weight=ft.FontWeight.W_500),
            mode_radio,
            ft.Divider(height=10, color="transparent"),
            
            ft.Text(state.t("label.target") if hasattr(state, "t") else "Select Target:", size=14, weight=ft.FontWeight.W_500),
            search_holder_field,  # ✅ تم وضع حقل البحث هنا
            find_passes_btn,
            pass_dropdown,
            class_dropdown,
            ft.Divider(height=10, color="transparent"),
            
            ft.Text(state.t("label.step_message") if hasattr(state, "t") else "Enter Message:", size=14, weight=ft.FontWeight.W_500),
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