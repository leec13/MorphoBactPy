# -*- coding: iso-8859-15 -*-

import javax.swing as swing
import java.awt as awt
from javax.swing import BorderFactory
from javax.swing.border import EtchedBorder, TitledBorder
from java.awt import Font

from ij import ImageStack, ImagePlus, WindowManager, IJ
from ij.gui import Roi, NonBlockingGenericDialog, Overlay
from ij.plugin.frame import RoiManager
from ij.plugin.filter import MaximumFinder

import sys
import os
import time
import glob
import os.path as path
import getpass
import shutil
import random
import math

username=getpass.getuser()

#mypath=os.path.expanduser(IJ.getDirectory("plugins")+"MeasureCells")
mypath=os.path.expanduser(os.path.join("~","Dropbox","MacrosDropBox","py","MorphoBactProject"))
sys.path.append(mypath)

from org.python.core import codecs
codecs.setDefaultEncoding('utf-8')

from MorphoBact import Morph
from RangeRois import RangeRois

class StackCells(swing.JFrame):
	def __init__(self): 
		swing.JFrame.__init__(self, title="Stack Cells")
		self.__impD = IJ.getImage()
		self.setDefaultCloseOperation(swing.JFrame.DISPOSE_ON_CLOSE)
		self.__n=0
		self.__widthl = "11"
		self.__iplist = []
		self.__init = False
		self.__initDIA = False
		self.__initFLUO = False
		self.__skip = False
		self.__avg = True
		self.__mosa = True
		self.__maxfinder = True
		self.__appmedian = True
		self.__fire = True
		self.__align = True
		self.__alignC = False
		self.__enlarge = True
		self.__measures = True
		self.__sens = []
		self.__listrois = []
		self.__cellsrois = []
		self.__Cutoff = 0
		self.__labels = []
		self.__maxraf = 1.1
		self.__minraf = 0.0
		self.__conEllipses = False

		self.__dictCells = {}
		
		self.__rm = RoiManager.getInstance()
		if (self.__rm==None): self.__rm = RoiManager()
		self.run()
		
	def run(self) :
		

		self.size=(1100, 400)
		self.contentPane.layout = awt.BorderLayout()
		self.__display = swing.JTextField(preferredSize=(400, 30), horizontalAlignment=swing.SwingConstants.LEFT)
		self.__setDisplay()
		line = BorderFactory.createEtchedBorder(EtchedBorder.LOWERED)
		northpanel1=swing.JPanel(awt.FlowLayout(awt.FlowLayout.LEFT))
		northpanel1.setBorder(line)
		northpanel1.add(self.__display)
		new = swing.JButton("New", size=(100, 70), actionPerformed=self.__new)
		northpanel1.add(new)
		add = swing.JButton("Add", size=(100, 70), actionPerformed=self.__add)
		northpanel1.add(add)
		roiman = swing.JButton("Add Roi manager", size=(100, 70), actionPerformed= self.__addroi)
		northpanel1.add(roiman)
		end = swing.JButton("End", size=(100, 70), actionPerformed= self.__end)
		northpanel1.add(end)

		#grid = awt.GridLayout()
		#grid.setRows(2)
		#northpanel=swing.JPanel(grid)
		#northpanel.add(northpanel1)

		#northpanel2=swing.JPanel(awt.FlowLayout(awt.FlowLayout.LEFT))

		grid0 = awt.GridLayout()
		grid0.setRows(6)
		northpanel2=swing.JPanel(grid0)
		
		northpanel2.setBorder(line)
		label=swing.JLabel("Label2")
		label.setText("Line width ?")
		northpanel2.add(label)
		self.__display2 = swing.JTextField(preferredSize=(50, 30), horizontalAlignment=swing.SwingConstants.LEFT)
		self.__display2.text = "11"
		northpanel2.add(self.__display2)

		label=swing.JLabel("Label3")
		label.setText("Noise for peaks ?")
		northpanel2.add(label)
		self.__display3 = swing.JTextField(preferredSize=(50, 30), horizontalAlignment=swing.SwingConstants.LEFT)
		self.__display3.text = "100"
		northpanel2.add(self.__display3)

		label=swing.JLabel("Label4")
		label.setText("Fluo threshold ?")
		northpanel2.add(label)
		self.__display4 = swing.JTextField(preferredSize=(50, 30), horizontalAlignment=swing.SwingConstants.LEFT)
		self.__display4.text = "170"
		northpanel2.add(self.__display4)
		
		#northpanel3=swing.JPanel(awt.FlowLayout(awt.FlowLayout.LEFT))
		#northpanel3.setBorder(line)

		label=swing.JLabel("Label5")
		label.setText("Min of length ?")
		northpanel2.add(label)
		self.__display5 = swing.JTextField(preferredSize=(50, 30), horizontalAlignment=swing.SwingConstants.LEFT)
		self.__display5.text = "50"
		northpanel2.add(self.__display5)

		label=swing.JLabel("Label6")
		label.setText("Max of length ?")
		northpanel2.add(label)
		self.__display6 = swing.JTextField(preferredSize=(50, 30), horizontalAlignment=swing.SwingConstants.LEFT)
		self.__display6.text = "500"
		northpanel2.add(self.__display6)

		dia = swing.JButton("DIA", size=(100, 70), actionPerformed= self.__dia)
		northpanel2.add(dia)
		fluo = swing.JButton("FLUO", size=(100, 70), actionPerformed= self.__fluo)
		northpanel2.add(fluo)


		southpanel=swing.JPanel(awt.FlowLayout(awt.FlowLayout.RIGHT))
		southpanel.setBorder(line)
		
		help = swing.JButton("Help", size=(100, 70), actionPerformed=self.__help)
		
		self.__label=swing.JLabel("Label")
		southpanel.add(self.__label)
		close = swing.JButton("Close", size=(100, 70), actionPerformed=self.__close)

		southpanel.add(help)
		southpanel.add(close)		
				
		grid = awt.GridLayout()
		grid.setRows(4)
		checkpanel=swing.JPanel(grid)
		checkpanel.setBorder(line)
		
		self.__box0=swing.JCheckBox(actionPerformed=self.__boxaction0)
		self.__box0.setText("Skip failed ROIs")
		self.__box0.setSelected(False)
		
		self.__box1=swing.JCheckBox(actionPerformed=self.__boxaction1)
		self.__box1.setText("Mosaic")
		self.__box1.setSelected(True)
		
		self.__box2=swing.JCheckBox(actionPerformed=self.__boxaction2)
		self.__box2.setText("Mean Projection")
		self.__box2.setSelected(True)

		self.__box3=swing.JCheckBox(actionPerformed=self.__boxaction3)
		self.__box3.setText("Max Finder")
		self.__box3.setSelected(True)

		self.__box4=swing.JCheckBox(actionPerformed=self.__boxaction4)
		self.__box4.setText("Median filter")
		self.__box4.setSelected(True)

		self.__box5=swing.JCheckBox(actionPerformed=self.__boxaction5)
		self.__box5.setText("Fire LUT")
		self.__box5.setSelected(True)

		self.__box6=swing.JCheckBox(actionPerformed=self.__boxaction6)
		self.__box6.setText("Auto Align Left")
		self.__box6.setSelected(True)

		self.__box7=swing.JCheckBox(actionPerformed=self.__boxaction7)
		self.__box7.setText("Auto Enlarge")
		self.__box7.setSelected(True)

		self.__box8=swing.JCheckBox(actionPerformed=self.__boxaction8)
		self.__box8.setText("Measures")
		self.__box8.setSelected(True)
		
		self.__box9=swing.JCheckBox(actionPerformed=self.__boxaction9)
		self.__box9.setText("Auto Align Center")
		self.__box9.setSelected(False)
		
		self.__box10=swing.JCheckBox(actionPerformed=self.__boxaction10)
		self.__box10.setText("Use ellipses")
		self.__box10.setSelected(False)
		
		checkpanel.add(self.__box0)
		checkpanel.add(self.__box1)
		checkpanel.add(self.__box2)
		checkpanel.add(self.__box3)
		checkpanel.add(self.__box4)
		checkpanel.add(self.__box5)
		checkpanel.add(self.__box6)
		checkpanel.add(self.__box7)
		checkpanel.add(self.__box8)
		checkpanel.add(self.__box9)
		checkpanel.add(self.__box10)
		
		grid = awt.GridLayout()
		grid.setRows(10)
		checkpanel2=swing.JPanel(grid)
		checkpanel2.setBorder(line)

		label=swing.JLabel("Label7")
		label.setText("Max of Solidity")
		checkpanel2.add(label)
		self.__display7 = swing.JTextField(preferredSize=(50, 30), horizontalAlignment=swing.SwingConstants.LEFT)
		self.__display7.text = "1"
		checkpanel2.add(self.__display7)

		label=swing.JLabel("Label8")
		label.setText("Min of Solidity")
		checkpanel2.add(label)
		self.__display8 = swing.JTextField(preferredSize=(50, 30), horizontalAlignment=swing.SwingConstants.LEFT)
		self.__display8.text = "0"
		checkpanel2.add(self.__display8)

		label=swing.JLabel("Label9")
		label.setText("Max of Area")
		checkpanel2.add(label)
		self.__display9 = swing.JTextField(preferredSize=(50, 30), horizontalAlignment=swing.SwingConstants.LEFT)
		self.__display9.text = "1447680"
		checkpanel2.add(self.__display9)

		label=swing.JLabel("Label10")
		label.setText("Min of Area")
		checkpanel2.add(label)
		self.__display10 = swing.JTextField(preferredSize=(50, 30), horizontalAlignment=swing.SwingConstants.LEFT)
		self.__display10.text = "1"
		checkpanel2.add(self.__display10)

		label=swing.JLabel("Label11")
		label.setText("Max of Circ")
		checkpanel2.add(label)
		self.__display11 = swing.JTextField(preferredSize=(50, 30), horizontalAlignment=swing.SwingConstants.LEFT)
		self.__display11.text = "1"
		checkpanel2.add(self.__display11)

		label=swing.JLabel("Label12")
		label.setText("Min of Circ")
		checkpanel2.add(label)
		self.__display12 = swing.JTextField(preferredSize=(50, 30), horizontalAlignment=swing.SwingConstants.LEFT)
		self.__display12.text = "0"
		checkpanel2.add(self.__display12)

		label=swing.JLabel("Label13")
		label.setText("Max of AR")
		checkpanel2.add(label)
		self.__display13 = swing.JTextField(preferredSize=(50, 30), horizontalAlignment=swing.SwingConstants.LEFT)
		self.__display13.text = "1392"
		checkpanel2.add(self.__display13)

		label=swing.JLabel("Label14")
		label.setText("Min of AR")
		checkpanel2.add(label)
		self.__display14 = swing.JTextField(preferredSize=(50, 30), horizontalAlignment=swing.SwingConstants.LEFT)
		self.__display14.text = "1"
		checkpanel2.add(self.__display14)

		label=swing.JLabel("Label15")
		label.setText("Max of Feret")
		checkpanel2.add(label)
		self.__display15 = swing.JTextField(preferredSize=(50, 30), horizontalAlignment=swing.SwingConstants.LEFT)
		self.__display15.text = "1392"
		checkpanel2.add(self.__display15)

		label=swing.JLabel("Label16")
		label.setText("Min of Feret")
		checkpanel2.add(label)
		self.__display16 = swing.JTextField(preferredSize=(50, 30), horizontalAlignment=swing.SwingConstants.LEFT)
		self.__display16.text = "1"
		checkpanel2.add(self.__display16)

		label=swing.JLabel("Label17")
		label.setText("Max of Mean")
		checkpanel2.add(label)
		self.__display17 = swing.JTextField(preferredSize=(50, 30), horizontalAlignment=swing.SwingConstants.LEFT)
		self.__display17.text = "65535"
		checkpanel2.add(self.__display17)

		label=swing.JLabel("Label18")
		label.setText("Min of Mean")
		checkpanel2.add(label)
		self.__display18 = swing.JTextField(preferredSize=(50, 30), horizontalAlignment=swing.SwingConstants.LEFT)
		self.__display18.text = "0"
		checkpanel2.add(self.__display18)

		label=swing.JLabel("Label19")
		label.setText("max ratio Axis/Feret")
		checkpanel2.add(label)
		self.__display19 = swing.JTextField(preferredSize=(50, 30), horizontalAlignment=swing.SwingConstants.LEFT)
		self.__display19.text = str(self.__maxraf)
		checkpanel2.add(self.__display19)

		label=swing.JLabel("Label20")
		label.setText("Min ratio Axis/Feret")
		checkpanel2.add(label)
		self.__display20 = swing.JTextField(preferredSize=(50, 30), horizontalAlignment=swing.SwingConstants.LEFT)
		self.__display20.text = str(self.__minraf)
		checkpanel2.add(self.__display20)

		label=swing.JLabel("Label21")
		label.setText("Max MinFeret")
		checkpanel2.add(label)
		self.__display21 = swing.JTextField(preferredSize=(50, 30), horizontalAlignment=swing.SwingConstants.LEFT)
		self.__display21.text = "1392"
		checkpanel2.add(self.__display21)

		label=swing.JLabel("Label22")
		label.setText("Min MinFeret")
		checkpanel2.add(label)
		self.__display22 = swing.JTextField(preferredSize=(50, 30), horizontalAlignment=swing.SwingConstants.LEFT)
		self.__display22.text = "1"
		checkpanel2.add(self.__display22)
		
		
		self.contentPane.add(northpanel1, awt.BorderLayout.NORTH)
		self.contentPane.add(checkpanel, awt.BorderLayout.WEST)
		self.contentPane.add(northpanel2, awt.BorderLayout.CENTER)
		self.contentPane.add(southpanel, awt.BorderLayout.SOUTH)
		self.contentPane.add(checkpanel2, awt.BorderLayout.EAST)


	def __close(self, event):
		self.oked = True
		time.sleep(0.01) 
		self.dispose()

	def __new(self, event): 
		self.__init = True
		self.__n += 1
		self.__name = "stackcells"+str(self.__n)
		self.__display.text = self.__name
		self.__sens[:] = []
		self.__listrois[:] = []
		self.__iplist[:] = []
		self.__cellsrois[:] = []
		self.__labels[:] = []

	def __add(self, event): 
		if ( not self.__init) : 
			IJ.showMessage("", "please start a new stack")
			return
		if ( not self.__initDIA) :
			IJ.showMessage("", "please select an image for DIA")
			return

		if ( not self.__initFLUO) :
			IJ.showMessage("", "please select an image for FLUO")
			return
		
		self.__widthl = self.__display2.getText()
		roi = self.__impD.getRoi()
		
		if roi == None : 
			IJ.showMessage("", "No selection")
			return

		if roi.getType() in [6,7] : 		
			nslice = self.__impD.getCurrentSlice()
			self.__impF.setSlice(nslice)
			self.__impF.setRoi(roi)
		elif roi.getType() in [2,4] :
			nslice = self.__impD.getCurrentSlice()
			self.__impF.setSlice(nslice)
			m=Morph(self.__impF, roi)
			m.setMidParams(10, 2)
			roi=m.MidAxis
			if roi == None :
				self.__display.text = "roi fail"
				if not self.__skip : IJ.showMessage("", "failed roi, please draw it as polyline")
				return				

		#if roi.getType() != 6 : self.__impF.setRoi(roi)
		else : 
			IJ.showMessage("", "This selection is not yet allowed")
			return

		self.__impF.setRoi(roi)
		
		straightener = Straightener()
		new_ip = straightener.straighten(self.__impF, roi, int(self.__widthl))
		
		self.__iplist.append(new_ip)
		self.__labels.append(self.__isF.getShortSliceLabel(nslice))
		
		self.__display.text = self.__name + " cell " + str(len(self.__iplist)) +" width="+str(new_ip.getWidth())+ " height="+ str(new_ip.getHeight())
		roi.setPosition(self.__impD.getCurrentSlice())	

		self.__rm = RoiManager.getInstance()
		if (self.__rm==None): self.__rm = RoiManager()
		
		self.__rm.add(self.__impD, roi, len(self.__iplist))
		self.__cellsrois.append((roi, self.__impD.getCurrentSlice()))
		#self.__rm.runCommand("Show All")

		IJ.selectWindow(self.__impD.getTitle()) 
		
		
	def __end(self, event): 
		if len(self.__iplist)==0 : 
			IJ.showMessage("", "Stack is empty")
			return
		self.__ipw=[ ip.getWidth() for ip in self.__iplist ]
		self.__iph=[ ip.getHeight() for ip in self.__iplist ]
		maxw=max(self.__ipw)
		maxh=max(self.__iph)
		if self.__enlarge : 
			resizelist = [ ip.resize(maxw, maxh, True) for ip in self.__iplist ]
			
		else : 
			resizelist = []
			for ip in self.__iplist :
				tempip = ShortProcessor(maxw, maxh)
				tempip.copyBits(ip, 0, 0, Blitter.COPY)
				resizelist.append(tempip)
				
		ims = ImageStack(maxw, maxh) 	
		
		
		#for ip in resizelist : ims.addSlice("", ip)
		for i in range(len(resizelist)) : 
			ims.addSlice(self.__labels[i], resizelist[i])
		
		
		self.__impRes = ImagePlus(self.__name, ims)
		self.__impRes.show()

		self.__sens = [1 for i in range(len(self.__iplist)) ]
		
		if self.__appmedian : IJ.run(self.__impRes, "Median...", "radius=1 stack")
		
		if self.__align : self.__falign()
		if self.__avg : self.__favg()
		if self.__mosa : self.__fmosa()
		if self.__maxfinder : self.__fmaxfinder()
		if self.__fire : IJ.run(self.__impRes, "Fire", "")
		if self.__measures : self.__fmeasures()
		
		self.__sens[:] = []
		self.__listrois[:] = []
		self.__iplist[:] = []
		self.__cellsrois[:] = []
		self.__ipw[:] = []
		self.__iph[:] = []

		self.__init = False
		
	def __dia(self, event): 
		IJ.run("Set Scale...", "distance=0 known=0 pixel=1 unit=pixel")
		#IJ.run("Properties...", "channels=1 slices=1 frames=20 unit=pixel pixel_width=1.0000 pixel_height=1.0000 voxel_depth=1.0000 frame=[1 sec] origin=0,0");
		self.__impD = IJ.getImage()
		self.__isD = self.__impD.getImageStack()
		self.__display.text = "DIA="+self.__impD.getTitle()
		self.__initDIA = True

	def __fluo(self, event): 
		IJ.run("Set Scale...", "distance=0 known=0 pixel=1 unit=pixel")
		self.__impF = IJ.getImage()
		self.__isF = self.__impF.getImageStack()
		self.__display.text = "FLUO="+self.__impF.getTitle()
		self.__initFLUO = True

	def __addroi(self, event) :
		if ( not self.__init) : 
			IJ.showMessage("", "please start a new stack")
			return
		if ( not self.__initDIA) :
			IJ.showMessage("", "please select an image for DIA")
			return

		if ( not self.__initFLUO) :
			IJ.showMessage("", "please select an image for FLUO")
			return

		twres = TextWindow("measures-"+self.__name, "label\tname\tsol\tarea\tcirc\tAR\tFeret\taxis\traf\tdMajor\tdFeret\tdArea", "", 300, 450)
		tab="\t"
		
		self.__widthl = self.__display2.getText()
		IJ.selectWindow(self.__impF.getTitle())

		self.__rm = RoiManager.getInstance()
		if (self.__rm==None): self.__rm = RoiManager()

		if self.__impF.getImageStackSize() > 1 :
			roisarray =[(roi, self.__rm.getSliceNumber(roi.getName())) for roi in self.__rm.getRoisAsArray()]
		else : 
			roisarray =[(roi, 1) for roi in self.__rm.getRoisAsArray()]
			
		self.__rm.runCommand("reset")
		#self.__rm.runCommand("Delete")
		IJ.selectWindow(self.__impF.getTitle())

		self.__maxraf=float(self.__display19.text)
		self.__minraf=float(self.__display20.text)

		count=1

		for roielement in roisarray :
			roi = roielement[0]
			pos = roielement[1]
			lab = self.__impF.getImageStack().getShortSliceLabel(pos)

			if lab==None : lab=str(pos)
			
			if self.__conEllipses :
				IJ.selectWindow(self.__impF.getTitle())
				self.__impF.setRoi(roielement)
				IJ.run(self.__impF,  "Fit Ellipse", "")
				ellipse=imp.getRoi()
				params = ellipse.getParams()
				ferets = ellipse.getFeretValues()
				imp2 = Duplicator().run(self.__impF,pos,pos)
				IJ.run(imp2, "Rotate... ", "angle="+str(ferets[1])+" grid=0 interpolation=Bilinear enlarge slice")
				temproi=Roi((imp2.getWidth()-ferets[0])/2.0,(imp2.getHeight()-ferets[2])/2.0,ferets[0],ferets[2])
				imp2.setRoi(temproi)
				imp3 = Duplicator().run(imp2,1,1)
				ip3=imp3.getProcessor()
				
					if int(self.__display5.text) < ip3.getWidth() < int(self.__display6.text) : 
						self.__iplist.append(ip3)
						self.__display.text = self.__name + " cell " + str(len(self.__iplist))
						fer=Line(params[0],params[1],params[3],params[4])
						self.__cellsrois.append((ellipse, pos))
						self.__labels.append(self.__isF.getShortSliceLabel(pos))
				continue
			
			if roi.getType() in [6,7] : 
				self.__impF.setSlice(pos)
				self.__impF.setRoi(roi)
				self.__rm.runCommand("Add")

			elif roi.getType() in [2,4] :
				self.__impF.setSlice(pos)
				self.__impF.setRoi(roi)
				m=Morph(self.__impF, roi)
				m.setMidParams(10, 2)
				midroi=m.MidAxis
				if midroi == None : continue

				raf = m.MaxFeret/midroi.getLength()
				
				if (self.__maxraf < raf) or (raf < self.__minraf) : continue

				maxsol = float(self.__display7.text)
				minsol = float(self.__display8.text)
				maxarea = float(self.__display9.text)
				minarea = float(self.__display10.text)
				maxcirc = float(self.__display11.text)
				mincirc = float(self.__display12.text)
				maxar = float(self.__display13.text)
				minar = float(self.__display14.text)
				maxfer = float(self.__display15.text)
				minfer = float(self.__display16.text)
				maxmean = float(self.__display17.text)
				minmean = float(self.__display18.text)
				maxmferet = float(self.__display21.text)
				minmferet = float(self.__display22.text)

				testsol = (minsol< m.Solidity < maxsol)
				testarea = (minarea< m.Area < maxarea)
				testcirc = (mincirc< m.Circ < maxcirc)
				testar = (minar< m.AR < maxar)
				testfer = (minfer< m.MaxFeret < maxfer)
				testmean = (minmean < m.Mean < maxmean)
				testmferet = (minmferet < m.MinFeret < maxmferet)
				
				#print minmferet , m.MinFeret , maxmferet

				test = (testsol+testarea+testcirc+testar+testfer+testmean+testmferet)/7	

				if test : 				
					
					fmaj, ffmx, fa =[],[],[]
					for r in m.getMidSegments(10, 40, 0) :
						if r == None : continue
						m2=Morph(self.__impF, r)
						fmaj.append(m2.Major)
						ffmx.append(m2.MaxFeret)
						fa.append(m2.Area)

					diffmajor, diffferet, diffarea = 0,0,0
					
					if len(fa) > 4 :
						medfmaj = self.listmean(fmaj[1:-1])
						medffmx = self.listmean(ffmx[1:-1])
						medfa   = self.listmean(fa[1:-1])

						diffmajor = (max(fmaj[1:-1])-medfmaj)/medfmaj
						diffferet = (max(ffmx[1:-1])-medffmx)/medffmx
						diffarea = (max(fa[1:-1])-medfa)/medfa

					twres.append(lab+tab+str(roi.getName())+tab+str(m.Solidity)+tab+str(m.Area)+tab+str(m.Circ)+tab+str(m.AR)+tab+str(m.MaxFeret)+tab+str(midroi.getLength())+tab+str(m.MaxFeret/midroi.getLength())+tab+str(diffmajor)+tab+str(diffferet)+tab+str(diffarea))
					#print lab+tab+str(roi.getName())+tab+str(m.Solidity)+tab+str(m.Area)+tab+str(m.Circ)+tab+str(m.AR)+tab+str(m.MaxFeret)+tab+str(midroi.getLength())+tab+str(m.MaxFeret/midroi.getLength())+tab+str(diffmajor)+tab+str(diffferet)+tab+str(diffarea)

					self.__impF.setRoi(roi)
					self.__rm.runCommand("Add")
					self.__impF.killRoi()
					self.__impF.setRoi(midroi)
					
					#self.__dictCells[str(roi.getName())]=(str(roi.getName()), lab, roi)
					self.__dictCells[count]=(str(roi.getName()), lab, roi)
					count=count+1
					
				else : 
					#print "test falls"
					continue

			else : 
				#print "wrong type"
				continue
			
			straightener = Straightener()
			new_ip = straightener.straighten(self.__impF, midroi, int(self.__widthl))
			
			if int(self.__display5.text) < new_ip.getWidth() < int(self.__display6.text) : 
				self.__iplist.append(new_ip)
				self.__display.text = self.__name + " cell " + str(len(self.__iplist))
				#print "add", roi.getName(), roi.getType()
				self.__cellsrois.append((midroi, pos))
				self.__labels.append(self.__isF.getShortSliceLabel(pos))


		#roisarray=self.__rm.getRoisAsArray()		
		#self.__rm.runCommand("reset")
		#self.__rm.runCommand("Delete")
		

		self.__impD.killRoi()
		self.__impF.killRoi()
		IJ.selectWindow(self.__impD.getTitle()) 

	def __boxaction0(self, event):
		self.__skip = event.getSource().isSelected()
		
	def __boxaction1(self, event):
		self.__mosa = event.getSource().isSelected()
		#self.__setDisplay(str(event.getSource().text)+" is "+str(event.getSource().isSelected()))
		
	def __boxaction2(self, event):
		self.__avg = event.getSource().isSelected()
		#self.__setDisplay(str(event.getSource().text)+" is "+str(event.getSource().isSelected()))

	def __boxaction3(self, event):
		self.__maxfinder = event.getSource().isSelected()
		#self.__setDisplay(str(event.getSource().text)+" is "+str(event.getSource().isSelected()))

	def __boxaction4(self, event):
		self.__appmedian = event.getSource().isSelected()
		#self.__setDisplay(str(event.getSource().text)+" is "+str(event.getSource().isSelected()))

	def __boxaction5(self, event):
		self.__fire = event.getSource().isSelected()
		#self.__setDisplay(str(event.getSource().text)+" is "+str(event.getSource().isSelected()))

	def __boxaction6(self, event):
		self.__align = event.getSource().isSelected()
		#self.__setDisplay(str(event.getSource().text)+" is "+str(event.getSource().isSelected()))

	def __boxaction7(self, event):
		self.__enlarge = event.getSource().isSelected()
		#self.__setDisplay(str(event.getSource().text)+" is "+str(event.getSource().isSelected()))

	def __boxaction8(self, event):
		self.__measures = event.getSource().isSelected()
		#self.__setDisplay(str(event.getSource().text)+" is "+str(event.getSource().isSelected()))

	def __boxaction9(self, event):
		self.__alignC = event.getSource().isSelected()
		#self.__setDisplay(str(event.getSource().text)+" is "+str(event.getSource().isSelected()))
	
	def __boxaction10(self, event):
		self.__conEllipses = event.getSource().isSelected()
	
	def __favg(self) :
		zp = ZProjector(self.__impRes) 
		zp.setMethod(ZProjector.AVG_METHOD)
		zp.doProjection() 
		imp = zp.getProjection()
		imp.show()
		if self.__fire : IJ.run(imp, "Fire", "")

	def __fmosa(self) :
		mm = MontageMaker()
		imp = mm.makeMontage2(self.__impRes, 1, self.__impRes.getStackSize(), 1, 1, self.__impRes.getStackSize(), 1, 0, False)
		imp.setTitle("MONTAGE"+self.__name)
		imp.show()
		if self.__fire : IJ.run(imp, "Fire", "")

	def __fmaxfinder(self) :
		#stack = self.__impRes.getStack()
		self.__impD.killRoi()
		self.__impF.killRoi()
		stack = self.__impF.getStack()
		n_slices = stack.getSize()
		#newstack=ImageStack(self.__impRes.getWidth(), self.__impRes.getHeight())
		newstack=ImageStack(self.__impF.getWidth(), self.__impF.getHeight())
		noise = self.__display3.text
		for index in range(1,n_slices+1):
			IJ.selectWindow(self.__impF.getTitle())
			self.__impF.setSlice(index)
			ip = self.__impF.getProcessor()
			mf=MaximumFinder()
			ipmax = mf.findMaxima(ip, int(noise), 0, 0, False, False)
			newstack.addSlice("", ipmax)
			

		newimage=ImagePlus("max points"+self.__name, newstack)
		newimage.show()
		newimage.updateAndDraw()
		
		listip = []
		for roi in self.__cellsrois : 
			straightener = Straightener()
			newimage.setSlice(roi[1])
			newimage.setRoi(roi[0])
			listip.append(straightener.straighten(newimage, roi[0], int(self.__widthl)))
		
		ipw=[ ip.getWidth() for ip in listip ]
		iph=[ ip.getHeight() for ip in listip ]
		maxw=max(ipw)
		maxh=max(iph)
		
		if self.__enlarge : resizelist = [ ip.resize(maxw, maxh, True) for ip in listip ]
		
		elif  self.__alignC : 
			resizelist = []
			for ip in listip :
				tempip = ByteProcessor(maxw, maxh)
				tempip.copyBits(ip, 0, 0, Blitter.COPY)
				resizelist.append(tempip)

		else :
			resizelist = []
			for ip in listip :
				tempip = ByteProcessor(maxw, maxh)
				tempip.copyBits(ip, 0, 0, Blitter.COPY)
				resizelist.append(tempip)
				
		ims = ImageStack(maxw, maxh) 	
		
		#for ip in resizelist : ims.addSlice("", ip)
		for i in range(len(resizelist)) : 
			ims.addSlice(self.__labels[i], resizelist[i])
		
		self.__impMax = ImagePlus(self.__name+"-max", ims)
		self.__impMax.show()
		stack = self.__impMax.getStack() # get the stack within the ImagePlus
		n_slices = stack.getSize()
		
		for index in range(1, n_slices+1):
			self.__impMax.killRoi()	
			self.__impMax.setSlice(index)
			roi = self.__listrois[index-1]
			
			if self.__sens[index-1]<0 : 
				self.__impMax.setRoi(roi)
				ip1 = self.__impMax.getProcessor()
				ip1.flipHorizontal()
				self.__impMax.killRoi()
				self.__impMax.updateAndDraw()

			ip = self.__impMax.getProcessor()
			for i in range(ip.getWidth()*ip.getHeight()) :
				if ip.getf(i) > 0 : ip.setf(i, 255)
				#else : ip.setf(i, 0)

		IJ.run(self.__impMax, "8-bit", "")
		IJ.run(self.__impMax, "Options...", "iterations=2 count=1 black edm=Overwrite do=Close stack")
		IJ.run(self.__impMax, "Ultimate Points", "stack")
		
		self.__impMax.updateAndDraw()
		


	def __falign(self) :
		
		#self.__impRes=IJ.getImage()
		stack = self.__impRes.getStack() # get the stack within the ImagePlus
		n_slices = stack.getSize() # get the number of slices
		ic = ImageCalculator()
		w = self.__impRes.getWidth()
		h = self.__impRes.getHeight()
		self.__sens[:] = []
		self.__listrois[:] = []

		
		
		for index in range(1, n_slices+1):	
			
			self.__impRes.setSlice(index)
			ip1 = stack.getProcessor(index)
			imp1 = ImagePlus("imp1-"+str(index), ip1)
			imp1sqr = ic.run("Multiply create 32-bit", imp1, imp1)			

			IJ.setThreshold(imp1sqr, 1, 4294836225)
			IJ.run(imp1sqr, "Create Selection", "")
			roi = imp1sqr.getRoi()
			rect=roi.getBounds()
			roi = Roi(rect)
			self.__listrois.append(roi)
			ipsqr = imp1sqr.getProcessor()
			is1 = ipsqr.getStatistics()
			self.__impRes.killRoi()

			
			
			if is1.xCenterOfMass > w/2.00 : 
				self.__impRes.setRoi(roi)
				ip1 = self.__impRes.getProcessor()
				ip1.flipHorizontal()
				self.__impRes.killRoi()
				self.__sens.append(-1)
			else : self.__sens.append(1)
				
			self.__impRes.updateAndDraw()

			
	def __fmeasures(self) : 
		self.__Cutoff = float(self.__display4.text)
		nslices = self.__impRes.getImageStackSize() 
		rt = ResultsTable()
		rt.show("RT-"+self.__name)
		twpoints = TextWindow("points-"+self.__name, "index\tlabel\tname\tx\ty\taxis\tcellw\tcellh", "", 200, 450)
		twlabels = TextWindow("labels-"+self.__name, "index\tlabel\tname\tnpoints", "", 200, 450)

		isres = self.__impRes.getImageStack()
		
		for index in range(1, nslices+1):	
			self.__impRes.setSlice(index)
			self.__impRes.killRoi()
			roi = self.__listrois[index-1]
			self.__impRes.setRoi(roi)
			analyser= Analyzer(self.__impRes, Analyzer.LABELS+Analyzer.CENTER_OF_MASS+Analyzer.CENTROID+Analyzer.INTEGRATED_DENSITY+Analyzer.MEAN+Analyzer.KURTOSIS+Analyzer.SKEWNESS+Analyzer.MIN_MAX+Analyzer.SLICE+Analyzer.STACK_POSITION+Analyzer.STD_DEV, rt)
			analyser.measure()
			rt.show("RT-"+self.__name)
			
			rect=roi.getBounds()
			ip = self.__impRes.getProcessor()

			xCoord = []
			yCoord = []
			currentPixel = []

			m00 = 0.00
			m10 = 0.00
			m01 = 0.00
			
			mc20 = 0.00
			mc02 = 0.00
			mc11 = 0.00
			mc30 = 0.00
			mc03 = 0.00
			mc21 = 0.00
			mc12 = 0.00
			mc40 = 0.00
			mc04 = 0.00
			mc31 = 0.00
			mc13 = 0.00

			mm20 = 0.00
			mm02 = 0.00
			mm11 = 0.00
			mm30 = 0.00
			mm03 = 0.00
			mm21 = 0.00
			mm12 = 0.00
			mm40 = 0.00
			mm04 = 0.00
			mm31 = 0.00
			mm13 = 0.00
			
			
			for y in range(rect.y, rect.y+rect.height, 1) :
				for x in range(rect.x, rect.x+rect.width, 1) :
					xCoord.append(x+0.5)
					yCoord.append(y+0.5)
					#pixel=ip.getf(x,y)-self.__Cutoff
					pixel = ip.getPixelValue(x,y)-self.__Cutoff
					if pixel < 0 : pixel = 0
					currentPixel.append(pixel)
					m00 += currentPixel[-1]
					m10 += currentPixel[-1]*xCoord[-1]
					m01 += currentPixel[-1]*yCoord[-1]


			xm = m10/(m00+0.00000001)
			ym = m01/(m00+0.00000001)

			xc = rect.width/2.00
			yc = rect.height/2.00

			for i in range(rect.width*rect.height) :

				xcrel = xCoord[i]-xc
				ycrel = yCoord[i]-yc
			
				#mc20 += currentPixel[i]*(xCoord[i]-xc)*(xCoord[i]-xc)
				#mc02 += currentPixel[i]*(yCoord[i]-yc)*(yCoord[i]-yc)
				#mc11 += currentPixel[i]*(xCoord[i]-xc)*(yCoord[i]-yc)
				#
				#mc30 += currentPixel[i]*(xCoord[i]-xc)*(xCoord[i]-xc)*(xCoord[i]-xc)
				#mc03 += currentPixel[i]*(yCoord[i]-yc)*(yCoord[i]-yc)*(yCoord[i]-yc)
				#mc21 += currentPixel[i]*(xCoord[i]-xc)*(xCoord[i]-xc)*(yCoord[i]-yc)
				#mc12 += currentPixel[i]*(xCoord[i]-xc)*(yCoord[i]-yc)*(yCoord[i]-yc)
				#
				#mc40 += currentPixel[i]*(xCoord[i]-xc)*(xCoord[i]-xc)*(xCoord[i]-xc)*(xCoord[i]-xc)
				#mc04 += currentPixel[i]*(yCoord[i]-yc)*(yCoord[i]-yc)*(yCoord[i]-yc)*(yCoord[i]-yc)
				#mc31 += currentPixel[i]*(xCoord[i]-xc)*(xCoord[i]-xc)*(xCoord[i]-xc)*(yCoord[i]-yc)
				#mc13 += currentPixel[i]*(xCoord[i]-xc)*(yCoord[i]-yc)*(yCoord[i]-yc)*(yCoord[i]-yc)

				mc20 += currentPixel[i]*xcrel*xcrel
				mc02 += currentPixel[i]*ycrel*ycrel
				mc11 += currentPixel[i]*xcrel*ycrel
				
				mc30 += currentPixel[i]*xcrel*xcrel*xcrel
				mc03 += currentPixel[i]*ycrel*ycrel*ycrel
				mc21 += currentPixel[i]*xcrel*xcrel*ycrel
				mc12 += currentPixel[i]*xcrel*ycrel*ycrel
				
				mc40 += currentPixel[i]*xcrel*xcrel*xcrel*xcrel
				mc04 += currentPixel[i]*ycrel*ycrel*ycrel*ycrel
				mc31 += currentPixel[i]*xcrel*xcrel*xcrel*ycrel
				mc13 += currentPixel[i]*xcrel*ycrel*ycrel*ycrel

			
			for i in range(rect.width*rect.height) :
				mm20 += currentPixel[i]*(xCoord[i]-xm)*(xCoord[i]-xm)
				mm02 += currentPixel[i]*(yCoord[i]-ym)*(yCoord[i]-ym)
				mm11 += currentPixel[i]*(xCoord[i]-xm)*(yCoord[i]-ym)

				mm30 += currentPixel[i]*(xCoord[i]-xm)*(xCoord[i]-xm)*(xCoord[i]-xm)
				mm03 += currentPixel[i]*(yCoord[i]-ym)*(yCoord[i]-ym)*(yCoord[i]-ym)
				mm21 += currentPixel[i]*(xCoord[i]-xm)*(xCoord[i]-xm)*(yCoord[i]-ym)
				mm12 += currentPixel[i]*(xCoord[i]-xm)*(yCoord[i]-ym)*(yCoord[i]-ym)

				mm40 += currentPixel[i]*(xCoord[i]-xm)*(xCoord[i]-xm)*(xCoord[i]-xm)*(xCoord[i]-xm)
				mm04 += currentPixel[i]*(yCoord[i]-ym)*(yCoord[i]-ym)*(yCoord[i]-ym)*(yCoord[i]-ym)
				mm31 += currentPixel[i]*(xCoord[i]-xm)*(xCoord[i]-xm)*(xCoord[i]-xm)*(yCoord[i]-ym)
				mm13 += currentPixel[i]*(xCoord[i]-xm)*(yCoord[i]-ym)*(yCoord[i]-ym)*(yCoord[i]-ym)

			
			
			xxcVar = mc20/m00
			yycVar = mc02/m00
			xycVar = mc11/m00

			xcSkew = mc30/(m00 * math.pow(xxcVar,(3.0/2.0)))
			ycSkew = mc03/(m00 * math.pow(yycVar,(3.0/2.0)))

			xcKurt = mc40 / (m00 * math.pow(xxcVar,2.0)) - 3.0
			ycKurt = mc04 / (m00 * math.pow(yycVar,2.0)) - 3.0

			ecc = (math.pow((mc20-mc02),2.0)+(4.0*mc11*mc11))/m00
			
			xxmVar = mm20/m00
			yymVar = mm02/m00
			xymVar = mm11/m00

			xmSkew = mm30/(m00 * math.pow(xxmVar,(3.0/2.0)))
			ymSkew = mm03/(m00 * math.pow(yymVar,(3.0/2.0)))

			xmKurt = mm40 / (m00 * math.pow(xxmVar,2.0)) - 3.0
			ymKurt = mm04 / (m00 * math.pow(yymVar,2.0)) - 3.0

			ecm = (math.pow((mm20-mm02),2.0)+(4.0*mm11*mm11))/m00

			rt.addValue("xxcVar", xxcVar)
			rt.addValue("yycVar", yycVar)
			rt.addValue("xycVar", xycVar)

			rt.addValue("xcSkew", xcSkew)
			rt.addValue("ycSkew", ycSkew)

			rt.addValue("xcKurt", xcKurt)
			rt.addValue("ycKurt", ycKurt)

			rt.addValue("Ecc", ecc)

			rt.addValue("xxmVar", xxmVar)
			rt.addValue("yymVar", yymVar)
			rt.addValue("xymVar", xymVar)

			rt.addValue("xmSkew", xmSkew)
			rt.addValue("ymSkew", ymSkew)

			rt.addValue("xmKurt", xmKurt)
			rt.addValue("ymKurt", ymKurt)

			rt.addValue("Ecm", ecm)

			rt.addValue("roiw", rect.width)
			rt.addValue("roih", rect.height)

			rt.addValue("cellw", self.__ipw[index-1])
			rt.addValue("cellh", self.__iph[index-1])

			self.__impRes.killRoi()

			xCoord[:] = []
			yCoord[:] = []
			currentPixel[:] = []
			points = []
			points[:] = []
			npointsmax = 0
			
			#lab = self.__labels[index-1]
			nameroi = self.__dictCells[index][0]
			lab = self.__dictCells[index][1]
			
			self.__impMax.setSlice(index)
			ipmax = self.__impMax.getProcessor()
			for y in range(ipmax.getHeight()) :
				for x in range(ipmax.getWidth()) :
					if ipmax.getPixelValue(x,y) > 0 : 
						twpoints.append(str(index)+"\t"+lab+"\t"+nameroi+"\t"+str(x)+"\t"+str(y)+"\t"+str(self.__cellsrois[index-1][0].getLength())+"\t"+str(self.__ipw[index-1])+"\t"+str(self.__iph[index-1]))
						npointsmax+=1
			rt.addValue("npoints", npointsmax)

			twlabels.append(str(index)+"\t"+lab+"\t"+nameroi+"\t"+str(npointsmax))
			rt.show("RT-"+self.__name)
			
		rt.show("RT-"+self.__name)
		
	
	def __setDisplay(self, val=""): 
		self.__display.text = str(val)

	def setLabel(self, text):
		self.__label.setText(text)

	def listmean(self, l) : return float(sum(l)/len(l))

	def listmedian(self, l) :
		s=l[:]
		s.sort()
		w=len(l)
		return float(s[(w-1)/2]) if (w%2 == 1) else float((s[w/2]+s[(w/2)-1]))/2

	def __help(self, event):
		IJ.log(""" 

		--------------------------------------------------------------------------------------
		New = Starts a new process with stacked cells
		Add = Adds un ROI as a new cell in the stack (poly segments line or a closed area ROI)
		Add Roi manager = adds all the ROIs contained in the roi manager
		End = Stops the stack process and generates images and results
		--------------------------------------------------------------------------------------

		--------------------------------------------------------------------------------------
		Line width = width of the cells in pixels.
		Noise for peaks =  value passed to detect peaks function
		Fluo threshold = value of the background in the fluo image. Used for acurated calculus of moments.
		Min length = filter for small short cells
		Max length = filter for long cells
		--------------------------------------------------------------------------------------
		
		--------------------------------------------------------------------------------------
		DIA = Select the image and click to set the source image for cells ROI
		FLUO = Select the image and click to set the image containig the fluorescence signal
		(if Add Roi manager selected, this is not take in to account)
		--------------------------------------------------------------------------------------

		--------------------------------------------------------------------------------------
		Skip failed ROIs = debug option
		Generate Mosaic = Generates a vertcal image with all the stacked cells
		Mean Projection = creates the projection of all cells by mean method
		Create maxFinder = uses the maxFinder function to generate peaks information
		Apply median = smooth the streched images by a 3x3 median filter
		Apply Fire LUT = shows all images with false colors (Fire LUT)
		Auto Align = Flip the cells to align the center of mass in the left part of the images
		Auto enlarge = Stretch the cell to fit the length of the longuest cell
		Generate measures =  creates a text windows with measures parameters.
		
		""")

# ------ end ---------------

if __name__ == "__main__":

	cs=StackCells()
	cs.show()
	cs.setLabel("")