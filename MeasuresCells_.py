# -*- coding: iso-8859-15 -*-
from ij import ImageStack, ImagePlus, WindowManager
from ij.gui import Roi, NonBlockingGenericDialog, Overlay
from ij.process import ImageProcessor
from ij.plugin.frame import RoiManager

from java.awt import TextField, Panel, GridLayout, ComponentOrientation, Label, Checkbox, BorderLayout, Button, Color, Font, Rectangle, Frame, FileDialog
from java.lang import Double,Boolean,Float
from java.awt.event import MouseAdapter,MouseEvent

from javax.swing import JOptionPane,JFrame, JPanel

import sys
import os
import time
import glob
import os.path as path
import getpass
import shutil
import tempfile

username=getpass.getuser()

mypath=os.path.expanduser(IJ.getDirectory("plugins")+"MeasureCells")
#mypath=os.path.expanduser("~/Dropbox/MacrosDropBox/py/MeasureCells_9")
sys.path.append(mypath)

from org.python.core import codecs
codecs.setDefaultEncoding('utf-8')

from MorphoBact import Morph
from BacteriaCell import Bacteria_Cell
from LinkRoisAB import link
from RangeRois import RangeRois
from BacteriaTracking import Bacteria_Tracking
from CreateListfiles import createListfiles
from CellsSelection import CellsSelection


class MeasuresCells(object) :
	"""
	This class allows the user to measure several parameters of cells in a stack.

	
	Data Structures :
	
	self.__dictCells={"cellname1" : cell1,.... }
	self.__dictMeasures={cell 1 : dic1, ...}
	dic1={"Area" : [ measure1,...],...} 
		

	"""

	
	def __init__(self):	
		self.__dictCells={}
		self.__measures=[]
		self.__measurescompl=[]
		#self.__dictImages={}
		self.__dictMeasures={}
		#dictionary of the rectangles of the diagrams.
		self.__gridrectangle={}
		self.__listcellname=[]
		self.__allcells=[]
		self.__minLife=0
		self.__maxLife=0
		if IJ.getDirectory("image") is not None : self.__pathdir = IJ.getDirectory("image")
		else : self.__pathdir=IJ.getDirectory("current")
		self.__optionSave=False
		self.__optionSaveBactTrack=False
		self.__optionImport=False
		self.__activeTitle=""
		self.__useTime = False
		self.__optionImages = True
		self.__imagesnames = []
		self.__listfiles = ["","",""]
		self.__defaultcellsval = []
		self.__savetables = True
		self.__savemode = True
		self.__batch = False
		self.__onlyselect = True
		self.__onlystart = True
		self.__noise = 150
		self.__minLife = 2
		self.__batchanalyse = False
		self.__listpaths = []
		self.__time = time.strftime('%d-%m-%y_%Hh%Mm%Ss',time.localtime())
		self.__updateoverlay = True

		measures1 = ["MaxFeret","MinFeret","AngleFeret","XFeret","YFeret","Area","Angle","Major","Minor","Solidity","AR","Round","Circ","XC","YC","FerCoord","FerAxis","MidAxis"]
		measures2 = ["Mean","StdDev","IntDen","Kurt","Skew","XM","YM","Fprofil","MidProfil","NFoci","ListFoci","ListAreaFoci","ListPeaksFoci","ListMeanFoci"]
		measures_global = ["Latency", "velocity", "cumulatedDist"]
		
		
		self.__defaultmeasures=[False for m in measures1+measures2]
		self.__defaultmeasures_global=[False for m in measures_global]

		self.__measuresparambool=[]
		self.__measuresparambool_global=[]

		self.__nextstack = True
		self.__dictNcells = {}

		IJ.run("Options...", "iterations=1 count=1 black edm=Overwrite do=Nothing")
	

	def run(self) :
		
		nextstep=self.__mainsettings()					# step 1
		if nextstep : nextstep = self.__selectionSettings()		# step 2
		
		else : 
			IJ.showMessage("Bye...")
			return False
		
		if nextstep : nextstep = self.__runMethode()			# step 3
		else : 
			IJ.showMessage("Bye...")
			return False

		f = open(self.__pathdir+self.__time+"-listpaths.txt", "w")
		
		for i in range(len(self.__imagesnames)) :
			name = self.__imagesnames[i]
			if name[-4:]!=".tif" : name=name+".tif"
			if not self.__batch : IJ.showMessage("Analysis of stack : "+name)
			self.__pathdir = self.__listpaths[i]
			while nextstep :
				if len(self.__imagesnames) > 1 : self.__activeTitle = name
				if self.__batch : 
					self.__img=WindowManager.getImage(name)
					IJ.selectWindow(self.__img.getID())
					nextstep = True
				else : nextstep = self.__selectMeasureStack()		# step 4
					
				self.__maxLife = self.__img.getImageStackSize()
				if nextstep : nextstep = self.__settings(name)
				else : 
					IJ.showMessage("Bye...")
					return False
			nextstep=True

			try : self.__dictCells[name]
			except KeyError : 
				try : self.__dictCells[name[:-4]]
				except KeyError :
					try : self.__dictCells[name+".tif"]
					except KeyError :
						print "error" 
						continue
					else: 
						name = name+".tif"
						if self.__dictNcells[name] > 0 : 
							f.write(self.__listpaths[i]+"\n")
							continue
				else : 
					name = name[:-4]
					if self.__dictNcells[name] > 0 : 
						f.write(self.__listpaths[i]+"\n")
						continue
					
			if self.__dictNcells[name] > 0 : 
				f.write(self.__listpaths[i]+"\n")
				continue
		

		f.close()
		return True

		
		
	
	
##----------------------------------- step 1 -----------------------------------------#
	def __mainsettings(self) :
		
		
		# options : 
		#We ask if the user wants to import cells from .cell files
		# we track the cells in a stack that the user has to choose.
		
		def outputpath(event) : 
			self.__pathdir=IJ.getDirectory("image")
			self.__pathdir=IJ.getDirectory("")
			self.__text.setText(self.__pathdir)
			

		panel0=Panel()
		pathbutton=Button("Select output path", actionPerformed = outputpath)
		#pathbutton.actionPerformed = outputpath
		self.__text = TextField(self.__pathdir)
		panel0.add(pathbutton)
		panel0.add(self.__text)

		firstgd=NonBlockingGenericDialog("First choices")
		firstgd.addMessage("------------------  WELCOME  ----------------------")
		firstgd.addMessage("")
		firstgd.addMessage("Please fill the following options")
		firstgd.addMessage("")
		choices=["Already opened images", "Files from hard disk"]
		firstgd.addChoice("Images source : ", choices, choices[0])				# 1 choice
		firstgd.addCheckbox("Run in batch mode ?", False)					# 2 batch 
		firstgd.addMessage("")
		firstgd.addCheckbox("Import a set of cells from hardisk ?", self.__optionImport) 	# 3 import
		firstgd.addMessage("")
		firstgd.addNumericField("Size factor (binning)", 2, 0)					# 4 number
		firstgd.addPanel(panel0)
		firstgd.showDialog()

		
		#self.__optionImages=firstgd.getNextBoolean()
		choice=firstgd.getNextChoiceIndex()							# 1 choice
		self.__batch = firstgd.getNextBoolean()							# 2 batch
		self.__optionImport=firstgd.getNextBoolean()						# 3 import
		self.__binning = firstgd.getNextNumber()						# 4 number
		if choice==0 : self.__optionImages=True
		else : self.__optionImages=False 

		if firstgd.wasCanceled() : return False

		

		#IJ.showMessage("Select a working directory to save results")
		#self.__pathdir=IJ.getDirectory("image")
		#self.__pathdir=IJ.getDirectory("")

		#self.__pathdir=self.__pathdir+imp.getShortTitle()+"/"+time.strftime('%d-%m-%y_%Hh%Mm%Ss',time.localtime())+"/"

		if self.__pathdir is not None : return True
		else : return False

#----------------------------------- step 2 -----------------------------------------#

	def __selectionSettings(self) :
		if self.__optionImages :
			self.__img=IJ.getImage()
			self.__activeTitle=self.__img.getTitle()			
			self.__listpaths.append(self.__pathdir+self.__img.getShortTitle()+"/"+self.__time+"/")
			self.__rootpath = self.__listpaths[0]
			out=self.__selectTrackStack()
		else : out = self.__selectFiles()
		return out
		
#----------------------------------- step 3 -----------------------------------------#			
			
	def __runMethode(self) :
		
		#------
		if self.__optionImages and self.__optionImport : self.__ImportCells(self.__imagesnames)
		elif self.__optionImages : self.__runTracking(self.__img)
		elif self.__optionImport : 
			self.__buildstacks()
			self.__ImportCells(self.__imagesnames)
		else : 
			self.__runTracking(self.__listfiles[2])

		return True
		
		#-----
		#if self.__optionImport : self.__ImportCells("image1")
		#else :
		#	if self.__optionImages : self.__runTracking(self.__img)
		#	else : 
		#		self.__runTracking(self.__listfiles[2])
		#		
		#return True
     			
				

	def __selectTrackStack(self) : 
		gd0=NonBlockingGenericDialog("Stack Choice")
		idimages=WindowManager.getIDList()
		#images=[WindowManager.getImage(imgID) for imgID in idimages if WindowManager.getImage(imgID).getImageStackSize()>1 ]
		images=[WindowManager.getImage(imgID) for imgID in idimages]
		imagesnames=[img.getTitle() for img in images]
		for i in range(len(imagesnames)) : 
			if imagesnames[i] == self.__activeTitle : activindex=i
				
		gd0.addChoice("Select a stack in the list : ",imagesnames,imagesnames[activindex])
		gd0.showDialog()
			
		chosenstack=gd0.getNextChoice()
		self.__img = WindowManager.getImage(chosenstack)
		self.__maxLife = self.__img.getImageStackSize()

		IJ.selectWindow(self.__img.getID())
		self.__activeTitle=self.__img.getTitle()
		self.__imagesnames[:]=[]
		#self.__imagesnames.append("image1")
		self.__imagesnames.append(self.__activeTitle)

		if gd0.wasOKed() : return True
		else : 	return False

		
	def __runTracking(self, source) :
		bact = Bacteria_Tracking()
		bact.setPositionslist(self.__imagesnames)
		bact.run(source, self.__listpaths, self.__binning, self.__batch)
		
		#self.__pathdir = bact.getPathdir()
		
		for name in self.__imagesnames : 
			self.__dictCells[name]=bact.getDictCells(name)
		return True
		
	def __selectMeasureStack(self) : 
		# We allow the user to choose what to measure in the stack, and on which stack.
		gd1=NonBlockingGenericDialog("Stack Choice for measures")
		idimages=WindowManager.getIDList()
		images=[WindowManager.getImage(imgID) for imgID in idimages if WindowManager.getImage(imgID).getImageStackSize()>1 ]
		imagesnames=[img.getTitle() for img in images]

		activindex=0
		
		for i in range(len(imagesnames)) : 
				if imagesnames[i] == self.__activeTitle : 
					activindex=i
				
		gd1.addChoice("Select a stack in the list : ",imagesnames,imagesnames[activindex])
		gd1.showDialog()
		chosenstack=gd1.getNextChoice()
		self.__img=WindowManager.getImage(chosenstack)
		IJ.selectWindow(self.__img.getID())
		if gd1.wasOKed() : return True
		else : 	return False


	def __selectFiles(self) :
		self.__listfiles = createListfiles()
		#self.__imagesnames=["position"+p for p in self.__listfiles[3]]
		self.__imagesnames=[self.__listfiles[1][0].split("_")[1]+p for p in self.__listfiles[3]]
		self.__rootpath = self.__pathdir
		#self.__listpaths = [self.__pathdir+self.__listfiles[0]+p+"/"+self.__time+"/" for p in self.__listfiles[3]]
		self.__listpaths = [self.__pathdir+self.__listfiles[0]+p+"/"+self.__time+"/" for p in self.__listfiles[3]]
		
		return True
		
		
		

	#Lets the user to choose different measures to make, and displays it following the choice of the user.
	def __settings(self, imgName) :
		"""
		Lets the user to choose different measures to make, and displays it following the choice of the user.
		
		"""

		try : dico=self.__dictCells[imgName]
		except KeyError : 
			try : dico=self.__dictCells[imgName[:-4]]
			except KeyError : return False
			else : imgName=imgName[:-4]
		
		dico=self.__dictCells[imgName]
		for cellname in dico.keys() :
			self.__dictMeasures[dico[cellname]]={}
			
		# Represents the datas on a diagram
		def diagrambuttonPressed(event) :
			IJ.showMessage("Push 'Auto' button each time you want to see the diagram")
			x1=10
			y1=20
			x2=100
			y2=50
			x3=60
			y3=30
			xr=10
			yr=20
			wr=20
			hr=20

			
			rect=Rectangle(xr,yr,wr,hr)
			
			#img=IJ.getImage()
			#nbslices=self.__img.getImageStackSize()
			nbslices=self.__maxLife
			IJ.run("Hyperstack...", "title=Diagram type=32-bit display=Color width="+str(x2+(nbslices+1)*x3)+" height="+str(y2+y3*len(dico))+" channels=1 slices="+str(len(self.__measures))+" frames=1")
			im=IJ.getImage()
			ip=im.getProcessor()
			for i in range(len(self.__measures)) :
				indiceligne=0
				maxvalue=0
				minvalue=1000000
				im.setPosition(1,i+1,1)
				for cellname in self.__listcellname :
					indiceligne+=1
					for indicecolonne in range(1,nbslices+1):
						rect.setLocation(x2+indicecolonne*x3+int(x3/6),(y1+indiceligne*y3-int(y3/2)))
						# we create at the first iteration a dictionary with the rectangles (for a future use)
						if i==0 :
							self.__gridrectangle[(indiceligne,indicecolonne)]=Rectangle(rect)
						im.setRoi(rect)
						ipr=im.getProcessor()
						# we find the min and max values of the datas for a measure given.
						if self.__dictMeasures[dico[cellname]][self.__measures[i]][indicecolonne-1]>maxvalue :
							maxvalue=self.__dictMeasures[dico[cellname]][self.__measures[i]][indicecolonne-1]
						if self.__dictMeasures[dico[cellname]][self.__measures[i]][indicecolonne-1]<minvalue :
							minvalue=self.__dictMeasures[dico[cellname]][self.__measures[i]][indicecolonne-1]
						# we fill the rectangle with the value of the measure
						ipr.setValue(self.__dictMeasures[dico[cellname]][self.__measures[i]][indicecolonne-1])
						ipr.fill()
				# we write the names and the n° of slices on the image with the maxvalue.
				ip.setValue(maxvalue)
				ip.moveTo(x1,y1)
				ip.drawString(self.__measures[i])
				for j in range(1,nbslices+1) :
					ip.moveTo(x2+j*x3,y1)
					ip.drawString("Slice "+str(j))
				j=0
				for cellname in self.__listcellname :
					ip.moveTo(x1,y2+j*y3)
					ip.drawString(cellname)
					j+=1
			im.killRoi()
			im=IJ.run(im,"Fire","")
			IJ.run("Brightness/Contrast...", "")
			#im.setMinAndMax(minvalue,maxvalue)
			#im.updateImage()
			
			#we add a mouse listener in order to be able to show the roi corresponding to a rectangle when the user clicks on it.
			listener = ML()
			listener.name=imgName
			for imp in map(WindowManager.getImage, WindowManager.getIDList()):
				if imp.getTitle().startswith("Diagram") : 
					win = imp.getWindow()
 					if win is None:
						continue
					win.getCanvas().addMouseListener(listener)
		
		# Represents the datas on a series of graphs.
		def graphbuttonPressed(event) :
			
			colors=[]
			#img=IJ.getImage()
			#nbslices=self.__img.getImageStackSize()
			nbslices=self.__maxLife

			acell=dico.values()[0]
			if self.__useTime : 
				x = acell.getListTimes()
				namex="Time sec"
			else : 
				x = range(1,nbslices+1)
				namex = "Frame"
			maxx=max(x)
			minx=min(x)
			
			#x=[i for i in range(1,nbslices+1)]
			font=Font("new", Font.BOLD, 14)
			tempname = WindowManager.getUniqueName(self.__img.getShortTitle())
			for i in range(len(self.__measures)) :
				#print "i", i, self.__measures[i]
				yarray=[]
				flag=True
				miny=10000000000
				maxy=-1000000000
				#we find the min and max values in order to set the scale.
				for cellname in self.__listcellname :	
					colors.append(dico[cellname].getColor())
					yarray.append(self.__dictMeasures[dico[cellname]][self.__measures[i]])
					#for meas in self.__dictMeasures[dico[cellname]][self.__measures[i]] :
					for meas in yarray[-1] :
						if (meas<miny) and (Double.isNaN(meas)==False) :
							miny=meas
					if max(yarray[-1])>maxy : maxy=max(yarray[-1])
				
				miny-=0.1*miny
				maxy+=0.1*maxy
				count=0.05
				
				for j in range(len(yarray)) :
					if j==0 :
						if len(self.__measures)>1 :
							plot=Plot("Plots-"+str(self.__measures[i]),namex,str(self.__measures[i]),x,yarray[j])
							
						else : 
							plot=Plot("Plot-"+tempname,namex,str(self.__measures[i]),x,yarray[j])
							
						plot.setLimits(minx,maxx,miny,maxy)
						plot.setColor(colors[j])
						plot.changeFont(font)
						plot.addLabel(0.05, count, self.__listcellname[j])
					else :
						plot.setColor(colors[j])
						plot.setLineWidth(3)
						plot.addPoints(x,yarray[j],Plot.LINE)
						plot.addLabel(0.05, count, self.__listcellname[j])

					count+=0.05
						
				plot.setColor(colors[0])
				plot.show()
				
			if len(self.__measures)>1 :
				IJ.run("Images to Stack", "name="+tempname+"-plots title=Plots- use")

		#def histbuttonPressed(event) :
		#	
		#	pass

		# Represents the values in a tab.
		def tabbuttonPressed(event) :
		
			tab="\t"
			headings=[]
			measures=[]
			#img=IJ.getImage()
			#for i in range(self.__img.getImageStackSize()+1) :
			for i in range(self.__maxLife+1) :
				headings.append("Slice "+str(i))
			
			headings[0]=WindowManager.getUniqueName(self.__img.getShortTitle())
			#for m in self.__measurescompl :
			for m in self.__dictMeasures[dico[self.__listcellname[0]]].keys() :
				
				headstring=""
				for head in headings: 
					headstring+=head+tab
				tw=TextWindow(self.__listfiles[0]+"-"+m,headstring,"",800,600)
				tp=tw.getTextPanel()
				#for cellname in dico.keys() :
				for cellname in self.__listcellname :
					line=[]
					line=[str(meas)+tab for meas in self.__dictMeasures[dico[cellname]][m]]
					line.insert(0, cellname+tab)
					linestr=""
					for s in line: linestr+=s
					tp.appendLine(linestr)
				tp.updateDisplay()

			if self.__measuresparambool_global[0] :
				tw=TextWindow("Latency","cell\tLatency", "",800,600)
				tp=tw.getTextPanel()
				for i in range(len(self.__listcellname)) :
					#if latencies[i][0] : line=self.__listcellname[i]+"\t"+str(latencies[i][1])
					#else : line=self.__listcellname[i]+"\t"+"NaN"
					line=self.__listcellname[i]+"\t"+str(latencies[i][1])
					tp.appendLine(line)
				tp.updateDisplay() 
				
		def helpbuttonPressed(event) :

			IJ.showMessage("TO DO")

		def newsetPressed(event) :
			gd0.dispose()
			self.__settings()

		def alignbuttonPressed(event) :
			IJ.showMessage("TO DO")


		def mergebuttonPressed(event) :
			IJ.showMessage("TO DO")

		def saveResults() :
			
			#if len(self.__listcellname) == 0 :
			
			nbslices=self.__maxLife
			acell=dico.values()[0]
			if self.__useTime : 
				x = acell.getListTimes()
				namex="Time_sec"
			else : 
				x = range(1,nbslices+1)
				namex = "Frame"
							
			if not path.exists(self.__rootpath+"Results/") : os.makedirs(self.__rootpath+"/Results/", mode=0777)
			tab="\t"
			nl="\n"
			measures=[]
			headstring=""
			#if self.__savemode : mode = "a"
			#else : mode ="w"
			mode = "a"
			
			#for i in range(1, self.__maxLife+1) :headstring += "Slice_"+str(i)+tab
			for i in range(self.__maxLife) :headstring += str(x[i])+tab
			
			#for m in self.__measurescompl :
			for m in self.__dictMeasures[dico[self.__listcellname[0]]].keys() :
				f = open(self.__rootpath+"Results/"+m+".txt", mode)
				#f.write(m+nl)
				f.write(imgName+"-"+self.__time+"-"+m+"-"+namex+tab+headstring+nl)
				if len(self.__listcellname) == 0 : f.write("no cells")
				else : 
					for cellname in self.__listcellname :
						linestr=cellname+tab
						for measure in self.__dictMeasures[dico[cellname]][m] :
							#print m, cellname, measure 
							linestr += str(measure)+tab
						linestr+=nl
						f.write(linestr)
				f.close()

			if self.__measuresparambool_global[0] :
				m = "Latency"
				f = open(self.__rootpath+"Results/"+m+".txt", mode)
				f.write(imgName+"-"+self.__time+"-"+m+nl)
				for i in range(len(self.__listcellname)) :
					#if latencies[i][0] : line=self.__listcellname[i]+"\t"+str(latencies[i][1])
					#else : line=self.__listcellname[i]+"\t"+"NaN"
					line=self.__listcellname[i]+"\t"+str(latencies[i][1])
					line+=nl
					f.write(line)
				f.close()
				
			

			

		#
		# ----------- main measures dialog -------------------------
		#
     		# Allows the user to choose the measures to make, etc..
		
		measureslabels_indep=["MaxFeret","MinFeret","AngleFeret","XFeret","YFeret","Area","Angle","Major","Minor","Solidity","AR","Round","Circ","XC","YC","FerCoord","FerAxis","MidAxis"]
		measureslabels_dep=["Mean","StdDev","IntDen","Kurt","Skew","XM","YM","Fprofil","MidProfil","NFoci","ListFoci","ListAreaFoci","ListPeaksFoci","ListMeanFoci"]
		measureslabels_global=["Latency", "velocity", "cumulatedDist"]
		measureslabels_dep_tabonly=set(["MidAxis","FerCoord","FerAxis","Fprofil","MidProfil","ListFoci","ListAreaFoci","ListPeaksFoci","ListMeanFoci"])
		ens_measures_global=set(measureslabels_global)
		ens_measures_indep=set(measureslabels_indep)
		ens_measures_dep=set(measureslabels_dep)
		measureslabels=[]
		
		for label in measureslabels_indep :
			measureslabels.append(label)

		for label in measureslabels_dep :
			measureslabels.append(label)

		#self.__defaultmeasures=[False for i in range(len(measureslabels))]
		#self.__defaultmeasures_global=[False for i in range(len(measureslabels_global))]

		gdmeasures=NonBlockingGenericDialog("MeasuresChoice")
		gdmeasures.setFont(Font("Courrier", 1, 10))
		gdmeasures.addMessage("*******     TIME SETTINGS     *******")
		gdmeasures.addCheckbox("Only starting at begining  :", self.__onlystart)				# 1 only start
		gdmeasures.addNumericField("Minimal Lifetime  : ",self.__minLife,0)
		gdmeasures.addNumericField("Maximal Lifetime  : ",self.__maxLife,0)
		#gdmeasures.addNumericField("Maximal Lifetime  : ",self.__img.getImageStackSize(),0)
		gdmeasures.addCheckbox("x axis in seconds", self.__useTime)				# 2 use time
		gdmeasures.addMessage("")
		gdmeasures.addMessage("")
		gdmeasures.addMessage("Choose the measures to make on the cells : ")			
		gdmeasures.addMessage("*******     TIME MEASURES     *******")
		gdmeasures.addCheckboxGroup(4,8,measureslabels,self.__defaultmeasures)
		gdmeasures.addMessage("")
		gdmeasures.addMessage("*******     GLOBAL MEASURES     *******")
		gdmeasures.addMessage("PLEASE : If you have selected movement parameters you MUST to select XC and YC !")
		gdmeasures.addCheckboxGroup(3,1,measureslabels_global,self.__defaultmeasures_global)
		gdmeasures.addNumericField("Noise value for maxima finder: ",self.__noise,0)
		gdmeasures.addMessage("")	
		gdmeasures.addMessage("*******     OPTIONS     *******")
		gdmeasures.addCheckbox("Select the cells in next dialog ?", self.__onlyselect)			# 3 only select
		gdmeasures.addCheckbox("Save results to text files ?", self.__savetables)			# 4 save files
		#gdmeasures.addCheckbox("Append mode ?", self.__savemode)					# 5 append mode
		gdmeasures.addCheckbox("Analyse in batch mode ?", self.__batchanalyse)				# 6 analysis batch mode
		gdmeasures.addCheckbox("Update overlay ?", self.__updateoverlay)				# 7 update overlay
		gdmeasures.addMessage("")
		gdmeasures.addMessage("")
		help_panel=Panel()
		helpbutton=Button("HELP")
		helpbutton.actionPerformed = helpbuttonPressed
		help_panel.add(helpbutton)	
		gdmeasures.addPanel(help_panel)	
		gdmeasures.hideCancelButton()

		if not self.__batchanalyse :
			gdmeasures.showDialog()
			self.__onlystart=gdmeasures.getNextBoolean() 						# 1 only start
			self.__minLife=gdmeasures.getNextNumber()
			self.__maxLife=gdmeasures.getNextNumber()
			self.__useTime=gdmeasures.getNextBoolean()						# 2 use time

			self.__measuresparambool=[]
			self.__measuresparambool_global=[]
			for i in range(len(measureslabels)) : 
				self.__measuresparambool.append(gdmeasures.getNextBoolean())
				self.__defaultmeasures[i]=self.__measuresparambool[-1]
			for i in range(len(measureslabels_global)) : 
				self.__measuresparambool_global.append(gdmeasures.getNextBoolean())
				self.__defaultmeasures_global[i] = self.__measuresparambool_global[i]
 
			self.__noise=gdmeasures.getNextNumber()
			self.__onlyselect=gdmeasures.getNextBoolean()						# 3 only select
			self.__savetables = gdmeasures.getNextBoolean()						# 4 save files
			#self.__savemode = gdmeasures.getNextBoolean()						# 5 append mode
			self.__batchanalyse = gdmeasures.getNextBoolean()					# 6 analyse mode
			self.__updateoverlay = gdmeasures.getNextBoolean()					# 7 update overlay

		# we update a list of all cells that have a lifetime corresponding to what the user chose.
		if len (self.__allcells) == 0 :
			for cellname in dico.keys() :
				if dico[cellname].getLifeTime()>=self.__minLife : #and dico[cellname].getLifeTime()<=self.__maxLife :
					if self.__onlystart :
						if dico[cellname].getSlideInit()<2 : self.__allcells.append(cellname)
						else : self.__allcells.append(cellname)

		
		if self.__noise == 0 : self.__noise = None
		if self.__batchanalyse : self.__onlyselect = False
		
		if self.__onlyselect : 
			
			try : 
				self.__gw
			except AttributeError :
				if not path.exists(self.__pathdir+"Selected-Cells/") : os.makedirs(self.__pathdir+"/Selected-Cells/", mode=0777)				
				self.__gw = CellsSelection()
				self.__gw.setTitle(imgName)
				self.__gw.run(self.__allcells, self.__pathdir+"ROIs/")
				self.__gw.show()
				self.__gw.setSelected(self.__allcells)
				while not self.__gw.oked and self.__gw.isShowing() : 
					self.__gw.setLabel("Validate selection with OK !!")
					self.__listcellname = list(self.__gw.getSelected())
				self.__gw.resetok()
				self.__gw.setLabel("...")
				self.__gw.hide()
			else : 
				if self.__gw.getTitle() == imgName :
					self.__gw.show()
					self.__gw.setSelected(self.__listcellname)
					self.__listcellname[:]=[]
					while not self.__gw.oked and self.__gw.isShowing() : 
						self.__gw.setLabel("Validate selection with OK !!")
						self.__listcellname = list(self.__gw.getSelected())
					
					self.__gw.resetok()
					self.__gw.setLabel("...")
					self.__gw.hide()

				else : 
					self.__gw.dispose()
					if not path.exists(self.__pathdir+"Selected-Cells/") : os.makedirs(self.__pathdir+"/Selected-Cells/", mode=0777)				
					self.__gw = CellsSelection()
					self.__gw.setTitle(imgName)
					self.__gw.run(self.__allcells, self.__pathdir+"ROIs/")
					self.__gw.show()
					self.__gw.setSelected(self.__allcells)
					self.__listcellname[:]=[]
					while not self.__gw.oked and self.__gw.isShowing() : 
						self.__gw.setLabel("Validate selection with OK !!")
						self.__listcellname = list(self.__gw.getSelected())
					self.__gw.resetok()
					self.__gw.setLabel("...")
					self.__gw.hide()

			filestodelet=glob.glob(self.__pathdir+"Selected-Cells/*.cell")
			for f in filestodelet : os.remove(f)
			for cell in self.__listcellname :
				shutil.copy(self.__pathdir+"Cells/"+cell+".cell",self.__pathdir+"Selected-Cells/"+cell+".cell")

			self.__dictNcells[imgName] = len(self.__listcellname)
		
		else : 
			self.__listcellname = list(self.__allcells)
			self.__dictNcells[imgName] = len(self.__listcellname)

		if len(self.__listcellname) == 0 : 
			self.__dictNcells[imgName] = 0
			return False
		
		self.__img.hide()
		
		# we make the measures.
		for i in range(len(measureslabels)) :
			IJ.showProgress(i, len(measureslabels))
			if  self.__measuresparambool[i]==True :
				
				self.__measurescompl.append(measureslabels[i])
				
				if (measureslabels[i] in measureslabels_dep_tabonly)==False :
					self.__measures.append(measureslabels[i])
				
				if (i<18) and (measureslabels[i] in ens_measures_indep) :
					self.__measureAll(self.__img,measureslabels[i],False, imgName, self.__noise)
					ens_measures_indep.discard(measureslabels[i])
					
				if i>=18 :
					self.__measureAll(self.__img,measureslabels[i],True, imgName, self.__noise)
					
		if self.__measuresparambool_global[0] : # calculate latency
			latencies=[]
			for i in range(len(self.__listcellname)) : 
				IJ.showProgress(i, len(self.__listcellname))
				latencies.append(self.latencie(self.__listcellname[i], self.__img, imgName, self.__useTime))

		if self.__measuresparambool_global[1] : # calculate velocity
			self.__measures.append("velocity")
			#velocities=[]
			for i in range(len(self.__listcellname)) : 
				IJ.showProgress(i, len(self.__listcellname))
				self.__measureVelocity(self.__img,imgName)

		if self.__measuresparambool_global[2] : # calculate cumulatedDistance
			self.__measures.append("cumulatedDist")
			#velocities=[]
			for i in range(len(self.__listcellname)) : 
				IJ.showProgress(i, len(self.__listcellname))
				self.__measurecumulDist(self.__img,imgName)	
				
		
		self.__img.show()

		self.__img.getProcessor().resetThreshold()		

		
		if self.__updateoverlay :
			if self.__img.getOverlay() is not None : self.__img.getOverlay().clear()
		
			outputrois=[]
			cellnames=[]
			self.__img.hide()
			for cellname in self.__listcellname :
				
				for r in dico[cellname].getListRoi():
					if isinstance(r,Roi) : 
						pos=r.getPosition()
						#print "MC overlay", cellname, r.getName(), pos
						#r.setPosition(0)
						#overlay.add(r)
						outputrois.append(r)
						if "cell" in r.getName() : cellnames.append(r.getName())
						else : cellnames.append(str(pos)+"-"+cellname)
						#print cellnames[-1]

			rm = RoiManager.getInstance()
			if (rm==None): rm = RoiManager()
			rm.show()
			self.__img.show()
			IJ.selectWindow(self.__img.getTitle())
			rm.runCommand("reset")
			for i in range(len(outputrois)) :
				outputrois[i].setName(cellnames[i])
				rm.addRoi(outputrois[i])
				rm.select(rm.getCount()-1)
				rm.runCommand("Rename", cellnames[i])
			
			IJ.run("Show Overlay", "")
			rm.runCommand("UseNames", "true")
			rm.runCommand("Associate", "true")
			IJ.run(self.__img, "Labels...", "color=red font=12 show use")
			IJ.run(self.__img, "From ROI Manager", "")
			rm.runCommand("Show None")
			rm.runCommand("Show All")


		# ----------- batch analyse ------------------------
		if self.__batchanalyse :
			if self.__savetables :  saveResults()
			self.__dictMeasures.clear()
     			self.__allcells[:]=[]
     			self.__measurescompl[:]=[]
     			self.__measures[:]=[] 
			return False
			
		# ---------- display methodes dialog ----------------
		# Allows the user to choose how to see the results of the measures.		
		
		gd0=NonBlockingGenericDialog("Display")

		gd0.addMessage("How do you want to see the results ?")
		
		panel0=Panel()
		
		diagrambutton=Button("Diagram")
		diagrambutton.actionPerformed = diagrambuttonPressed
		panel0.add(diagrambutton)

		graphbutton=Button("Graph")
		graphbutton.actionPerformed = graphbuttonPressed
		panel0.add(graphbutton)

		tabbutton=Button("Tab")
		tabbutton.actionPerformed = tabbuttonPressed
		panel0.add(tabbutton)
		gd0.addPanel(panel0)
		gd0.addCheckbox("Analyse next stack ?", self.__nextstack)
		gd0.hideCancelButton()	
		gd0.showDialog()

		self.__nextstack = gd0.getNextBoolean()

		# ---------- save tables ---------------------------
		if self.__savetables :  saveResults()
		
		# --------- re-start analysis -------------------
		
     		self.__dictMeasures.clear()
     		#self.__listcellname[:]=[]
     		self.__allcells[:]=[]
     		self.__measurescompl[:]=[]
     		self.__measures[:]=[]

     		if self.__nextstack : return False
     		else : return True
		
	# add the measures for all the cells, and has a parameter "changeslice" that allows the program to know if the measure depends on the image or not (eg : intensity). 
	def __measureAll(self,img,measure,changeslice, name, noise) :
		"""
		Measures a characteristic for all the cells in a stack.

		"""
		dico=self.__dictCells[name]
		
		if changeslice == True : img.setSlice(1)
		for cellname in dico.keys() :
			roitemp=dico[cellname].getRoi(0)
			self.__dictMeasures[dico[cellname]][measure]=[]
			if isinstance(roitemp,Roi) :
				m=Morph(img,roitemp)				
				if noise is not None : m.setNoise(noise)
				self.__dictMeasures[dico[cellname]][measure].append(m.__getattribute__(measure))
				#self.__dictMeasures[dico[cellname]][measure].append(Morph(img,roitemp).__getattribute__(measure))
			else :
				self.__dictMeasures[dico[cellname]][measure].append(Double.NaN)
		
		for i in range(2,img.getImageStackSize()+1) :
			if changeslice == True : img.setSlice(i)
			for cellname in dico.keys() :
				roitemp=dico[cellname].getRoi(i-1)
				if isinstance(roitemp,Roi) :
					m=Morph(img,roitemp)				
					if noise is not None : m.setNoise(noise)
					self.__dictMeasures[dico[cellname]][measure].append(m.__getattribute__(measure))
					#self.__dictMeasures[dico[cellname]][measure].append(Morph(img,roitemp).__getattribute__(measure))
				else :
					self.__dictMeasures[dico[cellname]][measure].append(Double.NaN)

	def __measurecumulDist(self, img, name) :
		measure = "cumulatedDist"
		dico=self.__dictCells[name]
		for cellname in dico.keys() :
			roitemp=dico[cellname].getRoi(0)
			xc = self.__dictMeasures[dico[cellname]]["XC"]
			yc = self.__dictMeasures[dico[cellname]]["YC"]
			d=[]
			d.append(0)
			for i in range(1,len(xc)-1) :
				tempseq = [ xc[i], xc[i+1], yc[i], yc[i+1] ]
				if not any(Double.isNaN(val)==True for val in tempseq ) :
					lastdist = Morph.distMorph([[1, xc[i], xc[i+1]],[1, yc[i], yc[i+1]]])
					d.append(d[-1]+lastdist)
				else : d.append(Double.NaN)
			d.append(Double.NaN)
			self.__dictMeasures[dico[cellname]][measure]=d
			del(d)		
					
	def __measureVelocity(self, img, name) :
		measure = "velocity"
		dico=self.__dictCells[name]
		for cellname in dico.keys() :
			roitemp=dico[cellname].getRoi(0)
			xc = self.__dictMeasures[dico[cellname]]["XC"]
			yc = self.__dictMeasures[dico[cellname]]["YC"]
			d=[]
			for i in range(len(xc)-1) :
				tempseq = [ xc[i], xc[i+1], yc[i], yc[i+1] ]
				if not any(Double.isNaN(val)==True for val in tempseq ) :
					d.append(Morph.distMorph([[1, xc[i], xc[i+1]],[1, yc[i], yc[i+1]]]))
				else : d.append(Double.NaN)
			d.append(Double.NaN)
			self.__dictMeasures[dico[cellname]][measure]=d
			del(d)					

	def latencie(self, cellname, img, name, usetime) :
		cell=self.__dictCells[name][cellname] 
		x = cell.getListTimes()
		init=cell.getSlideInit()-1
		fin=cell.getSlideEnd()
		counter = 0
		areainit = Morph(img, cell.getRoi(init)).Area
		latency = (False, "NaN")
		sol=[]
		for i in range(init,fin, 1) : 
			if usetime : time = x[i]-x[init]
			else : time = i - init
			roi = cell.getRoi(i)
			if isinstance(roi, Roi) : 
				m = Morph(img, roi)
				sol.append(m.Solidity)
				area = m.Area
				if sol[-1]<0.8 and (area/areainit)>1.3 and sol[-2]>0.8: 
					latency = (True, time)
					break
				if sol[-1]>=0.8 and i == fin-1 : latency = (False, "end="+str(time))
				
		return latency				
				

	def getImp(self) :
		return self.__img
	
	def getGridRect(self) :
		return self.__gridrectangle

	# shows the ROI on the image corresponding to a square on the diagram.
	def ShowRoi(self,imp,point, name):
		for indices in self.__gridrectangle.keys() :
			if self.__gridrectangle[indices].contains(point) :
				roitemp=self.__dictCells[name][self.__listcellname[indices[0]-1]].getRoi(indices[1]-1)
		if isinstance(roitemp,Roi) :
			idimages=WindowManager.getIDList()
			for i in range(len(idimages)) :
				if idimages[i]==self.__img.getID() :
					IJ.selectWindow(self.__img.getID())	
			rm = RoiManager.getInstance()
			for i in range(rm.getCount()) :
				if rm.getName(str(i))==roitemp.getName() :
					rm.select(i)
					selectroi=self.__img.getRoi()
					#col=rm.getSelectedRoisAsArray().getStrokeColor()
					selectroi.setStrokeColor(Color.red)
					selectroi.setStrokeWidth(3)
					self.__img.updateAndDraw()
					break

	# build stacks from listfiles when the importcells option is used
	def __buildstacks(self) :
		listfiles = self.__listfiles[2]
		positionsList = self.__imagesnames
		
		if not isinstance(listfiles[0],list) and os.path.isfile(listfiles[0]) : 
			if len(positionsList)==0 : tempname = WindowManager.getUniqueName("image")
			else : tempname = positionsList[0]
			tempd = tempfile.mkdtemp()
			fichier = open(tempd+"/"+tempname+".tif","w")
			rawtimes=[]
			rawtimes.append(0)
			zerotimes=0
			for i in range(len(listfiles)-1) :
				difftimes=int((os.stat(listfiles[i+1]).st_mtime-os.stat(listfiles[i]).st_mtime))
				if difftimes==0 : zerotimes+=1
				rawtimes.append(rawtimes[-1]+difftimes)
				fichier.writelines(listfiles[i]+"\n")
			
			fichier.writelines(listfiles[-1]+"\n")
			fichier.close()
			IJ.run("Stack From List...","open="+tempd+"/"+tempname+".tif")
			n=WindowManager.getImageCount()
			tempid=WindowManager.getNthImageID(n)
			tempimg=WindowManager.getImage(tempid)
			tempimg.show()
			#self.__dictImages[tempname]=tempimg
			#tempimg.hide()
			nameimages=tempname+"tif"
			#if zerotimes/len(rawtimes) > 0.5 : rawtimes=range(len(listfiles))
			#self.__dictTimeStack[tempname]=rawtimes
			

		#elif isinstance(listfiles[0][0],str) :
		elif os.path.isfile(listfiles[0][0]) : 
			nameimages=[]
			rawtimes=[]
			rawtimes.append(0)
			for i in range(len(listfiles)) :
				if len(positionsList)==0 : tempname = WindowManager.getUniqueName("image"+str(i+1))
				else : tempname = positionsList[i]
				tempd = tempfile.mkdtemp()
				fichier = open(tempd+"/"+tempname+".tif","w")
				zerotimes=0
				for j in range(len(listfiles[i])-1) :
					difftimes=int((os.stat(listfiles[i][j+1]).st_mtime-os.stat(listfiles[i][j]).st_mtime))
					if difftimes==0 : zerotimes+=1
					rawtimes.append(rawtimes[-1]+difftimes)
					fichier.writelines(listfiles[i][j]+"\n")

				fichier.writelines(listfiles[i][-1]+"\n")
				fichier.close()
				IJ.run("Stack From List...","open="+tempd+"/"+tempname+".tif")
				n=WindowManager.getImageCount()
				tempid=WindowManager.getNthImageID(n)
				tempimg=WindowManager.getImage(tempid)
				tempimg.show()
				#self.__dictImages[tempname]=tempimg
				nameimages.append(tempname)
				#if zerotimes/len(rawtimes) > 0.5 : rawtimes=range(len(listfiles[i]))
				
				#self.__dictTimeStack[tempname]=rawtimes
				rawtimes=[] 
				rawtimes.append(0)
								
		
		else : 
			nameimages=[]
			print "ERROR IN BUILDSTACK"

		return nameimages


	# imports the cells, and creates a dictionnary with all the data previously calculated.
	def __ImportCells(self, imagesnames) :

		#self.__dictCells[imgName]={}
		
		rm = RoiManager.getInstance()
		if (rm==None): rm = RoiManager()
		rm.runCommand("reset")

		listpaths = []
		listfilescells=[]

		if self.__optionImages :
			IJ.showMessage("Select the folder 'Cells' containing the cells to import")
			selectdir=IJ.getDirectory("image")
			selectdir=IJ.getDirectory("")
			listfilescells.extend(glob.glob(selectdir+"/*"))
			listpaths.append("")

		else : 
			IJ.showMessage("Select the text file containing the list cell paths (listpaths.txt)")
			selectdir=IJ.getDirectory("current")
			frame = Frame("Text file settings ?")
			fd = FileDialog(frame)
			fd.setDirectory(selectdir)
			fd.show()
			selectdir = fd.getDirectory() 
			textfile = fd.getFile()
			fichier = open(selectdir+textfile,"r")
			listpaths=[ glob.glob(f.split("\n")[0]+"Selected-Cells"+"/*") for f in fichier.readlines()]

			#for f in templist : 
			#	listpaths.append(f.split("\n")+"Cells")
				
			listfilescells.append("")

		if listfilescells[0]=="" : importmode = True
		else : importmode = False
		
		for j in range(len(listpaths)) :
			self.__dictCells[imagesnames[j]]={}
			if importmode : listfilescells = listpaths[j]
			pathtemp = []
			for cellfile in listfilescells :
				filetemp = open(cellfile,"r")
				linestemp=filetemp.readlines()
				for line in linestemp :
					params=line.split("=")
					values=params[1].split("\n")
					if params[0] == "NAMECELL" :
						celltemp=Bacteria_Cell(str(values[0]))
						self.__dictCells[imagesnames[j]][values[0]]=celltemp
						self.__dictMeasures[self.__dictCells[imagesnames[j]][values[0]]]={} 


					if params[0] == "PATHROIS" :
						pathtemp.append(str(values[0]))
						
					if params[0] == "NSLICES" : 
						for i in range(int(values[0])) :
							celltemp.getListRoi().append("")
				
					if params[0] == "SLICEINIT" :
						celltemp.setSlideInit(int(values[0]))
						for i in range(int(values[0])-2) :
							celltemp.setRoi("NOT HERE YET",i)
				
					if params[0] == "SLICEEND" :
						celltemp.setSlideEnd(int(values[0]))
						for i in range(int(values[0])) :
							celltemp.setRoi("LOST",i)
				
					if params[0] == "COLOR" :
						colorstemp=values[0].split(";")
						celltemp.setColor(Color(int(colorstemp[0]),int(colorstemp[1]),int(colorstemp[2])))
		
		
			indiceroi=0
			ind=0
			tempimp = WindowManager.getImage(imagesnames[j])
			if tempimp is not None : 
				IJ.selectWindow(imagesnames[j])
				tempimp.show()
			else : 
				if imagesnames[j][-4:]==".tif" : 
					IJ.selectWindow(imagesnames[j][:-4])
					tempimp = IJ.getImage()
				else : 
					IJ.selectWindow(imagesnames[j]+".tif")
					tempimp = IJ.getImage()
					
			rm.runCommand("reset")
			
			for cellname in self.__dictCells[imagesnames[j]].keys() :
				rm.runCommand("Open", pathtemp[ind])
				ind+=1
				nbtemp=self.__dictCells[imagesnames[j]][cellname].getLifeTime()
				for i in range(nbtemp) :
					rm.select(tempimp, indiceroi)
					roi=rm.getSelectedRoisAsArray()[0]
					self.__dictCells[imagesnames[j]][cellname].setRoi(roi,i+self.__dictCells[imagesnames[j]][cellname].getSlideInit()-1)
					indiceroi+=1

			IJ.run("Show Overlay", "")
			rm.runCommand("UseNames", "true")
			rm.runCommand("Associate", "true")
			IJ.run(tempimp, "Labels...", "color=red font=12 show use")
			if rm.getCount()>0 : IJ.run(tempimp, "From ROI Manager", "")
			rm.runCommand("Show None")
			rm.runCommand("Show All")

			roipath = os.path.split(pathtemp[0])[0]+"/"
			rootpath = roipath.rsplit("/", 2)[0]+"/"

			self.__listpaths[j] = rootpath
			self.__rootpath=rootpath

	
		
class ML(MouseAdapter):
	
	name="image1"
	
	def mousePressed(self, event):
		canvas = event.getSource()
		point=event.getPoint()
		X = canvas.offScreenX(point.x)
		Y = canvas.offScreenY(point.y)
		newpoint=Point(X,Y)
		imp = canvas.getImage()
		measurescells.ShowRoi(imp,newpoint, self.name)

	
					
if __name__ == "__main__":

	measurescells=MeasuresCells()
	print "End = ", measurescells.run()
	
