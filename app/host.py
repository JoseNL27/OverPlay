import threading
from http.server import SimpleHTTPRequestHandler, HTTPServer
import ngrok


PORT = 8000


class NoCacheHandler(SimpleHTTPRequestHandler):

    def end_headers(self):
        self.send_header(
            "Cache-Control",
            "no-store, no-cache, must-revalidate, max-age=0"
        )
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")

        super().end_headers()


def start_server():
    server = HTTPServer(
        ("localhost", PORT),
        NoCacheHandler
    )

    print(f"OverPlay local: http://localhost:{PORT}")

    server.serve_forever()


# Arrancar servidor Python
thread = threading.Thread(
    target=start_server,
    daemon=True
)

thread.start()


# Crear túnel HTTPS
forwarder = ngrok.forward(
    f"localhost:{PORT}",
    authtoken_from_env=True
)
print()
print("================================")
print("       OVERPLAY ONLINE")
print("================================")
print()
print(f"HTTPS: {forwarder.url()}")
print()
print("Pulsa Ctrl+C para cerrar.")


# Mantener el proceso vivo
try:
    input()
except KeyboardInterrupt:
    pass