import threading
from django.conf import settings
from django.core.mail import send_mail
from django.utils.html import strip_tags

def send_lead_email_notification_async(contact_obj):
    """
    Sends an instant HTML notification to the site owner's Gmail in a background thread 
    so the web page response is instantaneous.
    """
    def _send():
        try:
            if not getattr(settings, 'EMAIL_HOST_USER', None) or not getattr(settings, 'EMAIL_HOST_PASSWORD', None):
                # SMTP credentials not yet provided in .env
                return

            recipient = getattr(settings, 'NOTIFICATION_RECIPIENT_EMAIL', 'upadhayaybhojraj@gmail.com')
            subject = f"⚡ [NEW LEAD] {contact_obj.inquiry_type} from {contact_obj.name}"
            
            clean_phone = (contact_obj.phone or '').replace('+', '').replace(' ', '').replace('-', '')
            wa_link = f"https://wa.me/{clean_phone}" if clean_phone else None

            html_message = f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #0c1411; color: #f1f5f9; padding: 20px; }}
    .card {{ max-width: 600px; margin: 0 auto; background-color: #121A17; border: 2px solid #F9CD05; border-radius: 16px; overflow: hidden; box-shadow: 0 10px 30px rgba(0,0,0,0.5); }}
    .header {{ background: linear-gradient(135deg, #1A2421, #0E1613); padding: 24px; text-align: center; border-bottom: 2px solid rgba(249, 205, 5, 0.4); }}
    .header h2 {{ color: #F9CD05; margin: 0; font-size: 22px; letter-spacing: 1px; }}
    .badge {{ display: inline-block; background: rgba(249, 205, 5, 0.15); color: #F9CD05; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: bold; margin-top: 8px; border: 1px solid rgba(249, 205, 5, 0.4); }}
    .body {{ padding: 24px; line-height: 1.6; }}
    .row {{ margin-bottom: 14px; border-bottom: 1px solid rgba(255,255,255,0.06); padding-bottom: 10px; }}
    .label {{ color: #94a3b8; font-size: 12px; text-transform: uppercase; font-weight: bold; display: block; margin-bottom: 3px; }}
    .value {{ color: #ffffff; font-size: 15px; font-weight: 600; }}
    .msg-box {{ background: rgba(0,0,0,0.3); border-left: 3px solid #10B981; padding: 14px; border-radius: 8px; color: #e2e8f0; font-style: italic; margin-top: 8px; }}
    .actions {{ padding: 20px 24px; background: #0E1613; text-align: center; border-top: 1px solid rgba(255,255,255,0.08); }}
    .btn {{ display: inline-block; padding: 10px 20px; margin: 6px; border-radius: 8px; text-decoration: none; font-weight: bold; font-size: 14px; }}
    .btn-reply {{ background: #F9CD05; color: #121A17; }}
    .btn-wa {{ background: #10B981; color: #ffffff; }}
    .footer {{ text-align: center; padding: 14px; font-size: 11px; color: #64748b; }}
  </style>
</head>
<body>
  <div class="card">
    <div class="header">
      <h2>&lt; BHOJ RAJ /&gt; LEAD ALERT</h2>
      <div class="badge">{contact_obj.inquiry_type}</div>
    </div>
    <div class="body">
      <div class="row">
        <span class="label">Client / Sender Name</span>
        <span class="value">{contact_obj.name}</span>
      </div>
      <div class="row">
        <span class="label">Email Address</span>
        <span class="value"><a href="mailto:{contact_obj.email}" style="color: #38bdf8; text-decoration: none;">{contact_obj.email}</a></span>
      </div>
      <div class="row">
        <span class="label">Phone / WhatsApp</span>
        <span class="value">{contact_obj.phone or 'Not Provided'}</span>
      </div>
      <div class="row">
        <span class="label">Transmission Message</span>
        <div class="msg-box">{contact_obj.message}</div>
      </div>
    </div>
    <div class="actions">
      <a href="mailto:{contact_obj.email}?subject=Re: {contact_obj.inquiry_type} - Bhojraj Upadhayay" class="btn btn-reply">✉️ Reply via Email</a>
      {"<a href='" + wa_link + "' class='btn btn-wa' target='_blank'>💬 Chat on WhatsApp</a>" if wa_link else ""}
    </div>
    <div class="footer">
      Transmission received from rajabhoj.com.np &bull; Instant Telemetry Dispatch
    </div>
  </div>
</body>
</html>
"""
            plain_message = f"""
NEW LEAD INQUIRY: {contact_obj.inquiry_type}
Name: {contact_obj.name}
Email: {contact_obj.email}
Phone: {contact_obj.phone or 'N/A'}
Message: {contact_obj.message}

Reply to: {contact_obj.email}
            """

            send_mail(
                subject=subject,
                message=plain_message,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@rajabhoj.com.np'),
                recipient_list=[recipient],
                html_message=html_message,
                fail_silently=True
            )
        except Exception:
            pass

    # Launch in background thread so client response has zero latency
    t = threading.Thread(target=_send)
    t.daemon = True
    t.start()
