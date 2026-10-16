"""Local server for the TA1 web viewer (serves .glb with the right MIME type). Usage: python3 serve.py [port]"""
import http.server, socketserver, sys, os
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   # serve khuon-vien/, open /web/
class H(http.server.SimpleHTTPRequestHandler):
    extensions_map = {**http.server.SimpleHTTPRequestHandler.extensions_map, ".glb": "model/gltf-binary"}
port = int(sys.argv[1]) if len(sys.argv) > 1 else 8770
socketserver.TCPServer.allow_reuse_address = True
with socketserver.ThreadingTCPServer(("127.0.0.1", port), H) as srv:
    print(f"Serving http://127.0.0.1:{port}/web/", flush=True); srv.serve_forever()
