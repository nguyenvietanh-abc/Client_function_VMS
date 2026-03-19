import customtkinter as ctk
import requests
import json
import threading
from datetime import datetime
import paho.mqtt.client as mqtt

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class BodyCameraApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Body Camera - Giả lập")
        self.geometry("420x720")
        self.resizable(False, False)
        
        self.HTTP_BASE = "http://192.168.1.XXX:3000/api"   # ←←← THAY IP PC16
        self.BROKER = "192.168.1.XXX"
        self.device_id = "BodyCamera009"          # ←←← MẶC ĐỊNH ĐÚNG VỚI VMS
        self.gateway_id = "GW001"
        self.mqtt_client = None
        self.current_frame = None
        
        self.show_activate_screen()

    # ====================== MQTT - DEVICE RESPONSE + LOG TERMINAL ======================
    def connect_mqtt(self):
        if self.mqtt_client: return
        self.mqtt_client = mqtt.Client(client_id=f"BodyCam_{self.device_id}")
        self.mqtt_client.on_connect = self.on_mqtt_connect
        self.mqtt_client.on_message = self.on_mqtt_message
        self.mqtt_client.connect(self.BROKER, 1883, 60)
        threading.Thread(target=self.mqtt_client.loop_forever, daemon=True).start()
        print(f"[{datetime.now().strftime('%H:%M:%S')}] [Body Camera] MQTT Connected")

#subcribe topic 1 get commamd
    def on_mqtt_connect(self, client, userdata, flags, rc):
        topic = f"/v1/bodycam/dev/{self.gateway_id}/{self.device_id}/command"
        client.subscribe(topic)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] [Body Camera] Subscribed: {topic}")

#Topic 2 get command && publish response
    def on_mqtt_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode())
            service_id = payload.get("serviceId")
            mid = payload.get("mid")
            client_id = payload.get("clientId")
            
            print(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] [Body Camera nhận lệnh] serviceId = {service_id} | mid = {mid}")
#Create response
            response = {
                "clientId": client_id,
                "serviceId": service_id,
                "eventTime": datetime.now().strftime("%Y%m%dT%H%M%SZ"),
                "mid": mid,
                "errCode": 0,
                "paras": {"deviceTime": datetime.now().strftime("%Y%m%dT%H%M%SZ"), "message": f"Device auto-response: {service_id}"}
            }
#publish response to topic (command response)
            response_topic = f"/v1/devices/{self.gateway_id}/commandResponse"
            self.mqtt_client.publish(response_topic, json.dumps(response), qos=1)
            print(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] [Body Camera gửi response] → {response_topic} | mid = {mid}")
        except Exception as e:
            print(f"[Lỗi MQTT] {e}")

    # ====================== Mode monitor ======================
    def clear_screen(self):
        if self.current_frame: self.current_frame.destroy()

    def show_activate_screen(self):
        self.clear_screen()
        frame = ctk.CTkFrame(self, corner_radius=0)
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        self.current_frame = frame
        
        ctk.CTkLabel(frame, text="Kích hoạt thiết bị", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=30)
        ctk.CTkLabel(frame, text="Lưu ý: Phải dùng tên BodyCamera009 để khớp với VMS Client", text_color="yellow").pack(pady=5)
        
        ctk.CTkLabel(frame, text="Tên thiết bị").pack(anchor="w", padx=10)
        self.name_entry = ctk.CTkEntry(frame, placeholder_text="BodyCamera009")
        self.name_entry.pack(pady=5, padx=10, fill="x")
        
        ctk.CTkLabel(frame, text="Địa chỉ IP Gateway").pack(anchor="w", padx=10)
        self.ip_entry = ctk.CTkEntry(frame, placeholder_text="192.168.1.XXX")
        self.ip_entry.pack(pady=5, padx=10, fill="x")
        
        ctk.CTkLabel(frame, text="Port Gateway").pack(anchor="w", padx=10)
        self.port_entry = ctk.CTkEntry(frame, placeholder_text="8080")
        self.port_entry.pack(pady=5, padx=10, fill="x")
        
        ctk.CTkButton(frame, text="Kích hoạt thiết bị", fg_color="#4B9CFF", height=50,
                      command=self.activate_device).pack(pady=40, padx=20, fill="x")

    def activate_device(self):
        self.device_id = self.name_entry.get() or "BodyCamera009"   # ←←← BẮT BUỘC KHỚP VỚI VMS
        gw_ip = self.ip_entry.get() or "192.168.1.XXX"
        self.BROKER = gw_ip
        self.HTTP_BASE = f"http://{gw_ip}:3000/api"
        print(f"[Activate OK] DeviceID = {self.device_id}")
        self.connect_mqtt()
        self.show_register_screen()

    # (Phần đăng ký, đăng nhập, PTT giữ nguyên như trước - bạn có thể copy từ file cũ nếu cần)

    def show_register_screen(self):
        self.clear_screen()
        frame = ctk.CTkFrame(self, corner_radius=0)
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        self.current_frame = frame
        ctk.CTkLabel(frame, text="Đăng ký tài khoản", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=30)
        # ... (các entry giống code cũ)
        ctk.CTkButton(frame, text="Đăng ký", fg_color="#00AA00", height=50, command=self.register_user).pack(pady=30, fill="x")

    def register_user(self):
        print("[Register OK]")
        self.show_login_screen()

    def show_login_screen(self):
        self.clear_screen()
        frame = ctk.CTkFrame(self, corner_radius=0)
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        self.current_frame = frame
        ctk.CTkLabel(frame, text="Đăng nhập và kích hoạt phiên", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=20)
        ctk.CTkButton(frame, text="Đăng nhập", fg_color="#00AA00", height=50, command=self.login_user).pack(pady=30, fill="x")

    def login_user(self):
        print("[Login OK]")
        self.show_main_screen()

    def show_main_screen(self):
        self.clear_screen()
        frame = ctk.CTkFrame(self, fg_color="#0A0A0A")
        frame.pack(fill="both", expand=True)
        self.current_frame = frame
        ctk.CTkLabel(frame, text="PTT - Gọi nhóm", font=ctk.CTkFont(size=18)).pack(pady=(300,10))
        ctk.CTkButton(frame, text="☎ PTT - Gọi nhóm", fg_color="#FF6600", height=70).pack(pady=20, padx=40, fill="x")

if __name__ == "__main__":
    app = BodyCameraApp()
    app.mainloop()
