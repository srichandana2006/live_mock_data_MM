import os
import sys
import subprocess
import threading
import signal
import time

# List of simulator scripts to run
SIMULATORS = [
    ("AUTH", "live_auth_simulator.py"),
    ("DUAL", "live_dual_simulator.py"),
    ("PODCAST", "live_podcast_simulator.py")
]

# Track processes to allow clean shutdown
processes = []

def stream_output(prefix, process):
    """Reads stdout of a subprocess and prints it with a prefix."""
    try:
        for line in iter(process.stdout.readline, b''):
            decoded_line = line.decode('utf-8', errors='replace').strip()
            if decoded_line:
                print(f"[{prefix}] {decoded_line}")
    except Exception as e:
        print(f"[{prefix}] Error reading output: {e}")

def main():
    print("=" * 60)
    print("      MELODYMEET MULTI-SCHEMAS LIVE MOCK DATA RUNNER")
    print("=" * 60)
    print("Initializing simulators...")

    # Start each simulator script
    for prefix, filename in SIMULATORS:
        script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
        if not os.path.exists(script_path):
            print(f"[ERROR] Script '{filename}' not found at {script_path}")
            continue

        print(f"Starting {filename}...")
        # Forward command-line arguments to the child processes
        cmd = [sys.executable, "-u", script_path] + sys.argv[1:]
        p = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=1
        )
        processes.append((prefix, p))

        # Start thread to read and print output concurrently
        t = threading.Thread(target=stream_output, args=(prefix, p), daemon=True)
        t.start()

    print("\nAll simulators are now running concurrently in the background.")
    print("Press Ctrl+C to terminate all simulators cleanly.\n")
    print("-" * 60)

    try:
        # Keep main thread alive
        while True:
            # Check if any process has exited unexpectedly
            for prefix, p in processes:
                poll = p.poll()
                if poll is not None:
                    print(f"\n[WARNING] Process {prefix} exited with code {poll}")
                    processes.remove((prefix, p))
            if not processes:
                print("All simulator processes have terminated.")
                break
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\nTermination requested. Stopping all simulators...")
    finally:
        # Terminate all processes cleanly
        for prefix, p in processes:
            print(f"Stopping {prefix} simulator...")
            try:
                p.terminate()
                p.wait(timeout=2)
            except subprocess.TimeoutExpired:
                print(f"Forcing {prefix} simulator shutdown...")
                p.kill()
            except Exception as e:
                print(f"Error shutting down {prefix}: {e}")
        print("All simulators stopped.")

if __name__ == "__main__":
    main()
