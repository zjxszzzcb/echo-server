import argparse
import json
import logging
import socket
import sys

from dataclasses import dataclass, field
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Dict, Union
from urllib.parse import urlparse, parse_qs

# Colored logging support
class ColoredFormatter(logging.Formatter):
    """Formatter adding colors to log output"""
    
    COLORS = {
        'DEBUG': '\033[94m',  # Blue
        'INFO': '\033[92m',   # Green
        'WARNING': '\033[93m', # Yellow
        'ERROR': '\033[91m',  # Red
        'RESET': '\033[0m'    # Reset
    }
    
    def format(self, record):
        log_message = super().format(record)
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        return f"{color}{log_message}{self.COLORS['RESET']}"

# Configure logger
def setup_logger():
    """Setup logger with colored output"""
    new_logger = logging.getLogger("echo-server")
    new_logger.setLevel(logging.INFO)
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # Create formatter
    formatter = ColoredFormatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(formatter)
    
    # Add handler
    new_logger.addHandler(console_handler)
    
    return new_logger

logger = setup_logger()

@dataclass
class RequestDetails:
    """Model for formatting and storing HTTP request details"""
    method: str = ""
    endpoint: str = ""
    query_params: Dict[str, Union[str, list]] = field(default_factory=dict)
    headers: Dict[str, str] = field(default_factory=dict)
    body: str = ""

    def to_string(self) -> str:
        """Convert request details to formatted string"""
        return (f"[Method]: {self.method}\n"
                f"[Endpoint]: {self.endpoint_string}\n"
                f"[Headers]: {self.headers_string}\n"
                f"[Body]: {self.body}")

    @property
    def endpoint_string(self) -> str:
        """Generate complete endpoint string with query parameters"""
        if not self.query_params:
            return self.endpoint
        
        query_params_string = '&'.join([f"{k}={v}" for k, v in self.query_params.items()])
        return f"{self.endpoint}?{query_params_string}"

    @property
    def headers_string(self) -> str:
        """Generate formatted HTTP headers string"""
        return '\n'.join([f"{k}: {v}" for k, v in self.headers.items()])


class RequestHandler(BaseHTTPRequestHandler):
    """HTTP request handler that echoes all received request information"""
    
    def log_message(self, log_format: str, *args) -> None:
        """Override log method to use configured logger"""
        logger.debug(log_format % args)

    def handle_request(self):
        """Handle all HTTP request types and echo request information"""
        # Parse URL and query parameters
        parsed_url = urlparse(self.path)
        url = parsed_url.path
        query_params = parse_qs(parsed_url.query)
        # Convert query param values from lists to single values when possible
        query_params = {k: v[0] if len(v) == 1 else v for k, v in query_params.items()}

        # Get request headers
        # Use dict() to avoid type checking issues with HTTPMessage.items()
        headers = {header.lower(): value for header, value in dict(self.headers).items()}

        # Get request body
        content_length = int(headers.get('content-length', 0))
        body = self.rfile.read(content_length).decode('utf-8') if content_length > 0 else ""

        # Build response data
        response_data = {
            "request_details": {
                "method": self.command,
                "endpoint": url,
                "query_params": query_params,
                "headers": headers,
                "body": body
            }
        }

        request_details = RequestDetails(**response_data["request_details"])
        logger.info(f"Received request: \n"
                    f"{'=' * 80}\n"
                    f"{request_details.to_string()}\n"
                    f"{'=' * 80}")

        # Send response
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(response_data, indent=2, ensure_ascii=False).encode('utf-8'))

    def __getattr__(self, name):
        """Dynamically handle all do_* methods (GET, POST, PUT, etc.)"""
        if name.startswith('do_'):
            return self.handle_request
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")


def check_port(port: int, host: str = '127.0.0.1') -> bool:
    """Check if specified port is in use
    
    Args:
        port: Port to check
        host: Host address to check, defaults to localhost
        
    Returns:
        True if port is in use, False otherwise
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except (socket.error, socket.timeout, socket.herror, socket.gaierror) as e:
        logger.error(f"Socket error when checking port: {e}")
        return False


def run_http_server(port: int):
    """Run HTTP server on specified port
    
    Args:
        port: Port for server to listen on
    """
    server_address = ('', port)  # '' means listen on all addresses
    # Explicit type conversion to satisfy type checker
    handler_class = RequestHandler
    httpd = HTTPServer(server_address, handler_class) # type: ignore

    logger.info(f"HttpEchoServer listening on port: {port}")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down the server...")
    finally:
        httpd.server_close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='HTTP Echo Server')
    parser.add_argument('-p', '--port', type=int, default=5550)

    use_port = parser.parse_args().port

    logger.setLevel(logging.DEBUG)
    for handler in logger.handlers:
        handler.setLevel(logging.DEBUG)

    if not check_port(use_port):
        run_http_server(use_port)
    else:
        logger.error(f"Port {use_port} is already in use. ")
        sys.exit(1)