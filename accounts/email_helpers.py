"""Password reset email delivery: Resend API (preferred if configured) or Django SMTP."""

from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request

from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


def send_password_reset_otp_email(to_address: str, subject: str, body: str) -> None:
    """
    Send OTP email. If RESEND_API_KEY is set, uses Resend's HTTP API (no Gmail SMTP).
    Otherwise uses Django's SMTP (EMAIL_* settings).
    """
    key = getattr(settings, 'RESEND_API_KEY', '') or ''
    if key:
        _send_via_resend(to_address, subject, body, key)
        return
    send_mail(
        subject,
        body,
        settings.DEFAULT_FROM_EMAIL,
        [to_address],
        fail_silently=False,
    )


def _send_via_resend(to_address: str, subject: str, body: str, api_key: str) -> None:
    from_email = getattr(settings, 'RESEND_FROM_EMAIL', 'onboarding@resend.dev')
    payload = {
        'from': from_email,
        'to': [to_address],
        'subject': subject,
        'text': body,
    }
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        'https://api.resend.com/emails',
        data=data,
        headers={
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
        },
        method='POST',
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            if resp.status not in (200, 201):
                raise RuntimeError(f'Resend HTTP {resp.status}')
    except urllib.error.HTTPError as e:
        detail = e.read().decode('utf-8', errors='replace')
        logger.error('Resend HTTP %s: %s', e.code, detail)
        raise RuntimeError(f'Resend error {e.code}: {detail}') from e


def delivery_error_user_message(exc: Exception) -> str:
    """User-visible text when send_password_reset_otp_email fails."""
    text = str(exc).lower()
    if 'resend' in text or '401' in text or '403' in text:
        return (
            'Resend rejected the request. Create an API key at https://resend.com, set RESEND_API_KEY '
            'in .env, and verify your sending domain or use onboarding@resend.dev for testing.'
        )
    if '422' in text or 'validation' in text:
        return (
            'Resend could not send (invalid from/to). Check RESEND_FROM_EMAIL and recipient address.'
        )
    return smtp_error_user_message(exc)


def smtp_error_user_message(exc: Exception) -> str:
    """
    Map low-level SMTP failures to actionable text. Gmail 535 is almost always
    wrong password type (need App Password) or copy/paste issues.
    """
    text = str(exc).lower()
    code = getattr(exc, 'smtp_code', None)
    if code == 535 or '535' in text or 'username and password not accepted' in text:
        return (
            'Gmail rejected the email login. Use a 16-character App Password, not your normal '
            'Gmail password. In your Google Account: Security → 2-Step Verification (turn it on) → '
            'App passwords → create one for Mail, paste it into EMAIL_HOST_PASSWORD in .env '
            'with no spaces. Set DEFAULT_FROM_EMAIL to the same address as EMAIL_HOST_USER. '
            'Alternatively set RESEND_API_KEY in .env to use Resend instead of Gmail SMTP. '
            'Details: https://support.google.com/mail/?p=BadCredentials'
        )
    if '534' in text or 'authentication mechanism' in text:
        return (
            'The mail server rejected the authentication method. Check EMAIL_HOST, port '
            '(587 + TLS, or 465 + SSL), and your App Password.'
        )
    if 'connection' in text and 'refused' in text:
        return (
            'Could not reach the mail server. Check your network, firewall, and EMAIL_HOST / port.'
        )
    return (
        'Could not send email. Set RESEND_API_KEY for Resend, or verify EMAIL_HOST_USER, '
        'EMAIL_HOST_PASSWORD, and DEFAULT_FROM_EMAIL for SMTP.'
    )
