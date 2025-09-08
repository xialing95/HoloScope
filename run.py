from flask import Flask, request, render_template_string
from app import __APinit__

app = Flask(__name__)

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head><title>Network Mode Switch</title></head>
<body>
  <h1>Network Mode Switch</h1>
  <button onclick="fetch('/set_ap').then(res => res.text()).then(alert)">Switch to Access Point</button>
  <hr>
  <form id="wifiForm">
    SSID: <input name="ssid" required><br>
    Password: <input name="password" type="password" required><br>
    <button type="submit">Connect to WiFi</button>
  </form>

  <script>
    document.getElementById('wifiForm').onsubmit = async e => {
      e.preventDefault();
      const form = e.target;
      const data = new URLSearchParams(new FormData(form));
      const res = await fetch('/set_wifi', {
        method: 'POST',
        body: data,
      });
      alert(await res.text());
    }
  </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/set_ap')
def set_ap():
    success, msg = __APinit__.switch_to_ap()
    status = 200 if success else 500
    return msg, status

@app.route('/set_wifi', methods=['POST'])
def set_wifi():
    ssid = request.form.get('ssid')
    password = request.form.get('password')
    if not ssid or not password:
        return "SSID and password required.", 400
    success, msg = __APinit__.connect_wifi(ssid, password)
    status = 200 if success else 500
    return msg, status

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
