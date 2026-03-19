import customtkinter as ctk
import requests
import json
import threading
from datetime import datetime
import time

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class VMSClientGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("VMS - Body Camera")
        self.geometry("1280x800")

        self.gateway_ip = "192.168.1.107"
        self.gateway_port = 3000
        self.current_camera = None
        self.cameras_list = []
        self.demo_shown = False  # chỉ hiển thị thông báo demo 1 lần

        self.last_mid = None
        self.is_polling = False
        self.is_recording = False

        self.create_widgets()
        self.load_cameras_from_gateway()

    def create_widgets(self):
        header = ctk.CTkFrame(self, height=60)
        header.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(header, text="VMS - Body Camera", font=ctk.CTkFont(size=24, weight="bold")).pack(side="left", padx=20)

        # Chọn Gateway IP
        gateway_frame = ctk.CTkFrame(header)
        gateway_frame.pack(side="right", padx=20)
        ctk.CTkLabel(gateway_frame, text="Gateway IP:").pack(side="left", padx=5)
        self.gateway_entry = ctk.CTkEntry(gateway_frame, width=180)
        self.gateway_entry.insert(0, self.gateway_ip)
        self.gateway_entry.pack(side="left", padx=5)
        ctk.CTkButton(gateway_frame, text="Kết nối", fg_color="#00AA00", command=self.change_gateway).pack(side="left", padx=5)
        ctk.CTkButton(gateway_frame, text="Refresh", fg_color="#FFAA00", command=self.load_cameras_from_gateway).pack(side="left", padx=5)

        main = ctk.CTkFrame(self)
        main.pack(fill="both", expand=True, padx=10, pady=10)
        main.grid_columnconfigure(1, weight=1)

        self.left = ctk.CTkScrollableFrame(main, width=280)
        self.left.grid(row=0, column=0, sticky="nsew", padx=(0,10))

        self.center = ctk.CTkFrame(main, fg_color="#0A0A0A")
        self.center.grid(row=0, column=1, sticky="nsew", padx=10)
        self.create_live_view()

        self.right = ctk.CTkFrame(main, width=320)
        self.right.grid(row=0, column=2, sticky="nsew")
        self.create_ptt_panel()

    def change_gateway(self):
        new_ip = self.gateway_entry.get().strip()
        if new_ip:
            self.gateway_ip = new_ip
            self.load_cameras_from_gateway()

    def load_cameras_from_gateway(self):
        try:
            url = f"http://{self.gateway_ip}:{self.gateway_port}/api/cameras"
            r = requests.get(url, timeout=8)
            if r.status_code == 200:
                data = r.json()
                self.cameras_list = data.get("cameras", [])
        except Exception as e:
            print(f"[VMS] Lỗi kết nối gateway: {e}")

        # DEMO FALLBACK - BodyCamera009 luôn có sẵn
        if not self.cameras_list:
            self.cameras_list = [{
                "clientId": "BodyCamera009",
                "status": "Online (demo)",
                "area": "Khu vực test",
                "user": "Demo User"
            }]
            if not self.demo_shown:
                self.response_box.insert("end", f"[Demo] Gateway {self.gateway_ip} chưa có heartbeat thực tế → dùng BodyCamera009\n")
                self.demo_shown = True

        self.update_camera_list_ui()

    def update_camera_list_ui(self):
        for widget in self.left.winfo_children():
            widget.destroy()

        for cam in self.cameras_list:
            item = ctk.CTkFrame(self.left, height=80)
            item.pack(fill="x", pady=3, padx=5)
            name = cam["clientId"]
            ctk.CTkLabel(item, text=name, font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=10)
            ctk.CTkLabel(item, text=f"● {cam.get('status')} • {cam.get('area')}", text_color="green").pack(anchor="w", padx=10)
            ctk.CTkLabel(item, text=cam.get('user'), text_color="gray").pack(anchor="w", padx=10)
            item.bind("<Button-1>", lambda e, n=name: self.switch_camera(n))

        if self.cameras_list and not self.current_camera:
            self.switch_camera(self.cameras_list[0]["clientId"])

    def switch_camera(self, name):
        self.current_camera = name
        self.live_label.configure(text=f"Live Stream từ {name}")

    def create_live_view(self):
        self.live_label = ctk.CTkLabel(self.center, text="Live Stream từ BodyCamera009", font=ctk.CTkFont(size=20), height=380)
        self.live_label.pack(fill="both", expand=True, pady=10)

        ctrl = ctk.CTkFrame(self.center)
        ctrl.pack(fill="x", pady=10)
        ctk.CTkButton(ctrl, text="Live Action", fg_color="#00AA00", command=lambda: self.send_command("startLive")).pack(side="left", padx=5)
        ctk.CTkButton(ctrl, text="Snapshot", fg_color="#FFAA00", command=lambda: self.send_command("takeSnapshot")).pack(side="left", padx=5)
        self.rec_btn = ctk.CTkButton(ctrl, text="Record", fg_color="#AA0000", command=self.toggle_record)
        self.rec_btn.pack(side="left", padx=5)
        ctk.CTkButton(ctrl, text="SOS", fg_color="#FF0000", command=lambda: self.send_command("sendSOS")).pack(side="left", padx=5)

        self.response_box = ctk.CTkTextbox(self.center, height=280)
        self.response_box.pack(fill="both", expand=True, padx=10, pady=10)
        self.response_box.insert("end", "Response sẽ hiển thị ở đây...\n")

    def toggle_record(self):
        self.is_recording = not getattr(self, "is_recording", False)
        cmd = "startRecord" if self.is_recording else "stopRecord"
        self.rec_btn.configure(text="Stop Record" if self.is_recording else "Record")
        self.send_command(cmd)

    def create_ptt_panel(self):
        ctk.CTkLabel(self.right, text="Bộ đàm PTT", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=10)

    def send_command(self, service_id):
        if not self.current_camera:
            return
        self.response_box.delete("1.0", "end")
        self.response_box.insert("end", f"[{datetime.now().strftime('%H:%M:%S')}] [GỬI] {service_id} đến {self.current_camera} qua gateway {self.gateway_ip}\nĐang chờ response...\n")

        data = {"clientId": self.current_camera, "serviceId": service_id}
        url = f"http://{self.gateway_ip}:{self.gateway_port}/api/command"

        try:
            r = requests.post(url, json=data, timeout=12)
            self.last_mid = r.json().get("mid")
            self.is_polling = True
            threading.Thread(target=self.poll_response, daemon=True).start()
        except Exception as e:
            self.response_box.insert("end", f"[Lỗi] {str(e)}\n")

    def poll_response(self):
        url = f"http://{self.gateway_ip}:{self.gateway_port}/api/command/response/{self.last_mid}"
        while self.is_polling and self.last_mid:
            try:
                r = requests.get(url, timeout=5)
                if r.status_code == 200:
                    data = r.json()
                    if data.get("status") == "completed":
                        self.after(0, lambda resp=data.get("response"): self.show_response(resp))
                        self.is_polling = False
                        break
            except:
                pass
            time.sleep(0.4)

    def show_response(self, response):
        self.response_box.delete("1.0", "end")
        self.response_box.insert("end", json.dumps(response, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    app = VMSClientGUI()
    app.mainloop()