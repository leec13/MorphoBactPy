
import javax.swing as swing
import java.awt as awt
from javax.swing import BorderFactory
from javax.swing.border import EtchedBorder, TitledBorder
from java.awt import Font




from ij import ImageStack, ImagePlus, WindowManager, IJ
from ij.gui import Roi, NonBlockingGenericDialog, Overlay, ImageRoi, Line, OvalRoi, PolygonRoi, ShapeRoi, TextRoi
from ij.process import ImageProcessor, ShortProcessor, ByteProcessor
from ij.plugin.frame import RoiManager
from ij.text import TextWindow
from ij.plugin import Straightener, Duplicator, ZProjector, MontageMaker, ImageCalculator
from ij.measure import ResultsTable

import sys
import os
import time
import glob
import os.path as path
import getpass
import shutil
import random

username=getpass.getuser()

#mypath=os.path.expanduser(IJ.getDirectory("plugins")+"MeasureCells")
mypath=os.path.expanduser(os.path.join("~","Dropbox","MacrosDropBox","py","MorphoBactProject"))
sys.path.append(mypath)

from org.python.core import codecs
codecs.setDefaultEncoding('utf-8')


class CellsSelection(swing.JFrame):
	def __init__(self): 
		swing.JFrame.__init__(self, title="Cells Selection")
		self.setFont(awt.Font("Courrier", 1, 10))
		self.__dictBox = {}
		self.__dictFiles = {}
		self.oked = False
		self.__mem=[]
		self.setDefaultCloseOperation(swing.JFrame.DISPOSE_ON_CLOSE) 
		
	def run(self, cells, path) :
		
		self.__cells=cells
		cells.sort()
		self.__cells.sort()
		self.__path=path
	
		if len(cells) <= 6 :
			cols=len(cells)
			rows=1
		else :
			cols=6
			rows=int(len(cells)/6)+1

		#print "cols", cols, "rows", rows
		self.setFont(awt.Font("Courrier", 1, 10))
		#self.size=(max(200*cols, 1100), max(70*rows, 300))
		self.size=(max(150*cols, 800), max(50*rows, 250))
		line = BorderFactory.createEtchedBorder(EtchedBorder.LOWERED)
			
		self.contentPane.layout = awt.BorderLayout()
		self.__display = swing.JTextField(preferredSize=(400, 30), horizontalAlignment=swing.SwingConstants.LEFT)
		self.__setDisplay()

		northpanel=swing.JPanel(awt.FlowLayout(awt.FlowLayout.LEFT))
		northpanel.setBorder(line)
		#northpanel.add(self.__display, awt.BorderLayout.NORTH)
		northpanel.add(self.__display)
		selectall = swing.JButton("select ALL", size=(100, 70), actionPerformed=self.__selectall)
		#northpanel.add(selectall, awt.BorderLayout.WEST)
		northpanel.add(selectall)
		selectnone = swing.JButton("select NONE", size=(100, 70), actionPerformed=self.__selectnone)
		#northpanel.add(selectnone, awt.BorderLayout.EAST)
		northpanel.add(selectnone)
		mem = swing.JButton("Memorize", size=(100, 70), actionPerformed= self.__memorize)
		northpanel.add(mem)
		recall = swing.JButton("Recall", size=(100, 70), actionPerformed=self.__recall)
		northpanel.add(recall)
		
		southpanel=swing.JPanel(awt.FlowLayout(awt.FlowLayout.RIGHT))
		southpanel.setBorder(line)
		self.__label=swing.JLabel("validate selection with ok")
		southpanel.add(self.__label)
		ok = swing.JButton("ok", size=(100, 70), actionPerformed=self.__ok)
		southpanel.add(ok)
		close = swing.JButton("close", size=(100, 70), actionPerformed=self.__close)
		southpanel.add(close)
		
		westpanel=swing.JPanel(awt.FlowLayout(awt.FlowLayout.CENTER), preferredSize=(150, 200))
		westpanel.setBorder(line)
		
		show = swing.JButton("show overlay", size=(100, 70), actionPerformed=self.__show)
		westpanel.add(show)
		hide = swing.JButton("hide overlay", size=(100, 70), actionPerformed=self.__hide)
		westpanel.add(hide)
		allframes = swing.JButton("show all", size=(100, 70), actionPerformed=self.__showall)
		westpanel.add(allframes)
		oneframe = swing.JButton("show one frame", size=(100, 70), actionPerformed=self.__showone)
		westpanel.add(oneframe)
		reset = swing.JButton("reset", size=(100, 70), actionPerformed=self.__reset)
		westpanel.add(reset)

		title = BorderFactory.createTitledBorder("Edit Cells")
		title.setTitleJustification(TitledBorder.CENTER)

		eastpanel = swing.JPanel(awt.FlowLayout(awt.FlowLayout.CENTER), preferredSize=(130, 200))
		eastpanel.setBorder(title)
		split = swing.JButton("split", size=(100, 70), actionPerformed=self.__split)
		eastpanel.add(split)
		
		grid = awt.GridLayout()
		grid.setRows(rows)
		checkpanel=swing.JPanel(grid)
		checkpanel.setFont(awt.Font("Courrier", 1, 10))
		self.__boxes=[swing.JCheckBox(actionPerformed=self.__boxaction) for i in range(len(cells))]
		for b in self.__boxes : b.setFont(awt.Font("Courrier", 1, 10))
		#self.__mem=[True for i in range(len(cells))]
		
		for i in range(len(self.__boxes)) : 
			self.__dictBox[cells[i]]=(cells[i], self.__boxes[i])
			
		for i in range(len(self.__boxes)) :
			self.__boxes[i].setText(str(cells[i]))
			self.__boxes[i].setSelected(True)
			checkpanel.add(self.__boxes[i])
		for i in range(rows*cols-len(self.__boxes)) : checkpanel.add(awt.Label(""))
		
		self.contentPane.add(northpanel, awt.BorderLayout.NORTH)
		self.contentPane.add(checkpanel, awt.BorderLayout.CENTER)
		self.contentPane.add(westpanel, awt.BorderLayout.WEST)
		self.contentPane.add(eastpanel, awt.BorderLayout.EAST)
		self.contentPane.add(southpanel, awt.BorderLayout.SOUTH)
		self.contentPane.setFont(awt.Font("Courrier", 1, 10))

		self.__rm = RoiManager.getInstance()
		if (self.__rm==None): self.__rm = RoiManager()
		self.__rm.runCommand("reset")
		
		listfilescells=[]
		listfilescells.extend(glob.glob(path+"*.zip"))


		#includecells = [filename for filename in listfilescells if filename.rsplit("/",1)[1][0:-4] in cells]
		includecells = [filename for filename in listfilescells if os.path.splitext(os.path.split(filename)[1])[0] in cells]
		
		for cell in includecells : 
			#c = cell.rsplit("/",1)[1][0:-4]
			c=os.path.splitext(os.path.split(cell)[1])[0]
			self.__dictFiles[c] = (c, cell)
		
		#for i in range(len(cells)) : 
		#	f=listfilescells[i].rsplit("/",1)[1][0:-4]
		#	#print "f=", f
		#	for c in cells :
		#		#print "c=", c, "f=", f
		#		if f==c :
		#			self.__dictFiles[c] = (c, listfilescells[i])
		#			#print "CS dictFiles", c, listfilescells[i]

	
	def __selectall(self, event): 
		for b in self.__boxes : b.setSelected(True)
		
	def __selectnone(self, event): 
		for b in self.__boxes : b.setSelected(False)

	def __ok(self, event): 
		self.oked = True
		#self.dispose()

	def __close(self, event):
		self.oked = True
		time.sleep(0.01) 
		self.dispose()

	def __memorize(self, event):
		self.__mem[:]=[]
		for i in range(len(self.__boxes)) : 
			if self.__boxes[i].isSelected() : 
				#print i, "mem", self.__boxes[i].text
				self.__mem.append(True)
			else : self.__mem.append(False)

	def __recall(self, event):
		for i in range(len(self.__boxes)) : 
			if self.__mem[i] : 
				self.__boxes[i].setSelected(True)
			else : self.__boxes[i].setSelected(False)

	def __show(self, event):
		IJ.run("Show Overlay", "")

	def __hide(self, event):
		IJ.run("Hide Overlay", "")

	def __showall(self, event) :
		self.__rm.runCommand("Associate", "false")
		self.__rm.runCommand("Show All")

	def __showone(self, event) : 
		self.__rm.runCommand("Associate", "true")
		self.__rm.runCommand("Show All")

	def __reset(self, event) : 
		self.__rm.runCommand("reset")
		
	def __boxaction(self, event):
		self.__setDisplay(str(event.getSource().text)+" is "+str(event.getSource().isSelected()))
		
		if event.getSource().isSelected() :  #print self.__dictFiles[event.getSource().text][1]
			#self.__rm.runCommand("reset")
			
			self.__rm.runCommand("Open", self.__dictFiles[event.getSource().text][1])
		
		
		
	def __setDisplay(self, val=""): 
		self.__display.text = str(val)

	def __split(self, event) : 
		sel = self.getSelected()
		if len(sel) != 1 : 
			IJ.showMessage("only one cell should be selected !")
			return
		else : 
			cellname = sel[0]
			rois = self.__rm.getRoisAsArray()
			self.__rm.runCommand("reset")
			n = int(IJ.getNumber("slice to split ?", 1))
			for i in range(n) : 
				self.__rm.addRoi(rois[i])
			#print self.__path+cellname+"-a.zip"
			self.__rm.runCommand("Save", self.__path+cellname+"-a.zip")
			self.__rm.runCommand("reset")
			for i in range(n, len(rois)) : 
				self.__rm.addRoi(rois[i])
			self.__rm.runCommand("Save", self.__path+cellname+"-b.zip")
			self.__rm.runCommand("reset")

		root = self.__path.rsplit(os.path.sep, 2)[0]+os.path.sep
		
		if not path.exists(root+"Cells"+os.path.sep) :os.makedirs(root+"Cells"+os.path.sep, mode=0777)

		fichiertemp = open(root+"Cells"+os.path.sep+cellname+"-a.cell","w")
		fichiertemp.write("NAMECELL="+cellname+"-a\n")
		fichiertemp.write("PATHCELL="+root+"Cells"+os.path.sep+cellname+"-a.cell\n")
		fichiertemp.write("PATHROIS="+root+"ROIs"+os.path.sep+cellname+"-a.zip\n")
		fichiertemp.write("NSLICES="+str(len(rois))+"\n")
		fichiertemp.write("SLICEINIT="+str(1)+"\n")
		fichiertemp.write("SLICEEND="+str(n)+"\n")
		r = random.randrange(5,205,1)
		g = random.randrange(10,210,1)
		b = random.randrange(30,230,1)
		fichiertemp.write("COLOR="+str(r)+";"+str(g)+";"+str(b)+"\n")
		fichiertemp.close()

		fichiertemp = open(root+"Cells"+os.path.sep+cellname+"-b.cell","w")
		fichiertemp.write("NAMECELL="+cellname+"-b\n")
		fichiertemp.write("PATHCELL="+root+"Cells"+os.path.sep+cellname+"-b.cell\n")
		fichiertemp.write("PATHROIS="+root+"ROIs"+os.path.sep+cellname+"-b.zip\n")
		fichiertemp.write("NSLICES="+str(len(rois))+"\n")
		fichiertemp.write("SLICEINIT="+str(n+1)+"\n")
		fichiertemp.write("SLICEEND="+str(len(rois))+"\n")
		r = random.randrange(5,205,1)
		g = random.randrange(10,210,1)
		b = random.randrange(30,230,1)
		fichiertemp.write("COLOR="+str(r)+";"+str(g)+";"+str(b)+"\n")
		fichiertemp.close()

		
	def getSelected(self) :
		#selected=[self.__cells[i] for i in range(len(self.__cells)) if self.__boxes[i].isSelected()]
		selected=[b.getText() for b in self.__boxes if b.isSelected()]
		return selected

	def setSelected(self, selected) :
		for b in self.__boxes : b.setSelected(False)
		#for s in selected : print str(s)
		for c in self.__cells : 
			#print str(c)
			if c in selected :
				self.__dictBox[c][1].setSelected(True)

	def resetok(self): 
		self.oked = False

	def setLabel(self, text):
		self.__label.setText(text)
			

# ------ end ---------------

if __name__ == "__main__":

	#gw
	for i in range(3) : 
		try : 
			gw
		except NameError :
			print "not define"
			cells=["cell"+"%04i" % (i) for i in range(300)]
			gw = CellsSelection()
			#gw.run(cells, "/Users/leon/Pictures/Equipes/Tam_Mignot/Emilia/MCPs-GFP/all/difA-tests/difA-1/14-11-11_22h05m50s/ROIs/")
			gw.run(cells, "/Users/leon/Dropbox/MacrosDropBox/imagesTest/files/WT/22-11-11_18h16m51s/ROIs/")
			gw.show()
			gw.setLabel("XXXXX")		
		
		else : 
			print "define"
			while not gw.oked and gw.isShowing() : cells = gw.getSelected()
			gw.setLabel("YYYY")
			print cells

	print "fin"

	#cells=["cell"+str(i) for i in range(5)]
	#gw = CellsSelection()
	#gw.run(cells)
	#gw.show()

	#selected=[cells[i] for i in range(1,3,1)]
	#gw.setSelected(selected)
	#while not gw.oked and gw.isShowing() : pass
	
