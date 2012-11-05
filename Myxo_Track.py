# -*- coding: iso-8859-15 -*-
from ij import ImageStack, ImagePlus, WindowManager, IJ
from ij.gui import Roi, NonBlockingGenericDialog, Overlay
from ij.plugin.frame import RoiManager
from ij.plugin import RGBStackMerge

from java.awt import TextField, Panel, GridLayout, ComponentOrientation, Label, Checkbox, BorderLayout, Button, Color, Font, Rectangle, Polygon
from java.lang import Double,Boolean,Float
from java.awt.event import MouseAdapter,MouseEvent
from java.awt import Point, Color, Font


from javax.swing import JOptionPane,JFrame, JPanel

import sys
import os
import time
import glob
import os.path as path
import getpass
import shutil
import random

username=getpass.getuser()

mypath=os.path.expanduser(IJ.getDirectory("plugins")+"MeasureCells")
#mypath=os.path.expanduser("~/Dropbox/MacrosDropBox/py/MeasureCells_7")
#mypath=os.path.expanduser(os.path.join("~","Dropbox","MacrosDropBox","py","MeasureCells_7"))
sys.path.append(mypath)

from org.python.core import codecs
codecs.setDefaultEncoding('utf-8')

from MorphoBact import Morph
from BacteriaCell import Bacteria_Cell
from CellsSelection import CellsSelection

imp=IJ.getImage()
hs=3
sw=1
#Color.blue, Color.green, Color.magenta, Color.orange, Color.yellow
#red=Color(255,0,0)
#green=Color(0,255,0)

IJ.showMessage("Select the folder 'Cells' containing the cells to import")
selectdir=IJ.getDirectory("image")
selectdir=IJ.getDirectory("")

#pathdir=str(selectdir).rsplit("/", 2)[0]+"/ROIs/"
pathdir=os.path.join(os.path.split(os.path.split(selectdir)[0])[0], "ROIs", "")
#rootdir=str(selectdir).rsplit("/", 2)[0]+"/"
rootdir=os.path.join(os.path.split(os.path.split(selectdir)[0])[0], "")

listfilescells=[]
listrois=[]
listfilescells.extend(glob.glob(selectdir+"*"))
listrois.extend(glob.glob(pathdir+"*"))


#allcells=[]
allcellnames=[]
for cellfile in listfilescells :
	#allcells.append(Bacteria_Cell.makeCell(cellfile))
	#name=cellfile.rsplit("/", 1)[1][:-len(".cell")]
	name=os.path.splitext(os.path.split(cellfile)[1])[0]
	#allcellnames.append(allcells[-1].getName())
	allcellnames.append(name)

dictRois={}
for r in listrois :
	#cle=r.rsplit("/", 1)[1][:-len(".zip")]
	cle=os.path.splitext(os.path.split(r)[1])[0]
	if cle in allcellnames : dictRois[cle]=r

rm = RoiManager.getInstance()
if (rm==None): rm = RoiManager()


rm.runCommand("UseNames", "true")
rm.runCommand("Associate", "true")
rm.runCommand("Show None")

gw = CellsSelection()
gw.setTitle(imp.getTitle())
gw.run(dictRois.keys(), pathdir)
gw.show()
gw.setSelected(dictRois.keys())
while not gw.oked and gw.isShowing() : 
	gw.setLabel("Validate selection with OK !!")
	listcellname = list(gw.getSelected())
gw.resetok()
gw.setLabel("...")
gw.hide()

rm.runCommand("reset")

if imp.getOverlay() is not None : imp.getOverlay().clear()
overlay=Overlay()
imp.setOverlay(overlay)
gd0=NonBlockingGenericDialog("settings")
gd0.addCheckbox("Show the overlay during the process ? (slow option)", False)
gd0.addNumericField("Minimal Lifetime  : ",10,0)
gd0.addNumericField("Minimal distance to reversion  : ",2,0)
gd0.addNumericField("Sub sampling ?  : ",1,0)
gd0.showDialog()

isShow = gd0.getNextBoolean()
minLife = gd0.getNextNumber()
mind = gd0.getNextNumber()
subs = gd0.getNextNumber()

if gd0.wasCanceled() : 
	isShow = True
	imp.show()
else :
	if  isShow : imp.show()
	else : imp.hide()

dicSens, dicSpeed, dicAngle, dicCumuld, dicPos ={},{},{}, {}, {}
dicSpeedA, dicSpeedB, dicSpeedC, dicMidAxis, dicFeret = {},{},{},{},{}


maxx=-1
maxspeed=-1
maxcumuld=-1

colors = []
ncells= len(listfilescells)
if ncells > 0 :
	step=200/ncells
	if step<1 : step=1
	for i in range(ncells) : 
		r = random.randrange(5,205,step)
		g = random.randrange(10,210,step)
		b = random.randrange(30,230,step)
		colors.append(Color(r, g, b))

if  isShow : imp.show()
else : imp.hide()

cles=[]
now = time.strftime('%d-%m-%y_%Hh%Mm%Ss',time.localtime())

IJ.log("-------start at "+now+"  ------")


#for cell in listfilescells :
f1 = open(rootdir+now+"-R1-MT.txt", "w")
tab="\t"
f1.write("cell"+tab+"maxFrames"+tab+"maxcumul"+tab+"nrevs"+"\n")

for cle in listcellname :
	rm.runCommand("reset")
	#cle = cell.rsplit("/", 1)[1][:-len(".cell")]
	#cles.append(cle)
	rm.runCommand("Open", dictRois[cle])
	rm.runCommand("Show None")
	RawroisArray=rm.getRoisAsArray()
	if len(RawroisArray)< minLife : continue
	roisArray=[RawroisArray[i] for i in range(0,len(RawroisArray), subs)]
	IJ.showStatus(cle)
	IJ.showProgress(listcellname.index(cle), len(listcellname)) 

	dxA=[]
	dyA=[]
	dxB=[]
	dyB=[]
	dA=[]
	dB=[]

	sensA = 1
	sensB = -1
	nrev = 0
	
	color=colors.pop(0)
	colorA=color.brighter()
	colorB=color.darker()

	r=colorA.getRed()
	g=colorA.getGreen()
	b=colorA.getBlue()

	reversions, speed, angles, cumuld, pos = [sensA],[0],[0], [0], []
	speedA, speedB, speedC = [0],[0], [(0,0)]
	midaxislength = []
	Feret = []

	pointsA={}
	pointsB={}
	centres={}

	i0 = roisArray[0].getPosition()
	end = roisArray[-1].getPosition()
	
	imp.setSlice(i0)
	t=Morph(imp, roisArray[0])
	try : polygon=t.MidAxis.getPolygon()
	except AttributeError : 
		print "break at", cle, i
		break

	#xpoints = Morph(imp, roisArray[0]).MidAxis.getPolygon().xpoints
	#ypoints = Morph(imp, roisArray[0]).MidAxis.getPolygon().ypoints
	#npoints = Morph(imp, roisArray[0]).MidAxis.getPolygon().npoints

	xpoints = polygon.xpoints
	ypoints = polygon.ypoints
	npoints = polygon.npoints

	midaxislength.append(npoints)
	Feret.append(t.MaxFeret)
	
	ci = len(xpoints)//2
	centres[0]=(xpoints[ci], ypoints[ci])
	pos.append(centres[0])

	pointsA[0]=(xpoints[0], ypoints[0])
	pointsB[0]=(xpoints[-1], ypoints[-1])
	
	for i in range(1, len(roisArray), 1) :
		IJ.showProgress(i, len(roisArray)) 
		imp.setSlice(i+i0)

		t=Morph(imp, roisArray[i])
		#print cle, i, t.MidAxis
		#try : xpoints = t.MidAxis.getPolygon()
		#except AttributeError : 
		#	print "break"
		#	break
		try : polygon=t.MidAxis.getPolygon()
		except AttributeError : 
			print "break at", cle, i
			break

		xpoints = polygon.xpoints
		ypoints = polygon.ypoints
		npoints = polygon.npoints

		midaxislength.append(npoints)
		Feret.append(t.MaxFeret)
		
		
		#xpoints = t.MidAxis.getPolygon().xpoints
		#ypoints = t.MidAxis.getPolygon().ypoints
		#npoints = t.MidAxis.getPolygon().npoints
		ci = len(xpoints)//2
		centres[i]=(xpoints[ci], ypoints[ci])
		pos.append(centres[i])

		# chgt repere pour centroide
		x0=pointsA[i-1][0]-centres[i-1][0]
		y0=pointsA[i-1][1]-centres[i-1][1]


		x1=xpoints[0]-centres[i][0]
		y1=ypoints[0]-centres[i][1]
	
		x2=xpoints[-1]-centres[i][0]
		y2=ypoints[-1]-centres[i][1]

		d1=Morph.distMorph([(1,x0,x1),(1, y0, y1)]) # dist from old A to new extem1
		d2=Morph.distMorph([(1,x0,x2),(1, y0, y2)])# dist from old A to new extem2
		
		if d1<=d2 :
			pointsA[i]=(xpoints[0], ypoints[0]) # new A is the closest from old A
			pointsB[i]=(xpoints[-1], ypoints[-1])
		else : 
			pointsB[i]=(xpoints[0], ypoints[0])
			pointsA[i]=(xpoints[-1], ypoints[-1]) # new A is the closest from old A

		# ------- coordonées image ------------
		xa0=pointsA[i-1][0]
		xa1=pointsA[i][0]
		ya0=pointsA[i-1][1]
		ya1=pointsA[i][1]

		xb0=pointsB[i-1][0]
		xb1=pointsB[i][0]
		yb0=pointsB[i-1][1]
		yb1=pointsB[i][1]

		xc0=centres[i-1][0]
		yc0=centres[i-1][1]		

		xc1=centres[i][0]
		yc1=centres[i][1]

		# ------------ coordonées old centre -----------
		#norme vecteur oldC to newA ATTENTION COORDONNEES IMAGE INVERSEES
		#vA1=(xa1-xc0, yc0-ya1)
		#vA0=(xa0-xc0, yc0-ya0)
		#vB1=(xb1-xc0, yc0-yb1)
		#vB0=(xb0-xc0, yc0-yb0)
		vC1=(xc1-xc0, yc0-yc1)
		#vA0A1=(xa1-xa0, ya0-ya1)
		#vB0B1=(xb1-xb0, yb0-yb1)
		#A0xA0A1=(vA0[0]*vA0A1[0]+vA0[1]*vA0A1[1])
		#B0xB0B1=(vB0[0]*vB0B1[0]+vB0[1]*vB0B1[1])

		#da=Morph.distMorph([(1, xa1, xc0),(1, ya1, yc0)]) #from old center to new A
		#db=Morph.distMorph([(1, xb1, xc0),(1, yb1, yc0)]) #from old center to new B
		#dc=Morph.distMorph([(1, xc1, xc0),(1, yc1, yc0)]) #from old center to new Center
		#daa=Morph.distMorph([(1, xa1, xa0),(1, ya1, ya0)]) #from old A to new A
		#dbb=Morph.distMorph([(1, xb1, xb0),(1, yb1, yb0)]) #from old A to new A

		#speedA.append(A0xA0A1)
		#speedB.append(B0xB0B1)
		speedC.append(vC1)

		#methode centres :
		dc=Morph.distMorph([(1, xc0, xc1),(1, yc0, yc1)])
		speed.append(dc)
		if dc>mind :
			da=Morph.distMorph([(1, xa1, xc0),(1, ya1, yc0)])
			db=Morph.distMorph([(1, xb1, xc0),(1, yb1, yc0)])
			if da>=db : 
				
				#sens.append("A")
				reversions.append(sensA)
			else : 
				#sens.append("B")
				reversions.append(sensB)
		else : 
			if reversions[-1]==sensA : reversions.append(sensA)
			else : reversions.append(sensB)
		
		if reversions[-2]*reversions[-1]<1 : nrev+=1
		
		#---- end centres 
		
		if reversions[-1]==sensA :
			ar=Arrow(xa0,ya0, xa1,ya1)
			#ar.setStrokeColor(Color.green)
			ar.setStrokeColor(colorA)
			ar.setStrokeWidth(sw)
			ar.setHeadSize(hs)
			overlay.add(ar)
		else :
			ar=Arrow(xb0,yb0, xb1,yb1)
			#ar.setStrokeColor(Color.red)
			ar.setStrokeColor(colorB)
			ar.setStrokeWidth(sw)
			ar.setHeadSize(hs)
			overlay.add(ar)

		#speed.append(Morph.distMorph([(1, centres[i-1][0], centres[i][0]),(1, centres[i-1][1], centres[i][1])]))
		#angles.append(t.AngleFeret)
		cumuld.append(cumuld[-1]+speed[-1])
		#time.sleep(0.2)

	else : cles.append(cle)

	speedA.append(0)
	speedB.append(0)

	for i in range(2,len(pointsA)) :
		speedA.append((pointsA[i-1][0]-pointsA[i-2][0])*(pointsA[i][0]-pointsA[i-1][0])+(pointsA[i-2][1]-pointsA[i-1][1])*(pointsA[i-1][1]-pointsA[i][1])) #scalaire a0a1Xa1a2
		speedB.append((pointsB[i-1][0]-pointsB[i-2][0])*(pointsB[i][0]-pointsB[i-1][0])+(pointsB[i-2][1]-pointsB[i-1][1])*(pointsB[i-1][1]-pointsB[i][1]))

	dicSens[cle]=reversions
	dicSpeed[cle]=speed
	dicSpeedA[cle]=speedA
	dicSpeedB[cle]=speedB
	dicSpeedC[cle]=speedC
	dicMidAxis[cle]=midaxislength
	dicFeret[cle] = Feret
	#dicAngle[cle]=angles
	dicCumuld[cle]=cumuld
	dicPos[cle]=pos
	
	if i > maxx : maxx = i
	if max(speed) > maxspeed : maxspeed = max(speed)
	if max(cumuld) > maxcumuld : maxcumuld = max(cumuld)
	tab="\t"
	
	if cle in cles : 
		IJ.log(cle+tab+str(len(reversions))+tab+str(max(cumuld))+tab+str(nrev))
		f1.write(cle+tab+str(len(reversions))+tab+str(max(cumuld))+tab+str(nrev)+"\n")
	
	del(reversions)
	del(speed)
	del(speedA)
	del(speedB)
	del(speedC)
	del(midaxislength)
	del(Feret)
	#del(angles)
	del(cumuld)
	del(pos)
	#print dicPos[cle][0][0]

IJ.log("-------end-------")

IJ.log(str(len(cles))+" cells")

f1.close()

#temprgb = IJ.createImage("Untitled", "RGB Black", 578, 555, 1)
#rgbstack = temprgb.createEmptyStack()
#temprgb.hide()

for cle in cles :
	reversions, speed, speedA, speedB, speedC, cumuld = dicSens[cle], dicSpeed[cle], dicSpeedA[cle], dicSpeedB[cle], dicSpeedC[cle], dicCumuld[cle]
	midaxislength = dicMidAxis[cle]
	Feret = dicFeret[cle]
	for i in range(maxx-len(reversions)) : 
		reversions.append(Double.NaN)
		speed.append(Double.NaN)
		speedA.append(Double.NaN)
		speedB.append(Double.NaN)
		speedC.append((Double.NaN,Double.NaN))
		midaxislength.append(Double.NaN)
		Feret.append(Double.NaN)
		cumuld.append(Double.NaN)
		
	
	plot1=Plot("Reversions-"+cle,"frames","",range(maxx),reversions)
	plot1.setLimits(1,maxx,-1.1,1.1)
	#plot1.show()

	ip1=plot1.getProcessor()
	ip1.invert()
	implot1=ImagePlus("plot1", ip1)
	#implot1.show()
	istack=ImageStack(ip1.getWidth(), ip1.getHeight())
	istack.addSlice("reversions", ip1)
	
	plot2=Plot("Speed-"+cle,"","",range(maxx),speed)
	plot2.setLimits(1,maxx,0,maxspeed*1.1)
	ip2=plot2.getProcessor()
	ip2.invert()
	implot2=ImagePlus("plot2", ip2)
	#implot2.show()
	#plot2.show()
	istack.addSlice("speed", ip2)
	
	plot3=Plot("CumulDist-"+cle,"","",range(maxx),cumuld)
	plot3.setLimits(1,maxx,0,maxcumuld*1.1)
	ip3=plot3.getProcessor()
	ip3.invert()
	implot3=ImagePlus("plot3", ip3)
	#implot3.show()
	#plot3.show()
	istack.addSlice("cumul", ip3)
	imstack=ImagePlus("stack3", istack)
	
	#IJ.run("Images to Stack", "name="+cle+"-plots title="+cle+" use")
	imstack.show()
	IJ.selectWindow("stack3")
	#imtorgb=[implot1,implot2,implot3]
	#rgbcon=RGBStackMerge()
	#IJ.run("Merge Channels...", "red="+implot1.getTitle()+" green="+implot2.getTitle()+" blue="+implot3.getTitle()+" gray=*None*");
	#lastimage=IJ.getImage()
	
	#lastimage = rgbcon.mergeChannels(imtorgb, True) 
	#lastimage.show()
	#IJ.run("Invert", "stack")
	IJ.run("Stack to RGB", "")
	lastimage=IJ.getImage()
	imstack.close()
	#cp = lastimage.getProcessor().convertToRGB()
	cp = lastimage.getProcessor()
	try : rgbstack.addSlice(cle, cp)
	except NameError : 
		rgbstack = lastimage.createEmptyStack()
		rgbstack.addSlice(cle, cp)
	lastimage.close()
	#IJ.selectWindow(cle+"-plots")
	#IJ.getImage().hide()
	
	del(reversions)
	del(speed)
	del(cumuld)

imprgb=ImagePlus("rgbStack", rgbstack)
imprgb.show()
IJ.selectWindow("rgbStack")
IJ.run("Hide Overlay", "")
#IJ.run("Images to Stack", "name=RGB-plots title=(RGB) use")

imp.show()
IJ.selectWindow(imp.getTitle())
imp.setOverlay(overlay)
IJ.run("Show Overlay", "")


for i in range(len(cles)) :
	pos=dicPos[cles[i]]
	command = 'Overlay.drawString("'+cles[i]+'", '+str(pos[0][0])+', '+str(pos[0][1])+')'
	IJ.runMacro(command)


f2 = open(rootdir+now+"-R2-MT.txt", "w")
f3 = open(rootdir+now+"-R3-MT.txt", "w")
f4 = open(rootdir+now+"-R4-MT.txt", "w")

tab="\t"

line2 = ["sens"+cle+tab+"speed"+cle+tab+"cumul"+cle for cle in cles]
line3 = ["scalA"+cle+tab+"scalB"+cle+tab+"oriX"+cle+tab+"oriY"+cle for cle in cles]
line4 = ["midaxis"+cle+tab+"Feret"+cle for cle in cles]

f2.write(tab.join(line2)+"\n")
f3.write(tab.join(line3)+"\n")
f4.write(tab.join(line4)+"\n")

for i in range(maxx) :
	line2 = [str(dicSens[cle][i])+tab+str(dicSpeed[cle][i])+tab+str(dicCumuld[cle][i]) for cle in cles]
	line3 = [str(dicSpeedA[cle][i])+tab+str(dicSpeedB[cle][i])+tab+str(dicSpeedC[cle][i][0])+tab+str(dicSpeedC[cle][i][1]) for cle in cles]
	line4 = [str(dicMidAxis[cle][i])+tab+str(dicFeret[cle][i]) for cle in cles]
	f2 .write(tab.join(line2)+"\n")
	f3 .write(tab.join(line3)+"\n")
	f4.write(tab.join(line4)+"\n")
	#print i, line

f2.close()
f3.close()
f4.close()

dictRois.clear()
for r in listrois :
	#cle=r.rsplit("/", 1)[1][:-len(".zip")]
	cle=os.path.splitext(os.path.split(r)[1])[0]
	if cle in cles : dictRois[cle]=r

gw = CellsSelection()
gw.setTitle(imp.getTitle())
gw.run(dictRois.keys(), pathdir)
gw.show()
gw.setSelected(dictRois.keys())
while not gw.oked and gw.isShowing() :
	pass 
	#gw.setLabel("Validate selection with OK !!")
	#listcellname = list(gw.getSelected())
gw.resetok()
gw.setLabel("...")
gw.hide()

		