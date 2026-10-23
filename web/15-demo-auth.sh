#!/bin/sh
# Turns on HTTP basic auth when DEMO_USER and DEMO_PASSWORD are set; otherwise the site stays open.
set -e

if [ -n "$DEMO_USER" ] && [ -n "$DEMO_PASSWORD" ]; then
    printf '%s:{PLAIN}%s\n' "$DEMO_USER" "$DEMO_PASSWORD" > /tmp/htpasswd
    printf 'auth_basic "Customer Insights demo";\nauth_basic_user_file /tmp/htpasswd;\n' > /tmp/auth.conf
else
    : > /tmp/auth.conf
fi
