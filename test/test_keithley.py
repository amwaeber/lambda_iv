import pandas as pd
import pyvisa as visa
import time

rm = visa.ResourceManager()
# rm.list_resources()
keithley = rm.open_resource('GPIB0::24::INSTR')
# print(keithley.query('*IDN?'))

# internal_in_ms = 500
# number_of_readings = 10

# Reset
keithley.write("*RST")
keithley.write(":SOUR:FUNC:MODE VOLT")
keithley.write(":SOUR:SWE:SPAC LIN")
keithley.write(f":SOUR:VOLT:STAR {-0.01}")
keithley.write(f":SOUR:VOLT:STOP {0.35}")
keithley.write(f":SOUR:SWE:POIN {100}")
keithley.write(":SOUR:VOLT:MODE SWE")
keithley.write(f":TRIG:COUN {100}")
keithley.write(":ARM:COUNT 1")
keithley.write(":TRIG:DEL 0.0")
keithley.write(":SOUR:DEL 0.0")
keithley.write(f":SOUR:VOLT:RANGE {20}")
keithley.write(f":SENSE:CURR:PROT {0.5}")
keithley.write(":SENSE:FUNC:CONC OFF")
keithley.write(":SENSE:FUNC 'CURR'")
keithley.write(":SENSE:CURR:RANGE 0.1")
keithley.write(":SENSE:CURR:NPLC 0.01")
keithley.write(":SENSE:AVERAGE:STAT OFF")
keithley.write(":DISP:ENAB OFF")
keithley.write(":SYSTEM:AZERO:STAT OFF")
keithley.write(":ROUT:TERM REAR")
keithley.write(":SYST:RSEN ON;")
keithley.write(":TRAC:CLE")
keithley.write(f":TRAC:POIN {100}")
keithley.write(":TRAC:FEED SENS")
time.sleep(0.1)

keithley.write(":OUTPUT ON")
keithley.write(":TRAC:FEED:CONT NEXT")
keithley.write(":INIT")
time.sleep(1.0)  # npoints * 2ms
keithley.write("OUTPUT OFF")
dat = keithley.query_ascii_values("trace:data?")

keithley.write(":OUTPUT ON")
keithley.write(":TRAC:FEED:CONT NEXT")
keithley.write(":INIT")
time.sleep(1.0)  # npoints * 2ms
keithley.write("OUTPUT OFF")
dat2 = keithley.query_ascii_values("trace:data?")

keithley.write(":OUTPUT ON")
keithley.write(":TRAC:FEED:CONT NEXT")
keithley.write(":INIT")
time.sleep(1.0)  # npoints * 2ms
keithley.write("OUTPUT OFF")
dat3 = keithley.query_ascii_values("trace:data?")

# set voltage to 0
keithley.write(":ABOR")
keithley.write("OUTPUT OFF")
rm.close()

voltages = dat[0::5]
currents = dat[1::5]
times = dat[3::5]

data = pd.DataFrame({
    'Time (s)': times,
    'Voltage (V)': voltages,
    'Current (A)': currents})
