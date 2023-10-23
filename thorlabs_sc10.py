# -*- coding: utf-8 -*-
# revisão 30/08/2023

import pyvisa as visa
from pyvisa import constants
import time

class ThorlabsSC10():
    '''
    Keywords (Commands and Queries)
    
    -----------------------------------------------------------------------------------------
           Command or Query            |                  Function
    -----------------------------------------------------------------------------------------
    ?          | Get commands          | Returns a list of available commands
    -----------------------------------------------------------------------------------------
    id?        | Get ID Returns        | the model number and firmware revision
    -----------------------------------------------------------------------------------------
    ens        | Toggle enable         | Enables/Disables the shutter
    -----------------------------------------------------------------------------------------
    ens?       | Get enable            | Returns “0” if the shutter is disabled and “1” if
               |                       | enabled
    -----------------------------------------------------------------------------------------
    rep=n      | Set repeat count      | Sets repeat count for repeat mode. The value n must
               |                       | be from 1 to 99.
    -----------------------------------------------------------------------------------------
    rep?       | Get repeat count      | Returns the repeat count.
    -----------------------------------------------------------------------------------------
               |                       |    Where n equals an associated mode—
               |                       |    mode=1: Sets the unit to Manual Mode
    mode=n     | Set operating mode    |    mode=2: Sets the unit to Auto Mode
               |                       |    mode=3: Sets the unit to Single Mode
               |                       |    mode=4: Sets the unit to Repeat Mode
               |                       |    mode=5: Sets the unit to the External Gate Mode
    -----------------------------------------------------------------------------------------
    mode?      | Get operating mode    | Returns the operating mode value.
    -----------------------------------------------------------------------------------------
               |                       | Where n denotes trigger mode (see section 4.1.4 for
    trig=n     | Set trigger mode      |  more details) —
               |                       |        trig=0: Internal trigger mode
               |                       |        trig=1: External trigger mode
    -----------------------------------------------------------------------------------------
    trig?      | Get trigger mode      | Returns the trigger mode.
    -----------------------------------------------------------------------------------------
               |                       | Where n denotes ex-trigger mode—
    xto=n      | Set ex-trigger mode   |    xto=0: Trigger Out TTL follows shutter output.
               |                       |    xto=1: Trigger Out TTL follows controller output.
    -----------------------------------------------------------------------------------------
    xto?       | Get ex-trigger mode   | Returns the ex-trigger mode.
    -----------------------------------------------------------------------------------------
    open=n     | Set open duration     | Sets the shutter open time in ms. The value n must
               |                       |  have 6 digits or less.
    -----------------------------------------------------------------------------------------
    open?      | Get open duration     | Returns the shutter close time in ms.
    -----------------------------------------------------------------------------------------
    shut=n     | Set close duration    | Sets the shutter close time in ms. The value n must
               |                       | have 6 digits or less.
    -----------------------------------------------------------------------------------------
    shut?      | Get close duration    | Returns the shutter close time in ms.
    -----------------------------------------------------------------------------------------
    closed?    | Get closed state      | Returns “1” if the shutter is closed or “0” if open.
    -----------------------------------------------------------------------------------------
    interlock? | Get Interlock tripped | Returns “1” if interlock is tripped, otherwise “0”.
    -----------------------------------------------------------------------------------------
               |                       | Where n denotes option for baud rate—
    baud=n     | Set baud rate         |      baud=0: Sets the SC10 serial baud rate to 9.6 K
               |                       |      baud=1: Sets the SC10 serial baud rate to 115 K
    -----------------------------------------------------------------------------------------
    baud?      | Get baud rate         | Returns “0” for 9.6 K or “1” for 115 K.
    -----------------------------------------------------------------------------------------
    save       | Save mode information | Save baud rate and output trigger mode.
    -----------------------------------------------------------------------------------------
    savp       | Store configuration   | Save current settings (ex. mode, open time, closed
               |                       |  time) into EEPROM.
    -----------------------------------------------------------------------------------------
    resp       | Load configuration    | Load settings from EEPROM.
    -----------------------------------------------------------------------------------------
    

    Usage
    -----
    import thorlabs_sc10 as tl
    import time

    '''
           
    def __init__(self):
        self.brand = 'Thorlabs'
        self.model = 'SC10'
        
    def rs232_set_up(self, com_port):
        self.rm = visa.ResourceManager()
        #self.ports = rm.list_resources()
        self.ser = self.rm.open_resource(com_port)
        self.ser.write_termination='\r'
        self.ser.read_termination='>'
        self.ser.baud_rate = 9600
        self.ser.data_bits = 8
        self.ser.parity = visa.constants.Parity.none
        self.ser.stop_bits = visa.constants.StopBits.one
        self.ser.flow_control = visa.constants.VI_ASRL_FLOW_NONE
        self.ser.timeout = 25000
        #return self.com

    def id(self):
        self.id = self.ser.query('id?')
        self.id = self.id[3:]
        return self.id
    
    def shutter_state(self):
        self.state = self.ser.query('closed?')
        self.state = int(self.state[-3:])
        return self.state

    def resp_time(self):
        self.op_time = self.open_time = self.ser.query('open?')
        self.op_time = int(self.op_time[-3:])
        self.op_time = self.op_time/1000
        return self.op_time

    def trigger(self):
        self.ser.write('ens')
                              
    def open_shutter(self):
        self.shutter_state()
        if self.state == 1:
            self.ser.write('ens')
            self.ser.read()
        else:
            pass

    def close_shutter(self):
        self.shutter_state()
        if self.state == 0:
            self.ser.write('ens')
            self.ser.read()
        else:
            pass

    def rs232_close(self):
        self.ser.close() 
        
        
    
