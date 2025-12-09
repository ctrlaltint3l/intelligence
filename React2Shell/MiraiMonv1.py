import socket
import struct
import time
import ipaddress

# --- Configuration ---
C2_IP = "205.185.121.141" # The target C2 server
C2_PORT = 23              # Mirai typically uses Telnet port for C2
TIMEOUT = 10              # Connection timeout in seconds

# --- Mirai Protocol Definitions ---
# These are the *typical* attack command IDs from the Mirai source code.
# The exact values may vary slightly for new botnet variants.
ATTACK_COMMANDS = {
    1: "UDP Flood",         # Raw UDP flood
    2: "VSE UDP Flood",     # Valve Source Engine query flood
    3: "SYN Flood",         # TCP SYN flood
    4: "ACK Flood",         # TCP ACK flood
    5: "STOMP Flood",       # TCP STOMP (Spoofed TPC Options) flood
    6: "GRE IP Flood",      # GRE IP (IP encapsulated in GRE) flood
    7: "GRE ETH Flood",     # GRE ETH (Ethernet encapsulated in GRE) flood
    8: "HTTP Flood",        # HTTP layer 7 flood
    9: "HOME Flood",        # Custom flood type (often related to Gafgyt)
    10: "OVH Flood",        # Custom flood for bypassing OVH mitigation
    # 11-15 are typically reserved for variants
}

def decode_ip(packed_ip):
    """Converts a 4-byte packed IP address to a dotted-quad string."""
    try:
        # Use ipaddress module for robust conversion
        return str(ipaddress.ip_address(packed_ip))
    except ValueError:
        return "Invalid IP"

def parse_attack_command(data):
    """
    Parses the binary DDoS command structure sent by the C2.
    
    Standard Mirai attack structure starts with 4-byte header:
    <Duration: 4 bytes> <Command_ID: 4 bytes> <Target_IP: 4 bytes> <Target_Port: 2 bytes> ...
    However, many variants use a simpler structure. We'll start with the most
    common simplified Mirai structure:
    
    <Command_ID: 4 bytes (little-endian unsigned int)>
    <Duration: 4 bytes (little-endian unsigned int)>
    <Target_IP: 4 bytes (network byte order)>
    <Target_Port: 2 bytes (network byte order)>
    <Flags/Options: remaining bytes...>
    
    Since we don't know the exact structure of this specific server, we'll
    attempt to decode based on common patterns. Let's assume the first 4 bytes
    are the Command ID and Duration, which is very common in variants.
    
    NOTE: The real Mirai uses a more complex TLV (Type-Length-Value) structure 
    after the initial command ID, but we'll try the common variant first.
    
    """
    if len(data) < 14: # Minimum expected length for a basic command
        return f"Raw Command (Too Short): {data.hex()}"

    try:
        # **Trial 1: Assume C2 sends Command ID first (2 bytes)**
        # This is a common structure in leaked C2 source code.
        # ! means Network Byte Order (Big-Endian), H=unsigned short (2 bytes)
        cmd_id_raw = struct.unpack('!H', data[0:2])[0] 
        cmd_duration = struct.unpack('!I', data[2:6])[0] # I=unsigned int (4 bytes)
        target_ip = decode_ip(data[6:10])
        target_port = struct.unpack('!H', data[10:12])[0]
        
        attack_name = ATTACK_COMMANDS.get(cmd_id_raw, f"Unknown (ID {cmd_id_raw})")
        
        # Log the decoded information
        log_entry = (
            f" Decoded Attack: **{attack_name}** (ID: {cmd_id_raw})\n"
            f"   - Target IP: **{target_ip}:{target_port}**\n"
            f"   - Duration: **{cmd_duration} seconds**\n"
            f"   - Raw Payload Size: {len(data)} bytes"
        )
        return log_entry
        
    except struct.error as e:
        return f"Raw Command (Parsing Error: {e}): {data.hex()}"

def run_client():
    """Main function to run the Mirai monitoring client."""
    
    # 1. Prepare Handshake Payload
    ARCH_ID = 6 
    initial_header = struct.pack('!BBBB', 0x00, 0x00, 0x00, ARCH_ID)
    source_string = "MyMonitoringBot"
    source_len = struct.pack('!B', len(source_string))
    bot_handshake_payload = initial_header + source_len + source_string.encode('ascii')

    print(f"Connecting to C2 at {C2_IP}:{C2_PORT}...")

    s = None
    try:
        # 2. Establish connection
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((C2_IP, C2_PORT))
        s.settimeout(TIMEOUT) 

        print(f"Sending bot handshake payload: {bot_handshake_payload.hex()}")
        s.sendall(bot_handshake_payload)

        print("\nHandshake successful. Monitoring C2 commands... (Press Ctrl+C to stop)")

        # 3. Command Monitoring Loop (with PONG logic)
        while True:
            try:
                # Use a smaller buffer size to catch shorter commands efficiently
                data = s.recv(1024)
                if not data:
                    print("\n[!] C2 closed the connection.")
                    break
                
                # Check for PING/PONG
                data_str = data.decode('ascii', errors='ignore').strip()
                
                if data_str == 'PING':
                    print(f"[{time.strftime('%H:%M:%S')}] >>> C2 Sent: PING. Responding with PONG.")
                    # PONG is the required response to keep the session alive
                    s.sendall(b'PONG\n') 
                elif len(data_str) < 5 and data_str != '':
                    # Simple text commands like 'PING' are typically 4 bytes. 
                    # If we receive short, non-PING text, just log the raw data.
                    print(f"[{time.strftime('%H:%M:%S')}] --- Short Text Command ({len(data)} bytes) ---")
                    print(f"Raw Hex: {data.hex()}")
                else:
                    # Assume this is a binary DDoS command or a longer instruction
                    print(f"\n[{time.strftime('%H:%M:%S')}] **ATTACK COMMAND INTERCEPTED**")
                    decoded_info = parse_attack_command(data)
                    print(decoded_info)
                    
            except socket.timeout:
                # Timeout is normal when the server is idle. Loop continues.
                pass
            except struct.error as e:
                # Catch errors during binary unpacking
                print(f"[{time.strftime('%H:%M:%S')}] [!] Critical Parsing Error: {e}")
            except KeyboardInterrupt:
                print("\n[!] Interrupted by user.")
                break

    except socket.error as e:
        print(f"\n[!] Fatal Connection Error: {e}")
    finally:
        if s:
            s.close()
        print("Client finished. Connection closed.")

# Run the client
run_client()
