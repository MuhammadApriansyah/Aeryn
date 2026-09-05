#!/bin/bash
# Setup SSH key-auth dari proot (sen) ke Termux host (u0_a396:8022).
# Jalankan SEKALI. Saat diminta password, ketik: 000
set -e

TERMUX_USER="u0_a396"
TERMUX_PORT="8022"
KEY="$HOME/.ssh/id_ed25519"

# 1. Generate key kalau belum ada
if [ ! -f "$KEY" ]; then
  echo "Membuat SSH key baru di $KEY ..."
  ssh-keygen -t ed25519 -N "" -f "$KEY"
else
  echo "Key sudah ada: $KEY"
fi

# 2. Salin public key ke Termux (interaktif — ketik password 000)
echo ""
echo "Menyalin public key ke Termux (saat diminta password, ketik: 000) ..."
ssh -p "$TERMUX_PORT" "$TERMUX_USER@127.0.0.1" \
  'mkdir -p ~/.ssh && chmod 700 ~/.ssh && cat >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys' \
  < "$KEY.pub"

# 3. Verifikasi (harus tanpa password setelah ini)
echo ""
echo "Verifikasi key-auth (harus TANPA password):"
ssh -p "$TERMUX_PORT" -o BatchMode=yes "$TERMUX_USER@127.0.0.1" \
  'echo SSH_KEY_AUTH_OK; uname -m; command -v python3 || echo "no python3"'

echo ""
echo "Selesai. Kini bisa pakai:  ssh termux \"<perintah>\""
echo "(pastikan ~/.ssh/config sudah punya Host termux — lihat deploy/ssh/config)"