import glob
import os
from os import path
from os import stat

from ij import IJ
from ij.gui import NonBlockingGenericDialog

def createListfiles() : 

	IJ.showMessage("Select a folder with the .tif files")
	selectdir=IJ.getDirectory("image")
	selectdir=IJ.getDirectory("")

	listfiles=glob.glob(selectdir+"*.tif")

	#fullprefix = str.rsplit(str(listfiles[0]), "/", 1)
	fullprefix = os.path.split(listfiles[0])
	root = fullprefix[0]
	lastprefix = str.split(fullprefix[1], "_")

	del(listfiles)


	gdselectfiles = NonBlockingGenericDialog("List files Choice")
	gdselectfiles.addMessage("")
	gdselectfiles.addStringField("Prefix ?", lastprefix[0], 32)
	gdselectfiles.addStringField("Filter (w00001DIA) ?", "1DIA")
	gdselectfiles.addStringField("Positions (s0001) ?", "1-2")
	gdselectfiles.addStringField("Temps (t0001) ?", "1-11")
	#gdselectfiles.addStringField("Files pattern", "*DIA_s*1_t*.tif", 32)
	gdselectfiles.showDialog()

	prefix = str(gdselectfiles.getNextString())
	channel = str(gdselectfiles.getNextString())
	temppositions = str(gdselectfiles.getNextString())
	positions = str.split(temppositions, "-")
	temptimes = str(gdselectfiles.getNextString())
	times = str.split(temptimes, "-")

	if channel != "" : channel = "_w000"+channel

	positionslist=[]
	if positions[0] != "" : 
		for p in range(int(positions[0]), int(positions[1])+1, 1) : 
			positionslist.append("_s"+"%04i"%(p))
	else : positionslist.append("")

	timeslist=[]		
	if times[0] != "" : 
		for t in range(int(times[0]), int(times[1])+1, 1) : 
			timeslist.append("_t"+"%04i"%(t))
	else : timeslist.append("")
	
	patterns=[]
	listfiles = []
	for p in positionslist :
		files = []
		for t in timeslist :
			patterns.append(channel+p+t+".tif")
			tempfilename = os.path.join(root, prefix+patterns[-1])
			files.append(tempfilename)
			#files.append(root+"/"+prefix+patterns[-1])
		listfiles.append(files)

	if len(listfiles)>1 : return (prefix, patterns, listfiles, positionslist)
	else : return (prefix, patterns, files, "_s0001")

if __name__ == "__main__":
	for f in createListfiles()[2] :
		print f 

