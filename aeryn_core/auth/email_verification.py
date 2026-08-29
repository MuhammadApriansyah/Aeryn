#!/usr/bin/env python3
"""
V41.0 — Email Verification & Password Reset.
Sistem verifikasi email dan reset password dengan token.
"""

import os
import uuid
import secrets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Dict
from datetime import datetime, timedelta

from aeryn_core.database.neon_db import get_neon
from aeryn_core.utils.logger import info, warn, error

# SMTP Config (dari environment)
SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASS = os.environ.get("SMTP_PASS", "")
SMTP_FROM = os.environ.get("SMTP_FROM", "noreply@aeryn.ai")


class EmailVerification:
    """Sistem verifikasi email."""
    
    def __init__(self):
        self.db = get_neon()
        self._init_table()
    
    def _init_table(self):
        """Inisialisasi tabel."""
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS email_verifications (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                email TEXT NOT NULL,
                token TEXT UNIQUE NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                verified_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );
        """)
        self.db.execute("""
            CREATE INDEX IF NOT EXISTS idx_email_ver_token ON email_verifications(token);
        """)
    
    def create_token(self, user_id: str, email: str) -> str:
        """Buat token verifikasi."""
        token = secrets.token_hex(32)
        expires_at = datetime.now() + timedelta(hours=24)
        
        self.db.insert('email_verifications', {
            'id': uuid.uuid4().hex,
            'user_id': user_id,
            'email': email,
            'token': token,
            'expires_at': expires_at,
        })
        
        return token
    
    def verify_token(self, token: str) -> Optional[Dict]:
        """Verifikasi token dan return user info."""
        result = self.db.fetchone("""
            SELECT id, user_id, email, expires_at
            FROM email_verifications
            WHERE token = %s AND verified_at IS NULL
        """, (token,))
        
        if not result:
            return None
        
        if result['expires_at'] < datetime.now():
            return None
        
        # Mark as verified
        self.db.execute("""
            UPDATE email_verifications SET verified_at = %s WHERE token = %s
        """, (datetime.now(), token))
        
        # Update user
        self.db.execute("""
            UPDATE users SET email_verified = 1 WHERE id = %s
        """, (result['user_id'],))
        
        return {
            "user_id": result['user_id'],
            "email": result['email'],
        }
    
    def send_verification_email(self, email: str, token: str) -> bool:
        """Kirim email verifikasi."""
        if not SMTP_USER or not SMTP_PASS:
            warn("SMTP not configured, skipping email")
            return False
        
        try:
            verification_link = f"https://aeryn.ai/verify?token={token}"
            
            msg = MIMEMultipart()
            msg['From'] = SMTP_FROM
            msg['To'] = email
            msg['Subject'] = "Verify your Aeryn account"
            
            body = f"""
            Hello,
            
            Please verify your email by clicking the link below:
            
            {verification_link}
            
            This link expires in 24 hours.
            
            If you didn't create an account, please ignore this email.
            
            Best,
            Aeryn Team
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
                server.starttls()
                server.login(SMTP_USER, SMTP_PASS)
                server.send_message(msg)
            
            info("Verification email sent", email=email)
            return True
            
        except Exception as e:
            error("Failed to send verification email", email=email, error=str(e))
            return False


class PasswordReset:
    """Sistem reset password."""
    
    def __init__(self):
        self.db = get_neon()
        self._init_table()
    
    def _init_table(self):
        """Inisialisasi tabel."""
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS password_resets (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                email TEXT NOT NULL,
                token TEXT UNIQUE NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                used_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );
        """)
        self.db.execute("""
            CREATE INDEX IF NOT EXISTS idx_pw_reset_token ON password_resets(token);
        """)
    
    def create_token(self, user_id: str, email: str) -> str:
        """Buat token reset password."""
        token = secrets.token_hex(32)
        expires_at = datetime.now() + timedelta(hours=1)
        
        self.db.insert('password_resets', {
            'id': uuid.uuid4().hex,
            'user_id': user_id,
            'email': email,
            'token': token,
            'expires_at': expires_at,
        })
        
        return token
    
    def verify_token(self, token: str) -> Optional[Dict]:
        """Verifikasi token reset."""
        result = self.db.fetchone("""
            SELECT id, user_id, email, expires_at
            FROM password_resets
            WHERE token = %s AND used_at IS NULL
        """, (token,))
        
        if not result:
            return None
        
        if result['expires_at'] < datetime.now():
            return None
        
        return {
            "reset_id": result['id'],
            "user_id": result['user_id'],
            "email": result['email'],
        }
    
    def mark_used(self, token: str):
        """Tandai token sudah dipakai."""
        self.db.execute("""
            UPDATE password_resets SET used_at = %s WHERE token = %s
        """, (datetime.now(), token))
    
    def send_reset_email(self, email: str, token: str) -> bool:
        """Kirim email reset password."""
        if not SMTP_USER or not SMTP_PASS:
            warn("SMTP not configured, skipping email")
            return False
        
        try:
            reset_link = f"https://aeryn.ai/reset-password?token={token}"
            
            msg = MIMEMultipart()
            msg['From'] = SMTP_FROM
            msg['To'] = email
            msg['Subject'] = "Reset your Aeryn password"
            
            body = f"""
            Hello,
            
            You requested a password reset. Click the link below to set a new password:
            
            {reset_link}
            
            This link expires in 1 hour.
            
            If you didn't request this, please ignore this email.
            
            Best,
            Aeryn Team
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
                server.starttls()
                server.login(SMTP_USER, SMTP_PASS)
                server.send_message(msg)
            
            info("Password reset email sent", email=email)
            return True
            
        except Exception as e:
            error("Failed to send reset email", email=email, error=str(e))
            return False


# Singletons
_email_verification = None
_password_reset = None

def get_email_verification() -> EmailVerification:
    global _email_verification
    if _email_verification is None:
        _email_verification = EmailVerification()
    return _email_verification

def get_password_reset() -> PasswordReset:
    global _password_reset
    if _password_reset is None:
        _password_reset = PasswordReset()
    return _password_reset
