import datetime
import numpy as np


def digital_to_voltage(value=0, bits=10, voltage_range=5.0):
    return (value / 2**bits) * voltage_range


def voltage_to_temperature_thermocouple(voltage=0):
    intrinsic_conversion = 100  # 1V = 100 C
    gain = 6.82
    return voltage * intrinsic_conversion / gain


def voltage_to_temperature(voltage=0, voltage_range=5.2):  # with 100kOhm thermistor
    serial_resistance = 56
    if voltage <= 0:
        return -1
    try:
        resistance = voltage * serial_resistance / (voltage_range - voltage)
        temperature = - 21.39443 * np.log(resistance) + 123.62807
        return temperature
    except ZeroDivisionError:
        return -1


def voltage_to_power(voltage=0):
    resistor = 390
    offset = 0.00004
    slope = 185
    if voltage >= 0:
        return (slope * (voltage / resistor) + offset)*1e3
    else:
        return -1
