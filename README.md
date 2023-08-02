# 1094 Amp Controller
controller code for EmpowerRF-1094 amplifier

**amp_control.py**

Python3 code to interface with arduino via serila *(/dev/ttyUSB)*. Sits on the RF emitter SBC, takes commands from the user, and sends them to the arduino.

commands:

1. get amplifer status (temp, current, state, gain, ect)
2. toggle logging to a log file
3. set logging frequency
4. set amplifer gain (VVA)
5. turn on/off the amp

**amp_control_arduino-v1.2.ino**

Arduino code to interface directly with amplifer. Pins A0 and A1 are used as ADC to read temp and current values. Pin A3 is set to digital output to toggle the amp state on/off.

The arduino communicates over I2C with a *MCP4725* DAC to output an variable voltage to adjust the VVA gain.
