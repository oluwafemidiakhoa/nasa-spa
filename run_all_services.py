#!/usr/bin/env python3
# NASA Space Weather Dashboard - Service Orchestrator
# Starts all required services in Docker container

import asyncio
import subprocess
import signal
import sys
import os
import time
from concurrent.futures import ThreadPoolExecutor

class ServiceOrchestrator:
    def __init__(self):
        self.processes = []
        self.running = True
        
    def start_api_server(self):
        print("Starting API server on port 9001...")
        cmd = ["python", "api_server.py"]
        process = subprocess.Popen(cmd)
        self.processes.append(process)
        return process
        
    def start_websocket_server(self):
        print("Starting WebSocket server on port 8765...")
        cmd = ["python", "websocket_server.py"]
        process = subprocess.Popen(cmd)
        self.processes.append(process)
        return process
        
    def start_web_server(self):
        print("Starting web interface on port 8080...")
        cmd = ["python", "-m", "http.server", "8080", "--directory", "."]
        process = subprocess.Popen(cmd)
        self.processes.append(process)
        return process
        
    def start_background_tasks(self):
        print("Starting background tasks...")
        cmd = ["python", "scheduler.py"]
        process = subprocess.Popen(cmd)
        self.processes.append(process)
        return process
        
    def health_check_server(self):
        from http.server import HTTPServer, BaseHTTPRequestHandler
        
        class HealthHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path == '/health':
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(b'{"status": "healthy", "services": "running"}')
                else:
                    self.send_response(404)
                    self.end_headers()
                    
            def log_message(self, format, *args):
                pass
        
        server = HTTPServer(('0.0.0.0', 9002), HealthHandler)
        server.serve_forever()
        
    def signal_handler(self, signum, frame):
        print(f"Received signal {signum}, shutting down...")
        self.running = False
        self.shutdown()
        
    def shutdown(self):
        print("Shutting down all services...")
        for process in self.processes:
            try:
                process.terminate()
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
        sys.exit(0)
        
    def run(self):
        signal.signal(signal.SIGTERM, self.signal_handler)
        signal.signal(signal.SIGINT, self.signal_handler)
        
        try:
            with ThreadPoolExecutor(max_workers=6) as executor:
                api_future = executor.submit(self.start_api_server)
                ws_future = executor.submit(self.start_websocket_server)
                web_future = executor.submit(self.start_web_server)
                bg_future = executor.submit(self.start_background_tasks)
                health_future = executor.submit(self.health_check_server)
                
                print("All services started successfully!")
                print("Health check available at: http://localhost:9002/health")
                print("API server: http://localhost:9001")
                print("WebSocket server: ws://localhost:8765")
                print("Web interface: http://localhost:8080")
                
                while self.running:
                    time.sleep(1)
                    for i, process in enumerate(self.processes):
                        if process.poll() is not None:
                            print(f"Service {i} died with return code {process.returncode}")
                            self.running = False
                            break
                            
        except KeyboardInterrupt:
            print("Received keyboard interrupt")
        except Exception as e:
            print(f"Error running services: {e}")
        finally:
            self.shutdown()

if __name__ == "__main__":
    orchestrator = ServiceOrchestrator()
    orchestrator.run()
