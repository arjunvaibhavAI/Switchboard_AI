import ctypes
import os
import time 

class PIIEngine:
    def __init__(self):
        # 1. Path Setup
        current_dir = os.path.dirname(os.path.abspath(__file__))
        if os.name == 'nt':
            lib_name = "scanner.dll"
        else:
            lib_name = "scanner.so"
        
        dll_path = os.path.join(current_dir, "..", "core_engine", lib_name)
        self.dll_path = os.path.abspath(dll_path)

        # 2. Load the C Library
        try:
            self.lib = ctypes.CDLL(self.dll_path)
            # Define that we send a character pointer and receive an integer
            self.lib.analyze_and_redact.argtypes = [ctypes.c_char_p]
            self.lib.analyze_and_redact.restype = ctypes.c_int
            print(f"[System] Native Redaction Engine Loaded: {self.dll_path}")
        except Exception as e:
            print(f"[CRITICAL] Bridge failed to connect to C Engine: {e}")
            import sys
            sys.exit(1)

    def scan_and_redact(self, text: str):
        """
        Calculates latency and redacts PII in-place via C.
        """
        if not text:
            return "", False, 0.0
            
        # Start high-precision timer
        start = time.perf_counter()
        
        # Convert to mutable buffer so C can write '*' directly into the memory
        buf = ctypes.create_string_buffer(text.encode('utf-8'))
        
        # Execute C Logic
        result = self.lib.analyze_and_redact(buf)
        
        # End timer and calculate milliseconds
        latency_ms = (time.perf_counter() - start) * 1000
        
        # Return: (The cleaned text, True/False if risk was found, The speed)
        return buf.value.decode('utf-8'), bool(result), round(latency_ms, 4)

# Create the instance that main.py will import
engine = PIIEngine()