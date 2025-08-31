import time, csv, os
from datetime import datetime
import board, busio
import digitalio
import adafruit_mcp3xxx.mcp3008 as MCP
from adafruit_mcp3xxx.analog_in import AnalogIn
import RPi.GPIO as GPIO

BUZZER_PIN = 18
GPIO.setmode(GPIO.BCM)
GPIO.setup(BUZZER_PIN, GPIO.OUT)

spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)
cs = digitalio.DigitalInOut(board.D5)
mcp = MCP.MCP3008(spi, cs)
chan = AnalogIn(mcp, MCP.P0)

oxygen_file = "oxygen_log.csv"
alarm_file = "alarm_log.csv"
for fpath, header in [(oxygen_file, ["Timestamp","Oxygen (%)","Threshold (%)","Status","Voltage (V)"]),
                      (alarm_file, ["Timestamp","Oxygen (%)","Threshold (%)","Event"])]:
    if not os.path.exists(fpath):
        with open(fpath,"w",newline="") as file:
            csv.writer(file).writerow(header)

O2_REF_VOLT = 0.011
LOW_ALARM = 19.5
buzzer_status = "UNMUTE"
last_alarm_state = "NORMAL"

def calculate_o2(voltage):
    return round((voltage / O2_REF_VOLT) * 21, 2)

def log_alarm(o2, threshold, event):
    with open(alarm_file,"a",newline="") as f:
        csv.writer(f).writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), o2, threshold, event])

while True:
    voltage = chan.voltage
    o2 = calculate_o2(voltage)
    status = "Normal"

    if o2 < LOW_ALARM and buzzer_status=="UNMUTE":
        GPIO.output(BUZZER_PIN, GPIO.HIGH)
        status = "LOW OXYGEN ALERT"
        if last_alarm_state!="ALARM":
            log_alarm(o2, LOW_ALARM, "ALARM TRIGGERED")
            last_alarm_state="ALARM"
    else:
        GPIO.output(BUZZER_PIN, GPIO.LOW)
        if last_alarm_state=="ALARM" and o2 >= LOW_ALARM:
            log_alarm(o2, LOW_ALARM, "ALARM CLEARED")
            last_alarm_state="NORMAL"

    with open(oxygen_file,"a",newline="") as f:
        csv.writer(f).writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), o2, LOW_ALARM, status, voltage])

    time.sleep(1)
