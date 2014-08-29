

from ij.measure import ResultsTable
from ij.plugin.filter import Analyzer, ThresholdToSelection, MaximumFinder, BackgroundSubtracter
from ij.gui import Line, ProfilePlot, PolygonRoi, Roi, EllipseRoi, ShapeRoi, Wand, PointRoi
from ij.process import ByteProcessor, ImageProcessor
from ij import IJ, ImagePlus

from ij import ImageStack, ImagePlus, WindowManager, IJ
from ij.gui import Roi, NonBlockingGenericDialog, Overlay, ImageRoi, Line, OvalRoi, PolygonRoi, ShapeRoi, TextRoi
from ij.plugin.frame import RoiManager
from ij.plugin.filter import MaximumFinder, Analyzer
from ij.text import TextWindow
from ij.plugin import Straightener, Duplicator, ZProjector, MontageMaker, ImageCalculator
from ij.process import ShortProcessor, ByteProcessor
from ij.measure import ResultsTable

import math
import time

import java.lang.Float as Float

from org.python.core import codecs
codecs.setDefaultEncoding('utf-8')


class Morph(object):
	"""
		Fourni les mesures principales pour l'analyse des cellules bactériennes:
		proprietés:
		1-MaxFeret
		2-MinFeret
		3-AngleFeret
		4-XFeret
		5-YFeret
		6-Area
		7-Mean
		8-StdDev
		9-IntDen
		10-Kurt
		11-Skew
		12-Angle
		13-Major
		14-Minor
		15-Solidity
		16-AR
		17-Round
		18-Circ.
		19-XM
		20-YM
		21-X
		22-Y
		23-FerCoord: tuple contenant x1, y1, x2, y2 du MaxFeret
		24-Fprofil: list contenant les valeurs du profil le long de MaxFeret
		25-FerAxis: Line ROI
		26-MidAxis: Polyline ROI de l'axe median par skeletonize
		27-MidProfil: list contenant les valeurs du profil le long de MidAxis
		28-nb Foci
		29-ListFoci: liste des positions des foci par cellule
		30-ListAreaFoci: liste des area des foci
		31-ListPeaksFoci: liste des int max des foci
		32-ListMeanFoci liste des int mean des foci
		
		toute les proprietés mettent a jour l'image cible par: object.propriete=imp
		
		Methodes:
		getFeretSegments(n segments)
		getMidSegments(n segments, radius, tool 0= ligne perpendiculaire, 1= cercle, 2= ligne tangente)
		selectInitRoi: active la ROI initiale
		
		Statics:
		distMorph(liste de coordonées a mesurer= (coefficient, valeur initiale, valeur finale))
		
		setteurs:
		setImage(ImagePlus)
		setImageMeasures(imagePlus) met a jours les mesures avec imagePlus
		setImageMidprofil(imagePlus) met a jours le profil avec imagePlus
		setLineWidth(width) afecte la largeur de ligne pour le profil pour Fprofile et MidProfil defaut = 0
		setshowFprof(True) affiche le graphique de profil Fprofil defaut = False
		setMidParams(longueur mesurer l'angle de l'extremité en pixels defaut=10, coefficient pour prolonger et trouver l'intersection avec le contour defaut=1.3
		
	"""

	def __Measures(self):

		self.__boolmeasures=True
		if (self.__contour is not None) and  (self.__contour.getType() not in [9,10]):
			self.__image.killRoi()
			self.__image.setRoi(self.__contour)
			self.__ip=self.__image.getProcessor()
			self.__rt= ResultsTable()
			analyser= Analyzer(self.__image, Analyzer.AREA+Analyzer.CENTER_OF_MASS+Analyzer.CENTROID+Analyzer.ELLIPSE+Analyzer.FERET+Analyzer.INTEGRATED_DENSITY+Analyzer.MEAN+Analyzer.KURTOSIS+Analyzer.SKEWNESS+Analyzer.MEDIAN+Analyzer.MIN_MAX+Analyzer.MODE+Analyzer.RECT+Analyzer.SHAPE_DESCRIPTORS+Analyzer.SLICE+Analyzer.STACK_POSITION+Analyzer.STD_DEV, self.__rt)
			analyser.measure()
			#self.__rt.show("myRT")
		else:
			self.__rt = ResultsTable()
			analyser = Analyzer(self.__image, Analyzer.AREA+Analyzer.CENTER_OF_MASS+Analyzer.CENTROID+Analyzer.ELLIPSE+Analyzer.FERET+Analyzer.INTEGRATED_DENSITY+Analyzer.MEAN+Analyzer.KURTOSIS+Analyzer.SKEWNESS+Analyzer.MEDIAN+Analyzer.MIN_MAX+Analyzer.MODE+Analyzer.RECT+Analyzer.SHAPE_DESCRIPTORS+Analyzer.SLICE+Analyzer.STACK_POSITION+Analyzer.STD_DEV, self.__rt)
			analyser.measure()
			#self.__rt.show("myRT")
			maxValues=self.__rt.getRowAsString(0).split("\t")
			heads=self.__rt.getColumnHeadings().split("\t")
			for val in heads: self.__rt.setValue(val, 0, Float.NaN)
			#self.__rt.show("myRT")

	# calculate the 1/2 , 1/4 ... 1/n positions for a liste while 1/n >= 1 returns a dict = 0: (0, [0, 0, pos(1/2)]) 1: (1, [-1, -0.5, -pos(1/4)], [0, 0, pos(1/2)], [1, 0.5, pos(1/2)])
	def __Centers(self, line) :
		L=len(line)
		l2=L//2
		l=L
		pos={}
		for i in range(self.log2(L)) : 
			l = l//2
			pos[i]=l
		l=L
		dicPos={}
		jtot=1
		for i in range(self.log2(L)) :
			s=[]
			j=1
			while (l2-j*pos[i])>0 or (l2+j*pos[i])<L :
				s.append((-j,(l2-j*pos[i])))
				s.append((j,(l2+j*pos[i])))
				j=j+1
			s.append((0,l2))
			s.sort()
			if ((len(s)+1)*pos[i]-L)//pos[i] > 0 :
				del s[0]
				del s[-1]

			else : pass
			if len(s) - 1  != 0 : jtot= (( len(s) - 1 ) / 2.00)+1
			else : jtot=1
			centers=[[v[0], v[0]/jtot, v[1]] for v in s]
			dicPos[i]=(i, centers)	
			del(s)
		return dicPos
		
	#calculate angle from the center of the midline to ends
	def __flexAngle(self) :
		try : 
			p1 = self.__midLine[0]
			p3 = self.__midLine[-1]
		except AttributeError : 
			self.__midline()
			p1 = self.__midLine[0]
			p3 = self.__midLine[-1]

		icenter = self.__midCenters[0][1][0][2]
		p2 = self.__midLine[icenter]
		#xpoints = (429,472,466)
		#ypoints = (114,133,99)
		xpoints = [int(p1[0]), int(p2[0]), int(p3[0])]
		ypoints = [int(p1[1]), int(p2[1]), int(p3[1])]
		#print ypoints
		#return ""
		r = PolygonRoi(xpoints, ypoints, 3, Roi.ANGLE)
		return r.getAngle()

	def __NbFoci(self):
		self.__boolFoci=True
		self.__image.killRoi()
		self.__image.setRoi(self.__contour)
		self.__ip=self.__image.getProcessor()
		rt=ResultsTable.getResultsTable()
		rt.reset()
		mf=MaximumFinder()
		mf.findMaxima(self.__ip, self.__noise, 0, MaximumFinder.LIST, True, False)
		self.__listMax[:]=[]
		
		#feret=self.getFercoord()
		#xc=feret[0]-((feret[0]-feret[2])/2.0)
		#yc=feret[1]-((feret[1]-feret[3])/2.0)

		#print xc, yc

		xc=self.getXC()
		yc=self.getYC()

		#print xc, yc
		
		for i in range(rt.getCounter()):
			x=int(rt.getValue("X", i))
			y=int(rt.getValue("Y", i))
			size=self.__localwand(x, y, self.__ip, self.__seuilPeaks, self.__peaksMethod, self.__light)
			coord=[(1, xc, x), (1, yc, y)]
 			d=self.distMorph(coord,"Euclidean distance")
 			d=( d / (self.getMaxF()/2) )*100
 			self.__listMax.append((x, y, size[0], size[1], size[2], size[3], size[4], d))
		rt.reset()
		
			
	def __FeretAxis(self):

		__boolFL=True
		if (self.__contour is not None) and (self.__contour.getType() in range(1,11)):
			self.__image.killRoi()
			self.__image.setRoi(self.__contour)
			if self.__contour.getType() in [1,5,9,10]:
				self.__polygon=self.__contour.getPolygon()
			else:
				self.__polygon=self.__contour.getFloatPolygon()
			points = self.__polygon.npoints
			self.__polx = self.__polygon.xpoints
			self.__poly = self.__polygon.ypoints
			diameter=0.0
			for i in range(points):
				for j in range(i, points):
					dx=self.__polx[i]-self.__polx[j]
					dy=self.__poly[i]-self.__poly[j]
					d=math.sqrt(dx*dx+dy*dy)
					if d>diameter:
						diameter=d
						i1=i
						i2=j
			
			tempDictY={ self.__poly[i1]:(self.__polx[i1],self.__poly[i1],self.__polx[i2],self.__poly[i2]), self.__poly[i2]:(self.__polx[i2],self.__poly[i2],self.__polx[i1],self.__poly[i1]) }			
			
			minY=min((self.__poly[i1],self.__poly[i2]))
			maxY=max((self.__poly[i1],self.__poly[i2]))
			lineTuple=tempDictY[maxY]
			
			self.__x1=lineTuple[0]
			self.__y1=lineTuple[1]
			self.__x2=lineTuple[2]
			self.__y2=lineTuple[3]
			
			self.__line= Line(self.__x1,self.__y1,self.__x2,self.__y2)			
			
			
		elif (self.__contour is not None) and (self.__contour.getType()==0):
			self.__x2=self.__contour.getBounds().x
			self.__y2=self.__contour.getBounds().y
			self.__x1=self.__contour.getBounds().x+self.__contour.getBounds().width
			self.__y1=self.__contour.getBounds().y+self.__contour.getBounds().height
			self.__line= Line(self.__x1,self.__y1,self.__x2,self.__y2)


		else:
			self.__x1="NaN"
			self.__y1="NaN"
			self.__x2="NaN"
			self.__y2="NaN"
			self.__fprofArray="NaN"
		
	def __FeretProfile(self):
		"""
			genere le profile le long du diametre de Feret
		"""
		self.__line.setWidth(self.__lw)
		self.__image.setRoi(self.__line, True)
		self.__fprof= ProfilePlot(self.__image)
		self.__fprofArray=self.__fprof.getProfile()
		if self.__showFpro: self.__fprof.createWindow()
		self.__image.killRoi()
		self.__line.setWidth(0)
		self.__image.setRoi(self.__contour)
		return self.__fprofArray
		
	def __midline(self):
		debug=False
		#print "line 251", self.__boolML
		if self.__boolML :
			ordpoints=self.__midLine[:]
			npoints=len(ordpoints)
			xpoints=[point[0] for point in ordpoints]
			ypoints=[point[1] for point in ordpoints]
			polyOrd=PolygonRoi(xpoints, ypoints, npoints, PolygonRoi.POLYLINE)
			return polyOrd

		#if self.getMaxF()<15 : return None
			#self.__FeretAxis()
			#return self.__line

		self.__boolML=True
		self.__image.killRoi()
		self.__image.setRoi(self.__contour)
		boundRect=self.__contour.getBounds()
		boundRoi=Roi(boundRect)
		xori=boundRect.x
		yori=boundRect.y
		wori=boundRect.width
		hori=boundRect.height
		ip2 = ByteProcessor(self.__image.getWidth(), self.__image.getHeight())
		ip2.setColor(255)
		ip2.setRoi(self.__contour)
		ip2.fill(self.__contour)
		skmp=ImagePlus("ip2", ip2)
		skmp.setRoi(xori-1,yori-1,wori+1,hori+1)
		ip3=ip2.crop()
		skmp3=ImagePlus("ip3", ip3)
		skmp3.killRoi()
		#-------------------------------------------------------------
		if debug : 
			skmp3.show()
			IJ.showMessage("imp3 l287")
		#-------------------------------------------------------------
		IJ.run(skmp3, "Skeletonize (2D/3D)", "")
		#IJ.run(skmp3, "Skeletonize", "")
		#-------------------------------------------------------------
		if debug : 
			skmp3.show()
			IJ.showMessage("imp3 l294")
		#-------------------------------------------------------------
		IJ.run(skmp3, "BinaryConnectivity ", "white")
		ip3.setThreshold(3,4, ImageProcessor.BLACK_AND_WHITE_LUT)
		IJ.run(skmp3, "Convert to Mask", "")
		#-------------------------------------------------------------
		if debug : 
			skmp3.show()
			IJ.showMessage("imp3 l302")
		#-------------------------------------------------------------
		#IJ.run(skmp3, "Skeletonize", "")
		#-------------------------------------------------------------
		if debug : 
			skmp3.updateAndDraw() 
			skmp3.show()
			IJ.showMessage("imp3 l308")
		#-------------------------------------------------------------
		rawPoints=[]
		w=ip3.getWidth()
		h=ip3.getHeight()
		
		rawPoints=[(x+xori,y+yori,self.__sommeVals(x,y,ip3)) for x in range(w) for y in range(h) if ip3.getPixel(x,y)==255]
		tempbouts=[val for val in rawPoints if val[2]==2]

		if len(tempbouts)!=2 : return None
		# test
		#if len(tempbouts)!=2 :
		#	
		#	IJ.run(skmp3, "BinaryConnectivity ", "white")
		#	ip3.setThreshold(3,3, ImageProcessor.BLACK_AND_WHITE_LUT)
		#	IJ.run(skmp3, "Convert to Mask", "")
		#	#-------------------------------------------------------------
		#	if debug==debug : 
		#		skmp3.updateAndDraw() 
		#		skmp3.show()
		#		IJ.showMessage("if test l 328")
		##-------------------------------------------------------------
		#	rawPoints=[(x+xori,y+yori,self.__sommeVals(x,y,ip3)) for x in range(w) for y in range(h) if ip3.getPixel(x,y)==255]
		#	tempbouts=[val for val in rawPoints if val[2]==2]
			
		ip3.setRoi(boundRect)
		if rawPoints==[]: return None
		npoints=len(rawPoints)
		xpoints=[point[0] for point in rawPoints]
		ypoints=[point[1] for point in rawPoints]
		valpoints=[point[2] for point in rawPoints]
		
		bouts={}
		
		if tempbouts==[]: return None
		
		if tempbouts[0][1]>tempbouts[1][1]:
			bouts["A"]=tempbouts[0]
			bouts["B"]=tempbouts[1]
		else:
			bouts["A"]=tempbouts[1]
			bouts["B"]=tempbouts[0]

		rawPoints.remove(bouts["A"])

		rawPoints.remove(bouts["B"])
		rawPoints.append(bouts["B"])

		tempList=[val for val in rawPoints]

		p=bouts["A"]
		Dist={}
		ordPoints=[]
		
		for j in range(len(rawPoints)):
			Dist.clear()
			for i in range(len(tempList)):
				dx=p[0]-tempList[i][0]
				dy=p[1]-tempList[i][1]
				d=math.sqrt(dx*dx+dy*dy)
				Dist[d]=tempList[i]

			distList=Dist.keys()
			mind=min(distList)
			nextpoint=Dist[mind]
			ordPoints.append(nextpoint)
			tempList.remove(nextpoint)
			p=nextpoint

		ordPoints.insert(0, bouts["A"])
		
		npoints=len(ordPoints)
		if npoints < 4 : return None
		xpoints=[point[0] for point in ordPoints]
		ypoints=[point[1] for point in ordPoints]
		polyOrd1=PolygonRoi(xpoints, ypoints, npoints, PolygonRoi.POLYLINE)
		
		f=min(self.__midParams[0], len(xpoints)//2)
		
		angleA1=polyOrd1.getAngle(xpoints[0],ypoints[0], xpoints[1],ypoints[1])
		angleA2=polyOrd1.getAngle(xpoints[1],ypoints[1], xpoints[2],ypoints[3])
		angleA = (angleA1+angleA2)/2.00
		angleA=polyOrd1.getAngle(xpoints[0],ypoints[0], xpoints[f],ypoints[f])
		angleA=angleA*(math.pi/180)
		
		angleB1=polyOrd1.getAngle(xpoints[-2],ypoints[-2], xpoints[-1],ypoints[-1])
		angleB2=polyOrd1.getAngle(xpoints[-3],ypoints[-3], xpoints[-2],ypoints[-2])
		angleB = (angleB1+angleB2)/2.00
		angleB=polyOrd1.getAngle(xpoints[-f],ypoints[-f], xpoints[-1],ypoints[-1])
		angleB=angleB*(math.pi/180)

		coef=self.__midParams[1]
		
		xa = xpoints[0]-coef*f*math.cos(angleA)
		ya = ypoints[0]+coef*f*math.sin(angleA)
		xb = xpoints[-1]+coef*f*math.cos(angleB)
		yb = ypoints[-1]-coef*f*math.sin(angleB)

		lineA=Line(xpoints[0],ypoints[0], xa, ya)
		lineB=Line(xpoints[-1],ypoints[-1], xb, yb)
		lineA.setWidth(0)
		lineB.setWidth(0)
		lineA.setStrokeWidth(0) 
		lineB.setStrokeWidth(0)
		
		ip2.setColor(0)
		ip2.fill()
		ip2.setColor(255)
		ip2.setRoi(lineA)
		lineA.drawPixels(ip2)
		ip2.setRoi(lineB)
		lineB.drawPixels(ip2)

		ip2.setRoi(self.__contour)
		ip2.setColor(0)
		ip2.fillOutside(self.__contour)
		ip2=ip2.crop()
		imb=ImagePlus("new-ip2", ip2)
				
		#-------------------------------------------------------------
		if debug : 
			imb.show()
			IJ.showMessage("imb l416")
		#-------------------------------------------------------------
		w2=ip2.getWidth()
		h2=ip2.getHeight()
		ip4 = ByteProcessor(w2+2, h2+2)
		im4=ImagePlus("im4", ip4)

		for i in range(w2):
			for j in range(h2):
				ip4.set(i+1,j+1,max([ip2.getPixel(i,j),ip3.getPixel(i,j)]))
		#im4.show()
		#-------------------------------------------------------------
		if debug : 
			im4.show()
			IJ.showMessage("im4 l430")
		#-------------------------------------------------------------
		im4.killRoi()
		#IJ.run(im4, "Skeletonize (2D/3D)", "")
		#IJ.run(skmp3, "Skeletonize", "")
		#-------------------------------------------------------------
		if debug : 
			imb.show()
			IJ.showMessage("imb l300")
		#-------------------------------------------------------------
		#IJ.run(skmp3, "Skeletonize", "")
		ip4=im4.getProcessor()
		
		rawPoints2=[]
		w4=ip4.getWidth()
		h4=ip4.getHeight()
		

		rawPoints2=[(x+xori-2,y+yori-2,self.__sommeVals(x,y,ip4)) for x in range(w4) for y in range(h4) if ip4.getPixel(x,y)==255]
		self.__MidBouts=[val for val in rawPoints2 if val[2]==2]

		# test
		if len(self.__MidBouts)!=2 : 
			IJ.run(im4, "BinaryConnectivity ", "white")
			ip4.setThreshold(3,3, ImageProcessor.BLACK_AND_WHITE_LUT)
			IJ.run(im4, "Convert to Mask", "")
			rawPoints2=[(x+xori-2,y+yori-2,self.__sommeVals(x,y,ip4)) for x in range(w4) for y in range(h4) if ip4.getPixel(x,y)==255]
			self.__MidBouts=[val for val in rawPoints2 if val[2]==2]
		
		ordpoints=[]
		p0=self.__MidBouts[0]
		rawPoints2.remove(p0)
		c=0
		
		while p0!=self.__MidBouts[1]:
			if c<len(rawPoints2):
				point=rawPoints2[c]
			else: break
			if abs(point[0]-p0[0])<2 and abs(point[1]-p0[1])<2:
				p0=point
				ordpoints.append(point)
				rawPoints2.remove(point)
				c=0
			else: c=c+1

		ordpoints.insert(0, self.__MidBouts[0])
		self.__midLine=ordpoints[:]
		self.__midCenters = self.__Centers(self.__midLine)
		npoints=len(ordpoints)
		xpoints=[point[0] for point in ordpoints]
		ypoints=[point[1] for point in ordpoints]

		polyOrd=PolygonRoi(xpoints, ypoints, npoints, PolygonRoi.POLYLINE)

		
		#print self.__midLine
		#print self.__MidBouts
		#print xpoints
		#print ypoints

		return polyOrd
		
	def __sommeVals(self, x, y, ip):

		return (ip.getPixel(x,y)+ip.getPixel(x-1,y-1)+ip.getPixel(x,y-1)+ip.getPixel(x+1,y-1)+ip.getPixel(x-1,y)+ip.getPixel(x+1,y)+ip.getPixel(x-1,y+1)+ip.getPixel(x,y+1)+ip.getPixel(x+1,y+1))/255

	def __localwand(self, x, y, ip, seuil, method, light):
		self.__image.killRoi()
		ip.snapshot()
		if method == "mean" : 
			peak=ip.getPixel(x,y)
			tol = (peak - self.getMean())*seuil
			w = Wand(ip)
			w.autoOutline(x, y, tol, Wand.EIGHT_CONNECTED)
			#print "method=", method, tol, peak
			
		elif method == "background" : 
			radius = self.getMinF()/4 
			bs = BackgroundSubtracter()
			#rollingBallBackground(ImageProcessor ip, double radius, boolean createBackground, boolean lightBackground, boolean useParaboloid, boolean doPresmooth, boolean correctCorners) 
			bs.rollingBallBackground(ip, radius, False, light, False, True, False)
			peak=ip.getPixel(x,y)
			tol = peak*seuil
			w = Wand(ip)
			w.autoOutline(x, y, tol, Wand.EIGHT_CONNECTED)
			ip.reset()
			#print "method=", method, tol, radius, peak
			
		else : 
			peak=ip.getPixel(x,y)
			tol = peak*seuil
			w = Wand(ip)
			w.autoOutline(x, y, tol, Wand.EIGHT_CONNECTED)
			#print "method=", method, tol

		peak=ip.getPixel(x,y)
		temproi=PolygonRoi(w.xpoints, w.ypoints, w.npoints, PolygonRoi.POLYGON)
		self.__image.setRoi(temproi)
		#self.__image.show()
		#time.sleep(1)
		#peakip=self.__image.getProcessor()
		#stats=peakip.getStatistics()
		temprt = ResultsTable()
		analyser = Analyzer(self.__image, Analyzer.AREA+Analyzer.INTEGRATED_DENSITY+Analyzer.FERET, temprt)
		analyser.measure()
		#temprt.show("temprt")
		rtValues=temprt.getRowAsString(0).split("\t")
		area=float(rtValues[1])
		intDen=float(rtValues[4])
		feret=float(rtValues[2])
		mean=intDen/area
		#time.sleep(2)
		temprt.reset()
		self.__image.killRoi()
		return [peak, area, mean, intDen, feret]
					
		
	
	def __MidProfil(self):
		if not self.__boolML :  self.__midline()
		ip=self.__image.getProcessor()
		line=Line(self.__midLine[0][0],self.__midLine[0][1],self.__midLine[-1][0],self.__midLine[-1][1])
		line.setWidth(self.__lw)

		self.__MprofArray=[]
		self.__MprofArray[:]=[]
		for i in range(0,len(self.__midLine)-1):
			templine=Line(self.__midLine[i][0],self.__midLine[i][1],self.__midLine[i+1][0],self.__midLine[i+1][1])
			templine.setWidth(self.__lw)
			self.__image.setRoi(templine)
			#time.sleep(0.5)
			temprof= ProfilePlot(self.__image)
			temparray=temprof.getProfile()
			self.__MprofArray+=temparray
		templine.setWidth(0)
		#if self.__showMidpro: self.__fprof.createWindow()	 
		return
		
	def getFeretSegments(self, n):
		self.__boolFS=True
		if(not self.__boolFL):
			self.__FeretAxis()
		radius=self.getMinF()
		lsegment=self.__line.getLength()/((n-1)*2)
		xo=self.__x1
		yo=self.__y1
		xf=self.__x2
		yf=self.__y2
		angle1=self.getAngF()*(math.pi/180)
		angle2=self.getAngF()*(math.pi/180)+(math.pi/2)
		avancex=(lsegment*2)*math.cos(angle1)
		avancey=(lsegment*2)*math.sin(angle1)
		delta90x=(radius)*math.cos(angle2)
		delta90y=(radius)*math.sin(angle2)
		self.__line.setWidth(int(lsegment*2))
		#self.__image.setRoi(self.__line)
		tempcontour=self.__contour.clone()
		shapeContour=ShapeRoi(tempcontour)
		segsRoi=[]
		for i in range(n):
			tempLine=Line(xo-delta90x, yo+delta90y, xo+delta90x, yo-delta90y)
			tempLine.setWidth(int(lsegment*2))
			poly=tempLine.getPolygon()
			roipol=PolygonRoi(poly, Roi.POLYGON)
			shapePoly= ShapeRoi(roipol)
			interShape=shapePoly.and(shapeContour)
			segsRoi.append(interShape.shapeToRoi())
			xo=xo+avancex
			yo=yo-avancey

		
		#self.__image.setRoi(self.__contour, True)
		#time.sleep(0)
		self.__line.setWidth(0)
		#self.__image.setRoi(tempcontour)
		
		#self.__image.updateAndDraw() 
		
		return segsRoi # return Roi array

	def getMidSegments(self, n=10, r=5, tool=0):
		self.__boolMS=True
		if(not self.__boolML):
			self.__midline()
		lsegment=int(len(self.__midLine)/n)
		if lsegment<2:lsegment=2
		ls2=int(len(self.__midLine)/(2*n))
		if ls2<1: ls2=1
		ip=self.__image.getProcessor()
		#print(len(self.__midLine), lsegment, ls2)
		xo=self.__MidBouts[0][0]
		yo=self.__MidBouts[0][1]
		xf=self.__MidBouts[1][0]
		yf=self.__MidBouts[1][1]
		line1=Line(xo,yo,xf,yf)
		line1.setWidth(0)
		angles=[line1.getAngle(self.__midLine[i][0], self.__midLine[i][1], self.__midLine[i+lsegment][0], self.__midLine[i+lsegment][1]) for i in range(0,len(self.__midLine)-lsegment,lsegment)]
		points=[self.__midLine[i] for i in range(0,len(self.__midLine),lsegment)]
		lastangle=line1.getAngle(self.__midLine[-ls2][0],self.__midLine[-ls2][1],self.__midLine[-1][0],self.__midLine[-1][1])
		angles.append(lastangle)
		tempcontour=self.__contour.clone()
		shapeContour=ShapeRoi(tempcontour)
		angles=[angle*(math.pi/180)+(math.pi/2) for angle in angles]
		line1.setWidth((ls2+1)*2)
		segsRoi=[]
		linesRois=[]
		cRois=[]
		for i in range(len(angles)):
			x=points[i][0]
			y=points[i][1]
			cRois.append(PointRoi(x,y))
			if tool==0: # ligne perpendiculaire d'épaiseur  (ls2+1)*2
				line1.setWidth((ls2+1)*2)
				x1=x+r*math.cos(angles[i])
				y1=y-r*math.sin(angles[i])
				x2=x-r*math.cos(angles[i])
				y2=y+r*math.sin(angles[i])
				#print(x, y, x1, y1, x2, y2)
				tempLine=Line(x1,y1,x2,y2)
				linesRois.append(tempLine)
				tempLine.setWidth((ls2+1)*2)
				#self.__image.setRoi(tempLine, True)
				#time.sleep(0.3)
				poly=tempLine.getPolygon()
				roipol=PolygonRoi(poly, Roi.POLYGON)
				shapePoly= ShapeRoi(roipol)
			elif tool==1:
				#r1=r*0.7
				x1=x+r
				y1=y-r
				x2=x-r
				y2=y+r
				ellipse=EllipseRoi(x1, y1, x2, y2, 1)
				linesRois.append(ellipse)
				#print(x, y, x1, y1, x2, y2)
				#self.__image.setRoi(ellipse, True)
				shapePoly= ShapeRoi(ellipse)
				#time.sleep(0.3)
			else:
				x1=x
				y1=y
				line1.setWidth(r)
				if (i+1)<len(points):
					x2=points[i+1][0]
					y2=points[i+1][1]
				else:
					#x1=x+lsegment*math.cos(angles[i]-(math.pi/2))
					#y1=y-lsegment*math.sin(angles[i]-(math.pi/2))
					x2=x+lsegment*math.cos(angles[i]-(math.pi/2))
					y2=y-lsegment*math.sin(angles[i]-(math.pi/2))
					#x2=xf
					#y2=yf
				
				tempLine=Line(x1,y1,x2,y2)
				linesRois.append(tempLine)
				tempLine.setWidth(r)
				#self.__image.setRoi(tempLine, True)
				#time.sleep(0.5)
				poly=tempLine.getPolygon()
				roipol=PolygonRoi(poly, Roi.POLYGON)
				shapePoly= ShapeRoi(roipol)
			
			interShape=shapePoly.and(shapeContour)
			interRoi=interShape.shapeToRoi()
			segsRoi.append(interShape.shapeToRoi())
		line1.setWidth(0)
		return (segsRoi, linesRois, cRois)

	def selectInitRoi(self):
		self.__image.killRoi()
		self.__image.setRoi(self.__contour)
		time.sleep(0)

	@staticmethod
	def distMorph(coord,distmethod="Euclidean distance"):
		if distmethod == "Euclidean distance" :
			s=[val[0]*(val[2]-val[1])*(val[2]-val[1]) for val in coord]
			#print s
			#print sum(s)
			return math.sqrt(sum(s))
		if distmethod == "Logarithm distance" :
			s=[val[0]*abs(math.log(val[2]/val[1])) for val in coord]
			return sum(s)
			
	@staticmethod
	def log2(n) : return math.log(n)/math.log(2)
	
	def Out(self): print("out")

	

#------ end methodes---------------
#------ constructeur -------------

	def __init__(self, imp, roi):
		self.__lw=0
		self.__showFpro=False
		self.__Feret=[] 
		self.__image=imp
		self.__cal=imp.getCalibration()
		self.__contour=roi.clone()
		self.__boolmeasures=False
		self.__boolFP=False
		self.__boolFL=False
		self.__boolML=False
		self.__boolMP=False
		self.__boolFS=False
		self.__boolMS=False
		self.__boolFoci=False
		self.__midParams=[10, 1.3]
		self.__listMax=[]
		self.__noise=150
		self.__seuilPeaks=0.75
		self.__peaksMethod="mean"
		self.__light=False
		self.__distot=0.00
		self.__flexangle=0.00
		#print "dropbox MorphoBactProject"
	
#---------- end constructor---------
#---------- getteurs----------------
	
	def getMaxF(self):
		if(not self.__boolmeasures): self.__Measures()
		return self.__rt.getValue("Feret", 0)
	def getMinF(self):
		if(not self.__boolmeasures): self.__Measures()
		return self.__rt.getValue("MinFeret", 0)
	def getXF(self):
		if(not self.__boolmeasures): self.__Measures() 
		return self.__rt.getValue("FeretX", 0)
	def getYF(self): 
		if(not self.__boolmeasures): self.__Measures()
		return self.__rt.getValue("FeretY", 0)
	def getAngF(self):
		if(not self.__boolmeasures): self.__Measures()
		return self.__rt.getValue("FeretAngle", 0)
	def getArea(self): 
		if(not self.__boolmeasures): self.__Measures()
		return self.__rt.getValue("Area", 0)
	def getMean(self):
		if(not self.__boolmeasures): self.__Measures()
		return self.__rt.getValue("Mean", 0)
	def getKurt(self):
		if(not self.__boolmeasures): self.__Measures()
		return self.__rt.getValue("Kurt", 0)
	def getSkew(self):
		if(not self.__boolmeasures): self.__Measures()
		return self.__rt.getValue("Skew", 0)
	def getIntDen(self):
		if(not self.__boolmeasures): self.__Measures()
		return self.__rt.getValue("IntDen", 0)
	def getStdDev(self):
		if(not self.__boolmeasures): self.__Measures()
		return self.__rt.getValue("StdDev", 0)
	def getAngle(self): 
		if(not self.__boolmeasures): self.__Measures()
		return self.__rt.getValue("Angle", 0)
	def getMajor(self): 
		if(not self.__boolmeasures): self.__Measures()
		return self.__rt.getValue("Major", 0)
	def getMinor(self): 
		if(not self.__boolmeasures): self.__Measures()
		return self.__rt.getValue("Minor", 0)
	def getSolidity(self): 
		if(not self.__boolmeasures): self.__Measures()
		return self.__rt.getValue("Solidity", 0)
	def getAR(self): 
		if(not self.__boolmeasures): self.__Measures()
		return self.__rt.getValue("AR", 0)
	def getRound(self): 
		if(not self.__boolmeasures): self.__Measures()
		return self.__rt.getValue("Round", 0)
	def getCirc(self): 
		if(not self.__boolmeasures): self.__Measures()
		return self.__rt.getValue("Circ.", 0)
	def getXM(self): 
		if(not self.__boolmeasures): self.__Measures()
		return self.__rt.getValue("XM",0)
	def getYM(self): 
		if(not self.__boolmeasures): self.__Measures()
		return self.__rt.getValue("YM",0)
	def getXC(self): 
		if(not self.__boolmeasures): self.__Measures()
		return self.__rt.getValue("X",0)
	def getYC(self): 
		if(not self.__boolmeasures): self.__Measures()
		return self.__rt.getValue("Y",0)

	def getNfoci(self):
		if(not self.__boolFoci):self.__NbFoci()
		return len(self.__listMax)

	def getListFoci(self):
		if(not self.__boolFoci):self.__NbFoci()
		xy=[]
		for val in self.__listMax:
			xy.append((val[0], val[1]))
		return xy

	def getListPeaksFoci(self):
		if(not self.__boolFoci):self.__NbFoci()
		peaks=[]
		for val in self.__listMax:
			peaks.append(val[2])
		return peaks

	def getListAreaFoci(self):
		if(not self.__boolFoci):self.__NbFoci()
		areas=[]
		for val in self.__listMax:
			areas.append(val[3])
		return areas

	def getListMeanFoci(self):
		if(not self.__boolFoci):self.__NbFoci()
		means=[]
		for val in self.__listMax:
			means.append(val[4])
		return means

	def getListIntDenFoci(self):
		if(not self.__boolFoci):self.__NbFoci()
		ints=[]
		for val in self.__listMax:
			ints.append(val[5])
		return ints

	def getListFeretFoci(self):
		if(not self.__boolFoci):self.__NbFoci()
		ferets=[]
		for val in self.__listMax:
			ferets.append(val[6])
		return ferets

	def getListDistsFoci(self):
		if(not self.__boolFoci):self.__NbFoci()
		dists=[]
		for val in self.__listMax:
			dists.append(val[7])
		return dists

	def getFercoord(self):
		"""
			FerCoord: tuple contenant x1, y1, x2, y2 du MaxFeret
		"""
		if (not self.__boolFL): self.__FeretAxis()
		return (self.__x1,self.__y1,self.__x2,self.__y2)
	def getFprofil(self):
		"""
			Fprofil: list contenant les valeurs du profil le long de MaxFeret
		"""
		if (not self.__boolFL): self.__FeretAxis()
		self.__FeretProfile()
		return self.__fprofArray
	def getFerAxis(self):
		"""
			FerAxis: Line ROI
		"""
		if(not self.__boolFL): self.__FeretAxis()
		return self.__line
		
	def getMidAxis(self):
		"""
			MidAxis: Polyline ROI de l'axe median par skeletonize
		"""
		if(not self.__boolML): return self.__midline()

	def getMidSegs(self, n, r, tool):
		"""
			Rois des segments 0 = rois , 1 = points, 2 = lines ou ellipses
		"""
		if(not self.__boolMS): return self.getMidSegments(n, r, tool)
		
	def getMidProfil(self):
		"""
			MidProfil: list contenant les valeurs du profil le long de MidAxis
		"""
		self.__MidProfil()
		return self.__MprofArray

	def getMidPoints(self) :
		"""
			MidPoints : list of two extreme points of mid Axis
		"""
		if(not self.__boolML): self.__midline()
		return self.__MidBouts

	def getCenters(self) :
		if(not self.__boolML): self.__midline()
		return self.__midCenters

	def getFlexAngle(self) :
		return self.__flexAngle()


#------ setteurs --------

	def setImage(self, imp):
		self.__image=imp

	def setImageMeasures(self, imp):
		self.__image=imp
		self.__Measures()
		
	def setImageFprofil(self, imp):
		self.__image=imp
		self.__FeretProfile()

	def setImageMidprofil(self, imp):
		self.__image=imp
		self.__MidProfil()

	def setLineWidth(self, lw):
		self.__lw=lw

	def setshowFpro(self, fpshow):
		self.__showFpro=fpshow

	def setMidParams(self, lseg, coeff):
		self.__midParams[:]=[]
		self.__midParams.append(lseg)
		self.__midParams.append(coeff)

	def setNoise(self, noise):
		self.__noise=noise

	def setSeuilPeaks(self, seuil):
		self.__seuilPeaks=seuil

	def setpeaksMethod(self, method):
		self.__peaksMethod=method

	def setlight(self, light):
		self.__light=light

		
#------- properties -----------------------
	
	MaxFeret=property(getMaxF, setImageMeasures, doc="caliper max Feret=")
	MinFeret=property(getMinF, setImageMeasures, doc="caliper min Feret=")
	AngleFeret=property(getAngF, setImageMeasures, doc="angle Feret=")
	XFeret=property(getXF, setImageMeasures, doc="X Feret=")
	YFeret=property(getYF, setImageMeasures, doc="Y Feret=")
	Area=property(getArea, setImageMeasures, doc="Area=")
	Mean=property(getMean, setImageMeasures, doc="Mean=")
	Kurt=property(getKurt, setImageMeasures, doc="Kurtosis=")
	Skew=property(getSkew, setImageMeasures, doc="Skewness=")
	IntDen=property(getIntDen, setImageMeasures, doc="Integrated Intensity=")
	StdDev=property(getStdDev, setImageMeasures, doc="Standard Deviation=")
	Angle=property(getAngle, setImageMeasures, doc="Angle=")
	Major=property(getMajor, setImageMeasures, doc="Major ellipse axis=")
	Minor=property(getMinor, setImageMeasures, doc="Minor ellipse axis=")
	Solidity=property(getSolidity, setImageMeasures, doc="Solidity area/convexHull=")
	AR=property(getAR, setImageMeasures, doc="Major axis/Minor axis=")
	Round=property(getRound, setImageMeasures, doc="Area/(pi*Major*Major)=1/AR=")
	Circ=property(getCirc, setImageMeasures, doc="(4*pi*Area)/(perimeter*perimeter)=")
	XM=property(getXM, setImageMeasures, doc="X center of Mass=")
	YM=property(getYM, setImageMeasures, doc="Y center of Mass=")
	XC=property(getXC, setImageMeasures, doc="X of centroid=")
	YC=property(getYC, setImageMeasures, doc="Y of centroid=")
	
	NFoci=property(getNfoci, setImageMeasures, doc="nb foci in the roi=")
	ListFoci=property(getListFoci, setImageMeasures, doc="list of foci coordinates=")
	ListPeaksFoci=property(getListPeaksFoci, setImageMeasures, doc="list of foci peaks=")
	ListAreaFoci=property(getListAreaFoci, setImageMeasures, doc="list of foci areas=")
	ListMeanFoci=property(getListMeanFoci, setImageMeasures, doc="list of foci means=")
	ListIntDenFoci=property(getListIntDenFoci, setImageMeasures, doc="list of foci IntDen=")
	ListFeretFoci=property(getListFeretFoci, setImageMeasures, doc="list of foci Ferets=")
	ListDistsFoci=property(getListDistsFoci, setImageMeasures, doc="list of foci distances=")
	
	FerCoord=property(getFercoord, doc="x1, y1, x2, y2 of Feret diameter =")
	Fprofil=property(getFprofil, setImageFprofil, doc="Profil along Feret diameter") 	# return array values
	FerAxis=property(getFerAxis, doc="ROI along Feret diameter")				# return Roi
	
	MidAxis=property(getMidAxis, doc="ROI along the median axis")				# return Roi
	MidProfil=property(getMidProfil, setImageMidprofil, doc="profile values of mid axis")	# return array values
	MidPoints=property(getMidPoints, doc= "extreme points of mid line")

	Centers=property(getCenters, doc= "list of positions (tuples) of 1/2 of the midaxis, 1/4, 1/8 ...") # return a list of tuples
	FlexAngle=property(getFlexAngle, doc="angle of the center of midline to ends")	
	
#--------------------- end -------------------------------------------------------

if __name__ == "__main__":
	
	imp1=IJ.getImage()

	n=10
	
	if n==10 :

		roi=imp1.getRoi()
		m=Morph(imp1, roi)
		m.setMidParams(20, 5)
		midline=m.MidAxis
		#imp1.setRoi(midline)
		#midline.drawPixels(imp1.getProcessor())
		shape=2
		segs=m.getMidSegments(10, 40, shape)
		outtype=1
		for seg in segs[outtype] :
			time.sleep(0.5)
			if outtype==1 and shape==0 : seg.setStrokeWidth(1)
			imp1.setRoi(seg)
			#seg.drawPixels(imp1.getProcessor()) 
		
		#print m.Out()
	else :
		rm = RoiManager.getInstance()
		rois = rm.getRoisAsArray()
		for r in rois :
			#imp1.setRoi(r)
			m = Morph(imp1, r)
			imp1.setSlice(r.getPosition())
			print r.getName()
			#IJ.log(str(m.Area))
			#IJ.log(str(m.MaxFeret))
			#print  m.MidAxis is not None
			midline=m.MidAxis
			if midline is None : IJ.log("None")
			#if (midline == None) : IJ.log("None")
			else : 
				#IJ.log("slide = "+str(r.getPosition())+"; l = "+str(midline.getPolygon().npoints)+"; area = "+str(m.Area)+"; feret = "+str(m.MaxFeret))
				imp1.setRoi(midline)
			time.sleep(0)
		
	
	