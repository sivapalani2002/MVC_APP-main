import serial
import time

class SerialModel:
    def __init__(self, port="COM19", baudrate=115200, timeout=1):
        try:
            self.ser = serial.Serial(port, baudrate, timeout=timeout)
            time.sleep(2)  # Wait for the board to initialize
        except serial.SerialException as e:
            print(f"Serial error: {e}")
            self.ser = None

    def send_command(self, command):
        if not self.ser:
            print("Serial port is not initialized.")
            return
        
        try:
            # Ensure command starts with '$'
            if not command.startswith('$'):
                command = '$' + command

            # Append '\r\n' automatically
            command += '\r\n'

            # Send command
            self.ser.write(command.encode())
            self.ser.flush()  # Ensure data is sent
            time.sleep(0.1)  # Small delay to ensure board receives it
            print(f"Sent: {command.strip()}")

            # Read response
            response = self.ser.readline().decode().strip()
            print(f"Received: {response}")

        except Exception as e:
            print(f"Error: {e}")

    def close(self):
        if self.ser:
            self.ser.close()

if __name__ == "__main__":
    serial_model = SerialModel()
    
    try:
        while True:
            command = input("Enter command (or 'exit' to quit): ")
            if command.lower() == 'exit':
                break
            serial_model.send_command(command)
    finally:
        serial_model.close()