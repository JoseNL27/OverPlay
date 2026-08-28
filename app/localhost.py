from http.server import SimpleHTTPRequestHandler, test


class NoCacheHandler(SimpleHTTPRequestHandler):

  def end_headers(self):
    # Desactiva la caché por completo
    self.send_header(
        "Cache-Control", "no-store, no-cache, must-revalidate, max-age=0"
    )
    self.send_header("Pragma", "no-cache")
    self.send_header("Expires", "0")
    super().end_headers()


if __name__ == "__main__":
  # Escucha en todas las interfaces (0.0.0.0) y en el puerto 8000
  test(HandlerClass=NoCacheHandler, port=8000, bind="0.0.0.0")