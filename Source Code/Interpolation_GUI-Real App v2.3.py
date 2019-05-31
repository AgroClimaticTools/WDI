from PyQt4.QtCore import *
from PyQt4.QtGui import *
import sys,os,time
from numpy import *
import numpy.core._methods
import numpy.lib.format
from scipy.interpolate import griddata
from math import pow,sqrt
from os import listdir
from os.path import isfile, join

def pointValue(x,y,power,xv,yv,values,radius):  
    nominator=0  
    denominator=0
    D=[]
    for i in range(0,len(values)):
        dist = sqrt((x-xv[i])*(x-xv[i])+(y-yv[i])*(y-yv[i]))
        D.append(float(dist))        
        #If the point is really close to one of the data points, return the data point value to avoid singularities 
        if(dist<0.0000000001):
            return values[i]
        elif(dist>0.0000000001 and dist<radius):
            nominator=nominator+(values[i]/pow(dist,power))  
            denominator=denominator+(1/pow(dist,power))
    #Return NODATA if the denominator is zero  
    if denominator > 0:  
        value = nominator/denominator  
    else:  
        value = 'NaN'  
    return value  

def IDW(xv,yv,values,xi,yi,radius,power=2):  
    valuesGrid = zeros((len(yi),len(xi[0])))  
    for x in range(0,len(xi)):  
        for y in range(0,len(yi[0])):  
            valuesGrid[x][y] = pointValue(xi[x][y],yi[x][y],power,xv,yv,values,radius)
    return valuesGrid

class TitleBar(QDialog):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        self.setWindowFlags(Qt.FramelessWindowHint)
        StyleTitleBar='''QDialog{
background-color: rgb(2,36,88);
}
QLabel{
color: rgb(0, 255, 255);
font: 11pt "MS Shell Dlg 2";
}'''
        self.setStyleSheet(StyleTitleBar)
        self.setAutoFillBackground(True)
##        self.adjustSize()
        self.setFixedSize(700,30)
        Style_minimize='''QToolButton{
background-color: transparent;
color: rgb(255, 255, 255);
border: none;
}
QToolButton:hover{
background-color: rgb(66, 131, 221,230);
border: none;
}'''
        Style_close='''QToolButton{
background-color: rgb(217, 0, 0);
color: rgb(255, 255, 255);
border: none;
}
QToolButton:hover{
background-color: rgb(255, 0, 0);
border: none;
}'''
        Font=QFont('MS Shell Dlg 2',11)
        Font.setBold(True)
        
        self.minimize = QToolButton(self)
        self.minimize.setText('–')
        self.minimize.setFixedHeight(20)
        self.minimize.setFixedWidth(25)
        self.minimize.setStyleSheet(Style_minimize)
        self.minimize.setFont(Font)
        
        self.close = QToolButton(self)
        self.close.setText(u"\u00D7")
        self.close.setFixedHeight(20)
        self.close.setFixedWidth(45)
        self.close.setStyleSheet(Style_close)
        self.close.setFont(Font)

        image = QPixmap("Interpolation-2.png")
        labelImg =QLabel(self)
        labelImg.setFixedSize(QSize(20,20))
        labelImg.setScaledContents(True)
        labelImg.setPixmap(image)
        labelImg.setStyleSheet('border: none;')
        label = QLabel(self)
        label.setText("  Weather Data Interpolator")
        label.setFont(Font)
        label.setStyleSheet('border: none;')
        hbox=QHBoxLayout(self)
        hbox.addWidget(labelImg)
        hbox.addWidget(label)
        hbox.addWidget(self.minimize)
        hbox.addWidget(self.close)
        hbox.insertStretch(2,600)
        hbox.setSpacing(1)
        hbox.setContentsMargins(5,0,5,0)
        
        self.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Fixed)
        self.maxNormal=False
        self.close.clicked.connect(self.closeApp)
        self.minimize.clicked.connect(self.showSmall)

    def showSmall(self):
        widget.showMinimized();

    def closeApp(self):
        widget.close()

    def mousePressEvent(self,event):
        if event.button() == Qt.LeftButton:
            widget.moving = True
            widget.offset = event.pos()

    def mouseMoveEvent(self,event):
        if widget.moving:
            widget.move(event.globalPos()-widget.offset)

        

class Interpolation(QWidget):
    def __init__(self, parent=None):
        super(Interpolation,self).__init__(parent)
        
        grid = QGridLayout()
        self.m_titlebar=TitleBar(self)
        grid.addWidget(self.m_titlebar, 0, 0)
        grid.addWidget(self.input(), 1, 0)
        grid.addWidget(self.output(), 2, 0)
        grid.addWidget(self.method(), 3, 0)
        grid.addWidget(self.progress(), 4, 0)
        self.setLayout(grid)
        grid.setContentsMargins(0,0,0,0)

##        self.setWindowTitle("Weather Data Interpolator")
        self.setFocus()
        self.adjustSize()
        self.Widget_Width  = self.frameGeometry().width()
        self.Widget_Height = self.frameGeometry().height()
##        print(self.Widget_Width,self.Widget_Height)
        self.setFixedSize(700,self.Widget_Height)
        
##        self.move(350,100)
        self.setWindowFlags(Qt.FramelessWindowHint)
##        self.setWindowFlags(Qt.WindowMaximizeButtonHint)
        self.started = False
        
    def input(self):

        ##########Layout for taking Lat-Lon Details and Climate data to be interpolated in Excel format##########

        gBox = QGroupBox("Inputs:")
        layout1 = QGridLayout()
        
        #input_label = QLabel("Inputs:")
        
        self.weatherfile_location = QLineEdit()
        self.browse2 = QPushButton("...")
        self.browse2.setMaximumWidth(25)
        self.browse2.clicked.connect(self.browse2_file)
        self.q1 = QPushButton("?")
        self.q1.setMaximumWidth(15)
        self.q1.clicked.connect(self.Info1)
        self.weatherfile_location.setPlaceholderText("Folder containing climate data to be interpolated (.csv or .txt)")
        #layout1.addWidget(input_label,0,0)
        layout1.addWidget(self.weatherfile_location,1,0,1,3)
        layout1.addWidget(self.q1,1,3,1,1)
        layout1.addWidget(self.browse2,1,4,1,1)

        ##########Layout for taking comma delimited vs tab delimited################################

        sublayout1 = QGridLayout()

        self.label1 = QLabel("Input Format:\t")
        self.b1 = QRadioButton("Comma Delimated (.csv)")
        #self.b1.setChecked(True)
        self.b2 = QRadioButton("Tab Delimited (.txt)")

        self.b1.toggled.connect(lambda:self.btnstate(self.b1))
        self.b2.toggled.connect(lambda:self.btnstate(self.b2))

        sublayout1.addWidget(self.label1,1,0)
        sublayout1.addWidget(self.b1,1,1)
        sublayout1.addWidget(self.b2,1,2)
        layout1.addLayout(sublayout1,2,0)

        ##########Layout for shape file##########

        self.LatLonfile_location = QLineEdit()
        self.LatLonfile_location.setPlaceholderText("Interpolation Points/Grids/Stations csv file (.csv)")
        self.q2 = QPushButton("?")
        self.q2.setMaximumWidth(15)
        self.q2.clicked.connect(self.Info2)
        self.browse3 = QPushButton("...")
        self.browse3.setMaximumWidth(25)
        self.browse3.clicked.connect(self.browse3_file)
        layout1.addWidget(self.LatLonfile_location,4,0,1,3)
        layout1.addWidget(self.q2,4,3,1,1)
        layout1.addWidget(self.browse3,4,4,1,1)
        gBox.setLayout(layout1)
        return gBox


    def output(self):

        ##########Layout for output file location and interpolation##########

        gBox = QGroupBox("Outputs:")
        layout4 = QGridLayout()
        
        self.outputfile_location = QLineEdit()
        self.outputfile_location.setPlaceholderText("Folder for interpolated climate data (.csv or .txt)")
        self.browse4 = QPushButton("...")
        self.browse4.setMaximumWidth(25)
        self.browse4.clicked.connect(self.browse4_file)
        layout4.addWidget(self.outputfile_location,1,0,1,3)
        layout4.addWidget(self.browse4,1,3,1,1)

        ########################Layout for taking comma delimited vs tab delimited################################

        sublayout2 = QGridLayout()
        output_label = QLabel("Output Format:\t")
        self.b3 = QRadioButton("Comma Delimated (.csv)")
        #self.b3.setChecked(True)
        self.b4 = QRadioButton("Tab Delimited (.txt)")

        self.b3.toggled.connect(lambda:self.btn2state(self.b3))
        self.b4.toggled.connect(lambda:self.btn2state(self.b4))
        
        sublayout2.addWidget(output_label,1,0)
        sublayout2.addWidget(self.b3,1,1)
        sublayout2.addWidget(self.b4,1,2)
        layout4.addLayout(sublayout2,2,0)
        gBox.setLayout(layout4)
        return gBox

    def method(self):

        ########################Layout for taking methods of interpolation################################
        gBox = QGroupBox("Methods:")
        layout5 = QGridLayout()
        self.b5 = QRadioButton("Linear")
        #self.b3.setChecked(True)
        self.b6 = QRadioButton("IDW")

        self.b5.toggled.connect(lambda:self.btn3state(self.b5))
        self.b6.toggled.connect(lambda:self.btn3state(self.b6))
        self.show_hide = QPushButton("Show Details")
        Font=QFont()
        Font.setBold(True)
        #self.show_hide.setFont(Font)
        self.show_hide.setCheckable(True)
        #self.show_hide.toggle()
        self.show_hide.clicked.connect(self.ShowHide)
        self.show_hide.setFixedWidth(90)
        self.show_hide.setFixedHeight(25)
        Style_show_hide_Button = """
QPushButton{
color: rgb(255, 255, 255);
background-color: rgb(66, 131, 221);
border: none;
}
QPushButton:Checked{
background-color: rgb(66, 131, 221);
border: none;
}
QPushButton:hover{
background-color: rgb(66, 131, 221,230);
border: none;
}
"""
        self.show_hide.setStyleSheet(Style_show_hide_Button)
        
        self.start = QPushButton("Interpolate")

        self.start.setFixedWidth(85)
        self.start.setFixedHeight(25)
        Style_Interpolate_Button = """
QPushButton{
color: rgb(255, 255, 255);
background-color: rgb(0,121,0);
border-color: none;
border: none;
}
QPushButton:hover{
background-color: rgb(0,121,0,230);
}
"""
        self.start.clicked.connect(self.start_interpolation)
        #self.start.setFont(Font)
        self.start.setStyleSheet(Style_Interpolate_Button)
        
        self.stop = QPushButton("Cancel")
        self.stop.setMaximumWidth(65)
        self.stop.setFixedHeight(25)
        Style_Cancel_Button = """
QPushButton{
color: rgb(255, 255, 255);
background-color: rgb(180,0,0,240);
border-color: none;
border: none;
}
QPushButton:hover{
background-color: rgb(180,0,0,220);
}
"""
        self.stop.clicked.connect(self.stop_interpolation)
        #self.stop.setFont(Font)
        self.stop.setStyleSheet(Style_Cancel_Button)
        
        layout5.addWidget(self.b5,1,1)
        layout5.addWidget(self.b6,1,2)
        layout5.addWidget(self.show_hide,1,3)
        layout5.addWidget(self.start,1,4)
        layout5.addWidget(self.stop,1,5)
        
        gBox.setLayout(layout5)
        return gBox


        ##########Layout for progress of interpolation##########
    def progress(self):
        gBox = QGroupBox()
        layout6 = QVBoxLayout() 
        
        STYLE2 = """
QProgressBar{
text-align: center;
}
QProgressBar::chunk {
background-color: rgb(0,121,0);
}
"""
        self.progressbar = QProgressBar()
        self.progressbarfinal = QProgressBar()
        #self.progressbar.setMinimum(1)
        self.progressbar.setFixedHeight(13)
        self.progressbarfinal.setFixedHeight(13)
        self.progressbar.setStyleSheet(STYLE2)
        self.progressbarfinal.setStyleSheet(STYLE2)
        self.textbox = QTextEdit()
        self.textbox.setReadOnly(True)
        self.textbox.moveCursor(QTextCursor.End)
        self.textbox.hide()
        self.scrollbar = self.textbox.verticalScrollBar()
        
        layout6.addWidget(self.progressbar)
        layout6.addWidget(self.progressbarfinal)
        layout6.addWidget(self.textbox)
        gBox.setLayout(layout6)
        return gBox        
    
    def browse2_file(self):
        weather_file = QFileDialog.getExistingDirectory(self,"Open Folder", r"C:\Users\Madhuri\OneDrive\0. M.Tech. Research Work\Codes\GUIs\Interpolation",
                                                        QFileDialog.ShowDirsOnly)
        self.weatherfile_location.setText(QDir.toNativeSeparators(weather_file))
        
    def browse3_file(self):
        LatLon_file = QFileDialog.getOpenFileName(self,caption = "Open File", directory=r"C:\Users\Madhuri\OneDrive\0. M.Tech. Research Work\Codes\GUIs\Interpolation",
                                                filter="Stations file (*.csv)")
        self.LatLonfile_location.setText(QDir.toNativeSeparators(LatLon_file))
        
    def browse4_file(self):
        output_file = QFileDialog.getExistingDirectory(self, "Save File in Folder", r"C:\Users\Madhuri\OneDrive\0. M.Tech. Research Work\Codes\GUIs\Interpolation",
                                                       QFileDialog.ShowDirsOnly)
        self.outputfile_location.setText(QDir.toNativeSeparators(output_file))  

    def Info1(self):
        QMessageBox.information(self, "Information About Input Files",
                                '''Sample input (.csv or .txt) should be same as it is shown in Sample Example:\nC:\Program Files (x86)\Weather Data Interpolator\Sample.csv
                                ''')
    def Info2(self):
        QMessageBox.information(self, "Information About Interpolation Grid/Point/Station File",
                                "Station file (.csv) should contain first column as latitude and second column as longitude of centroid of each grid. For example:\nC:\Program Files (x86)\Weather Data Interpolator\IND_1x1.csv")

    def btnstate(self,b):
        if b.text() == "Comma Delimated (.csv)" and b.isChecked() == True:
            self.seperator = ','
            self.seperatorname = '.csv'
        if b.text() == "Tab Delimited (.txt)" and b.isChecked() == True:
            self.seperator = '\t'
            self.seperatorname = '.txt'

    def btn2state(self,b):
        if b.text() == "Comma Delimated (.csv)" and b.isChecked() == True:
            self.seperator2 = ','
            self.seperatorname2 = '.csv'
        if b.text() == "Tab Delimited (.txt)" and b.isChecked() == True:
            self.seperator2 = '\t'
            self.seperatorname2 = '.txt'

    def btn3state(self,b):
        if b.text() == "Linear" and b.isChecked() == True:
            self.methodname = b.text()
        if b.text() == "IDW" and b.isChecked() == True:
            self.methodname = b.text()
    
    def start_interpolation(self):
        if not self.started:
            self.started = True
            self.Interpolate()

    def stop_interpolation(self):
        if self.started:
            self.started = False
            QMessageBox.information(self, "Information", "Interpolation is cancelled.")

    def ShowHide(self):
        if self.show_hide.text() == "Hide Details" and self.show_hide.isChecked() == False:
            self.show_hide.setText('Show Details')
            self.textbox.hide()
##            self.adjustSize()
            self.setFixedSize(700,self.Widget_Height+1)
##            print (self.frameGeometry().width(),self.frameGeometry().height())
        if self.show_hide.text() == "Show Details" and self.show_hide.isChecked() == True:
            self.show_hide.setText('Hide Details')
            self.textbox.show()
##            self.adjustSize()
            self.setFixedSize(700,self.Widget_Height+self.Widget_Height*2/3)
##            print (self.frameGeometry().width(),self.frameGeometry().height())
        
    def Interpolate(self):
        if self.weatherfile_location.text() == "":
            QMessageBox.critical(self, "Message", "Location of folder containing climate data files is not given.")
            self.started = False
        if self.LatLonfile_location.text() == "":
            QMessageBox.critical(self, "Message", "Lot Lon file (.csv) location is not given.")
            self.started = False
        if self.outputfile_location.text() == "":
            QMessageBox.critical(self, "Message", "Output location to store the interpolated files is not given")
            self.started = False

        try:
            sep = self.seperator
            sepname = self.seperatorname

            sep2 = self.seperator2
            sepname2 = self.seperatorname2
        except:
            QMessageBox.critical(self, "Message", "Format is not defined.")
            self.started = False
        try:
            method = self.methodname
        except:
            QMessageBox.critical(self, "Message", "Method of interpolation is not defined.")
            self.started = False
        
        self.textbox.setText("")
        ############# grid_x = Longitude, grid_y = Latitude ##############
        start = time.time()
        self.progressbarfinal.setMinimum(0)
        self.progressbarfinal.setValue(0)
        self.progressbar.setMinimum(0)
        self.progressbar.setValue(0)

        LatLon_loc = self.LatLonfile_location.text()
        if os.path.isfile(LatLon_loc):
            with open(LatLon_loc) as Fstation:
                Lat_Lon_List = Fstation.readlines()
                record = []
                for line in Lat_Lon_List:
                    record.append([word for word in line.split(",")  if word])

                Lat = [float(record[j][0]) for j in range(1, len(record))]
                Lon = [float(record[j][1]) for j in range(1, len(record))]
##            record = [r for r in table]

            latlon = [[Lat[i], Lon[i]] for i in range(len(Lat))]
            try:
                lat_diff = min([abs(Lat[0]-Lat[i]) for i in range(len(Lat)) if abs(Lat[0]-Lat[i])>0])
                lon_diff = min([abs(Lon[0]-Lon[i]) for i in range(len(Lon)) if abs(Lon[0]-Lon[i])>0])
                grid_x, grid_y = mgrid[min(Lon):max(Lon)+lon_diff:lon_diff,
                                       min(Lat):max(Lat)+lat_diff:lat_diff]
            except:
                grid_x, grid_y = mgrid[min(Lon):max(Lon)+2:1,
                                       min(Lat):max(Lat)+2:1]

        path = self.weatherfile_location.text()
        Out_path = self.outputfile_location.text()
        if os.path.isdir(path) or os.path.isdir(Out_path):
            weatherfiles = [join(path,f) for f in listdir(path) if isfile(join(path,f)) and str(sepname) in  f]
            weather = [f for f in listdir(path) if isfile(join(path,f)) and str(sepname) in  f]
            if len(weather) == 0:
                weatherfiles = []
                QMessageBox.critical(self, "Invalid Path", "Input folder does not contain any file (.csv or .txt).")
                self.started = False
        else:
            weatherfiles = []
            QMessageBox.critical(self, "Message", "Invalid Path.")
            self.started = False

        NoLines = 0
        for j in range(len(weatherfiles)):
            with open(weatherfiles[j]) as f:
                line = [line for line in f]
            NoLines = NoLines + len(line) 
                
        n = 0
        for j in range(len(weatherfiles)):
            self.progressbar.setValue(0)
            D = []
            with open(weatherfiles[j]) as f:
                line = [line for line in f]
                w = [w for w in line[0].split(',') if w]
            for i in range(4):
                D.append([word for word in line[i].split(",") if word])

            ncols = len(D[0])
            a=[[] for x in range(1,ncols)]
            for c in range(1,ncols):
                a[c-1].append(float(D[1][c])) #Longitude
                a[c-1].append(float(D[0][c])) #Latitude

            px = [float(D[1][c]) for c in range(1,ncols)] #Longitude
            py = [float(D[0][c]) for c in range(1,ncols)] #Latitude

            px = array(px)
            py = array(py)
            p = array(a)
            if sep2 ==',':
                filename = "%s\%s" % (Out_path, weather[j][:-4]+'.csv')
                file = open(filename,"w")
            if sep2 =='\t':
                filename = "%s\%s" % (Out_path, weather[j][:-4]+'.txt')
                file = open(filename,"w")
                
            rainvalues = array([float(D[2][x]) for x in range(1,ncols)])
            radius = 1
            if method == 'Linear':
                grid_rain = griddata(p, rainvalues, (grid_x, grid_y), method='linear')
            if method == 'IDW':
                grid_rain = IDW(px, py, rainvalues, grid_x, grid_y, radius, 2)
            LatData = ['N']
            LonData = ['E']
            
            for lat in range(len(grid_rain[1])):
                for lon in range(len(grid_rain)):
                    if [grid_y[lon][lat],grid_x[lon][lat]] in latlon and (str(grid_rain[lon][lat]) != 'nan'):
                        LatData.append(str("%.2f" % grid_y[lon][lat]))
                        LonData.append(str("%.2f" % grid_x[lon][lat]))
            
            CommaDelimatedLat = sep2.join([str(LatData[i]) for i in range(len(LatData))])
            CommaDelimatedLon = sep2.join([str(LonData[i]) for i in range(len(LonData))])
            file.write(CommaDelimatedLat+'\n')
            file.write(CommaDelimatedLon+'\n')
            app.processEvents()

            
            for row in range(2,len(line)):
                if self.started:
                    Data = [word for word in line[row].split(",") if word]
                    try:
                        rainvalues = array([float(Data[x]) for x in range(1,len(Data))])
                        if method == 'Linear':
                            grid_rain = griddata(p, rainvalues, (grid_x, grid_y), method='linear')
                        if method == 'IDW':
                            grid_rain = IDW(px, py, rainvalues, grid_x, grid_y, radius, 2)
                        InterpolatedData = [Data[0]]
                        #print (len(grid_rain[1]),len(grid_rain))
                        
                        for lat in range(len(grid_rain[1])):
                            for lon in range(len(grid_rain)):
                                if [grid_y[lon][lat],grid_x[lon][lat]] in latlon and (str(grid_rain[lon][lat]) != 'nan'):
                                    InterpolatedData.append("%.1f" % grid_rain[lon][lat])
                                    
                        CommaDelimatedData = sep2.join([str(InterpolatedData[i]) for i in range(len(InterpolatedData))])
                        file.write(CommaDelimatedData+'\n')                
                        if (row-1)%10 == 1 and (row+1) != 11:
                            self.textbox.append("Interpolating %dst day data" % (row-1))
                        elif (row-1)%10 == 2:
                            self.textbox.append("Interpolating %dnd day data" % (row-1))
                        elif (row-1)%10 == 3:
                            self.textbox.append("Interpolating %drd day data" % (row-1))
                        else:
                            self.textbox.append("Interpolating %dth day data" % (row-1))
                        app.processEvents()
                        self.scrollbar.setValue(self.scrollbar.maximum())
                        self.progressbar.setValue(row-1)
                        self.progressbar.setMaximum(len(line)-2)
                        self.progressbarfinal.setValue(n+1)
                        self.progressbarfinal.setMaximum(NoLines-2*len(weatherfiles))
                        n=n+1
                    except Exception as e:
                        self.textbox.append(str(e))
                else:
                    self.progressbarfinal.setValue(0)
                    self.progressbar.setValue(0)
                
            file.close()
        end = time.time()
        t = end-start
        if NoLines>0 and self.started:
            self.textbox.append("Total time taken in Interpolation: %.2d:%.2d:%.2d" % (t/3600,(t%3600)/60,t%60))
            QMessageBox.information(self, "Information", "Interpolation is completed.")
        
       
app = QApplication(sys.argv)
widget = Interpolation()
app_icon = QIcon()
app_icon.addFile(r'C:\python34\Interpolation-2.png', QSize(40,40))
app.setWindowIcon(app_icon)
pixmap = QPixmap("Splash_Window.png")
splash = QSplashScreen(pixmap)
splash.show()
#widget.setFixedWidth(500)
#widget.setFixedHeight(400)
screen_resolution = app.desktop().screenGeometry()
width, height = screen_resolution.width(), screen_resolution.height()
widget.move(width/2-widget.width()/2,height/2-widget.height()/2)
time.sleep(2)
widget.show()
splash.finish(widget)
app.exec_()
