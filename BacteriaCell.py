

from java.awt import TextField, Panel, GridLayout, ComponentOrientation, Label, Checkbox, BorderLayout, Button, Color, Font, Rectangle, Frame, FileDialog

from org.python.core import codecs
codecs.setDefaultEncoding('utf-8')


from ij import ImageStack, ImagePlus, WindowManager, IJ
from ij.gui import Roi, NonBlockingGenericDialog, Overlay, ImageRoi, Line, OvalRoi, PolygonRoi, ShapeRoi, TextRoi
from ij.process import ImageProcessor, ShortProcessor, ByteProcessor
from ij.plugin.frame import RoiManager
from ij.text import TextWindow
from ij.plugin import Straightener, Duplicator, ZProjector, MontageMaker, ImageCalculator
from ij.measure import ResultsTable


class Bacteria_Cell(object) :
	"""
		Object corresponding to a bacteria, with its caracteristics (ROIs on each slide, color, etc...).
		
	"""
	def __init__(self, name) :

		# list of all ROIs of the cell ( "NOT HERE YET" if it doesn't exist yet, or "LOST" if it disappears)
		#===> "div_cell1_cell2" if the cell is divided in two cells  ? pas possible de donner une liste de pointeurs vers les deux cellules filles ???
		self.__listRoi=[]								

		# list of all the times corresponding to the slides.
		self.__listTimes=[]								
		
		# dictionnary of all the useful informations on the cell
		#self.__dictCell={}								
		
		# name given to the cell
		self.__name=name								
		
		# color given to the cell 
		self.__color="blue"

		# lifetime of the cell
		self.__lifetime=0

		# number of the slice when it appears
		self.__slide_init=1

		# number of the slice when it disappears
		self.__slide_end=1

		# dictionnary of all measures made on the cell
		#self.__dictMeasures={}

	#***************************** Getters : *****************************


	def getColor(self):
		return self.__color

	def getLifeTime(self):
		return self.__slide_end-self.__slide_init+1

	def getSlideInit(self) :
		return self.__slide_init
		
	def getSlideEnd(self) :
		return self.__slide_end

	def getRoi(self, indice) :
		if 0<= indice < len(self.__listRoi):
			return self.__listRoi[indice]
		else :
			return None
		
	def getListRoi(self) :
		return self.__listRoi

	def getListTimes(self) :
		return self.__listTimes
		
	def getName(self): 
		return self.__name

	def getCellDict(self) :
		return self.__dictCell


		
	#***************************** Setters : *****************************

	def setColor(self, color):
		self.__color=color
		for roi in self.__listRoi :
			if isinstance(roi,Roi) == True :
				roi.setStrokeColor(color)
	
	def setSlideEnd(self, num) :
		self.__slide_end=num
			
	def setlistRois(self, roilist) :				
		self.__listRoi[:]=[]
		self.__listRoi=[r for r in roilist]
		#self.__buildDict()

	def setlistTimes(self, timeslist) :						
		self.__listTimes[:]=[]
		self.__listTimes=[t for t in timeslist] 
		#self.__buildDict()

	def setSlideInit(self, num) :
		self.__slide_init=num

	def setRoi(self, roi, indice) :
		self.__listRoi.insert(indice, roi)

	def testClass(self):
		print "ok class"

	@staticmethod
	def makeCell(cellfile) :

		filetemp = open(cellfile,"r")
		linestemp=filetemp.readlines()
		for line in linestemp :
			params=line.split("=")
			values=params[1].split("\n")
			if params[0] == "NAMECELL" :
				celltemp=Bacteria_Cell(str(values[0]))
			if params[0] == "PATHROIS" :
				pathtemp = str(values[0])
			if params[0] == "NSLICES" : 
				for i in range(int(values[0])) :
					celltemp.getListRoi().append("")
			if params[0] == "SLICEINIT" :
				celltemp.setSlideInit(int(values[0]))
				#for i in range(int(values[0])-2) :
				#	celltemp.setRoi("NOT HERE YET",i)
			if params[0] == "SLICEEND" :
				celltemp.setSlideEnd(int(values[0]))
				#for i in range(int(values[0])) :
				#	celltemp.setRoi("LOST",i)
				
			if params[0] == "COLOR" :
				colorstemp=values[0].split(";")
				celltemp.setColor(Color(int(colorstemp[0]),int(colorstemp[1]),int(colorstemp[2])))

		rm = RoiManager.getInstance()
		if (rm==None): rm = RoiManager()
		rm.runCommand("reset")
		rm.runCommand("Open", pathtemp)
		rois=rm.getSelectedRoisAsArray()
		celltemp.setlistRois(rois)
		rm.runCommand("UseNames", "true")
		rm.runCommand("Associate", "true")

		return celltemp
		
	#--
	
	name=property(getName, doc="")

	
if __name__ == "__main__":
	cell=Bacteria_Cell("test")
	cell2=Bacteria_Cell.makeCell("/Volumes/Equipes/Alain_Dolla/Corinne_Aubert/Anouchka/wt-stab/30-01-12_09h12m11s/Cells/cell0015.cell")
	print cell2.name
	print cell2.testClass()

	
	
	