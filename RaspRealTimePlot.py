import time
import serial
import datetime as dt
import matplotlib
# Force matplotlib to not use any Xwindows backend.
matplotlib.use('TkAgg') #comment out for debugging
import matplotlib.pyplot as plt
import matplotlib.cbook as cbook
#plt.switch_backend('Agg')
import matplotlib.animation as animation
from decimal import Decimal
import pandas as pd
import numpy as np
import os.path as path
import re
import gc
import os

#import logging
#logging.basicConfig(filename='/home/pi/Desktop/logEL.log', filemode='a', format=u'%(asctime)s - %(message)s', level=logging.DEBUG, encoding='utf-8')

count = 0

# Create figure for plotting
fig = plt.figure()
fig.patch.set_facecolor('whitesmoke')
hFont = {'fontname':'sans-serif', 'weight':'bold', 'size':'12'}

xs = ['T-9','T-8','T-7','T-6','T-5','T-4','T-3','T-2','T-1','Now'] 
ysTemp = []
ysAC = []
ysDC = []

#Real Time
axRT1 = fig.add_subplot(2, 2, 1)
axRT2 = axRT1.twinx()  # instantiate a second axes that shares the same x-axis
#Draw x and y lists
axRT1.clear()   
axRT2.clear()
axRT1.set_ylim([0, 4])
axRT2.set_ylim([10, 70])

axRT1.set_ylabel('Power Consumption kW', **hFont)
axRT2.set_ylabel('Temperature C', **hFont)
axRT1.set_xlabel('Seconds', **hFont)
axRT1.set_title('Power Consumption and Temperature - Real Time', **hFont)
lineTemp, = axRT2.plot([], [], 'r', label='Temp', linewidth = 4)
lineAC, = axRT1.plot([], [], 'b:', label='Mains', linewidth = 4)
lineDC, = axRT1.plot([], [], 'g--', label='Solar', linewidth = 4)
fig.legend([lineAC, lineDC,lineTemp], ['Mains', 'Solar', 'Temp'], fontsize=20)

#24Hours
ax1D1 = fig.add_subplot(2, 2, 3)
ax1D2 = ax1D1.twinx()  # instantiate a second axes that shares the same x-axis
ax1D1.set_title('Power Consumption and Temperature - Last 24 Hours', **hFont)
xs1Day = ['T-23', 'T-22', 'T-21', 'T-20', 'T-19', 'T-18', 'T-17', 'T-16', 'T-15', 'T-14', 'T-13', 'T-12', 'T-11', 'T-10', 'T-9', 'T-8', 'T-7', 'T-6', 'T-5', 'T-4', 'T-3', 'T-2', 'T-1', 'T']
ax1D1.set_xticklabels(xs1Day, rotation=45)
ax1D1.set_ylim([0, 4])
ax1D2.set_ylim([10, 70])
ax1D1.set_ylabel('Power Consumption kW', **hFont)
ax1D2.set_ylabel('Temperature C', **hFont)
ax1D1.set_xlabel('Hours', **hFont)
lineTemp1D, = ax1D2.plot([], [], 'r', label='Temp', linewidth = 4)
lineAC1D, = ax1D1.plot([], [], 'b:', label='Mains', linewidth = 4)
lineDC1D, = ax1D1.plot([], [], 'g--', label='Solar', linewidth = 4)

#Logo
with cbook.get_sample_data('/home/pi/Desktop/Logo.png') as image_file:
    image = plt.imread(image_file)

ax = fig.add_subplot(4, 2, 2)
ax.imshow(image)
ax.axis('off')  # clear x-axis and y-axis

#Solar Text Box
axSol = fig.add_subplot(4, 2, 4)
axSol.axis('off')

#Mains Text Box
axMains = fig.add_subplot(4, 2, 8)
axMains.axis('off')


ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=1)
ser.flush()

#logging.debug(u'Probe started')

# This function is called periodically from FuncAnimation
def animate(i, xs, ysTemp, ysAC, ysDC):

  values = getValues()
  #logging.debug('Serial: %s', str(values))
    
  if values != 0:
    temp_c = Decimal(re.search(r'\d+',values[3]).group())
    if temp_c < 0: temp_c = 0
    wAC = round(Decimal(re.search(r'\d+', values[1]).group())/1000, 2)
    if wAC < 0.35: wAC = 0
    aDC = float(re.search(r'\d+', values[2]).group()) #remove characters
    vDC = float(re.search(r'\d+', values[4][:5]).group()) #remove characters
    wDC = aDC * vDC
    wDC = round(abs(Decimal(wDC))/1000, 2)
    
    #logging.debug(u'Live values: temp: '+ str(temp_c) +' wAC: '+ str(wAC) +' wDC: ' + str(wDC))

    # Add x and y to lists
    ysTemp.append(temp_c)
    ysAC.append(wAC)
    ysDC.append(wDC)

    # Limit x and y lists to 10 items
    ysTemp = ysTemp[-10:]
    ysDC = ysDC[-10:]
    ysAC = ysAC[-10:]
    
    if len(ysTemp) == 10:
      axRT2.lines = []
      axRT1.lines =[]
      lineTemp, = axRT2.plot(xs, ysTemp, 'r', label='Temp', linewidth = 4)
      lineAC, = axRT1.plot(xs, ysAC, 'b:', label='Mains', linewidth = 4)
      lineDC, = axRT1.plot(xs, ysDC, 'g--', label='Solar', linewidth = 4)

    
  #######################################################
  
  if path.exists('/home/pi/Desktop/Hour.csv'):
    df1Day = pd.read_csv('/home/pi/Desktop/Hour.csv')

    
    if df1Day['Temp'].count() > 23:
      ax1D2.lines = []
      ax1D1.lines = []
      lineTemp1D, = ax1D2.plot(xs1Day, df1Day['Temp'], 'r', label='Temp', linewidth = 4)
      lineAC1D, = ax1D1.plot(xs1Day, df1Day['wAC'], 'b:', label='Mains', linewidth = 4)
      lineDC1D, = ax1D1.plot(xs1Day, df1Day['wDC'], 'g--', label='Solar', linewidth = 4)
  
      #logging.debug(u'1 Day Values Printed')
#############################################################
  
  #Text
  if path.exists('/home/pi/Desktop/Day.csv'):
    dfDaily = pd.read_csv('/home/pi/Desktop/Day.csv')
    df7Day = dfDaily.tail(7)
  
    axSol.clear()
    axSol.axis('off')
    textSol = ('\n Solar Energy Production \n'
               '\n'
               'Past 24 hours: ' + str(round(df1Day['wDC'].sum(), 2)) + ' kWh\n'
               'Past 7 days: ' + str(round(df7Day['wDC'].sum(), 2)) + ' kWh\n'
               'Past 30 days: ' + str(round(dfDaily['wDC'].sum(), 2)) + ' kWh'
               )
    axSol.text(0.5, 0, textSol, fontsize=20, fontweight='bold', horizontalalignment = 'center')
  
    axMains.clear()
    axMains.axis('off')
    textMains = ('Mains Energy Use \n'
                 '\n'
               'Past 24 hours: ' + str(round(df1Day['wAC'].sum(), 2)) + ' kWh\n'
               'Past 7 days: ' + str(round(df7Day['wAC'].sum(), 2)) + ' kWh\n'
               'Past 30 days: ' + str(round(dfDaily['wAC'].sum(), 2)) + ' kWh\n'
                 '\n'
               'Solar % past 30 days: ' + str(round( dfDaily['wDC'].sum() / (dfDaily['wDC'].sum() + dfDaily['wAC'].sum() ) * 100, 2) ) + '%'
               )  
    axMains.text(0.5, 0.5, textMains, fontsize=20, fontweight='bold', horizontalalignment = 'center')
    #logging.debug(u'7 Day Values Printed')
    
    del df1Day
    del df7Day
    del dfDaily
    gc.collect()
    #fig.clf()
    #plt.close()

def getValues():

  global count
  data = []
  measureList = 0
  
  if ser.in_waiting > 0:
    line = ser.readline().decode('utf-8').rstrip()
    #logging.debug(line)
    print(line)
    
    
    if line.count(',') == 4:
      measureList = list(line.split(","))
      wAC = measureList[1]
      if float(wAC) < 350: wAC = 0
      data.append([wAC, measureList[2], measureList[3], measureList[4]])
      print(data)
      count = count +1
      
    ###############################################################    
    #minutes
    if count == 60:
    
      ser.reset_output_buffer()
      ser.reset_output_buffer()
      ser.flush()
      
      df = pd.DataFrame(data, columns=['wAC', 'aDC', 'Temp', 'vDC'])
      df['wAC'] = pd.to_numeric(df["wAC"], downcast="float")/1000
      df['aDC'] = pd.to_numeric(df["aDC"].str.extract(r'(\d+)', expand=False), downcast="float")
      df['Temp'] = pd.to_numeric(df["Temp"], downcast="float")
      df['vDC'] = pd.to_numeric(df["vDC"], downcast="float")
      df['wDC'] = (df['aDC']*df['vDC'])/1000
      df['wDC'].round(2)
      df['wAC'].round(2)

      minData = [[df['wAC'].mean(), df['wDC'].mean(), df['Temp'].mean()]]

      dfTemp = pd.DataFrame(minData, columns=['wAC', 'wDC', 'Temp'])
        
      if path.exists('/home/pi/Desktop/Minute.csv'):
         dfMin = pd.read_csv('/home/pi/Desktop/Minute.csv')
         dfMin = pd.concat([dfMin, dfTemp], ignore_index=True)

      else:
          dfMin = pd.DataFrame(minData, columns=['wAC', 'wDC', 'Temp'])
        
      
      dfMin.to_csv('/home/pi/Desktop/Minute.csv', index = False)
      #logging.debug(u'Hourly saved to file')
        
      data = []
      count = 0
      
      del df
      del dfMin
      del dfTemp
      
    ###############################################################
    #Hourly
            
    #Save to hourly csv
            
    if path.exists('/home/pi/Desktop/Minute.csv'):
      df = pd.read_csv('/home/pi/Desktop/Minute.csv')
      
      if len(df) == 60:
        hourData = [[df['wAC'].mean(), df['wDC'].mean(), df['Temp'].mean()]]
      
        dfTemp = pd.DataFrame(hourData, columns=['wAC', 'wDC', 'Temp'])
      
        if path.exists('/home/pi/Desktop/Hour.csv'):
           dfHour = pd.read_csv('/home/pi/Desktop/Hour.csv')
           dfHour = pd.concat([dfHour, dfTemp], ignore_index=True)

        else:
            dfHour = pd.DataFrame(hourData, columns=['wAC', 'wDC', 'Temp'])
             
        #drop oldest row if more than 24 hours
        while len(dfHour) > 24:
            dfHour.drop(0, axis=0, inplace=True)
        
        dfHour.to_csv('/home/pi/Desktop/Hour.csv', index = False)
        dfHour.to_csv('/home/pi/Desktop/Hour2Daily.csv', index = False)
        #logging.debug(u'Hourly saved to file')
        
        os.remove("/home/pi/Desktop/Minute.csv")
        
        data = []
        del df
        del dfHour
        del dfTemp

    #########################################################################################
    #Daily
        
    if path.exists('/home/pi/Desktop/Hour2Daily.csv'):
      df = pd.read_csv('/home/pi/Desktop/Hour2Daily.csv')
      
      if len(df) == 24:
                  
        dayData = [[df['wAC'].sum(), df['wDC'].sum()]]
        dfTemp = pd.DataFrame(dayData, columns=['wAC', 'wDC'])
    
        if path.exists('/home/pi/Desktop/Day.csv'):
            dfDay = pd.read_csv('/home/pi/Desktop/Day.csv')
            dfDay = pd.concat([dfDay, dfTemp], ignore_index=True)

        else:
            dfDay = pd.DataFrame(dayData, columns=['wAC', 'wDC'])
        
        #drop oldest row if more than 24 hours
        while len(dfDay) > 30:
            dfDay.drop(0, axis=0, inplace=True)

        dfDay.to_csv('/home/pi/Desktop/Day.csv', index = False)
        #logging.debug(u'Daily saved to file')
        
        os.remove("/home/pi/Desktop/Hour2Daily.csv")
         
        del df
        del dfDay
        del dfTemp            
      

  return measureList

# Set up plot to call animate() function periodically
ani = animation.FuncAnimation(fig, animate, fargs=(xs, ysTemp, ysAC, ysDC), interval=1000, blit=False)
plt.get_current_fig_manager().full_screen_toggle()
plt.ioff()
plt.show()
plt.draw()
