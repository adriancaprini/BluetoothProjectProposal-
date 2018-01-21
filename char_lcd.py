#!/usr/bin/python
# Example using an RGB character LCD connected to an MCP23017 GPIO extender.
import time
import smbus
from ctypes import c_short
from ctypes import c_byte
from ctypes import c_ubyte
from time import sleep
import RPi.GPIO as GPIO
import Adafruit_CharLCD as LCD
import Adafruit_GPIO.MCP230xx as MCP


# Define MCP pins connected to the LCD.
lcd_rs        = 0
lcd_en        = 2
lcd_d4        = 3
lcd_d5        = 4
lcd_d6        = 5
lcd_d7        = 6
lcd_red       = 9
lcd_green     = 10
lcd_blue      = 8

# Define LCD column and row size for 16x2 LCD.
lcd_columns = 16
lcd_rows    = 2

# Alternatively specify a 20x4 LCD.
# lcd_columns = 20
# lcd_rows    = 4

# Initialize MCP23017 device using its default 0x20 I2C address.
gpio = MCP.MCP23017(0x20, busnum=1)

GPIO.setup(22, GPIO.OUT) #BCM PINOUTS FOR RPI GPIO

# Alternatively you can initialize the MCP device on another I2C address or bus.
# gpio = MCP.MCP23017(0x24, busnum=1)

# Initialize the LCD using the pins
lcd = LCD.Adafruit_RGBCharLCD(lcd_rs, lcd_en, lcd_d4, lcd_d5, lcd_d6, lcd_d7,
                              lcd_columns, lcd_rows, lcd_red, lcd_green, lcd_blue,
                              gpio=gpio)

DEVICE = 0x77 # Default device I2C address
BME280_DEVICE = 0x77 # BME280 I2C address
YL40_DEVICE = 0x48  # YL-40 I2C address
YL40_DEVICE_MASK = 0x40

#Initialize the Pi 
bus = smbus.SMBus(1) # Rev 2 Pi, Pi 2 & Pi 3 uses bus 1
                     # Rev 1 Pi uses bus 0

# Print a two line message

GPIO.output(22, 1)
#lcd.message('Hello\nworld!')
def getShort(data, index):
  # return two bytes from data as a signed 16-bit value
  return c_short((data[index+1] << 8) + data[index]).value

def getUShort(data, index):
  # return two bytes from data as an unsigned 16-bit value
  return (data[index+1] << 8) + data[index]

def getChar(data,index):
  # return one byte from data as a signed char
  result = data[index]
  if result > 127:
    result -= 256
  return result

def getUChar(data,index):
  # return one byte from data as an unsigned char
  result =  data[index] & 0xFF
  return result

#The foolowing code is for AD YL-40 PCF8591 board. 
#==========================================================================
def readYL40Analog(addr=YL40_DEVICE): 
  return_list = []
  aout = 0
  for a in range(0,4):
    bus.write_byte_data(YL40_DEVICE, 0x40+a, aout)    
    read_value = bus.read_byte(YL40_DEVICE) # This is the data from A/D channel.
    read_value = bus.read_byte(YL40_DEVICE) # Read Twice to get the current data. 
    return_list.append(read_value)
    aout = aout + 1
  return return_list

#The following code is for DA of YL-40 PCF8591 board. 
#==========================================================================
def writeYL40Digital(addr=YL40_DEVICE, digital_data=0): 
    bus.write_byte_data(addr, 0x41, digital_data)  # 0x41 is the D/A channel. 
    return

#The foolowing code is for BME280 board. 
#==========================================================================
def readBME280ID(addr=BME280_DEVICE):
  # Chip ID Register Address
  REG_ID     = 0xD0
  (chip_id, chip_version) = bus.read_i2c_block_data(addr, REG_ID, 2)
  return (chip_id, chip_version)

#Read Data from different registers on BME280 and calculate the Temperature, Humidity and Pressure.
def readBME280All(addr=BME280_DEVICE):   
  # Register Addresses
  REG_DATA = 0xF7
  REG_CONTROL = 0xF4
  REG_CONFIG  = 0xF5

  REG_CONTROL_HUM = 0xF2
  REG_HUM_MSB = 0xFD
  REG_HUM_LSB = 0xFE

  # Oversample setting - page 27
  OVERSAMPLE_TEMP = 2
  OVERSAMPLE_PRES = 2
  MODE = 1

  # Oversample setting for humidity register - page 26
  OVERSAMPLE_HUM = 2
  bus.write_byte_data(addr, REG_CONTROL_HUM, OVERSAMPLE_HUM)

  control = OVERSAMPLE_TEMP<<5 | OVERSAMPLE_PRES<<2 | MODE
  bus.write_byte_data(addr, REG_CONTROL, control)

  # Read blocks of calibration data from EEPROM
  # See Page 22 data sheet
  cal1 = bus.read_i2c_block_data(addr, 0x88, 24)
  cal2 = bus.read_i2c_block_data(addr, 0xA1, 1)
  cal3 = bus.read_i2c_block_data(addr, 0xE1, 7)

  # Convert byte data to word values
  # Read Temperature
  dig_T1 = getUShort(cal1, 0)
  dig_T2 = getShort(cal1, 2)
  dig_T3 = getShort(cal1, 4)
  # Read Pressure
  dig_P1 = getUShort(cal1, 6)
  dig_P2 = getShort(cal1, 8)
  dig_P3 = getShort(cal1, 10)
  dig_P4 = getShort(cal1, 12)
  dig_P5 = getShort(cal1, 14)
  dig_P6 = getShort(cal1, 16)
  dig_P7 = getShort(cal1, 18)
  dig_P8 = getShort(cal1, 20)
  dig_P9 = getShort(cal1, 22)
  # Read Humidity
  dig_H1 = getUChar(cal2, 0)
  dig_H2 = getShort(cal3, 0)
  dig_H3 = getUChar(cal3, 2)

  dig_H4 = getChar(cal3, 3)
  dig_H4 = (dig_H4 << 24) >> 20
  dig_H4 = dig_H4 | (getChar(cal3, 4) & 0x0F)

  dig_H5 = getChar(cal3, 5)
  dig_H5 = (dig_H5 << 24) >> 20
  dig_H5 = dig_H5 | (getUChar(cal3, 4) >> 4 & 0x0F)

  dig_H6 = getChar(cal3, 6)

  # Wait in ms (Datasheet Appendix B: Measurement time and current calculation)
  wait_time = 1.25 + (2.3 * OVERSAMPLE_TEMP) + ((2.3 * OVERSAMPLE_PRES) + 0.575) + ((2.3 * OVERSAMPLE_HUM)+0.575)
  time.sleep(wait_time/1000)  # Wait the required time  

  # Read temperature/pressure/humidity
  data = bus.read_i2c_block_data(addr, REG_DATA, 8)
  pres_raw = (data[0] << 12) | (data[1] << 4) | (data[2] >> 4)
  temp_raw = (data[3] << 12) | (data[4] << 4) | (data[5] >> 4)
  hum_raw = (data[6] << 8) | data[7]

  #Refine temperature
  var1 = ((((temp_raw>>3)-(dig_T1<<1)))*(dig_T2)) >> 11
  var2 = (((((temp_raw>>4) - (dig_T1)) * ((temp_raw>>4) - (dig_T1))) >> 12) * (dig_T3)) >> 14
  t_fine = var1+var2
  temperature = float(((t_fine * 5) + 128) >> 8);

  # Refine pressure and adjust for temperature
  var1 = t_fine / 2.0 - 64000.0
  var2 = var1 * var1 * dig_P6 / 32768.0
  var2 = var2 + var1 * dig_P5 * 2.0
  var2 = var2 / 4.0 + dig_P4 * 65536.0
  var1 = (dig_P3 * var1 * var1 / 524288.0 + dig_P2 * var1) / 524288.0
  var1 = (1.0 + var1 / 32768.0) * dig_P1
  if var1 == 0:
    pressure=0
  else:
    pressure = 1048576.0 - pres_raw
    pressure = ((pressure - var2 / 4096.0) * 6250.0) / var1
    var1 = dig_P9 * pressure * pressure / 2147483648.0
    var2 = pressure * dig_P8 / 32768.0
    pressure = pressure + (var1 + var2 + dig_P7) / 16.0

  # Refine humidity
  humidity = t_fine - 76800.0
  humidity = (hum_raw - (dig_H4 * 64.0 + dig_H5 / 16384.0 * humidity)) * (dig_H2 / 65536.0 * (1.0 + dig_H6 / 67108864.0 * humidity * (1.0 + dig_H3 / 67108864.0 * humidity)))
  humidity = humidity * (1.0 - dig_H1 * humidity / 524288.0)
  if humidity > 100:
    humidity = 100
  elif humidity < 0:
    humidity = 0

  return temperature/100.0,pressure/100.0,humidity

#Reset the BME280 board at the beginning of program. 
def ResetBME280Sensors(addr=BME280_DEVICE):
  REG_RESET = 0xE0 # Reset Register Address
  bus.write_byte_data(addr, REG_RESET, 0xB6)
  return bus.read_i2c_block_data(addr, REG_RESET, 1)

#Main program 
def main():
  (chip_id, chip_version) = readBME280ID()
 # lcd.message ("Chip ID     :", chip_id)
 # lcd.message ("Version     :", chip_version)
 # lcd.message ("______________________________________________________")
  #if (chip_id == 0x00):
 # lcd.message("Sensors Not Ready, Check Your Circuit") #if circuit is not ready for data. 

  count = 0
  ResetBME280Sensors()  #reset sensors before we start.
  read_YL_40 = bus.read_byte(YL40_DEVICE) # This is the data from A/D channel.

  while(1):
    temperature,pressure,humidity = readBME280All()
    lcd.message("BME280 Temperature: %s C" %  (str(temperature)))
    lcd.message("BME280 Pressure: %s hPa" % (str(pressure)))
  # lcd.message("BME280 Humidity : ", humidity, "%")
  # lcd.message("______________________________________________________")
    analog = readYL40Analog()
    #lcd.message("A/D Channel 0 (Photocell)  : ", analog[0],  "Voltage: ", analog[0]*5.0/255.0, " V")
    #lcd.message("A/D Channel 1 (Temperature): ", analog[1],  "Voltage: ", analog[1]*5.0/255.0, " V")  
  # lcd.message("A/D Channel 2 (AN2 Input)  : ", analog[2],  "Voltage: ", analog[2]*5.0/255.0, " V"
  # lcd.message("A/D Channel 3 (POT)        : ", analog[3],  "Voltage: ", analog[3]*5.0/255.0, " V")
  # lcd.message("______________________________________________________")
    analog[:] = []
    for data in range(0, 256):
      writeYL40Digital(YL40_DEVICE,data)
      sleep(0.001)       # Generate a ramp on DA/Output. 
    count += 1
    sleep(1)
    writeYL40Digital(YL40_DEVICE,0)  #finally make D/A output a 0
# lcd.message("______________________________________________________")
# lcd.message('Analog Signal Already Genearted from D/A Output')
# lcd.message("______________________________________________________")
    if (count == 10):    # exit the program after 10 readings. 
     break;

if __name__=="__main__":
   main()



# Wait 5 seconds
time.sleep(5.0)
GPIO.output(22, 0)

# Demo showing the cursor.
lcd.clear()
lcd.show_cursor(True)
#lcd.message('Show cursor')

time.sleep(5.0)

# Demo showing the blinking cursor.
lcd.clear()
lcd.blink(True)
#lcd.message('Blink cursor')

time.sleep(5.0)

# Stop blinking and showing cursor.
lcd.show_cursor(False)
lcd.blink(False)

# Demo scrolling message right/left.
lcd.clear()
#message = 'Scroll'
#lcd.message(message)
#for i in range(lcd_columns-len(message)):
#    time.sleep(0.5)
 #   lcd.move_right()
#for i in range(lcd_columns-len(message)):
#    time.sleep(0.5)
#    lcd.move_left()

# Demo turning backlight off and on.
lcd.clear()
#lcd.message('Flash backlight\nin 5 seconds...')
time.sleep(5.0)
# Turn backlight off.
lcd.set_backlight(0)
time.sleep(2.0)
# Change message.
lcd.clear()
#lcd.message('Goodbye!')
# Turn backlight on.
lcd.set_backlight(1)

