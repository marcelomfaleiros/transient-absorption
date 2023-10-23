# -*- coding: utf-8 -*-
# revisão 30/08/2023

import sys
import os
from transient_absorption_interface import Ui_MainWindow
import pyqtgraph as pg
from pyqtgraph.Qt import QtWidgets as qtw
from seabreeze.spectrometers import Spectrometer
from thorlabs_apt_device import BBD201
import thorlabs_sc10 as tl
import numpy as np
import time
import keyboard

class TransientAbsorption(qtw.QMainWindow, Ui_MainWindow):
    '''
    Device manager -> USB controllers -> APT USB Device -> Properties -> Enable VCP
        
    thorlabs_apt_device.devices.aptdevice module
    --------------------------------------------
        - APTDevice
        - APTDevice.close()
        - APTDevice.identify()
        - APTDevice.register_error_callback()
        - APTDevice.unregister_error_callback()
        - APTDevice.bays
        - APTDevice.channels
        - APTDevice.controller
        - APTDevice.keepalive_interval
        - APTDevice.keepalive_message
        - APTDevice.read_interval
        - APTDevice.update_interval
        - APTDevice.update_message
        - find_device()
        - list_devices()
        
    thorlabs_apt_device.devices.aptdevice_motor module
    --------------------------------------------------
        - APTDevice_BayUnit
        - APTDevice_BayUnit.genmoveparams
        - APTDevice_BayUnit.homeparams
        - APTDevice_BayUnit.jogparams
        - APTDevice_BayUnit.status
        - APTDevice_BayUnit.trigger
        - APTDevice_BayUnit.velparams
        - APTDevice_Motor
        - APTDevice_Motor.close()
        - APTDevice_Motor.home()
        - APTDevice_Motor.move_absolute()
        - APTDevice_Motor.move_jog()
        - APTDevice_Motor.move_relative()
        - APTDevice_Motor.move_velocity()
        - APTDevice_Motor.set_enabled()
        - APTDevice_Motor.set_home_params()
        - APTDevice_Motor.set_jog_params()
        - APTDevice_Motor.set_move_params()
        - APTDevice_Motor.set_velocity_params()
        - APTDevice_Motor.stop()
        - APTDevice_Motor.genmoveparams_
        - APTDevice_Motor.homeparams_
        - APTDevice_Motor.invert_direction_logic
        - APTDevice_Motor.jogparams_
        - APTDevice_Motor.status_
        - APTDevice_Motor.swap_limit_switches
        - APTDevice_Motor.velparams_ 
            
    Usage
    -----
    import transient_absorption as ta
    import time

    
    '''
           
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setObjectName("Transient Absorption")
        self.setupUi(self)

        self.strt_inttime_lineEdit.setText("10")
        self.strt_delay_lineEdit.setText("200")
        self.arb_move_lineEdit.setText("110")
        self.spc_delay_lineEdit.setText("0")
        self.spc_inttime_lineEdit.setText("10")
        self.dyn_inidelay_lineEdit.setText("-10000")
        self.dyn_findelay_lineEdit.setText("100000")
        self.dyn_stpdelay_lineEdit.setText("10000")
        self.dyn_wl_lineEdit.setText("400")
        self.dyn_inttime_lineEdit.setText("10")
                
        self.initialize_pushButton.clicked.connect(self.initialization)
        self.set_zerodelay_pushButton.clicked.connect(self.zero_delay)
        self.align_pushButton.clicked.connect(lambda: self.move_stage_fs(int(self.strt_delay_lineEdit.text())))
        self.arb_move_pushButton.clicked.connect(self.move_stage_mm)
        self.one_fs_pushButton.clicked.connect(lambda: self.move_stage_rel(1))
        self.none_fs_pushButton.clicked.connect(lambda: self.move_stage_rel(-1))
        self.five_fs_pushButton.clicked.connect(lambda: self.move_stage_rel(5))
        self.nfive_fs_pushButton.clicked.connect(lambda: self.move_stage_rel(-5))
        self.ten_fs_pushButton.clicked.connect(lambda: self.move_stage_rel(10))
        self.nten_fs_pushButton.clicked.connect(lambda: self.move_stage_rel(-10))        
        self.spc_meas_pushButton.clicked.connect(lambda: self.ta_dynamics(True))
        self.spc_clean_pushButton.clicked.connect(self.clear)
        self.spc_save_pushButton.clicked.connect(self.save)
        self.spc_exit_pushButton.clicked.connect(self.exit)
        self.dyn_meas_pushButton.clicked.connect(lambda: self.ta_dynamics(False))
        self.dyn_clean_pushButton.clicked.connect(self.clear)
        self.dyn_save_pushButton.clicked.connect(self.save)
        self.dyn_exit_pushButton.clicked.connect(self.exit)
              
    def graph_start(self):
        self.clear()
        
        self.wl_array = []
        self.deltaO_array = []
        
        self.graphicsView.showGrid(x=True, y=True, alpha=True)
        self.graphicsView.setLabel("left", "deltaO", units="a.u.")
        self.graphicsView.setLabel("bottom", "Wavelength", units="nm")
        
        #self.dataset = self.graphicsView.plot(self.wl_array, self.deltaO_array, pen=None, symbol='o')

    def initialization(self):
        self.stage = BBD201(serial_port='COM7', home=False)  #set up thorlabs translation stage
        self.stage.set_enabled(True)
        self.stage.home()
        self.zero = 'Delay zero not defined'
        while True:            
            if self.stage.status_[0][0]['homing'] == True:
                initialize_pos = self.stage.status["position"]
                self.initialize_label.setText("Homing: position = " + str(initialize_pos))
            elif self.stage.status_[0][0]['homed'] == True:
                initialize_pos = self.stage.status["position"]
                self.initialize_label.setText("Homed: position = " + str(initialize_pos))
                break                
            qtw.QApplication.processEvents()
        self.shutter = tl.ThorlabsSC10()                        #set up thorlabs shutter
        self.shutter.rs232_set_up('COM5')
        if self.shutter.id() == 'THORLABS SC10 VERSION 1.07':
            self.initialize_label.setText("Homed: position = " + str(initialize_pos)
                                          + '\nTHORLABS SC10 VERSION 1.07 - OK')
        self.oceanoptics = Spectrometer.from_first_available()  #set up ocean optics spectrometer
        if 'Spectrometer' in str(self.oceanoptics):
            self.initialize_label.setText("Homed: position = " + str(initialize_pos)
                                          + '\nTHORLABS SC10 VERSION 1.07 - OK'
                                          + '\n' + str(self.oceanoptics)[1:-10] + ' - OK')

        self.graph_start()

    def zero_delay(self):        
        self.zero = self.stage.status["position"]
        self.zero_pos_mm = self.zero/20000
        self.set_zero_delay_label.setText("Zero delay = " + str(self.zero_pos_mm) + " mm")
        return self.zero      

    def move_stage_rel(self, step_fs):
        step = int(step_fs * 0.0003 * 20000)                     
        if (int(self.stage.status["position"]) + step) <= 4400000:          
            self.stage.move_relative(step)            
            while True:
                curr_pos_mm = self.stage.status["position"]
                if type(self.zero) == int:
                    curr_pos_fs = int((curr_pos_mm - self.zero)/(20000*0.0003))
                    self.align_label.setText("Position = " + str(curr_pos_fs) + " fs")
                    self.arb_move_label.setText("Position = " + str(curr_pos_mm/20000) + " mm")
                    if curr_pos_fs == step_fs:
                        break
                else:
                    self.arb_move_label.setText("Position = " + str(curr_pos_mm/20000) + " mm")                
                    self.align_label.setText("Delay zero not defined")
                    if curr_pos_mm == step_fs:
                        break
                qtw.QApplication.processEvents() 

    def move_stage_mm(self):
        position_mm = float(self.arb_move_lineEdit.text()) * 20000
        position_mm = int(position_mm)
        if position_mm <= 4400000 or position_mm >= 0:          
            self.stage.move_absolute(position_mm)         
            while True:
                curr_pos_mm = self.stage.status["position"]
                if type(self.zero) == int:
                    self.curr_pos_fs = int((curr_pos_mm - self.zero)/(20000*0.0003))
                    self.arb_move_label.setText("Position = " + str(curr_pos_mm/20000) + " mm")                
                    self.align_label.setText("Position = " + str(self.curr_pos_fs) + " fs")
                    if curr_pos_mm == position_mm:
                        break
                else:
                    self.curr_pos_fs = int(curr_pos_mm/(20000*0.0003))
                    self.arb_move_label.setText("Position = " + str(curr_pos_mm/20000) + " mm")                
                    self.align_label.setText("Delay zero not defined")
                    if curr_pos_mm == position_mm:
                        break
                qtw.QApplication.processEvents()

    def move_stage_fs(self, position_fs):
        position_mm = int(round(position_fs * 0.0003 * 20000))
        delay_zero = self.zero
        new_position = delay_zero + position_mm                
        if new_position <= 4400000 or position_mm >= 0:          
            self.stage.move_absolute(new_position)            
            while True:
                curr_pos_mm = self.stage.status["position"]
                self.curr_pos_fs = int((curr_pos_mm - self.zero)/(20000*0.0003))
                self.align_label.setText("Position = " + str(self.curr_pos_fs) + " fs")
                self.arb_move_label.setText("Position = " + str(curr_pos_mm/20000) + " mm")              
                if self.curr_pos_fs == position_fs:
                    break
                qtw.QApplication.processEvents()  

    def spectrum(self):    
        self.oceanoptics.integration_time_micros(self.int_time)       #set integration time                               
        wl = self.oceanoptics.wavelengths()                     #take spectrum
        intensity = self.oceanoptics.intensities()
        
        return wl, intensity

    def ta_spectrum(self):                  
        self.shutter.close_shutter()            #close shutter
        time.sleep(0.5)
        spec_off = self.spectrum()
        #time.sleep(self.int_time)
        self.shutter.open_shutter()             #open shutter
        time.sleep(0.5)
        spec_on = self.spectrum()
        #time.sleep(self.int_time)
        self.shutter.close_shutter()
        
        wl_array = spec_on[0]
        deltaO_array = - np.log10(spec_on[1]/spec_off[1])

        return wl_array, deltaO_array

    def ta_dynamics(self, one_shot=bool):
        if one_shot == True:
            self.int_time = int(self.spc_inttime_lineEdit.text()) * 1000  #read integration time in ms
            self.move_stage_fs(int(self.spc_delay_lineEdit.text()))         #delay
            self.spec_currpos_label.setText("Position = " + str(self.curr_pos_fs) + " fs")
            qtw.QApplication.processEvents()
            self.ta_array = self.ta_spectrum()
            self.graphicsView.plot(self.ta_array[0], self.ta_array[1], pen=None, symbol='s',
                                   clear = True)
        elif one_shot == False:
            self.int_time = int(self.dyn_inttime_lineEdit.text()) * 1000  #read integration time in ms
            self.ini_delay = int(self.dyn_inidelay_lineEdit.text())
            self.fin_delay = int(self.dyn_findelay_lineEdit.text())
            self.stp_delay = int(self.dyn_stpdelay_lineEdit.text())
        
            for d in range(self.ini_delay, (self.fin_delay + self.stp_delay), self.stp_delay):
                if keyboard.is_pressed('Escape'):
                    break
                self.move_stage_fs(d)
                self.dyn_currpos_label.setText("Position = " + str(self.curr_pos_fs) + " fs")
                qtw.QApplication.processEvents()
                ta = self.ta_spectrum()
                self.graphicsView.plot(ta[0], ta[1], pen=None, symbol='o', clear = False)
                if d == self.ini_delay:
                    self.ta_array = (ta)
                else:
                    self.ta_array = np.vstack((self.ta_array, ta[1]))                
                        
                pg.QtWidgets.QApplication.processEvents()

    def save(self):
        raw_ta_array = np.vstack(self.ta_array)
        ta_data = raw_ta_array.transpose()
        file_spec = qtw.QFileDialog.getSaveFileName()[0]
        np.savetxt(file_spec, ta_data)          

    def clear(self):
        self.graphicsView.clear()

    def exit(self):
        self.stage.set_enabled(False)
        self.stage.close()
        self.close()

if __name__ == '__main__':
    app = qtw.QApplication([])
    tela = TransientAbsorption()
    tela.show()
    app.exec_()
