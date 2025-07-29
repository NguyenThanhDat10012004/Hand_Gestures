print("Sensors and actuator")
import platform
import serial
from serial.tools import list_ports
import time



# 2 last number is crc
RELAY1_ON =  [1,5,0,0,0xFF,0,0x8C,0x3A]
RELAY1_OFF = [1,5,0,0,0   ,0,0xCD,0xCA]


RELAY2_ON =  [1,5,0,1,0xFF,0,0xDD,0xFA]
RELAY2_OFF = [1,5,0,1,0   ,0,0x9C,0x0A]


RELAY3_ON =  [1,5,0,2,0xFF,0,0x2D,0xFA]
RELAY3_OFF = [1,5,0,2,0,0,0x6C,0x0A]


class ModbusMaster():
    def __init__(self) -> None:
        port_list=  list_ports.comports()
        if len(port_list)==0:
            raise Exception("No port found!")

        which_os = platform.system()
        if which_os == "Linux":
            name_ports = list(filter(lambda name: "USB" in name,map(lambda port: port.name,port_list)))
            portName = "/dev/"+ name_ports[0]
            print(portName)
        else:
            portName="None"
            for port in port_list:
                strPort = str(port)
                if "USB Serial" in strPort:
                    splitPort = strPort.split(" ")
                    portName = (splitPort[0])
        self.ser = serial.Serial(portName)
        self.ser.is_open
        self.ser.baudrate = 9600
        self.ser.stopbits = serial.STOPBITS_ONE
        self.ser.parity = serial.PARITY_NONE
        self.ser.bytesize = serial.EIGHTBITS
        print(self.ser.baudrate,self.ser.stopbits,self.ser.parity,self.ser.bytesize)
        
    def __enter__(self):
        return self

    def __exit__(self):
        print("closing the serial connection")
        self.close()

    def switch_actuator_1(self,state):
        if state == True:
            self.ser.write(RELAY1_ON)
        else:
            self.ser.write(RELAY1_OFF)

    def switch_actuator_2(self,state):
        if state == True:
            self.ser.write(RELAY2_ON)
        else:
            self.ser.write(RELAY2_OFF)
    
    def switch_actuator_3(self,state):
        if state == True:
            self.ser.write(RELAY3_ON)
        else:
            self.ser.write(RELAY3_OFF)

    def close(self):
        self.ser.close()

    def serial_read_data(self):
        ser = self.ser
        bytesToRead = ser.inWaiting()
        if bytesToRead > 0:
            out = ser.read(bytesToRead)
            data_array = [b for b in out]
            print(data_array)
            if len(data_array) >= 7:
                array_size = len(data_array)
                value = data_array[array_size - 4] * 256 + data_array[array_size - 3]
                return value
            else:
                return -1
        return 0


if __name__ == "__main__":
    a = ModbusMaster()
    while True:
        print("run?")
        a.switch_actuator_1(True)
        # time.sleep(0.03)
        a.switch_actuator_3(True)
        time.sleep(2)
        a.switch_actuator_1(False)
        time.sleep(0.03)
        a.switch_actuator_3(False)
        time.sleep(1)


