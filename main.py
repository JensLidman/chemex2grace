import os
import sys
import re
import shutil
import statistics as st
import argparse
import pathlib
RESULT_DIR = "result/"

repo_path= pathlib.Path(__file__).parent.absolute()
TEMPLATE_GRACE_R2 = f"{repo_path}/template_R2.agr"
TEMPLATE_GRACE_RES = f"{repo_path}/template_res.agr"

def getFileInfo(fileName):
	"""
	This will get the info from the filename
	Format from re: [delay time, magnet strength, temperature, type of file]
	- type of file is essential for reading mode
	"""
	info = {}
	arr = re.match(r'.+cpmg_ch3_mq_(\d+)ms_(\d+)mhz_(\d+)c.(\w+)',fileName)
	if(arr):
		info["delay"]=arr.group(1)
		info["magnet"]=arr.group(2)
		info["temp"]=arr.group(3)
		info["type"]=arr.group(4)
	return info


def readExpFile(fileName,type):
	"""
	This function will read all data from each file, then split it into datasets as an array in data where all datasets have a "name" and its "values"
	The "values" for exp file will be in a 4 column with
		delay, data, data error up, data error down
	and for the fit data will be 2 column with
		delay, data
	"""
	data =[]
	file = open(fileName,'r', encoding='utf8')
	
	allDataFromFile = file.read()
	allRes = allDataFromFile.split("\n\n") # Each dataset is seperated by two linebreaks
	file.close()
	
	for res in allRes:
		currentRes=""
		values=[]
		dataset={}
		for l in res.split("\n"):
			str =l.strip()
			r = re.match(r"\[([A-Za-z0-9_]+)-([A-Za-z0-9_]+)\]",str)
	
			if(r):
				dataset["name"]=r.group(1).strip()
			elif(str.startswith("#")):
				continue
			elif type == "fit":
				dataset["dataexist"]=True
				strList = str.split()
				if len(strList)==3:
					values.append([strList[0],strList[2]])
			elif type == "exp":
				strList = str.split()
				if len(strList)==5:
					values.append([strList[0],strList[2],strList[3],strList[4]])
		dataset["values"]=values
		if len(dataset["values"]) > 0:
			data.append(dataset)

	data_sorted = sorted(data,key=lambda x: x["name"][1:])

	return data_sorted


def getDataFromFileList(filedir):
	"""
	Reads all data from each file to one big data set ordered as:
	[[info],[[residue],[data]]]
	"""
	data = []
	filelist =os.listdir(filedir)
	
	print("Loading data from data dir\n")
	if len(filelist)>0:
		print("DataFiles included:\n ----------------------------------")
	else:
		print("No data files found\n")
		return data
	
	for f in filelist:
		if "cpmg" not in f :
			continue
		d1 ={}
		d1["info"]= getFileInfo(filedir+f)
		if not d1["info"]:
			return data
		
		if not d1["info"]["type"]  =="fit" and not d1["info"]["type"] == "exp": #This is to avoid additional files that have the same name
			continue
		else:
			print("|  "+f+" |")
		d1["resdata"]=readExpFile(filedir+f,d1["info"]["type"])
		
		
		data.append(d1)
	print(" ----------------------------------\n")

	return data
def getExpDataMean(data,magnet,resName):
	for expData in data:
		if  expData["info"]["type"] == "exp" and not expData["info"]["magnet"] == magnet:
			totErrUp = []
			totErrDown = []
			index = -1
			for i in range(len(expData["resdata"])):
				if expData["resdata"][i]["name"]==resName:
					index = i
					break
			if index ==-1:
				return 0.0,0.0
			for value in expData["resdata"][index]["values"]:
				totErrUp.append(float(value[2]))
				totErrDown.append(float(value[3]))
				
			return st.mean(totErrUp), st.mean(totErrDown) # Mean value of all errors in experimental data
	
def renameRes(res):
	"""
	This function will rename the string resname for grace, e.g. D will become a delta sign
	"""
	if "CD1" in res: return res.replace("CD1","\\xd1")
	elif "CD2" in res: return res.replace("CD2","\\xd2")
	elif "CG1" in res: return res.replace("CG1","\\xg1")
	elif "CG2" in res: return res.replace("CG2","\\xg2")
	elif "CB" in res: return res.replace("CB","\\xb")
	else: print(res+ " could not be converted")
	
def writeToR2GraceFile(magnet,R2,R2_name,missingRes,width):
	"""
	Writes the created R2 values to a existing tempalate file (This file have all the information of how the plot is supposed to look)
	The template have the syntac INSERT_AXIS for the names, and INSERT_DATA for the R2 values
	"""
	file_R2 = open(RESULT_DIR+"R2_diff_"+magnet+".agr",'w', encoding='utf8')
	template_R2 = open(TEMPLATE_GRACE_R2,'r')
	template = template_R2.read()
	template = template.replace("INSERT_AXIS",R2_name)
	template = template.replace("INSERT_DATA_R2",R2)
	template = template.replace("INSERT_MISSING",missingRes)
	template = template.replace("AXIS_WIDTH",width)
	file_R2.write(template)
	file_R2.close()
	template_R2.close()
	
def writeToR2pymolFile(magnet,R2):
	"""
	This will write the same R2 files as above, exept its an new empty file, and there will be no renaming
	"""
	file_R2 = open(RESULT_DIR+"R2_diff_"+magnet+".txt",'w', encoding='utf8')
	for i in R2:
		file_R2.write(i[0]+"\t"+i[1]+"\n")
	file_R2.close()
	
def arrangepeaklist(plist):
	"""
	Arranges the peaklist (if it is imported) with a sorting function and replacing certain characters to match
	the rest of the data.
	"""
	pFile = open(plist,'r')
	peaklist = []
	for peak in pFile:
		if "#" in peak:
			continue
		l = peak.strip().split()[0]
		if "-" in l:
			l = l.replace("-","C")
		peaklist.append(l)
	return sorted(peaklist,key=lambda x: x[1:])
	
def addMissingRes(data,plist):
	"""
	This will simply add a empty peak, if it is missing. With a key "dataexist" set as False
	"""
	for i in range(len(plist)):
		if not data[i]["name"]==plist[i]:
			dataset ={}
			dataset["name"]=plist[i]
			dataset["dataexist"]=False
			data.insert(i,dataset)
	return data
		
def calcR2(data,plist):
	"""
	This will make the calculation of R2 diff, which is the absolute value of the difference between the lowset value of the fitted data and the highest.
	There is no error in the fitted data, to get som errors they are taken from the experimental data.
	First the the correct detasets are extracted (info then type from directory) to be fit.
	"""
	peaklist = []
	if len(plist)>0:
		peaklist = arrangepeaklist(plist)

	fitDataList = []
	for d in data:
		if(d["info"]["type"]=="fit"):
			fitDataList.append(d)
	for d in fitDataList:
		fitData = addMissingRes(d["resdata"],peaklist)
		R2 = ""
		R2_axis= "@    xaxis  tick spec "+str(len(fitData))+"\n"
		R2_agr_axis = ""
		R2_pymol = []
		missingValues = []
		
		for i in range(len(fitData)):
				#import pdb; pdb.set_trace()
			diff = 0
			if  fitData[i]["dataexist"]:
				diff = float(fitData[i]["values"][0][1])-float(fitData[i]["values"][-1][1])
			else:
						missingValues.append([i,1])
			errUp,errDown = getExpDataMean(data,d["info"]["magnet"],fitData[i]["name"])
			
			R2_axis+= '@    xaxis  ticklabel '+str(i)+', "'+renameRes(fitData[i]["name"])+'"\n@    xaxis  tick major '+str(i)+', '+str(i)+'\n'
			R2 += str(i)+"\t"+str(diff)+"\t"+str(errUp)+"\t"+str(errDown)+"\n"
			if fitData[i]["dataexist"]:
				R2_pymol.append([fitData[i]["name"],str(diff)])
			else:
				R2_pymol.append([fitData[i]["name"],"NULL"])
		missingRes = ""
		for m in missingValues:
			missingRes += str(m[0])+"\t"+str(m[1])+"\n"
		width = str(float(len(fitData))-0.5)
		writeToR2GraceFile(d["info"]["magnet"],R2,R2_axis,missingRes,width)
		writeToR2pymolFile(d["info"]["magnet"],R2_pymol)

def writeResToGrace(dataTot):
	"""
	This function creates all diffrent plot files for each residue with datasets from all different files (From this raw data its 4 but has the option to be more)
	
	"""
	plot_dir=RESULT_DIR+"plots/"
	os.mkdir(plot_dir)
	template_file = open(TEMPLATE_GRACE_RES,'r')
	template = template_file.read()
	for i in range(len(dataTot[0]["resdata"])):
		index=0
		resName = dataTot[0]["resdata"][i]["name"]
		template_fixed = template.replace("INSERT_TITLE",renameRes(resName))
		res_file = open(plot_dir+resName+".agr","a")
		res_file.write(template_fixed)
		
		dataSorted = sorted(dataTot,key=lambda x: x["info"]["type"])
		"""
		The way grace want x axis is:
			@target G0.S0"\n@type xy\n
		"""
		for data in dataSorted:
			if data["info"]["type"] == "fit":
				res_file.write("@target G0.S"+str(index)+"\n@type xy\n")
				for l in data["resdata"][i]["values"]:
					res_file.write('%s %15s\n' % (l[0],l[1]))
				
			elif data["info"]["type"] == "exp":
				res_file.write("@target G0.S"+str(index)+"\n@type xydydy\n")
				for l in data["resdata"][i]["values"]:
					res_file.write('%s %15s %15s %15s\n' % (l[0],l[1],l[2],l[3]))
			res_file.write("&\n")
			index = index + 1
		res_file.close()
			
def checkData(dataTot):
	
	length_str = ""
	length = []
	for data in dataTot:
		length.append(len(data["resdata"]))
		length_str +=str(len(data["resdata"]))+"\t"

	m = min(length)
	everyMatch = True
	for data in dataTot:
		for i in range(m):
			if  not dataTot[0]["resdata"][i]["name"] == data["resdata"][i]["name"]:
				everyMatch = False
	if everyMatch:
		print("All data sets are equal residues with lengths of: "+ str(m))
	else:
		print("Datasets are not equal residues with lengths of: "+ length_str)

	return everyMatch

def createResultFolder():
	if os.path.exists(RESULT_DIR):
		shutil.rmtree(RESULT_DIR)
		print("Old result directory removed")
	os.mkdir(RESULT_DIR)

def main():
	parser = argparse.ArgumentParser()
	parser.add_argument("-n", "--name", action="store", nargs="?", help="Name of datafolder")
	parser.add_argument("-p", "--peaklist", action="store", nargs="?", help="Reference peaklist")
	args = parser.parse_args()
    
	print(args.name)

	data = getDataFromFileList(args.name)
    
	if len(data)>0:
		if checkData(data):
			createResultFolder()
			writeResToGrace(data)

			calcR2(data,args.peaklist)
	else:
		print("No data found")

if __name__ == "__main__":
	main()
