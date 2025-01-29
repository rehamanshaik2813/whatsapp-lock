import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from base64 import urlsafe_b64encode, urlsafe_b64decode
import random
import string
import sys
import psutil
import time
import ctypes
import cv2
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.popup import Popup
from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager, Screen

PASSWORD_FILE = 'password.txt'
KEY_FILE = 'key.txt'
EMAIL_FILE = 'email.txt'

def derive_key(password, salt):
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
        backend=default_backend()
    )
    key = kdf.derive(password.encode())
    return key

def encrypt_password(password, key):
    iv = os.urandom(16)
    cipher = Cipher(algorithms.AES(key), modes.CFB(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    encrypted_password = encryptor.update(password.encode()) + encryptor.finalize()
    return urlsafe_b64encode(iv + encrypted_password).decode()

def decrypt_password(encrypted_password, key):
    encrypted_password = urlsafe_b64decode(encrypted_password)
    iv = encrypted_password[:16]
    encrypted_password = encrypted_password[16:]
    cipher = Cipher(algorithms.AES(key), modes.CFB(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    decrypted_password = decryptor.update(encrypted_password) + decryptor.finalize()
    return decrypted_password.decode()

def generate_new_password(length=8):
    characters = string.ascii_letters + string.digits
    new_password = ''.join(random.choice(characters) for _ in range(length))
    return new_password

def capture_photo_and_send_email():
    # Capture photo using webcam
    camera = cv2.VideoCapture(0)
    ret, frame = camera.read()
    if ret:
        file_path = 'intruder.jpg'
        cv2.imwrite(file_path, frame)
        camera.release()
        cv2.destroyAllWindows()
        
        # Send email with photo attachment
        with open(EMAIL_FILE, 'r') as f:
            to_address = f.read()
        from_address = 'potthuricharanpadmasrikhar@gmail.com'
        password = 'bgyv tlgu aefs rnou'
        
        msg = MIMEMultipart()
        msg['From'] = from_address
        msg['To'] = to_address
        msg['Subject'] = 'Security Alert: Incorrect PIN Attempt'

        body = 'An incorrect PIN was entered. See the attached photo.'
        msg.attach(MIMEText(body, 'plain'))

        # Attach the photo
        attachment = open(file_path, 'rb')
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(attachment.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f'attachment; filename={file_path}')
        msg.attach(part)
        attachment.close()

        try:
            server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
            server.login(from_address, password)
            server.sendmail(from_address, to_address, msg.as_string())
            server.quit()
            print("Email sent successfully!")
        except Exception as e:
            print(f"Failed to send email: {e}")
        
        # Lock the screen
        ctypes.windll.user32.LockWorkStation()

class SetupScreen(Screen):
    def __init__(self, **kwargs):
        super(SetupScreen, self).__init__(**kwargs)
        self.layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        Window.fullscreen = True
        
        self.logo = Image(source='D:\\New folder\\Final Year Project\\egl.jpg', size_hint=(1, 5))
        self.layout.add_widget(self.logo)
        
        self.password_label = Label(text='Set Your Password:', font_size=50)
        self.layout.add_widget(self.password_label)
        
        self.password_input = TextInput(password=True, multiline=False, font_size=30)
        self.layout.add_widget(self.password_input)

        self.email_id_label = Label(text='Enter your email:', font_size=50)
        self.layout.add_widget(self.email_id_label)
        
        self.email_id_input = TextInput(multiline=False, font_size=30)
        self.layout.add_widget(self.email_id_input)
        
        self.submit_button = Button(text='Submit', font_size=50)
        self.submit_button.bind(on_press=self.submit_password)
        self.layout.add_widget(self.submit_button)
        
        self.add_widget(self.layout)
    
    def submit_password(self, instance):
        password = self.password_input.text
        email = self.email_id_input.text
        salt = os.urandom(16)
        key = derive_key(password, salt)
        encrypted_password = encrypt_password(password, key)
        
        with open(PASSWORD_FILE, 'w') as f:
            f.write(encrypted_password)
        with open(KEY_FILE, 'w') as f:
            f.write(urlsafe_b64encode(salt).decode())
        with open(EMAIL_FILE, 'w') as f:
            f.write(email)
        
        self.manager.current = 'lock_screen'

class LockScreen(Screen):
    def __init__(self, **kwargs):
        super(LockScreen, self).__init__(**kwargs)
        self.layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        Window.fullscreen = True
        
        self.logo = Image(source='D:\\New folder\\Final Year Project\\egl.jpg', size_hint=(1, 5))
        self.layout.add_widget(self.logo)
        
        self.pin_label = Label(text='Enter Pin Code:', font_size=50)
        self.layout.add_widget(self.pin_label)
        
        self.pin_input = TextInput(password=True, multiline=False, font_size=50)
        self.layout.add_widget(self.pin_input)
        
        self.submit_button = Button(text='Submit', font_size=50)
        self.submit_button.bind(on_press=self.submit_pin)
        self.layout.add_widget(self.submit_button)
        
        self.generate_button = Button(text='Generate New Password', font_size=50)
        self.generate_button.bind(on_press=self.generate_new_password)
        self.layout.add_widget(self.generate_button)
        
        self.add_widget(self.layout)
    
    def submit_pin(self, instance):
        with open(PASSWORD_FILE, 'r') as f:
            encrypted_password = f.read()
        with open(KEY_FILE, 'r') as f:
            salt = urlsafe_b64decode(f.read())
        
        pin = self.pin_input.text
        key = derive_key(pin, salt)
        try:
            decrypted_password = decrypt_password(encrypted_password, key)
            if pin == decrypted_password:
                self.show_popup('Success', 'Pin code accepted!')
                sys.exit()
                App.get_running_app().stop()
            else:
                self.show_popup('Error', 'Incorrect pin code. Try again.')
                capture_photo_and_send_email()
        except Exception as e:
            self.show_popup('Error', 'Incorrect pin code. Try again.')
            capture_photo_and_send_email()

    def generate_new_password(self, instance):
        new_password = generate_new_password()
        with open(EMAIL_FILE, 'r') as f:
            email = f.read()
        salt = os.urandom(16)
        key = derive_key(new_password, salt)
        encrypted_password = encrypt_password(new_password, key)
        
        with open(PASSWORD_FILE, 'w') as f:
            f.write(encrypted_password)
        with open(KEY_FILE, 'w') as f:
            f.write(urlsafe_b64encode(salt).decode())
        
        self.send_email('New Password Generated', f'Your new password is: {new_password}')
        self.show_popup('New Password', 'A new password has been generated and sent to your email.')

    def show_popup(self, title, message):
        content = BoxLayout(orientation='vertical')
        message_label = Label(text=message)
        content.add_widget(message_label)
        close_button = Button(text='Close')
        content.add_widget(close_button)
        
        popup = Popup(title=title, content=content, size_hint=(0.8, 0.5))
        close_button.bind(on_press=popup.dismiss)
        popup.open()
    
    def send_email(self, subject, message):
        with open(EMAIL_FILE, 'r') as f:
            to_address = f.read()
        from_address = 'potthuricharanpadmasrikhar@gmail.com'
        password = 'bgyv tlgu aefs rnou'
        
        msg = MIMEText(message)
        msg['Subject'] = subject
        msg['From'] = from_address
        msg['To'] = to_address
        
        try:
            server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
            server.login(from_address, password)
            server.sendmail(from_address, to_address, msg.as_string())
            server.quit()
        except Exception as e:
            print(f"Failed to send email: {e}")

class PinEntryApp(App):
    def build(self):
        self.sm = ScreenManager()
        
        if not os.path.exists(PASSWORD_FILE):
            self.sm.add_widget(SetupScreen(name='setup_screen'))
        self.sm.add_widget(LockScreen(name='lock_screen'))
        
        if os.path.exists(PASSWORD_FILE):
            self.sm.current = 'lock_screen'
        else:
            self.sm.current = 'setup_screen'
        
        return self.sm

if __name__ == '__main__':
    # Monitoring loop for checking WhatsApp
    while True:
        apps = [p.name() for p in psutil.process_iter()]
        if 'WhatsApp.exe' in apps:
            PinEntryApp().run()
        time.sleep(5)
