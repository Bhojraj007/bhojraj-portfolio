import re
from urllib.parse import urlparse
from django.utils import timezone
from .models import VisitorLog

class VisitorTelemetryMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Only track safe GET page views, skip static/media/admin/ajax polling
        path = request.path
        if (request.method == 'GET' and 
            not path.startswith('/static/') and 
            not path.startswith('/media/') and 
            not path.startswith('/admin/') and 
            not path.startswith('/favicon.') and 
            not path.startswith('/robots.txt') and 
            not path.startswith('/sitemap.xml')):
            
            try:
                self.record_telemetry(request, path)
            except Exception:
                pass

        return response

    def record_telemetry(self, request, path):
        # Extract IP
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '')

        # Session key
        if not request.session.session_key:
            request.session.save()
        session_key = request.session.session_key or ''

        # User Agent & Device parsing
        ua = request.META.get('HTTP_USER_AGENT', '')
        device_type = 'Desktop'
        ua_lower = ua.lower()
        if 'bot' in ua_lower or 'crawler' in ua_lower or 'spider' in ua_lower:
            device_type = 'Search Bot / Crawler'
        elif 'mobile' in ua_lower or 'android' in ua_lower or 'iphone' in ua_lower:
            device_type = 'Mobile Phone'
        elif 'tablet' in ua_lower or 'ipad' in ua_lower:
            device_type = 'Tablet'

        # Browser
        browser = 'Other'
        if 'edg' in ua_lower:
            browser = 'Microsoft Edge'
        elif 'chrome' in ua_lower and 'safari' in ua_lower:
            browser = 'Google Chrome'
        elif 'safari' in ua_lower and 'chrome' not in ua_lower:
            browser = 'Apple Safari'
        elif 'firefox' in ua_lower:
            browser = 'Mozilla Firefox'
        elif 'opera' in ua_lower or 'opr' in ua_lower:
            browser = 'Opera'

        # Operating System
        os_name = 'Other'
        if 'windows' in ua_lower:
            os_name = 'Windows OS'
        elif 'macintosh' in ua_lower or 'mac os' in ua_lower:
            os_name = 'macOS'
        elif 'android' in ua_lower:
            os_name = 'Android'
        elif 'iphone' in ua_lower or 'ipad' in ua_lower:
            os_name = 'iOS'
        elif 'linux' in ua_lower:
            os_name = 'Linux'

        # Referrer
        referrer = request.META.get('HTTP_REFERER', '')
        referrer_domain = ''
        if referrer:
            try:
                parsed = urlparse(referrer)
                referrer_domain = parsed.netloc or referrer[:50]
                if 'google' in referrer_domain:
                    referrer_domain = 'Google Search'
                elif 'linkedin' in referrer_domain:
                    referrer_domain = 'LinkedIn'
                elif 'facebook' in referrer_domain or 'fb.me' in referrer_domain:
                    referrer_domain = 'Facebook'
                elif 'twitter' in referrer_domain or 't.co' in referrer_domain or 'x.com' in referrer_domain:
                    referrer_domain = 'Twitter / X'
                elif 'github' in referrer_domain:
                    referrer_domain = 'GitHub'
            except Exception:
                referrer_domain = referrer[:50]
        else:
            referrer_domain = 'Direct / Bookmark'

        # Country from Cloudflare / proxy headers
        country = (
            request.META.get('HTTP_CF_IPCOUNTRY') or 
            request.META.get('HTTP_X_COUNTRY_CODE') or 
            request.META.get('GEOIP_COUNTRY_NAME') or 
            'Nepal'
        )
        city = request.META.get('HTTP_CF_IPCITY') or request.META.get('GEOIP_CITY') or ''

        # Check existing lead identity stored in session
        lead_name = request.session.get('visitor_lead_name', '')
        lead_email = request.session.get('visitor_lead_email', '')
        lead_phone = request.session.get('visitor_lead_phone', '')
        is_lead = bool(lead_name or lead_email)

        # Count visits
        prior_visits = VisitorLog.objects.filter(session_key=session_key).count() + 1

        VisitorLog.objects.create(
            ip_address=ip[:60],
            session_key=session_key[:100],
            path=path[:255],
            referrer=referrer[:500],
            referrer_domain=referrer_domain[:150],
            user_agent=ua,
            device_type=device_type,
            browser=browser,
            os=os_name,
            country=country[:100],
            city=city[:100],
            visitor_name=lead_name or None,
            visitor_email=lead_email or None,
            visitor_phone=lead_phone or None,
            is_lead=is_lead,
            visit_count=prior_visits
        )
