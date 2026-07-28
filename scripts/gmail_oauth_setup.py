#!/usr/bin/env python3
"""
Gmail OAuth2 Setup Script
Generates refresh token for sending emails via Gmail SMTP with OAuth2
"""

import urllib.parse
import http.server
import threading
import webbrowser

# Step 1: You need to create OAuth2 credentials in Google Cloud Console
#
# Instructions:
# 1. Go to https://console.cloud.google.com/
# 2. Create a new project (or select existing)
# 3. Enable Gmail API: https://console.cloud.google.com/apis/library/gmail.googleapis.com
# 4. Go to Credentials > Create Credentials > OAuth 2.0 Client ID
# 5. Application type: Desktop app
# 6. Name: "Marketing Agent"
# 7. Download JSON and fill in CLIENT_ID and CLIENT_SECRET below

# Replace these with your OAuth2 credentials
CLIENT_ID = "YOUR_CLIENT_ID_HERE"
CLIENT_SECRET = "YOUR_CLIENT_SECRET_HERE"

# Scopes needed for sending email
SCOPES = [
    "https://mail.google.com/",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.compose",
]

# OAuth2 endpoints
AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
REDIRECT_URI = "http://localhost:8085/callback"


def get_auth_url():
    """Generate authorization URL"""
    params = {
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": " ".join(SCOPES),
        "access_type": "offline",
        "prompt": "consent",
    }
    return f"{AUTH_URL}?{urllib.parse.urlencode(params)}"


class CallbackHandler(http.server.BaseHTTPRequestHandler):
    """Handle OAuth2 callback"""

    auth_code = None

    def do_GET(self):
        if "/callback" in self.path:
            query = urllib.parse.urlparse(self.path).query
            params = urllib.parse.parse_qs(query)

            if "code" in params:
                CallbackHandler.auth_code = params["code"][0]
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(b"""
                    <html>
                    <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
                        <h1 style="color: #4CAF50;">Authorization Successful!</h1>
                        <p>You can close this window and return to the terminal.</p>
                    </body>
                    </html>
                """)
            else:
                self.send_response(400)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(
                    b"<html><body><h1>Error: No authorization code received</h1></body></html>"
                )

        self.log_message = lambda *args: None  # Suppress logs


def exchange_code_for_tokens(auth_code):
    """Exchange authorization code for access and refresh tokens"""
    import requests

    data = {
        "code": auth_code,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code",
    }

    response = requests.post(TOKEN_URL, data=data)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error exchanging code: {response.status_code}")
        print(response.text)
        return None


def main():
    print("=" * 60)
    print("Gmail OAuth2 Setup")
    print("=" * 60)
    print()

    # Check if credentials are set
    if CLIENT_ID == "YOUR_CLIENT_ID_HERE" or CLIENT_SECRET == "YOUR_CLIENT_SECRET_HERE":
        print("ERROR: You need to set CLIENT_ID and CLIENT_SECRET first!")
        print()
        print("Follow these steps:")
        print("1. Go to https://console.cloud.google.com/")
        print("2. Create a new project")
        print("3. Enable Gmail API")
        print("4. Create OAuth2 credentials (Desktop app)")
        print("5. Copy CLIENT_ID and CLIENT_SECRET into this script")
        print()
        print("Or export them as environment variables:")
        print("  export GOOGLE_CLIENT_ID=your_client_id")
        print("  export GOOGLE_CLIENT_SECRET=your_client_secret")
        return

    # Generate auth URL
    auth_url = get_auth_url()

    print("Step 1: Open this URL in your browser:")
    print()
    print(auth_url)
    print()

    # Try to open browser automatically
    try:
        webbrowser.open(auth_url)
        print("(Browser opened automatically)")
    except:
        print("(Copy and paste the URL above into your browser)")

    print()
    print("Step 2: Sign in with hypernexusofficialllc@gmail.com")
    print("Step 3: Grant permissions")
    print("Step 4: Wait for redirect...")
    print()

    # Start local server to handle callback
    server = http.server.HTTPServer(("localhost", 8085), CallbackHandler)

    # Wait for callback in a separate thread
    def handle_request():
        server.handle_request()

    thread = threading.Thread(target=handle_request)
    thread.start()

    # Wait for auth code
    print("Waiting for authorization...")
    thread.join(timeout=120)  # 2 minute timeout

    if CallbackHandler.auth_code:
        print("\nAuthorization code received!")
        print("Exchanging for tokens...")

        tokens = exchange_code_for_tokens(CallbackHandler.auth_code)

        if tokens:
            print("\n" + "=" * 60)
            print("SUCCESS! Add these to your .env file:")
            print("=" * 60)
            print()
            print(f"GOOGLE_CLIENT_ID={CLIENT_ID}")
            print(f"GOOGLE_CLIENT_SECRET={CLIENT_SECRET}")
            print(f"GOOGLE_REFRESH_TOKEN={tokens.get('refresh_token', 'N/A')}")
            print()
            print("Then update SMTP settings:")
            print("SMTP_HOST=smtp.gmail.com")
            print("SMTP_PORT=587")
            print("SMTP_USERNAME=hypernexusofficialllc@gmail.com")
            print("SMTP_FROM=hypernexusofficialllc@gmail.com")
            print("SMTP_FROM_NAME=HyperNexus Official")
            print()
            print("=" * 60)
        else:
            print("\nFailed to exchange code for tokens")
    else:
        print("\nTimeout waiting for authorization")

    server.server_close()


if __name__ == "__main__":
    main()
