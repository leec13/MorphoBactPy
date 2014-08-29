import sys
import os
import os.path
import math
from sets import Set

from java.awt import TextField, Panel, GridLayout, ComponentOrientation, Label, Checkbox, BorderLayout, Button, Color
from java.awt.event import ActionListener, AdjustmentListener, WindowEvent
from java.awt import Font


from ij.plugin.frame import RoiManager


from ij import ImageStack, ImagePlus, WindowManager, IJ
from ij.gui import Roi, NonBlockingGenericDialog, Overlay, ImageRoi, Line, OvalRoi, PolygonRoi, ShapeRoi, TextRoi
from ij.plugin.frame import RoiManager
from ij.plugin.filter import MaximumFinder, Analyzer
from ij.text import TextWindow
from ij.plugin import Straightener, Duplicator, ZProjector, MontageMaker, ImageCalculator
from ij.process import ShortProcessor, ByteProcessor
from ij.measure import ResultsTable


from org.python.core import codecs
codecs.setDefaultEncoding('utf-8')

from ij import IJ, ImagePlus
from ij.measure import Calibration, Measurements
from ij.gui import Overlay, NonBlockingGenericDialog, Roi
from ij.plugin.filter import ParticleAnalyzer


#mypath=os.path.expanduser(IJ.getDirectory("plugins")+"MeasureCells")
mypath=os.path.expanduser(os.path.join("~","Dropbox","MacrosDropBox","py","MorphoBactProject"))

#mypath=os.path.expanduser("~/Dropbox/MacrosDropBox/py/MeasureCells_7")
#mypath=os.path.expanduser(os.path.join("~","Dropbox","MacrosDropBox","py","MeasureCells_7"))
sys.path.append(mypath)

from MorphoBact import Morph

class RangeRois(object):
	"""This class allows to sort an array of ROI according to a range of measures
		in a range between min and max values
	"""

	__rawRanges={}
	__image=None
	__test=""
	
	
	def __init__(self, rois, img): #constructor initialize a private rois array
		self.__roisArray=[]
		self.__roisArray+=rois
		self.__image=img
		self.__firstslice=img.getSlice()
		self.__ranges={}
		self.__test="ok"
		Roi.setColor(Color.BLUE)
		self.__setMaxValues()

	def setRoisarray(self, rois, img) : 
		self.__roisArray=[]
		self.__roisArray+=rois
		self.__image=img
		self.__firstslice=img.getSlice()
		self.__ranges={}
		self.__test="ok"
		Roi.setColor(Color.BLUE)

	def __setMaxValues(self) :
		areas, means, majors, minors=[],[],[],[]
		for roi in self.__roisArray:
			m=Morph(self.__image, roi)
			areas.append(m.Area)
			means.append(m.Mean)
			majors.append(m.Major)
			minors.append(m.Minor)
			
		maxarea=max(areas)*1000
		maxint=max(means)*10
		maxline=max(majors)*100
		maxminline=max(minors)*100
		minline=min(minors)
		
		self.__namemeasures=["Area", "Mean", "Angle", "Major", "Minor", "Solidity", "AR", "Round", "Circ"]
		self.__maxmeasures=[maxarea, maxint, 180*10, maxline, maxminline, 1*1000, (maxline/minline), 1*1000, 1*1000]
		self.__set1000=Set(["Solidity", "Round", "Circ"])
		self.__set10=Set(["Angle"])

		self.__dictMaxList={}
		for i in range(len(self.__namemeasures)) :
			self.__dictMaxList[self.__namemeasures[i]]=self.__maxmeasures[i]

	def setRange(self, stackposition, *params):
		"""
			This method expect a list of tuples composed by:
			(measure_name, min_value, max_value, boolean flag to apply or not)
		"""

		test=isinstance(params[0][0],str)
		#self.__ranges.clear()
		
		if test:
			self.__ranges[params[0][0]]=(params[0][0], params[0][1], params[0][2], params[0][3])

		else :
			for p in params:
				#print "p", p
				for i in range(len(p)):
					#self.__ranges[p[i][0]]=(p[i][0], p[i][1], p[i][2])
					if stackposition==1 : self.__ranges[p[i][0]]=(p[i][0], p[i][1], p[i][2], p[i][3])
					elif stackposition>1 and p[i][3] : self.__ranges[p[i][0]]=(p[i][0], p[i][1], p[i][2], p[i][3])
					else : self.__ranges[p[i][0]]=(p[i][0], 0, self.__dictMaxList[p[i][0]], p[i][3])

		
	def getIncludeRois(self):
		self.__yieldRois=[]
		self.__yieldRois[:]=[]
		for roi in self.__roisArray:
			m=Morph(self.__image, roi)
			state=0
			for r in self.__ranges.values():
				if r[1]<=m.__getattribute__(r[0])<=r[2]: state=state+0 
				else: state=state+1
			if state<1 : self.__yieldRois.append(roi)
		return self.__yieldRois


	def showSettingsDialog(self):
		if self.__image.getOverlay() is not None : self.__image.getOverlay().clear()
		rm = RoiManager.getInstance()
		if (rm==None): rm = RoiManager()
		#rm.runCommand("Deselect")
		#for i in range(rm.getCount()) : 
		#	rm.select(i)
		#	rm.runCommand("Set Color", "0000FF", 2)
		
		
		IJ.resetThreshold(self.__image)

		rm.runCommand("Show All")
		
		self.__ranges.clear()
		#areas, means, majors, minors=[],[],[],[]

		#for roi in self.__roisArray:
		#	m=Morph(self.__image, roi)
		#	areas.append(m.Area)
		#	means.append(m.Mean)
		#	majors.append(m.Major)
		#	minors.append(m.Minor)
			
		#maxarea=max(areas)*1000
		#maxint=max(means)*10
		#maxline=max(majors)*100
		#maxminline=max(minors)*100
		#minline=min(minors)
		
		#namemeasures=["Area", "Mean", "Angle", "Major", "Minor", "Solidity", "AR", "Round", "Circ"]
		#maxmeasures=[maxarea, maxint, 180*10, maxline, maxminline, 1*1000, (maxline/minline), 1*1000, 1*1000]
		#set1000=Set(["Solidity", "Round", "Circ"])
		#set10=Set(["Angle"])
		
		def buttonPressed(event):
			temprois=self.getIncludeRois()
			for roi in temprois:
				m=Morph(self.__image, roi)
				IJ.log("----------------------------------")
				IJ.log(roi.getName())
				for r in self.__ranges.values():
					IJ.log(r[0]+" min= "+str(r[1])+" < val="+str(m.__getattribute__(r[0]))+" < max= "+str(r[2]))
			IJ.run(self.__image, "Remove Overlay", "")
			o=Overlay()
			for roi in temprois:
				o.addElement(roi)
			self.__image.killRoi()
			self.__image.setOverlay(o)
			self.__image.updateAndDraw()

		def updatepressed(event):
			self.__image=IJ.getImage()
			rm = RoiManager.getInstance()
			if (rm==None): rm = RoiManager()
			rm.runCommand("reset")
			self.__image.killRoi()
			IJ.run("Threshold...")
			IJ.setAutoThreshold(self.__image, "MaxEntropy")
			
			rt=ResultsTable()
			pa=ParticleAnalyzer(ParticleAnalyzer.ADD_TO_MANAGER+ParticleAnalyzer.CLEAR_WORKSHEET , Measurements.AREA+Measurements.ELLIPSE+Measurements.MEAN, rt, 0.00, 10000.00, 0.00, 1.00)
			pa.analyze(self.__image)
			self.__roisArray=[]
			self.__roisArray=rm.getRoisAsArray()
			#for i in range(rm.getCount()) : 
			#	rm.select(i)
			#	rm.runCommand("Set Color", "0000FF", 2)
				
			IJ.resetThreshold(self.__image)
			rt.show("tempRT")
			areas=rt.getColumn(ResultsTable.AREA)
			means=rt.getColumn(ResultsTable.MEAN)
			majors=rt.getColumn(ResultsTable.MAJOR)
			minors=rt.getColumn(ResultsTable.MINOR)
			#print 0
			if self.__slidersDict["Area_max"].getMaximum() <  int(max(areas)+1):
			#	print 1
				self.__slidersDict["Area_max"].setMaximum(int(max(areas))+1)
			if self.__slidersDict["Area_min"].getMaximum() < int(max(areas)+1):
			#	print 2
				self.__slidersDict["Area_min"].setMaximum(int(max(areas))+1)
			if self.__slidersDict["Mean_max"].getMaximum() < int(max(means)+1):
			#	print 3
				self.__slidersDict["Mean_max"].setMaximum(int(max(means))+1)
			if self.__slidersDict["Mean_min"].getMaximum() < int(max(means)+1):
			#	print 4
				self.__slidersDict["Mean_min"].setMaximum(int(max(means))+1)
			if self.__slidersDict["Major_max"].getMaximum() < int(max(majors)):
			#	print 5
				self.__slidersDict["Major_max"].setMaximum(int(max(majors))+1)
			if self.__slidersDict["Major_min"].getMaximum() < int(max(majors)+1):
			#	print 6
				self.__slidersDict["Major_min"].setMaximum(int(max(majors))+1)
			if self.__slidersDict["Minor_max"].getMaximum() < int(max(minors)+1):
			#	print 7
				self.__slidersDict["Minor_max"].setMaximum(int(max(minors))+1)
			if self.__slidersDict["Minor_min"].getMaximum() < int(max(minors)+1):
			#	print 8
				self.__slidersDict["Minor_min"].setMaximum(int(max(minors))+1)
			if self.__slidersDict["AR_max"].getMaximum() < int((max(majors)+1)/min(minors)+1):
			#	print 9
				self.__slidersDict["AR_max"].setMaximum(int((max(majors)+1)/(min(minors))))
			if self.__slidersDict["AR_min"].getMaximum() < int((max(majors)+1)/min(minors)):
			#	print 10
				self.__slidersDict["AR_min"].setMaximum(int((max(majors)+1)/(min(minors))))

			#print 11
				
			for sb in self.__slidersDict.values():
				sb.repaint()

			#rm.runCommand("reset")
			#temprois=self.getIncludeRois()
			#IJ.run(self.__image, "Remove Overlay", "")
			#o=Overlay()
			#for roi in temprois:
			#	o.addElement(roi)
			#self.__image.killRoi()
			#self.__image.setOverlay(o)
			self.__image.updateAndDraw()

		def resetpressed(event):
			self.__ranges.clear()
			self.__image=IJ.getImage()
			rm = RoiManager.getInstance()
			if (rm==None): rm = RoiManager()
			rm.runCommand("reset")
			self.__image.killRoi()
			IJ.setAutoThreshold(self.__image, "MaxEntropy")
			rt=ResultsTable()
			pa=ParticleAnalyzer(ParticleAnalyzer.ADD_TO_MANAGER+ParticleAnalyzer.CLEAR_WORKSHEET , Measurements.AREA+Measurements.ELLIPSE+Measurements.MEAN, rt, 0.00, 10000.00, 0.00, 1.00)
			pa.analyze(self.__image)
			self.__roisArray=[]
			self.__roisArray=rm.getRoisAsArray()
			#rm.runCommand("Show All")
			#rm.runCommand("Select All")
			#rm.runCommand("Set Color", "blue")
			
			IJ.resetThreshold(self.__image)
			
			keys=self.__slidersDict.keys()
			for k in keys:
				if k.endswith("min"): 
					self.__slidersDict[k].setValue(0)
					self.__slidersDict[k].repaint()
				else:
					self.__slidersDict[k].setValue(self.__slidersDict[k].getMaximum())
					self.__slidersDict[k].repaint()
			
		def valueChanged(event):
			name=event.getSource().getName()
			names=name.split("_")
			factor=1
			if names[0] in self.__set1000: factor=0.001
			if names[0] in self.__set10:factor=0.1
			value=event.getSource().getValue()*factor
			if names[1]=="min":
				self.__ranges[names[0]]=(names[0], value, self.__slidersDict[names[0]+"_max"].getValue()*factor, self.__boxesDict[names[0]].getState())
				#self.__ranges[names[0]]=(names[0], value, self.__slidersDict[names[0]+"_max"].getValue()*factor)
			else: self.__ranges[names[0]]=(names[0], self.__slidersDict[names[0]+"_min"].getValue()*factor, value, self.__boxesDict[names[0]].getState())
				#self.__ranges[names[0]]=(names[0], self.__slidersDict[names[0]+"_min"].getValue()*factor, value)
			temprois=self.getIncludeRois()
			IJ.run(self.__image, "Remove Overlay", "")
			o=Overlay()
			for roi in temprois:
				o.addElement(roi)
			self.__image.killRoi()
			self.__image.setOverlay(o)
			self.__image.updateAndDraw()

		def selectAll(event):
			name=event.getSource().getLabel()
			names=name.split("_")
			factor=1
			if names[0] in self.__set1000: factor=0.001
			if names[0] in self.__set10:factor=0.1
			name=event.getSource().getLabel()
			names=name.split("_")
			value=event.getSource().getState()
			self.__ranges[names[0]]=(names[0], self.__slidersDict[names[0]+"_min"].getValue()*factor, self.__slidersDict[names[0]+"_max"].getValue()*factor, value)
			

		gd0=NonBlockingGenericDialog("settings")
		gd0.setResizable(True)
		gd0.setFont(Font("Courrier", 1, 8))
		count=0
		self.__slidersDict={}
		self.__boxesDict={}
		self.__boxesDict.clear()
		self.__slidersDict.clear()
		for i in range(len(self.__namemeasures)):
			gd0.setInsets(-10,0,0)			
			gd0.addSlider("Min"+self.__namemeasures[i], 0, self.__maxmeasures[i], 0)
			gd0.getSliders().get(count).adjustmentValueChanged = valueChanged
			gd0.getSliders().get(count).setName(self.__namemeasures[i]+"_min")
			self.__slidersDict[self.__namemeasures[i]+"_min"]=gd0.getSliders().get(count)			
			gd0.addSlider("Max"+self.__namemeasures[i], 0, self.__maxmeasures[i], self.__maxmeasures[i])
			gd0.getSliders().get(count+1).adjustmentValueChanged = valueChanged
			gd0.getSliders().get(count+1).setName(self.__namemeasures[i]+"_max")
			self.__slidersDict[self.__namemeasures[i]+"_max"]=gd0.getSliders().get(count+1)
			gd0.addCheckbox("all", True)
			gd0.getCheckboxes().get(i).itemStateChanged = selectAll
			gd0.getCheckboxes().get(i).setLabel(self.__namemeasures[i]+"_all")
			self.__boxesDict[self.__namemeasures[i]]=gd0.getCheckboxes().get(i)
			gd0.setInsets(-10,0,0)
			#gd0.addMessage("...........................................................................")

			count=count+2
		
		panel0=Panel()
		#trybutton=Button("Try")
		#trybutton.setActionCommand("DrawOverlay")
		#trybutton.actionPerformed = buttonPressed
		#updatebutton=Button("Update")
		#updatebutton.setActionCommand("Update")
		#updatebutton.actionPerformed = updatepressed
		#resetbutton=Button("Reset")
		#resetbutton.setActionCommand("Reset")
		#resetbutton.actionPerformed = resetpressed
		
		
		#panel0.add(trybutton)
		#panel0.add(updatebutton)
		#panel0.add(resetbutton)
		#gd0.addPanel(panel0)

		gd0.setResizable(True) 
		
		gd0.showDialog()
		#self.__image.setSlice(self.__firstslice)
		#self.__image.updateAndDraw()
			
				
		if gd0.wasOKed():
			#for key in self.__ranges.keys(): IJ.log("Measure : "+str(self.__ranges[key][0])+" min = "+str(self.__ranges[key][1])+" max = "+str(self.__ranges[key][2]))
			return self.__ranges

	
	includeRois=property(getIncludeRois, doc="rois include in the measures ranges")
		
#----- end class ----------

if __name__ == "__main__":
	rm=RoiManager.getInstance()
	rois=rm.getRoisAsArray()
	img=IJ.getImage()
	r=RangeRois(rois, img)
	r.showSettingsDialog()
	for roi in r.includeRois : print roi.getName()
	
	
	
	