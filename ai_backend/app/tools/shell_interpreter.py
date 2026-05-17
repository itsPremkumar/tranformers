import os
import sys
import queue
import subprocess
import threading
import time

class ShellInterpreter:
    def __init__(self):
        self.process = None
        self.output_queue = queue.Queue()
        self.done_event = threading.Event()
        self.start_process()

    def start_process(self):
        if self.process:
            self.terminate()

        # Determine OS shell command
        if sys.platform == "win32":
            start_cmd = ["cmd.exe"]
        else:
            start_cmd = [os.environ.get("SHELL", "bash")]

        my_env = os.environ.copy()
        my_env["PYTHONIOENCODING"] = "utf-8"

        print(f"[SHELL] Spawning persistent shell process: {start_cmd}")
        self.process = subprocess.Popen(
            start_cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=0,
            universal_newlines=True,
            env=my_env,
            encoding="utf-8",
            errors="replace"
        )

        # Spawn non-blocking thread listeners for stdout and stderr
        threading.Thread(
            target=self._read_stream,
            args=(self.process.stdout, False),
            daemon=True
        ).start()
        threading.Thread(
            target=self._read_stream,
            args=(self.process.stderr, True),
            daemon=True
        ).start()

    def _read_stream(self, stream, is_error):
        try:
            for line in iter(stream.readline, ""):
                # Clean and enqueue
                self.output_queue.put(line)
        except Exception as e:
            print(f"[SHELL ERROR] Exception while reading shell stream: {e}")

    def run_command(self, cmd: str, timeout: float = 8.0) -> str:
        """Executes a command and returns the accumulated stdout/stderr output."""
        if not self.process or self.process.poll() is not None:
            print("[SHELL] Subprocess offline. Restarting...")
            self.start_process()

        # Unique end of execution marker
        exec_marker = "##EXEC_DONE##"
        
        # Flush the queue to ensure a clean capture window
        while not self.output_queue.empty():
            try:
                self.output_queue.get_nowait()
            except queue.Empty:
                break

        # Write code command and echo the end-of-execution delimiter
        try:
            if sys.platform == "win32":
                full_code = f"{cmd}\necho {exec_marker}\n"
            else:
                full_code = f"{cmd}\necho {exec_marker}\n"

            self.process.stdin.write(full_code)
            self.process.stdin.flush()
        except Exception as e:
            print(f"[SHELL WRITE ERROR] Failed to send stdin: {e}")
            return f"Terminal Write Error: {e}"

        # Collect output until exec_marker is found or timeout is hit
        output_lines = []
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                # Non-blocking fetch with short wait
                line = self.output_queue.get(timeout=0.1)
                # Check for completion marker
                if exec_marker in line:
                    break
                # Filter out echoed commands if they get printed, or keep output clean
                if cmd in line and "echo" in line:
                    continue
                output_lines.append(line)
            except queue.Empty:
                continue

        # Format and return the result
        result = "".join(output_lines).strip()
        # Clean up absolute command echo lines if cmd is present in output
        clean_lines = []
        for line in result.split("\n"):
            if exec_marker in line:
                continue
            clean_lines.append(line)
            
        return "\n".join(clean_lines).strip()

    def terminate(self):
        if self.process:
            try:
                self.process.terminate()
                self.process.stdin.close()
                self.process.stdout.close()
                self.process.stderr.close()
            except Exception:
                pass
            self.process = None

# Global Singleton instance
shell_interpreter = ShellInterpreter()
