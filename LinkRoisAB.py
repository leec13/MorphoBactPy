# -*- coding: iso-8859-15 -*-

import sys
import os
import glob
import os.path 
import getpass
import math

from ij import IJ
from ij.gui import Roi


from java.lang import Double,Boolean

#mypath=os.path.expanduser(IJ.getDirectory("plugins")+"MeasureCells")
mypath=os.path.expanduser(os.path.join("~","Dropbox","MacrosDropBox","py","MorphoBactProject"))

sys.path.append(mypath)

username=getpass.getuser()

from org.python.core import codecs
codecs.setDefaultEncoding('utf-8')

from MorphoBact import Morph

def link(img, sliceA, sliceB, RoisA, RoisB, coeffs, distmethod, optionangle, nbdigits, boolnews) :
	"""
	 This function takes in entry an image, two slices, two arrays of ROIs, a list of coefficients, and a string corresponding to the name of a method.
	 It aims at linking the different ROIs of an image to the ROIs of another image, according to the method and to the coefficients given in entry.
	 It returns 3 lists of tuples :		- one in which the tuples correspond to two ROIs linked.
	 					- another one in which the tuples correspond to new bacteria
	 					- a last one in which the tuples correspond to "lost" bacteria.
	"""	


	rawcoeffs=[coeffs[i] for i in range(0,len(coeffs), 2)]
	#maxdists=[0.01*coeffs[i] for i in range(1,len(coeffs), 2)]
	maxdists=[coeffs[i] for i in range(1,len(coeffs), 2)]

	
	# Definition of the different parameters used in the distance.
	
	measure=[]
	measure.append("Area")
	measure.append("Angle")
	measure.append("MaxFeret")
	measure.append("XC")
	measure.append("YC")


	#Delata max normalization:
	coeffdist=[rawcoeffs[i]/(maxdists[i]*sum(rawcoeffs)) for i in range(5)]

	# Calcul of the constant in order to flag the cells that are out of range (according to the preferences of the user)
	#maxdisteuclarray=[]
	#maxdisteuclarray.append(math.sqrt(coeffdist[0]/sum(coeffdist)*(maxdists[0]*img.getWidth()*img.getHeight())**2))
	#maxdisteuclarray.append(math.sqrt(coeffdist[1]/sum(coeffdist)*(maxdists[1]*180)**2))
	#maxdisteuclarray.append(math.sqrt(coeffdist[2]/sum(coeffdist)*(maxdists[2]*math.sqrt((img.getWidth())**2+(img.getHeight())**2))**2))
	#maxdisteuclarray.append(math.sqrt(coeffdist[3]/sum(coeffdist)*(maxdists[3]*img.getWidth())**2))
	#maxdisteuclarray.append(math.sqrt(coeffdist[4]/sum(coeffdist)*(maxdists[4]*img.getHeight())**2))
	#maxdisteucl=max(maxdisteuclarray)

	maxdisteuclarray=[math.sqrt(coeffdist[i]*(maxdists[i]**2)) for i in range(5)]
	#MAXDIST=max(maxdisteuclarray)

	MAXDIST=math.sqrt(max(maxdists)**2)
	
	#if distmethod=="Logarithm distance" :
	#	for i in range(len(maxdists)) :
	#		if maxdists[i]==1 :
	#			maxdists[i]-=10**(-nbdigits)
	#	MAXDIST=max([abs(math.log(1-maxdists[i])) for i in range(5)])

	#if distmethod=="Euclidean distance" :
	#	maxdisteuclarray=[]
	#	maxdisteuclarray.append(math.sqrt(coeffdist[0]/sum(coeffdist)*(maxdists[0]*img.getWidth()*img.getHeight())**2))
	#	maxdisteuclarray.append(math.sqrt(coeffdist[1]/sum(coeffdist)*(maxdists[1]*180)**2))
	#	maxdisteuclarray.append(math.sqrt(coeffdist[2]/sum(coeffdist)*(maxdists[2]*math.sqrt((img.getWidth())**2+(img.getHeight())**2))**2))
	#	maxdisteuclarray.append(math.sqrt(coeffdist[3]/sum(coeffdist)*(maxdists[3]*img.getWidth())**2))
	#	maxdisteuclarray.append(math.sqrt(coeffdist[4]/sum(coeffdist)*(maxdists[4]*img.getHeight())**2))
	#	MAXDIST=max(maxdisteuclarray)
		
	#img.hide()


	# Creation of the "matrix" of the different distances between all couples of RoisA and RoisB possible.
	# The "matrix" is a dictionnary with tuples of ROIs (ROISA,ROISB) as key, and tuples (distance,(ROIA,ROIB)) as values
	
	listedist={}
	for roisA in RoisA :
		morphA=Morph(img, roisA)
		for roisB in RoisB :
			morphB=Morph(img, roisB)
			#if distmethod=="Logarithm distance" :
			#	val=[ [ coeffdist[i]/sum(coeffdist), morphA.__getattribute__(measure[i]), morphB.__getattribute__(measure[i]) ]  for i in range(3) ] 
			#	val.append([coeffdist[3]/sum(coeffdist),img.getWidth() ,max(morphA.__getattribute__(measure[3]),morphB.__getattribute__(measure[3]))-min(morphA.__getattribute__(measure[3]),morphB.__getattribute__(measure[3]))])
			#	val.append([coeffdist[4]/sum(coeffdist),img.getHeight() ,max(morphA.__getattribute__(measure[4]),morphB.__getattribute__(measure[4]))-min(morphA.__getattribute__(measure[4]),morphB.__getattribute__(measure[4]))])
			#else	:	val=[ [ coeffdist[i]/sum(coeffdist), morphA.__getattribute__(measure[i]), morphB.__getattribute__(measure[i]) ]  for i in range(5) ] 
			rawval=[ [ 1, morphA.__getattribute__(measure[i]), morphB.__getattribute__(measure[i]) ]  for i in range(5) ] 
			val=[ [ coeffdist[i], morphA.__getattribute__(measure[i]), morphB.__getattribute__(measure[i]) ]  for i in range(5) ] 
			#print rawval
			#print "----"
			#for v in val : print math.sqrt(v[0]*(v[2]-v[1])*(v[2]-v[1]))
			
			# We make sure there is no null value
			out=""
			
			for i in range(5): 
				if val[i][1]==0 :
					val[i][1]+=10**(-nbdigits)
				if val[i][2]==0 :
					val[i][2]+=10**(-nbdigits)
					
			#	if abs(rawval[i][2]-rawval[i][1])>maxdists[i]: out = "out of range"

			#print "area", rawval[0][2], "/", rawval[0][1],">", maxdists[0],"=", abs(rawval[0][2]/rawval[0][1])>maxdists[0]
			#print "feret", rawval[2][2], "/", rawval[2][1],">", maxdists[2],"=", abs(rawval[2][2]/rawval[2][1])>maxdists[2]

			if abs(rawval[1][2]-rawval[1][1])>maxdists[1]: out = "out of range"
			if abs(rawval[3][2]-rawval[3][1])>maxdists[3]: out = "out of range"
			if abs(rawval[4][2]-rawval[4][1])>maxdists[4]: out = "out of range"

			if abs(rawval[0][2]/rawval[0][1])>maxdists[0]: 
				out = "out of range"
			if abs(rawval[2][2]/rawval[2][1])>maxdists[2]: 
				out = "out of range"
				
			if optionangle==True :
				if val[1][1]>=178 : val[1][1]=180-val[1][1]
				if val[1][2]>=178 : val[1][2]=180-val[1][2]
			
			# We check if the value is in the interval defined by the user.
			#out=""
			#for i in range(3):
			#	if 1-(min(val[i][1], val[i][2])/max(val[i][1], val[i][2]))  > maxdists[i] : 
			#		out="out of range"
			#		print "out of range i=",i,"car : delta=",1-(min(val[i][1], val[i][2])/max(val[i][1], val[i][2]))," et maxdists[i] :",maxdists[i]
			#if distmethod=="Euclidean distance" :
			#	deltax=(max(val[3][1],val[3][2])-min(val[3][1],val[3][2]))/img.getWidth()
			#	deltay=(max(val[4][1],val[4][2])-min(val[4][1],val[4][2]))/img.getHeight()
			#	if deltax > maxdists[3] or deltay > maxdists[4] : 
			#		out="out of range"
			#		print "out of range 3-4 car : delta=",deltax,"  ",deltay," et maxdists3-4 :",maxdists[3]," ",maxdists[4]
			#if distmethod=="Logarithm distance" :
			#	if val[3][2]/val[3][1] > maxdists[3] or val[4][2]/val[4][1] > maxdists[4] : 
			#		out = "out of range"
			#		print "out of range 3-4 car : rapport=",val[3][2]/val[3][1],"  ",val[4][2]/val[4][1]," et maxdists3-4 :",maxdists[3]," ",maxdists[4]
			if out == "" :
				listedist[(roisA,roisB)]=(Morph.distMorph(val,distmethod),(roisA,roisB))
				
			else : listedist[(roisA,roisB)]=(MAXDIST,(roisA,roisB))
			
			
	# The mininum of all distances is found in the matrix, and if it is < to a certain value, then the couple of ROIs linked is added in a list "liens".
	# Then all couples having one of the two ROIs considered just before are deleted from the "matrix".
	# And while the length of "liens" is not equal to the minimum of the length of RoisA and RoisB, or the mininum is inferior to the value "seuil", we repeat the algorithm.
	# The list of tuples "liens" is returned by the function.
	#print listedist
	liens = []
	for i in range(min([len(RoisA),len(RoisB)])) :
		mindist=min(listedist.values())
		#print "(",mindist,";",i,";",min([len(RoisA),len(RoisB)]),")"
		if mindist[0]>=MAXDIST : 
			break
		else :
			minroisA=mindist[1][0]
			minroisB=mindist[1][1]
			liens.append((minroisA,minroisB))
			for cle in listedist.keys() :
				if cle[0]==minroisA or cle[1]==minroisB :
					del listedist[cle]

	# If any ROI of RoisA doesn't appear in the list of tuples "liens", then the ROI is considered to be "LOST"; and the list of tuples of ROIs lost is returned by the function.
	
	lost=[]
	for roisA in RoisA:
		marqueurtemp = False
		for lien in liens :
			if lien[0] == roisA :
				marqueurtemp = True
				break
		if marqueurtemp == False :
			lost.append(("LOST",roisA))


	# If any ROI of RoisB doesn't appear in the list of tuples "liens", then the ROI is considered to be "NEW"; and the list of tuples of new ROIs is returned by the function.
	
	new=[]
	if boolnews :
		for roisB in RoisB	:
			marqueurtemp = False
			for lien in liens :
				if lien[1] == roisB :
					marqueurtemp = True
					break
			if marqueurtemp == False :
				new.append(("NEW",roisB))


	# The function "link" returns a tuples of all three lists of tuples : "liens", "new", and "lost"
	
	return (liens,new,lost)
	
if __name__ == "__main__":
	link()