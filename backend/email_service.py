import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from url_detection import get_frontend_base_url, get_environment_info
from typing import Optional

class EmailService:
    def __init__(self):
        # Gmail SMTP configuration
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587  # TLS port
        self.sender_email = "tikschile@gmail.com"
        
        # Get password from environment
        self.sender_password = os.environ.get('EMAIL_PASSWORD', '')
        
        if not self.sender_password:
            print("⚠️ EMAIL_PASSWORD not configured - emails will not be sent")
        else:
            print(f"✅ Email service configured for {self.sender_email} via {self.smtp_server}:{self.smtp_port}")
        
    async def send_client_invitation(self, client_email: str, client_name: str, landing_url: str) -> bool:
        """Send invitation email to client with their landing page URL"""
        
        if not self.sender_password:
            print(f"❌ Cannot send email - EMAIL_PASSWORD not configured")
            return False
            
        try:
            msg = MIMEMultipart()
            msg['From'] = f"TIKS Platform <{self.sender_email}>"
            msg['To'] = client_email
            msg['Subject'] = f"🤖 Tu Asistente WhatsApp está listo - {client_name}"
            
            # HTML email template
            html_body = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Tu Asistente WhatsApp</title>
                <style>
                    body {{
                        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                        line-height: 1.6;
                        color: #333;
                        margin: 0;
                        padding: 0;
                        background-color: #f4f4f4;
                    }}
                    .container {{
                        max-width: 600px;
                        margin: 0 auto;
                        background: white;
                        border-radius: 10px;
                        overflow: hidden;
                        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                    }}
                    .header {{
                        background: linear-gradient(135deg, #25D366, #128C7E);
                        padding: 30px 20px;
                        text-align: center;
                        color: white;
                    }}
                    .header h1 {{
                        margin: 0;
                        font-size: 28px;
                        font-weight: 300;
                    }}
                    .content {{
                        padding: 40px 30px;
                    }}
                    .greeting {{
                        font-size: 18px;
                        margin-bottom: 20px;
                        color: #2c3e50;
                    }}
                    .message {{
                        font-size: 16px;
                        margin-bottom: 30px;
                        color: #555;
                    }}
                    .cta-button {{
                        display: inline-block;
                        background: linear-gradient(135deg, #25D366, #128C7E);
                        color: white;
                        padding: 15px 30px;
                        text-decoration: none;
                        border-radius: 50px;
                        font-weight: 600;
                        font-size: 16px;
                        margin: 20px 0;
                        transition: transform 0.2s ease;
                    }}
                    .cta-button:hover {{
                        transform: translateY(-2px);
                        box-shadow: 0 6px 12px rgba(37, 211, 102, 0.3);
                    }}
                    .instructions {{
                        background: #f8f9fa;
                        padding: 20px;
                        border-radius: 8px;
                        margin: 20px 0;
                        border-left: 4px solid #25D366;
                    }}
                    .instructions h3 {{
                        margin-top: 0;
                        color: #25D366;
                    }}
                    .footer {{
                        background: #f8f9fa;
                        padding: 20px;
                        text-align: center;
                        font-size: 14px;
                        color: #666;
                    }}
                    .emoji {{
                        font-size: 24px;
                        margin: 0 5px;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1><span class="emoji">🤖</span> Tu Asistente WhatsApp</h1>
                        <p>¡Ya está listo para usar!</p>
                    </div>
                    
                    <div class="content">
                        <div class="greeting">
                            ¡Hola <strong>{client_name}</strong>! 👋
                        </div>
                        
                        <div class="message">
                            Tu asistente inteligente de WhatsApp ha sido configurado exitosamente y está listo para comenzar a atender a tus clientes automáticamente.
                        </div>
                        
                        <div style="text-align: center;">
                            <a href="{landing_url}" class="cta-button">
                                <span class="emoji">📱</span> Activar mi Asistente
                            </a>
                        </div>
                        
                        <div class="instructions">
                            <h3>📋 Instrucciones de activación:</h3>
                            <ol>
                                <li>Haz clic en el botón de arriba para acceder a tu panel personal</li>
                                <li><strong>Espera 1-2 minutos</strong> mientras se genera tu código QR personalizado</li>
                                <li>Abre WhatsApp en tu teléfono → Menú → Dispositivos vinculados</li>
                                <li>Toca "Vincular un dispositivo" y escanea el código QR</li>
                                <li>¡Tu asistente comenzará a responder automáticamente!</li>
                            </ol>
                        </div>
                        
                        <div style="background: #fff3cd; border: 1px solid #ffeaa7; border-radius: 5px; padding: 15px; margin: 20px 0;">
                            <strong>⏱️ Importante:</strong> El código QR puede tardar 1-2 minutos en aparecer la primera vez. Si no aparece inmediatamente, simplemente espera un momento y actualiza la página.
                        </div>
                        
                        <div style="background: #e8f5e8; padding: 15px; border-radius: 5px; margin: 20px 0;">
                            <strong>🔒 Importante:</strong> Solo se puede conectar un teléfono por asistente. Una vez conectado, el código QR no funcionará en otros dispositivos.
                        </div>
                        
                        <div style="text-align: center; margin-top: 30px;">
                            <p style="color: #666; font-size: 14px;">
                                ¿Necesitas ayuda? <br>
                                Contáctanos: <a href="mailto:tikschile@gmail.com" style="color: #25D366;">tikschile@gmail.com</a>
                            </p>
                        </div>
                    </div>
                    
                    <div class="footer">
                        <p>Este mensaje fue enviado desde TIKS - Plataforma de Asistentes WhatsApp</p>
                        <p style="font-size: 12px;">Si no solicitaste este servicio, puedes ignorar este email.</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            msg.attach(MIMEText(html_body, 'html'))
            
            # Send email using Bluehosting SMTP
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()  # Enable TLS encryption
            
            # Better error handling for SMTP authentication
            try:
                server.login(self.sender_email, self.sender_password)
            except smtplib.SMTPAuthenticationError as auth_error:
                print(f"❌ SMTP Authentication failed: {auth_error}")
                print(f"   Server: {self.smtp_server}:{self.smtp_port}")
                print(f"   User: {self.sender_email}")
                print("   Check: Password, server settings, or contact hosting provider")
                server.quit()
                return False
            
            text = msg.as_string()
            server.sendmail(self.sender_email, client_email, text)
            server.quit()
            
            print(f"✅ Email sent successfully to {client_email} from {self.sender_email}")
            return True
            
        except Exception as e:
            print(f"❌ Error sending email to {client_email}: {str(e)}")
            return False

# Global email service instance
email_service = EmailService()