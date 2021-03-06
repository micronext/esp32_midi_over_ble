import time
import sys
import os

# pyserial
import serial
import serial.tools.list_ports as list_ports

# midi related
import mido

# pattern matching
import re


# Serial port parameters
SERIAL_SPEED = 9600
SERIAL_PORT = "/dev/cu.E-nstrument-ESP32SPP"
# Midi virtual port
MIDI_PORT = "IAC Driver Bus 1"
# BLUETOOTH ADDRESS
BLE_ADDRESS = "24-6f-28-b1-3f-a6"

# global var to safely exit the loop when program is ctr+c by user
close_serial_connection = False
# this is used to print a helpful message when everything is going right, so you can start waving the e-instrument
successfully_receiving_accelerometer_data = False

# This new data format is used to simplify converting serial data to useful accelerometer data
# accelerometer_data = [ax,ay,az,t,gx,gy,gz]


# Open the midi port
midi_port = mido.open_output(MIDI_PORT)


# Helper function to ensure bluetooth serial port is valid
def check_if_valid_serial_port(port_name):
    myports = [tuple(p)[0] for p in list(list_ports.comports())]
    if port_name not in myports:
        print(f"{port_name} is not a valid serial port")
        print("Available serial ports:")
        for serial_port in myports:
            print(serial_port)
        return False
    else:
        print(f"{port_name} is a Valid serial port!")
        return True


# Function to parse serial data from bytes to accelerometer data and update the global variable
def parse_serial(data):
    # convert from bytes to a string
    # output looks like b'Ax: 0.00 Ay: 0.01 Az: 0.77 T: 28.77 Gx: -0.18 Gy: -1.38 Gz: -0.50\r\n'
    data = str(data)
    # now get only the numbers as str in a list, remove Ax, Ay ...
    parsed = re.findall(r"[-+]?[0-9]*\.?[0-9]+", data)
    print(parsed)
    if len(parsed) == 7:
        # convert to a list of float
        accelerometer_data = [float(i) for i in parsed]
        # play midi
        parse_accel_play_midi(accelerometer_data)


# Function to play midi note given accelerometer data
# accelerometer_data = [ax,ay,az,t,gx,gy,gz]
def parse_accel_play_midi(accelerometer_data):
    # destructure list
    ax, ay, az, t, gx, gy, gz = accelerometer_data
    # Build a better algorithm to parse the data to produce midi notes since this currently only uses gx values
    if gx < -2:
        gx = gx / 1.1
        round_note = abs(round(gx))
        # Since midi notes are between 0 -127
        if round_note > 127:
            round_note = 127
        midinote = mido.Message("note_on", note=round_note, time=0.01)
        print(f"Playing: {midinote}")
        midi_port.send(midinote)


# Watch serial data
def serial_monitor():
    global close_serial_connection
    global successfully_receiving_accelerometer_data

    valid = check_if_valid_serial_port(SERIAL_PORT)
    if valid:
        # Trying to pair to device
        os.system(f"blueutil --connect {BLE_ADDRESS}")
        time.sleep(2)
        # print details
        print(f"Trying to connect to serial port ... {SERIAL_PORT}")

        try:
            # Connect to the serial port
            ser = serial.Serial(SERIAL_PORT, SERIAL_SPEED, timeout=2)

        except Exception as e:
            print(f"Problem connecting to bluetooth serial port: {e}")
            sys.exit()

        # if connected
        if ser.is_open:

            print("Connected to serial port, waiting to receive messages: ")
            # while connected
            while not close_serial_connection:
                try:
                    data = ser.readline()
                    parse_serial(data)
                    # if data == [] or len(data) == 0:
                    #     print(f"Received: {data}")
                    #     print(
                    #         "Ble serial not receiving data! Please try to reboot your e-instrument or try to re-connect to it!"
                    #     )
                    #     close_serial_connection = True
                    # else:
                    #     if not (successfully_receiving_accelerometer_data):
                    #         print("Receiving accelerometer data! You can start waving your e-instrument to produce midi notes!")
                    #         successfully_receiving_accelerometer_data = True

                    #     parse_serial(data)
                    # time.sleep(0.01)
                # If user ctr+c, close the serial port to avoid multiple open ports in the future during program shutdown
                except KeyboardInterrupt:
                    ser.close()
                    close_serial_connection = True
                    sys.exit()


serial_monitor()
