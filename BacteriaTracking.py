

from ij import ImageStack, ImagePlus, IJ, WindowManager
from ij.gui import Roi, NonBlockingGenericDialog
from ij.plugin.frame import RoiManager
from ij.plugin.filter import ParticleAnalyzer, BackgroundSubtracter
from ij.process import AutoThresholder
from ij.process import ImageProcessor
from ij.measure import ResultsTable, Measurements



from java.awt import TextField, Panel, GridLayout, ComponentOrientation, Label, Checkbox, BorderLayout, Button, Color, FileDialog, Frame, Font


from javax.swing import JOptionPane,JFrame

import sys
import os
import time
import glob
import os.path 
import getpass
import random
import glob
import tempfile


username=getpass.getuser()

#mypath=os.path.expanduser(IJ.getDirectory("plugins")+"MeasureCells")
mypath=os.path.expanduser(os.path.join("~","Dropbox","MacrosDropBox","py","MorphoBactProject"))
sys.path.append(mypath)

from org.python.core import codecs
codecs.setDefaultEncoding('utf-8')

from MorphoBact import Morph
from BacteriaCell import Bacteria_Cell
from LinkRoisAB import link
from RangeRois import RangeRois

class Bacteria_Tracking(object) :
	"""
	This class creates a dictionnary for all the cells in the capture, with a display of the ROIs, according to the preferences
	chosen by the user.
	
	Data Structures :
	
	__dict{"image 1" : dictCells1 , "image 2" : ,...}

	dictCells={"cellule1" : cellule1, ...}

	__dictImages["image 1" : stack1, ...]

	"""

	
	def __init__(self):
		
		# Sets the number of digits.
		self.__nbdigits=3
		IJ.run("Set Measurements...", "area mean standard modal min centroid center bounding fit shape feret's integrated median skewness kurtosis stack display redirect=None decimal="+str(self.__nbdigits))
		
		# Dictionnary of captures to analyse.
		self.__dictImages={}

		# Dictionnary of the times corresponding to the different slices.
		self.__dictTimeStack={}
		self.__pathdir=""

		# Dictionnary of the dictionnary of cells (key = name of stack, value = dictionnary of the cells of the stack).
		self.__dict={}

		# List of the parameters chosen by the user in order to calculate the distance.
		self.__distparam=[]

		# List of the parameters chosen by the user in order to find the particules in the stack.
		self.__params=[]

		# Char of the method used in order to calculate the distance (logarithm distance or euclidean distance).
		self.__distmethod="Euclidean distance"

		# Is true if the user wants to subtrack the background, with a radius of self.__radius.
		self.__subback=False
		# Is true if the user wants to run a pre processing macro.
		self.__runmacro=False
		self.__macropath=IJ.getDirectory("macros")
		
		self.__minArea=0
		self.__maxArea=1000000
		self.__minCirc=0.00
		self.__maxCirc=1.00

		self.__thresMethod="MaxEntropy"
		self.__manthresh=False
		self.__maxthr=255
		self.__minthr=0

		# Option in order to create a symmetry for angles close to 0 and 180.
		self.__optionAngle=False

		# Option in order to save ROIs in a folder.
		#self.__optionSave=False
		self.__optionNewCells=False
		self.__source=""
		self.__optionTimelapse=False
		self.__batch = False
		self.__positionsList = []
		self.__listpaths = []
		self.__pathdir = ""
		self.__selectdir = ""

		
	#def run(self, files=IJ.getImage(), **settings):
	def run(self, files, path, scale, batch, **settings):

		self.__distparam.append(1)		#AREA_COEFF
		#self.__distparam.append(1500/scale)	#AREA_MAXDELTA
		self.__distparam.append(2)		#AREA_MAXDELTA
		self.__distparam.append(5)		#ANGLE_COEFF
		self.__distparam.append(180)		#ANGLE_MAXDELTA
		self.__distparam.append(1)		#FERETMAX_COEFF
		#self.__distparam.append(150/scale)	#FERETMAX_MAXDELTA
		self.__distparam.append(2)		#FERETMAX_MAXDELTA
		self.__distparam.append(10)		#POSITIONX_COEFF
		self.__distparam.append(20/scale)	#POSITIONX_MAXDELTA
		self.__distparam.append(10)		#POSITIONY_COEFF
		self.__distparam.append(20/scale)	#POSITIONY_MAXDELTA
		
		self.__timelapse=600			#time lapse
		self.__radius=int(50/scale)

		self.__batch = batch

		nameimages=[]

		self.__listpaths = path
		
		if isinstance(files, ImagePlus) :
			#self.__dictImages["image1"]=files
			#nameimages.append("image1")
			if self.__batch : self.__ImportPref(1)
			self.__dictImages[files.getTitle()]=files
			nameimages.append(files.getTitle())
			self.__source="image"
			
		
		elif isinstance(files,list):
			if self.__batch : self.__ImportPref(1)
			nameimages=self.__buildstack(files)
			self.__source="list"
			 
			
			
		
		else : 
			nameimages=None
			print("pas de fichiers trouves")

		#tobool = ["self.__subback", "self.__manthresh", "self.__optionAngle", "self.__optionNewCells", "self.__optionTimelapse"]
		#self.__subback, self.__manthresh, self.__optionAngle, self.__optionNewCells, self.__optionTimelapse = map(bool, tobool)
			
		# if the user gives parameters, we use them.
		if len(settings) < 5 :
			#for name in nameimages :
			for i in range(len(nameimages)) :
				name = nameimages[i]
				self.__pathdir = self.__listpaths[i]
				if not self.__batch :
					self.__params=[]
					self.__minArea=0
					self.__maxArea=1000000
					self.__minCirc=0.00
					self.__maxCirc=1.00
				#image = self.__dictImages[name]
				out = self.__settings(name, i+1)
				if not out : return
				self.__track(name)
				self.__displayCells(name, False)
		else: 
			self.__params=list(settings["params"])
			self.__distparam=list(settings["distparam"])
			self.__distmethod=settings["distmethod"]
			self.__subback=settings["subback"]
			self.__radius=settings["radius"]
			for name in nameimages : 
			#for image in self.__dictImages.keys() :
				self.__track(name)
				self.__displayCells(name, False)

		for i in self.__dictImages.keys() : self.__dictImages[i].show()
		
			
	# Creates stacks according to the list of paths given by the user.	
	def __buildstack(self, listfiles):						
		"""
		Creates stacks according to the list of paths given by the user.
		
		
		"""
		
		

		if not isinstance(listfiles[0],list) and os.path.isfile(listfiles[0]) : 
			if len(self.__positionsList)==0 : tempname = WindowManager.getUniqueName("image")
			else : tempname = self.__positionsList[0]
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
			if self.__batch : tempimg.hide()
			else : tempimg.show()
			self.__dictImages[tempname]=tempimg
			tempimg.hide()
			nameimages=tempname
			if zerotimes/len(rawtimes) > 0.5 : rawtimes=range(len(listfiles))
			self.__dictTimeStack["image1"]=rawtimes
			

		#elif isinstance(listfiles[0][0],str) :
		elif os.path.isfile(listfiles[0][0]) : 
			nameimages=[]
			rawtimes=[]
			rawtimes.append(0)
			for i in range(len(listfiles)) :
				if len(self.__positionsList)==0 : tempname = WindowManager.getUniqueName("image"+str(i+1))
				else : tempname = self.__positionsList[i]
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
				#self.__dictImages["image"+str(i+1)]=tempimg
				#nameimages.append("image"+str(i+1))
				self.__dictImages[tempname]=tempimg
				nameimages.append(tempname)
				if zerotimes/len(rawtimes) > 0.5 : rawtimes=range(len(listfiles[i]))
				#self.__dictTimeStack["image"+str(i+1)]=rawtimes
				self.__dictTimeStack[tempname]=rawtimes
				rawtimes=[] 
				rawtimes.append(0)
				tempimg.hide()
			
		
		else : 
			nameimages=[]
			print "ERROR IN BUILDSTACK"

		return nameimages


	# Tracks all the cells in ONE stack.
	
	def __track(self, imgName) :							
		"""
			Tracks all the cells in ONE stack.
		"""			
		tobool = [self.__subback, self.__manthresh, self.__optionAngle, self.__optionNewCells, self.__optionTimelapse]
		self.__subback, self.__manthresh, self.__optionAngle, self.__optionNewCells, self.__optionTimelapse = map(bool, tobool)
		os.makedirs(self.__pathdir, mode=0777)			
		imp=self.__dictImages[imgName]
		IJ.run(imp, "Set Scale...", "distance=0 known=0 pixel=1 unit=pixel")
		self.__maxLife=imp.getImageStackSize()
		
		tempdict={}
		self.__dict[imgName]=tempdict	

		# We calculate the rois in the first image.
		RoisA = self.__calRois(imp,1)
		
		# we add the rois found in the first image in the dictionary of the cells.	
		for i in range(len(RoisA)) :
			t="%04i" % (i)
			oldname=RoisA[i].getName()
			#newname=oldname+"->cell"+t
			newname="cell"+t
			cellule = Bacteria_Cell(newname)
			RoisA[i].setName(newname)
			tempdict[newname]=cellule
			cellule.setRoi(RoisA[i],0)
			cellule.setSlideEnd(imp.getImageStackSize())
			cellule.setlistTimes(self.__dictTimeStack[imgName])
		
		# we look at all pairs of images at t and t+1 in the stack, and we search for connections between ROIs at t and t+1.
		tempstacksize=imp.getImageStackSize()
		for i in range(2,tempstacksize+1) :
			IJ.showProgress(i, tempstacksize)
		 	liens=[]
			news=[]
			losts=[]
			RoisA=[cellule.getRoi(i-2) for cellule in self.__dict[imgName].values() if isinstance(cellule.getRoi(i-2),Roi) ]
		 	RoisB = self.__calRois(imp,i)
		 	# link returns 3 lists of tuples : one of rois that correspond, one of new rois at a given slide, and one of lost rois at a given slide.
		 	outlink = link(imp, i-1, i, RoisA,RoisB, self.__distparam, self.__distmethod, self.__optionAngle, self.__nbdigits, self.__optionNewCells)
		 	liens=outlink[0]
		 	news=outlink[1]
		 	losts=outlink[2]

			# we update the tab of rois for the cells for which we found a new ROI in another slide.
			lastindex=0
			
			for lien in liens :
				celltemp=self.__getCell(imgName, lien[0], i-2)
				celltemp.setRoi(lien[1],i-1)
				tempname=str(celltemp.getName())
				endname=str.rsplit(tempname, "cell", 1)[1]
				lien[1].setName(lien[1].getName()+"cell"+str(endname))
				if int(endname)>lastindex : lastindex=int(endname)

			# we create new cells and add them to the dictionary
			count=lastindex+1
			for new in news :
				t="%04i" % (count)
				#new[1].setName(new[1].getName()+"->cell"+t)
				new[1].setName("cell"+t)
				celltemp = Bacteria_Cell("cell"+t)
				tempdict[celltemp.name]=celltemp
				for j in range(i-1) :
					celltemp.setRoi("NOT HERE YET",j)
				celltemp.setRoi(new[1],i-1)
				celltemp.setSlideInit(i)
				celltemp.setSlideEnd(imp.getImageStackSize())
				cellule.setlistTimes(self.__dictTimeStack[imgName])
				count=count+1
			
			# we complete the tab of rois of the cells that dispear in a slide.
			for lost in losts :
				celltemp=self.__getCell(imgName, lost[1], i-2)
				if celltemp is None : continue
				celltemp.setSlideEnd(i-1)
				for j in range(i-1,imp.getImageStackSize()) :
					celltemp.setRoi("LOST",j)

		#if self.__optionSave == True :
		self.__SaveStack(imgName,imp)
		
		self.__subback, self.__manthresh, self.__optionAngle, self.__optionNewCells, self.__optionTimelapse = map(bool, tobool)

	

	# Returns the ROIs of a slice given (identified with its n) in a stack
	def __calRois(self, imp, indice) :									
		"""
		Returns the ROIs of a slice given (identified with its n) in a stack
		"""
		##imp=self.__dictImages[nameimages]							 		# IL FAUT RCUPRER L'IMAGE DU STACK !!!!!
		#if self.__batch : imp.hide()
		#else : imp.show()
		#imp.hide()
		imp.show()
		if self.__batch : imp.hide()
		imp.setSlice(indice)
		imp.killRoi()
		ip = imp.getProcessor()

		bs=BackgroundSubtracter() 

		#if str(self.__subback) == "0" or str(self.__subback) == "1" : self.__subback = bool(int(self.__subback))
		#if self.__subback == True : IJ.run(imp, "Subtract Background...", "rolling="+str(self.__radius)+" light")
		if self.__subback == True : bs.rollingBallBackground(ip, self.__radius, False, True, False, True, False)

		if self.__runmacro :
			imp.show()
			imp.setSlice(indice)
			imp.updateAndDraw()
			IJ.runMacroFile(self.__macropath, imp.getTitle())
		
		
			
		imp.updateAndDraw()
		
		#if str(self.__manthresh) == "0" or str(self.__manthresh) == "1" : self.__manthresh = bool(int(self.__manthresh))
		
		#if self.__manthresh : IJ.setThreshold(imp, self.__minthr, self.__maxthr)
		if self.__manthresh : 
			ip.setThreshold(self.__minthr, self.__maxthr, ImageProcessor.RED_LUT)
		else : self.__setThreshold(imp, indice)
		
		rt=ResultsTable()
		pa1=ParticleAnalyzer(ParticleAnalyzer.SHOW_MASKS+ParticleAnalyzer.EXCLUDE_EDGE_PARTICLES , Measurements.AREA, rt, self.__minArea, self.__maxArea, self.__minCirc, self.__maxCirc)
		pa1.setHideOutputImage(True) 
		pa1.analyze(imp)
		
		masks=pa1.getOutputImage()
		masks.getProcessor().erode()
		masks.getProcessor().dilate()
		masks.getProcessor().invertLut()
		masks.getProcessor().threshold(1)
		
		rm = RoiManager.getInstance()
		if (rm==None): rm = RoiManager()
		rm.runCommand("reset")
		#rm.hide()
		
		pa2=ParticleAnalyzer(ParticleAnalyzer.ADD_TO_MANAGER+ParticleAnalyzer.CLEAR_WORKSHEET+ParticleAnalyzer.EXCLUDE_EDGE_PARTICLES , Measurements.AREA, rt, self.__minArea, self.__maxArea, self.__minCirc, self.__maxCirc) 
		pa2.analyze(masks)
		masks.close()
		
		temparray=rm.getRoisAsArray()
		for r in temparray :
			tempnameroi=r.getName()
			r.setPosition(indice)
			r.setName(str(indice)+"-"+tempnameroi)
			r.setStrokeWidth(1) 
		
		if len(self.__params) > 0 :
			for k in self.__params:
				#if k[0]=="Area": self.__minArea, self.__maxArea = str(k[1]), str(k[2])
				if k[0]=="Area": self.__minArea, self.__maxArea = k[1], k[2]
			for k in self.__params:
				#if k[0]=="Circ": self.__minCirc, self.__maxCirc = str(k[1]), str(k[2])
				if (k[0]=="Circ") and k[3] : self.__minCirc, self.__maxCirc = k[1], k[2]
				else : self.__minCirc, self.__maxCirc = 0, 1
			self.__rr.setRoisarray(temparray, imp)
			self.__rr.setRange(indice, self.__params)
			return self.__rr.includeRois
		else : return temparray

		
	

	def __setThreshold(self, imp, indice) :
		#imp=self.__dictImages[nameimages]		 		# IL FAUT RCUPRER L'IMAGE DU STACK !!!!!
		imp.setSlice(indice)
		ip=imp.getProcessor()
		ip.setAutoThreshold(self.__thresMethod, False, ImageProcessor.RED_LUT)
		#ip.autoThreshold()
		#if self.__batch : pass
		#else : 
		#	imp.show()
		#	imp.updateAndDraw()
		#IJ.setAutoThreshold(imp, self.__thresMethod)
			
	# Finds the cell corresponding to a ROI at a slice given.
	def __getCell(self, nameimages, roi, indice) :						
		"""
		Finds the cell corresponding to a ROI at a slice given.
		
		"""
		celltemp=None
		tempdict=self.__dict[nameimages]
		for namecell in tempdict.keys() :
			if tempdict[namecell].getRoi(indice) == roi : celltemp = self.__dict[nameimages][namecell]
		return celltemp

	# Displays all the ROIs of the cells with different colors
	
	def __displayCells(self, nameimage, methodeleon=False):
		"""
		Displays all the ROIs of the cells with different colors
		
		"""
		# we define a list of colors that will be used.

		colors = []
		ncells= len(self.__dict[nameimage])
		if ncells > 0 :
			step=200/ncells
			if step<1 : step=1
			for i in range(ncells) : 
				r = random.randrange(5,205,step)
				g = random.randrange(10,210,step)
				b = random.randrange(30,230,step)
				#r = int(0+i*step)
				#g = random.randrange(10, 190, 30)
				#b = int(250-i*step)
				
				colors.append(Color(r, g, b))

		else : 	colors=[Color.blue, Color.green, Color.magenta, Color.orange, Color.yellow]
		tempcolors=list(colors)
		# we try to have random and different colors for each cell.
		for cellname in self.__dict[nameimage].keys() :
			if len(tempcolors)>0 : 
				self.__dict[nameimage][cellname].setColor(tempcolors.pop(0))
			else :
				tempcolors=list(colors)
				self.__dict[nameimage][cellname].setColor(tempcolors.pop(0))
		

		self.__SaveCells(nameimage)
		
		rm = RoiManager.getInstance()
		if (rm==None): rm = RoiManager()
		rm.runCommand("reset")

		# if the user wants to save files, .zip for the ROIs are saved.
		#if self.__optionSave == True : 
		#os.mkdir(self.__pathdir+"ROIs/", mode=0777)
		os.makedirs(self.__pathdir+"ROIs/", mode=0777)
		tempimp = IJ.createImage("tempimp", "8-bit Black", self.__dictImages[nameimage].getWidth(), self.__dictImages[nameimage].getHeight(), 1)
		tempimp.show()
		for cellname in self.__dict[nameimage].keys() :
			for numslice in range(self.__dictImages[nameimage].getImageStackSize()) :
				r = self.__dict[nameimage][cellname].getRoi(numslice)
				try : 
					name=r.getName()
				
				except AttributeError : continue

				else :
					s = "%04i" % (numslice+1)
					#name=s+"-"+name.split("-", 1)[1]
					name=s+"-cell"+name.split("cell")[1]
					r.setName(name)
					try :
						rm.addRoi(r)
						rname=rm.getName(rm.getCount()-1)
						#rm.select(self.__dictImages[nameimage], rm.getCount()-1)
						rm.select(tempimp, rm.getCount()-1)
						rm.runCommand("Rename", name)
					except TypeError : continue
					
					
				#if isinstance(self.__dict[nameimage][cellname].getRoi(numslice),Roi) == True :
				#	s = "%04i" % (numslice)
				#	#rm.add(self.__dictImages[nameimage], self.__dict[nameimage][cellname].getRoi(numslice)  ,  numslice)
				#	name=self.__dict[nameimage][cellname].getRoi(numslice).getName()
				#	name=s+name
				#	self.__dict[nameimage][cellname].getRoi(numslice).setName(name)
				#	rm.addRoi(self.__dict[nameimage][cellname].getRoi(numslice))
			rm.runCommand("Save", self.__pathdir+"ROIs/"+cellname+".zip")
			rm.runCommand("reset")
		
		tempimp.close()
		
		# two methods in order to order the rois in the roi manager. (by cell or by image)
		#if methodeleon == True :
		#	for numslice in range(self.__dictImages[nameimage].getImageStackSize()) :
		#		for cellname in self.__dict[nameimage].keys() :
		#			if isinstance(self.__dict[nameimage][cellname].getRoi(numslice),Roi) == True :
		#				rm.addRoi(self.__dict[nameimage][cellname].getRoi(numslice))
		#else :
		#	rm.setVisible(True)
		#	for cellname in self.__dict[nameimage].keys() :	
		#		for numslice in range(self.__dictImages[nameimage].getImageStackSize()) :
		#			if isinstance(self.__dict[nameimage][cellname].getRoi(numslice),Roi) == True :
		#				rm.add(self.__dictImages[nameimage], self.__dict[nameimage][cellname].getRoi(numslice)  ,  numslice)
	

		#imp=self.__dictImages[nameimage]
		#imp.show()
		#rm.runCommand("Show None")
		#rm.runCommand("Show All")
		#rm.setEditMode(imp,False)
		
	# Allows the user to choose several parameters for the tracking.
	def __settings(self, imgName, flag) :
		"""
		Allows the user to choose several parameters for the tracking.
		
		"""
		
		#fenetre=JFrame("Import")
		#optionpane=JOptionPane("Do you want to import previous preferences ?",JOptionPane.QUESTION_MESSAGE ,JOptionPane.YES_NO_OPTION )
		#optionpane.setVisible(True)
		#dialog = optionpane.createDialog(fenetre, "Import")
     		#dialog.show()
     		#choice = optionpane.getValue()
     		#if choice==JOptionPane.YES_OPTION : self.__ImportPref()

		image=self.__dictImages[imgName]

		def outputpath(event) : 
			macrodir=IJ.getDirectory("macros")
			frame = Frame("Select the macro file")
			fd = FileDialog(frame)
			fd.setDirectory(macrodir)
			fd.show()
			macrodir = fd.getDirectory() 
			self.__macropath = fd.getFile()
			self.__text.setText(self.__macropath)
			print self.__macropath
			#self.__macropath=IJ.getDirectory("macros")
			#self.__macropath=IJ.getDirectory("")
			#self.__text.setText(self.__macropath)
		
		panel0=Panel()
		pathbutton=Button("Select macro file", actionPerformed = outputpath)
		#pathbutton.actionPerformed = outputpath
		self.__text = TextField(self.__macropath)
		panel0.add(pathbutton)
		panel0.add(self.__text)
		
		# -------- start batch mode --------- # 
		if self.__batch :
			pass
			#self.__ImportPref(flag) 
			image.hide()
		else :
			image.show()
			IJ.selectWindow(image.getID())
			gd0=NonBlockingGenericDialog("Settings")
			gd0.setFont(Font("Courrier", 1, 10))
			gd0.addMessage("---------------- PRE-PROCESSING OPTIONS -------------------")
			gd0.addCheckbox("Substract Background",self.__subback)				#box 1 subback
			gd0.addNumericField("Radius",self.__radius,0)
			gd0.addCheckbox("Run a macro for pre processing",self.__runmacro)		#box 2 runmacro
			gd0.addPanel(panel0)
			gd0.addMessage("-------------------------------------------")
			gd0.addMessage("Tracking parameters")
			gd0.addMessage("Coeffs modulate de weight of each parameter")
			gd0.addMessage("Max delta set the maximum allowed change in absolute units")
			gd0.addMessage(" ")
			gd0.addNumericField("Coeff Area   : ",self.__distparam[0],0)
			gd0.addNumericField("Max deltaArea   : ",self.__distparam[1],self.__nbdigits,6,"x times")
			gd0.addNumericField("Coeff Angle   : ",self.__distparam[2],0)
			gd0.addNumericField("Max deltaAngle   : ",self.__distparam[3],self.__nbdigits,6,"degrees")
			gd0.addNumericField("Coeff Feret   : ",self.__distparam[4],0)
			gd0.addNumericField("Max deltaFeret   : ",self.__distparam[5],self.__nbdigits,6,"x times")
			gd0.addNumericField("Coeff PositionX   : ",self.__distparam[6],0)
			gd0.addNumericField("Max deltaPositionX   : ",self.__distparam[7],self.__nbdigits,6,"pixels")
			gd0.addNumericField("Coeff PositionY   : ",self.__distparam[8],0)
			gd0.addNumericField("Max deltaPositionY   : ",self.__distparam[9],self.__nbdigits,6,"pixels")
			gd0.addMessage("-------------------------------------------")
			automethods=AutoThresholder.getMethods()
			gd0.addCheckbox("Manual Threshold",self.__manthresh)		#box 3 manthresh
			gd0.addChoice("Threshol Method : ",automethods,self.__thresMethod)
			gd0.addMessage("-------------------------------------------")
			#gd0.addCheckbox("Symmetry Around 0-180",self.__optionAngle)
			#gd0.addMessage("-------------------------------------------")
			#gd0.addCheckbox("Save cell files", self.__optionSave)
			#gd0.addMessage("-------------------------------------------")
			gd0.addCheckbox("Track new cells", self.__optionNewCells)	#box 4 newcells
			gd0.addMessage("-------------------------------------------")	
			gd0.addCheckbox("Generate time list with follow time lapse interval ?", self.__optionTimelapse)	#box 5 timelapse
			gd0.addNumericField("Estimated time lapse   : ",self.__timelapse,self.__nbdigits,6,"seconds")
			#gd0.hideCancelButton()
			gd0.showDialog()

			if gd0.wasCanceled() : return False
			#chosenstack=gd0.getNextChoice()
			#self.__img=WindowManager.getImage(chosenstack)
		
			self.__subback=gd0.getNextBoolean()				#box 1 subback
			self.__radius=gd0.getNextNumber()
			self.__runmacro=gd0.getNextBoolean()				#box 2 runmacro
			for i in range(10) : self.__distparam[i]=gd0.getNextNumber()
			#self.__distmethod=gd0.getNextChoice()
			self.__manthresh=gd0.getNextBoolean()				#box 3 manthresh
			self.__thresMethod=gd0.getNextChoice()
			#self.__optionAngle=gd0.getNextBoolean()
			#self.__optionSave=gd0.getNextBoolean()
			self.__optionNewCells=gd0.getNextBoolean()			#box 4 newcells
			self.__optionTimelapse=gd0.getNextBoolean()			#box 5 timelapse
			self.__timelapse=int(gd0.getNextNumber())
			
		# -------- start end batch mode --------- # 
		
		if self.__optionTimelapse :
			self.__dictTimeStack[imgName]=range(0,image.getImageStackSize()*self.__timelapse, self.__timelapse)

		if not self.__optionTimelapse and self.__source=="image" :
			self.__dictTimeStack[imgName]=range(0,image.getImageStackSize())
		
		#if option_import==True :
		#	temparray=
		#else : temparray=self.__calRois("image1", 1)
		#imp=self.__dictImages["image1"]
		if self.__manthresh :
			ip=image.getProcessor()
			self.__maxthr=ip.getMaxThreshold()
			self.__minthr=ip.getMinThreshold()

		temparray=self.__calRois(image, 1)
		self.__rr=RangeRois(temparray, image)		

		if (not self.__batch) : 
			image.show()
			self.__params=self.__rr.showSettingsDialog().values()
		if self.__batch : image.hide()

		return True
	

	# function that saves the cells in .cell
	def __SaveCells(self,nameimage):

		#os.mkdir(self.__pathdir+"Cells/", mode=0777)
		os.makedirs(self.__pathdir+"Cells/", mode=0777)
		for cellname in self.__dict[nameimage].keys():

			fichiertemp = open(self.__pathdir+"Cells/"+cellname+".cell","w")
			fichiertemp.write("NAMECELL="+cellname+"\n")
			fichiertemp.write("PATHCELL="+self.__pathdir+"Cells/"+cellname+".cell\n")
			fichiertemp.write("PATHROIS="+self.__pathdir+"ROIs/"+cellname+".zip\n")
			fichiertemp.write("NSLICES="+str(len(self.__dict[nameimage][cellname].getListRoi()))+"\n")
			fichiertemp.write("SLICEINIT="+str(self.__dict[nameimage][cellname].getSlideInit())+"\n")
			fichiertemp.write("SLICEEND="+str(self.__dict[nameimage][cellname].getSlideEnd())+"\n")
			colortemp=self.__dict[nameimage][cellname].getColor()
			fichiertemp.write("COLOR="+str(colortemp.getRed())+";"+str(colortemp.getGreen())+";"+str(colortemp.getBlue())+"\n")
			fichiertemp.close()

	# function that saves the preferences of the track made in a track.txt
	def __SaveStack(self,nameimage,imp):

		toparse = [self.__subback, self.__manthresh, self.__optionAngle, self.__optionNewCells, self.__optionTimelapse]
		self.__subback, self.__manthresh, self.__optionAngle, self.__optionNewCells, self.__optionTimelapse = map(self.parsebool, toparse)
		
		fichier = open(self.__pathdir+"Track.txt","w")
		fichier.write("NOMIMAGE="+imp.getTitle()+"\n")
		fichier.write("PATH="+str(IJ.getDirectory("image"))+"\n")
		fichier.write("NSLICES="+str(imp.getImageStackSize())+"\n")
		fichier.write("NCELLS="+str(len(self.__dict[nameimage]))+"\n")
		fichier.write("CELLSINFOPATH="+self.__pathdir+"\n")
		
		fichier.write("SUBBACK="+str(self.__subback)+"\n")
		fichier.write("SUBBACKRADIUS="+str(self.__radius)+"\n")
		fichier.write("DISTPARAM_AREA_COEFF="+str(self.__distparam[0])+"\n")
		fichier.write("DISTPARAM_AREA_MAXDELTA="+str(self.__distparam[1])+"\n")
		fichier.write("DISTPARAM_ANGLE_COEFF="+str(self.__distparam[2])+"\n")
		fichier.write("DISTPARAM_ANGLE_MAXDELTA="+str(self.__distparam[3])+"\n")
		fichier.write("DISTPARAM_FERETMAX_COEFF="+str(self.__distparam[4])+"\n")
		fichier.write("DISTPARAM_FERETMAX_MAXDELTA="+str(self.__distparam[5])+"\n")
		fichier.write("DISTPARAM_POSITIONX_COEFF="+str(self.__distparam[6])+"\n")
		fichier.write("DISTPARAM_POSITIONX_MAXDELTA="+str(self.__distparam[7])+"\n")
		fichier.write("DISTPARAM_POSITIONY_COEFF="+str(self.__distparam[8])+"\n")
		fichier.write("DISTPARAM_POSITIONY_MAXDELTA="+str(self.__distparam[9])+"\n")
		fichier.write("DISTMETHOD="+self.__distmethod+"\n")
		fichier.write("OPTIONMANTHRESH="+str(self.__manthresh)+"\n")
		fichier.write("THRESHMETHOD="+str(self.__thresMethod)+"\n")
		fichier.write("OPTIONANGLE="+str(self.__optionAngle)+"\n")
		fichier.write("OPTIONNEWCELLS="+str(self.__optionNewCells)+"\n")
		fichier.write("OPTIONTIMELAPSE="+str(self.__optionTimelapse)+"\n")
		fichier.write("TIMELAPSE="+str(self.__timelapse)+"\n")
		
		
		for params in self.__params :
			fichier.write(params[0]+"="+str(params[1])+";"+str(params[2])+"\n")
		fichier.close()


	# function that loads the preferences of a previous track in order to use them in this track.
	def __ImportPref(self, flag) :
		indiceinterest=5
		
		if len(self.__params) < 1 :
			if flag == 1 :
				IJ.showMessage("Select the text file containing the preferences you want (Track.txt file)")
				self.__selectdir=IJ.getDirectory("image")
				frame = Frame("Text file settings ?")
				fd = FileDialog(frame)
				fd.setDirectory(self.__selectdir)
				fd.show()
				self.__selectdir = fd.getDirectory() 
				self.__textfile = fd.getFile()
				#self.__selectdir=IJ.getDirectory("")
				#listfiles=glob.glob(selectdir+"*DIA_s0001*.tif")
			#fichier = open(self.__selectdir+"Track.txt","r")

			fichier = open(self.__selectdir+self.__textfile,"r")
			lignes=fichier.readlines()
			self.__params=[]
			for i in range(indiceinterest,len(lignes)):						# ATTENTION  CHANGER AVEC PARAM DE RANGEROI
				params=lignes[i].split("=")
				val=params[1].split("\n")
				if params[0]=="SUBBACK" : self.__subback=bool(int(val[0]))
				if params[0]=="SUBBACKRADIUS" : self.__radius=Double(val[0])
				if params[0]=="DISTPARAM_AREA_COEFF" : self.__distparam[0]=int(val[0])
				if params[0]=="DISTPARAM_AREA_MAXDELTA" : self.__distparam[1]=Double(val[0])
				if params[0]=="DISTPARAM_ANGLE_COEFF" : self.__distparam[2]=int(val[0])
				if params[0]=="DISTPARAM_ANGLE_MAXDELTA" : self.__distparam[3]=Double(val[0])
				if params[0]=="DISTPARAM_FERETMAX_COEFF" : self.__distparam[4]=int(val[0])
				if params[0]=="DISTPARAM_FERETMAX_MAXDELTA" : self.__distparam[5]=Double(val[0])
				if params[0]=="DISTPARAM_POSITIONX_COEFF" : self.__distparam[6]=int(val[0])
				if params[0]=="DISTPARAM_POSITIONX_MAXDELTA" : self.__distparam[7]=int(val[0])
				if params[0]=="DISTPARAM_POSITIONY_COEFF" : self.__distparam[8]=int(val[0])
				if params[0]=="DISTPARAM_POSITIONY_MAXDELTA" : self.__distparam[9]=int(val[0])
				if params[0]=="DISTMETHOD" : self.__distmethod=str(val[0])
				if params[0]=="OPTIONMANTHRESH" : self.__manthresh=bool(int(val[0]))
				if params[0]=="THRESHMETHOD" : self.__thresMethod=str(val[0])
				if params[0]=="OPTIONANGLE" : self.__optionAngle=bool(int(val[0]))
				if params[0]=="OPTIONNEWCELLS" : self.__optionNewCells=bool(int(val[0]))
				if params[0]=="OPTIONTIMELAPSE" : self.__optionTimelapse=bool(int(val[0]))
				if params[0]=="TIMELAPSE" : self.__timelapse=int(val[0])

				# imported booleans : self.__subback, self.__manthresh, self.__optionAngle, self.__optionNewCells, self.__optionTimelapse
		
				minmax=val[0].split(";")
				if params[0]=="Area" : self.__params.append(("Area",Double(minmax[0]),Double(minmax[1])))
				if params[0]=="Mean" : self.__params.append(("Mean",Double(minmax[0]),Double(minmax[1])))
				if params[0]=="Angle" : self.__params.append(("Angle",Double(minmax[0]),Double(minmax[1])))
				if params[0]=="Major" : self.__params.append(("Major",Double(minmax[0]),Double(minmax[1])))
				if params[0]=="Minor" : self.__params.append(("Minor",Double(minmax[0]),Double(minmax[1])))
				if params[0]=="Solidity" : self.__params.append(("Solidity",Double(minmax[0]),Double(minmax[1])))
				if params[0]=="AR" : self.__params.append(("AR",Double(minmax[0]),Double(minmax[1])))
				if params[0]=="Round" : self.__params.append(("Round",Double(minmax[0]),Double(minmax[1])))
				if params[0]=="Circ" : self.__params.append(("Circ",Double(minmax[0]),Double(minmax[1])))

	def getDictCells(self,nameimage) :
		#print "BT, dict", self.__dict.keys()
		return self.__dict[nameimage]

	def getDictImages(self):
		return self.__dictImages

	def getPathdir(self):
		return self.__pathdir

	def setPositionslist(self, positions) : 
		self.__positionsList=positions

	def parsebool(self, val) :
		if val : return str(1)
		else : return str(0)

			
############################################## end class Bacteria_Tracking ################################################################################################
		


if __name__ == "__main__":
	import os, glob
	from os import path
	
	bact=Bacteria_Tracking()
	#def run(self, files, path, scale, batch, **settings):														
	if IJ.showMessageWithCancel("", "active image ? (ok) \nfiles (cancel)") :
		bact.run(IJ.getImage(), "", 1, False)
	else :
		selectdir=IJ.getDirectory("image")
		selectdir=IJ.getDirectory("")
		listfiles=[]
		listfiles.append(glob.glob(selectdir+"*DIA_s0001*t000[1-9].tif"))
		listfiles.append(glob.glob(selectdir+"*DIA_s0002*t000[1-9].tif"))
		bact.run(listfiles)
		
