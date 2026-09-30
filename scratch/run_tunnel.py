import subprocess
import re
import sys
import os

proc = subprocess.Popen(
    ["./cloudflared.exe", "tunnel", "--protocol", "http2", "--url", "http://127.0.0.1:8000"],
    stderr=subprocess.PIPE,
    stdout=subprocess.PIPE,
    text=True,
    bufsize=1
)

url_found = None
while True:
    line = proc.stderr.readline()
    if not line:
        break
    sys.stderr.write(line)
    sys.stderr.flush()
    m = re.search(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com", line)
    if m:
        url_found = m.group(0)
        with open("scratch/public_url.txt", "w") as f:
            f.write(url_found)
        print(f"\n=======================================================\n>>> LIVE PUBLIC URL: {url_found}\n=======================================================\n", flush=True)
