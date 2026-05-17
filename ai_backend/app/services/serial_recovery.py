import time
import logging
import sys

logger = logging.getLogger(__name__)

# Try to import serial dynamically. If missing, print instruction instead of halting
try:
    import serial
    import serial.tools.list_ports
    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False
    logger.warning("[SERIAL] 'pyserial' library not found. Running in simulation mode. Install with: pip install pyserial")

class ResilientSerialConnection:
    def __init__(self, baud_rate=115200):
        self.baud_rate = baud_rate
        self.serial_port = None
        self.last_attempt = 0
        self.retry_delay = 5.0  # Seconds before attempting COM re-scan
        
    def _ensure_connection(self) -> bool:
        """Lazy loaded resilient serial port connector."""
        if not SERIAL_AVAILABLE:
            return False
            
        if self.serial_port and self.serial_port.is_open:
            return True
            
        now = time.time()
        if now - self.last_attempt < self.retry_delay:
            return False
            
        self.last_attempt = now
        logger.info("[SERIAL] Port scanner checking active COM binds...")
        
        try:
            ports = list(serial.tools.list_ports.comports())
            if not ports:
                logger.warning("[SERIAL WARNING] No active USB/COM ports detected on host system.")
                return False
                
            # Filter and bind to the first CH340, CP210X, or FTDI/Arduino device
            target_port = None
            for p in ports:
                desc = p.description.lower()
                if "ch340" in desc or "cp210" in desc or "usb" in desc or "serial" in desc or "com" in desc:
                    target_port = p.device
                    break
                    
            if not target_port:
                target_port = ports[0].device  # Fallback to the first found port
                
            logger.info(f"[SERIAL] Auto-connecting to port: {target_port}")
            self.serial_port = serial.Serial(target_port, self.baud_rate, timeout=1.0)
            logger.info(f"[SERIAL] Successfully bound to serial link: {target_port} at {self.baud_rate} baud.")
            
            # Log event to diagnostics Excel
            try:
                from app.services.diagnostic_logger import log_diagnostic_event
                log_diagnostic_event("Hardware Link", f"Successfully bound port: {target_port}", "success")
            except Exception:
                pass
                
            return True
        except Exception as e:
            logger.error(f"[SERIAL ERROR] Dynamic re-bind failed: {e}")
            self.serial_port = None
            return False
            
    def send_command(self, cmd: str) -> str:
        """Dispatch hardware command over physical serial connection with automatic re-binding."""
        # Clean prefix command if passed as direct payload
        if cmd.startswith("CMD:SERIAL_SEND:"):
            cmd = cmd[16:]
            
        print(f"[SERIAL EVENT] Processing outbound: '{cmd}'")
        
        if not self._ensure_connection():
            warn_msg = f"[SERIAL OFFLINE] Simulated routing for: '{cmd}' (Hardware offline or unplugged)"
            print(warn_msg)
            
            # Log failure to Excel
            try:
                from app.services.diagnostic_logger import log_diagnostic_event
                log_diagnostic_event("Hardware Outbox", f"Simulated: '{cmd}' (Offline)", "warning")
            except Exception:
                pass
                
            return "Simulated serial sweep. Hardware offline."
            
        try:
            self.serial_port.write((cmd + "\n").encode('utf-8'))
            self.serial_port.flush()
            success_msg = f"Command '{cmd}' successfully sent."
            
            # Log success to Excel
            try:
                from app.services.diagnostic_logger import log_diagnostic_event
                log_diagnostic_event("Hardware Outbox", f"Sent: '{cmd}'", "success")
            except Exception:
                pass
                
            return success_msg
        except Exception as e:
            logger.error(f"[SERIAL ERROR] Write transmission interrupted: {e}")
            self.serial_port = None  # Flag for re-bind on next call
            return f"Transmission failed: {e}. Auto-recovery sequence queued."

# Singleton driver instance
serial_dispatcher = ResilientSerialConnection()
