"""
MINECRAFT BOT - SIRF ALIVE RAHNE KE LIYE
Server: funark.aternos.me:57003
Version: PaperMC 1.21.11 (Protocol 764)
Python: 3.10.0

Yeh bot sirf:
1. Server se connect hota hai
2. Alive rehta hai (keep-alive packets)
3. Agar mar gaya to auto-respawn
4. Kuch aur nahi karta
"""

import socket
import threading
import time
import random
import struct
import json
import sys
import os

# Config load karo
with open('config.json', 'r') as f:
    config = json.load(f)

SERVER_IP = config['server_ip']
SERVER_PORT = config['server_port']
BOT_NAME = config['bot_name']
PROTOCOL = config['protocol']


class AliveBot:
    def __init__(self):
        self.sock = None
        self.connected = False
        self.running = True
        self.reconnect_count = 0
        self.start_time = time.time()
        
    def write_varint(self, value):
        """Varint encode"""
        result = bytearray()
        while True:
            if value & ~0x7F == 0:
                result.append(value & 0x7F)
                return bytes(result)
            result.append((value & 0x7F) | 0x80)
            value >>= 7
    
    def write_string(self, string):
        """String encode"""
        encoded = string.encode('utf-8')
        return self.write_varint(len(encoded)) + encoded
    
    def send_packet(self, packet_id, data=b''):
        """Send Minecraft packet"""
        try:
            packet = self.write_varint(packet_id) + data
            self.sock.send(self.write_varint(len(packet)) + packet)
            return True
        except:
            return False
    
    def send_chat(self, message):
        """Send chat message"""
        return self.send_packet(0x04, self.write_string(message))
    
    def handshake(self):
        """Minecraft protocol handshake"""
        data = (self.write_varint(PROTOCOL) + 
                self.write_string(SERVER_IP) + 
                struct.pack('>H', SERVER_PORT) + 
                self.write_varint(2))
        return self.send_packet(0x00, data)
    
    def login(self):
        """Login start"""
        return self.send_packet(0x00, self.write_string(BOT_NAME))
    
    def keep_alive_send(self):
        """Send keep-alive packet (0x15 for play state)"""
        keepalive_id = random.randint(0, 2**63-1)
        return self.send_packet(0x15, struct.pack('>q', keepalive_id))
    
    def respawn(self):
        """Auto respawn on death"""
        return self.send_packet(0x04, self.write_varint(0))
    
    def listen_for_packets(self):
            """Listen for server packets and react"""
            buffer = bytearray()
            
            while self.running and self.connected:
                try:
                    self.sock.settimeout(30)
                    try:
                        data = self.sock.recv(4096)
                    except socket.timeout:
                        # Timeout normal hai, keep-alive bhejo
                        self.keep_alive_send()
                        continue
                        
                    if not data:
                        print("[-] Server closed connection (empty data)")
                        self.connected = False
                        break
                    
                    buffer.extend(data)
                    print(f"[*] Received {len(data)} bytes from server")
                    
                    # Simple approach: sirf connection alive rakho
                    # Protocol parsing skip karo, sirf keep-alive bhejo
                    self.keep_alive_send()
                    
                    # Buffer ko clear karo periodically
                    if len(buffer) > 1024:
                        buffer = bytearray()
                        
                except socket.timeout:
                    self.keep_alive_send()
                    continue
                except ConnectionResetError:
                    print("[-] Connection reset by server")
                    self.connected = False
                    break
                except Exception as e:
                    print(f"[-] Listen error: {e}")
                    self.connected = False
                    break
            
            if self.running:
                self.reconnect_to_server()
    
    def read_varint_from_buffer(self, buffer, offset):
        """Read varint from buffer"""
        result = 0
        shift = 0
        pos = offset
        while True:
            if pos >= len(buffer):
                return None, pos
            byte = buffer[pos]
            result |= (byte & 0x7F) << shift
            pos += 1
            if not (byte & 0x80):
                return result, pos
            shift += 7
            if shift > 35:
                return None, pos
    
    def handle_packet(self, packet_id, data):
        """Handle incoming packets"""
        if packet_id == 0x02:  # Login success
            print(f"[✓] LOGIN SUCCESSFUL! Bot is now alive.")
            self.send_chat(f"/say 🤖 {BOT_NAME} is alive on server! Auto-respawn enabled!")
            self.print_uptime()
            
        elif packet_id == 0x03:  # Set compression
            threshold, _ = self.read_varint_from_buffer(data, 0)
            print(f"[*] Compression threshold: {threshold}")
            
        elif packet_id == 0x21:  # Keep alive
            self.keep_alive_send()
            
        elif packet_id in [0x1A, 0x1B, 0x0F]:  # Disconnect
            reason = ""
            try:
                reason_len, pos = self.read_varint_from_buffer(data, 0)
                reason = data[pos:pos+reason_len].decode('utf-8', errors='replace')
            except:
                pass
            print(f"[-] Disconnected: {reason}")
            self.connected = False
            
        elif packet_id == 0x36:  # Death event
            print("[💀] BOT DIED! Auto-respawning...")
            time.sleep(3)
            self.respawn()
            print("[🔄] Respawn command sent!")
            self.send_chat("/say 🔄 Respawned successfully!")
    
    def print_uptime(self):
        """Print bot uptime"""
        uptime = int(time.time() - self.start_time)
        hours = uptime // 3600
        minutes = (uptime % 3600) // 60
        seconds = uptime % 60
        print(f"[⏱] Uptime: {hours}h {minutes}m {seconds}s")
    
    def reconnect_to_server(self):
        """Reconnect to server"""
        if not self.running:
            return
            
        self.reconnect_count += 1
        print(f"\n[!] Reconnecting... (Attempt #{self.reconnect_count})")
        
        if self.sock:
            try:
                self.sock.close()
            except:
                pass
            self.sock = None
        
        self.connected = False
        
        # Exponential backoff (max 60 seconds)
        wait_time = min(10 * self.reconnect_count, 60)
        print(f"[!] Waiting {wait_time} seconds...")
        
        for i in range(wait_time, 0, -1):
            if not self.running:
                return
            print(f"\r[!] Reconnecting in {i:2d}s...", end='', flush=True)
            time.sleep(1)
        print()
        
        self.connect_to_server()
    
    def connect_to_server(self):
        """Main connection function"""
        try:
            print(f"\n{'='*50}")
            print(f"  🤖 ALIVE BOT v2.0")
            print(f"{'='*50}")
            print(f"  Server: {SERVER_IP}:{SERVER_PORT}")
            print(f"  Bot:    {BOT_NAME}")
            print(f"  Mode:   Keep Alive + Auto Respawn")
            print(f"{'='*50}")
            
            # Resolve DNS
            try:
                ip = socket.gethostbyname(SERVER_IP)
                print(f"[*] Resolved {SERVER_IP} -> {ip}")
            except:
                ip = SERVER_IP
                print(f"[*] Using hostname: {ip}")
            
            # Create socket
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(30)
            
            print(f"[*] Connecting...")
            self.sock.connect((ip, SERVER_PORT))
            print(f"[✓] TCP Connected!")
            
            # Handshake
            if not self.handshake():
                raise Exception("Handshake failed")
            print(f"[*] Handshake sent (Protocol {PROTOCOL})")
            
            # Login
            if not self.login():
                raise Exception("Login failed")
            print(f"[*] Login request sent")
            
            self.connected = True
            
            # Listen for packets
            self.listen_for_packets()
            
        except Exception as e:
            print(f"[-] Connection error: {e}")
            self.connected = False
            time.sleep(5)
            self.reconnect_to_server()
    
    def start(self):
        """Start the bot"""
        print("[*] Starting bot...")
        self.connect_to_server()


def main():
    """Main function"""
    bot = AliveBot()
    
    try:
        bot.start()
    except KeyboardInterrupt:
        print("\n\n[!] Bot stopped by user")
        bot.running = False
        bot.connected = False
        if bot.sock:
            try:
                bot.sock.close()
            except:
                pass
        print("[✓] Bot terminated. Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"[-] Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
