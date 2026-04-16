# -*- coding: utf-8 -*-
"""
Created on Mon Jun 27 19:19:33 2022

@author: Valdespino Mendieta Joaquin 

Version - 1.2


BIBLIOTECAS
""" 
import socket
import sys
import os
import time
from time import sleep
from datetime import datetime as dt
from datetime import timedelta
import threading
from PyQt5 import uic, QtWidgets
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtCore import QThread


qtCreatorFile = "IF-DataAdquisitionSystem.ui" # Nombre del archivo aquí.

Ui_MainWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)

class Worker(QObject):
    ##señales
    finished = pyqtSignal()  ##señal mandada al terminar la ejecucion del worker
    connect = pyqtSignal()  ##señar usada para habilitar y deshabilitar elementos graficos al iniciar
    progress = pyqtSignal(int) ##señal para actualizar el progress bar y los contadores de paquetes
    timepro = pyqtSignal(str) ## señal para actualizar el contador de tiempo
    timepb = pyqtSignal(int) ## señal para actualizar el progress bar por tiempo
    ##variables de ayuda
    mode = 0 ## selecciona el modo de ejecucion, 1 por paquetes o 2 por tiempo
    path = "" ##ruta deñ archivo para escribir la data obtenida
    tiempom = 0 ##variable que guarda el tiempo de la interfaz
    pack = 0   ##guarda la cantidad de paquetes
    flag =  0  ##bandera para terminar con la ejecucion de los ciclos, ligado al boton cancelar.
    start = 0   ##tiempo de inicio
    end = 0     ##tiempo final 
    inter = 0   ##variable para enviar señales intermedias de tiempo y actualizar marcador de tiempo
    
    def inicializar(self,modo,fullpath,tiempo,paquetes):  ##con esta "definicion de clase" 
    #inicializamos las variables para iniciar el proceso de ejecucion del hilo 
        self.mode = modo
        self.path = fullpath 
        self.tiempom = tiempo
        self.pack = paquetes
        

    def run(self): ##funcion para correr el hilo, el cual contiene la logica para adquirir y escribir los paquetes y mandar señales de actualizacion de interfaz
        """Long-running task."""
        ip = '192.168.0.10' # 128.197.41.10 | 192.168.0.10
        puerto = 0x505 #1285
        counter = 0
        
        print(self.tiempom)
        print(self.mode)
        print(self.path)
        print(self.pack)
        
        print("antes")
        try:
            sock = socket.socket( socket.AF_INET, socket.SOCK_DGRAM ,0) ##iniciamos el socket UDP para la adquisicion de datos
            sock.bind((ip, puerto)) ##usamos el ip y el puerto  para conectar
       
        
            self.connect.emit()
            fd = open(self.path,"wb") # apertura del archivo, tener en cuenta w para escribir y b para escritura de bits
    
            self.start = time.time() 
            startsignal = dt.now()
            timeout = self.start + (self.tiempom * 60) ##ajuste de tiempo de minutos a segundos
    
            if self.mode == 1: ##por numero de paquetes
                i=0
                for i in range(self.pack):
                    #sleep(0.25)
                    socketdata = sock.recv(9000) ##socketdata , addr  recibimos un paquete
                    fd.write(socketdata) ##escribimos los bits en el archivo
                    counter = counter+1
                    self.progress.emit(counter)  ##mandamos actualizacion de paquetes -> interfaz
                    datesignal = dt.now() - startsignal
                    self.timepro.emit(str(datesignal)) ##actualizamos el tiempo -> interfaz
                    if self.flag == 1: ##si  se presiona cancelar termina la ejecución
                        print(" se pudo cambiar - terminando ")
                        self.flag = 0;
                        break
            
            elif self.mode == 2: #por tiempo
                while True:
                    #sleep(0.25)
                    socketdata = sock.recv(9000) ##socketdata , addr
                    fd.write(socketdata)
                    counter = counter+1
                    self.progress.emit(counter)
                
                    datesignal = dt.now() - startsignal
                    progressbars = time.time() - self.start
                    self.timepro.emit(str(datesignal))  
                    self.timepb.emit(int(progressbars)) ##Esta señal exclusiva de este modo actualiza el progress bar por tiempo
                
                    if self.flag == 1:
                        print(" se pudo cambiar - terminando ")
                        self.flag = 0;
                        break
                    if time.time() >= timeout: ##en caso de llegar al tiempo o superar el tiempo limite dado por el usuario termina la ejecución
                        print("termino por tiempo")
                        break
    
            fd.close()  
    
            self.end = time.time() ##tiempo final
            
            sock.close() ##cerramos el socket y la conexion
        except Exception:  ##en caso de error terminar la ejecución 
            print("Error de conexion")
            self.finished.emit()
        #self.progress.emit(self.start-self.end)
        self.finished.emit() ##señal de termino del proceso del worker

#############################################################################
class MyApp(QtWidgets.QMainWindow, Ui_MainWindow):  ##clase para cargar la interfaz y conectar los elementos y dar funcionalidad
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)
        self.setupUi(self)
        
        ##BOTONES ligados a funciones
        self.Buscar.clicked.connect(self.directoryshow) ##boton  para buscar un directorio
        self.botoninit()  ##inicializacion del boton para iniciar el proceso de captura
        self.Cancelar.clicked.connect(self.Changeflag)
        self.Cancelar.setEnabled(False) ##ponemos desactivado el boton de cancelar
        
        ##botones clase radioButton - solo puede haber un radiobutton activo a la vez
        self.radioBMode1.clicked.connect(self.setMode1)
        self.radioBMode2.clicked.connect(self.setMode2)
        #self.Mtiempo.clicked.connect(self.MostrarTiempo)
        ##elementos auxiliares (atributos extra)
        self.flag = 0
        self.start = 0
        self.end = 0
        self.confirm =0
        self.modeT = 0
        self.worker = Worker()
        self.date = dt.now()
        
    def setMode1(self): ##cambiar a modo paquetes
        self.modeT = 1
        print(self.modeT)
    
    def setMode2(self): ##cambiar a  modo tiempo
        self.modeT = 2
        print(self.modeT)
        
    def botoninit(self):  ##boton 
        self.Iniciar.clicked.connect(self.Adquisicion) ##conexion para el boton de iniciar adquisición
        
    def directoryshow(self): 
        #self.pathFolder.setText("Boton press")
        Folderpath= str(QFileDialog.getExistingDirectory(self, "Open Directory", "")) ##abre una ventana emergente para buscar el directorio a elegir
        self.pathFolder.setText(Folderpath) ##coloca la ruta en la interfaz
        
    def crearHilo(self): ##no se usa - posible manera alternativa de manejar hilos -aumenta la complejidad.
        self.hilo = threading.Thread(target=self.Adquisicion)
        self.hilo.start()
        
       

        
    def Adquisicion(self): ##conexiones e inicializaciones para correr el worker a partir de un hilo proporcionado por PYQT5
        
        Modo = self.modeT
        print("el modo es "+str(Modo))
        ##time counter
        pathfull = self.pathFolder.toPlainText() +"/" + self.NameArch.toPlainText()+".raw" #generacion de la ruta para creacion del archivo
        print (pathfull)
        #obtencion de los parametros de ejecucion 
        tiempo = int(self.tiempo.value()) 
        paquetes = int( self.paquetes.value())
        
        if self.pathFolder.toPlainText() == "" or self.NameArch.toPlainText() == "" or ( Modo == 1 and paquetes <=0) or (Modo == 2 and tiempo<=0) or Modo == 0:
            #mandamos mensaje
            self.Message.setText("LLene los campos - directorio, nombre, o numero de tiempo o paquetes segun sea el caso elegido")
            
        elif os.path.exists(pathfull)==True:
            ##mandamos mensaje
            self.Message.setText("El archivo ya existe cambie el nombre")
            
        else: 
            #paso 1 iniciamos el objeto
            self.worker = Worker()
            # paso 2: Creamos un objeto QThread que es un hilo propio de QT para manejar sus instancias graficas
            self.thread = QThread()
            # paso 3: ajustamos el tipo de progress bar - seguira tiempo o seguira los paquetes
            if Modo == 1: self.barrap.setMaximum(paquetes)
            if Modo == 2: self.barrap.setMaximum(tiempo*60)
            
            self.date = dt.now()
            
            self.worker.inicializar(Modo,pathfull,tiempo,paquetes)
            # paso 4: Movemos el worker al hilo
            self.worker.moveToThread(self.thread)
            # paso 5: Conectamos las señales y los elementos de funcionalidad - metodos
            #elementos esenciales del worker
            self.thread.started.connect(self.worker.run)
            self.worker.finished.connect(self.thread.quit)
            self.worker.finished.connect(self.worker.deleteLater)
            self.thread.finished.connect(self.thread.deleteLater)
            
            ##elementos creados por nosotros 
            self.worker.progress.connect(self.reportProgress)
            self.worker.timepro.connect(self.reportTime)
            self.worker.timepb.connect(self.reportProgressbar)
            self.worker.connect.connect(self.changecancel)
            #self.worker.flag.connect(self.Cancelar.clicked.connect(self.Changeflag))
            # paso 6: Start - Thread
            self.thread.start()

            # Resets al finalizar la tarea del worker

            self.thread.finished.connect(
                lambda: self.Iniciar.setEnabled(True) #al finalizar reactivamos el boton iniciar
                )
            self.thread.finished.connect(
                lambda: self.Message.setText("termino con un tiempo de: "+ str(round(self.worker.end-self.worker.start,2))) ##al finalizar damos el tiempo de ejecución
                )
            self.thread.finished.connect(
                lambda: self.Cancelar.setEnabled(False) ##al finalizar desactivamos el boton cancelar
                )
            self.thread.finished.connect(
                lambda: self.reportLog() ##al finalizar creamos el LOG 
                )
            
    
    def changecancel(self): ##METODO CUANDO SE PULSA EL BOTON INICIAR, DESACTIVAMOS EL BOTON INICIAR Y ACTIVAMOS EL BOTON CANCELAR
            self.Iniciar.setEnabled(False)
            self.Cancelar.setEnabled(True)
    
    def reportLog(self): ##METODO PARA REALIZAR EL LOG - BASICAMENTE RECOPILAMOS LA INFORMACION DE LOS ELEMENTOS GRAFICOS EN SU ESTADO ACTUAL
        pathdoc = self.pathFolder.toPlainText() +"/" + self.NameArch.toPlainText()+".txt"  
        log  = open(pathdoc,"w") ##Abrimos el archivo
        log.write(pathdoc+"\n\n")
        log.write("Inicio de adquisición: "+str(self.date)+"\n\n")
        log.write("Finalización de adquisición: "+str(dt.now())+"\n\n")
        
        if self.modeT == 1: log.write("Modo: Paquetes -> "+str(self.paquetes.value())+" paquetes \n\n")
        if self.modeT == 2: log.write("Modo: Tiempo ->"+str(self.tiempo.value())+" min \n\n")
        
        log.write("Tiempo De ejecucion: "+str(self.Ttiempo.toPlainText())+"\n\n")
        log.write("Paquetes Capturados: "+str(self.Tpaquetes.toPlainText())+"\n\n")
        
        log.write("Tipo de Adquisición: "+str(self.TipoAdq.currentText())+"\n\n")
        log.write("Tipo de Fuente: "+str(self.Fuente.currentText())+"\n\n")
        if self.Fuente.currentText() == "Otro": log.write("Otro: "+str(self.Otro.toPlainText())+"\n\n")
        
        log.write("PANEL A \n\n")
        if self.A1.isChecked(): log.write("A1 ")
        if self.A2.isChecked(): log.write("A2 ")
        if self.A3.isChecked(): log.write("A3 ")
        if self.A4.isChecked(): log.write("A4 ")
        if self.A5.isChecked(): log.write("A5 ")
        if self.A6.isChecked(): log.write("A6 ")
        if self.A7.isChecked(): log.write("A7 ")
        if self.A8.isChecked(): log.write("A8 ")
        if self.A9.isChecked(): log.write("A9 ")
        log.write("\n\n")
        log.write("PANEL B \n\n")
        if self.B1.isChecked(): log.write("B1 ")
        if self.B2.isChecked(): log.write("B2 ")
        if self.B3.isChecked(): log.write("B3 ")
        if self.B4.isChecked(): log.write("B4 ")
        if self.B5.isChecked(): log.write("B5 ")
        if self.B6.isChecked(): log.write("B6 ")
        if self.B7.isChecked(): log.write("B7 ")
        if self.B8.isChecked(): log.write("B8 ")
        if self.B9.isChecked(): log.write("B9 ")
        log.write("\n\nCOMENTARIOS \n\n")
            
        log.write(str(self.comentario.toPlainText()))
        
        log.close()
        
        
    def reportProgressbar(self,x): ##Actualizacion del progress bar en caso del modo tiempo
        self.barrap.setValue(x)
        
        
    def reportProgress(self, n): ##actualizacion del elemento que muestra la cantidad de paquetes y el progress bar en caso de modo paquetes
        self.Tpaquetes.setText(str(n))
        if self.modeT ==1: self.barrap.setValue(n)
        
    def reportTime(self, ti): ##actualiza el elemento de la interfaz que contiene el tiempo transcurrido
        self.Ttiempo.setText(ti)
        
        
    def MostrarTiempo(self): ###muestra mensaje terminacion - no se usa
        self.Message.setText("Se han adquirido los datos con un tiempo de:"+ str(self.end-self.start))    
        
        
    def Changeflag(self):  ## metodo que se conecta al boton cancelar, para cambiar la bandera y de esta forma terminar los ciclos del worker
    
        if self.confirm == 0: ##PRESIONA UNA VEZ EL BOTON
            self.Message.setText("Seguro que quieres cancelar? presiona otra vez el boton otra vez para cancelar")
            self.confirm = 1
        else: ##PRESIONA UNA SEGUNDA VEZ EL BOTON
            self.flag = 1
            self.worker.flag = 1
            self.confirm =0
            print("enviar flag")
        
        ##MAIN - NO SE MODIFICA NADA AQUI
if __name__ == "__main__":
    app =  QtWidgets.QApplication(sys.argv)
    window = MyApp()
    window.show()
    sys.exit(app.exec_())