import os
import sys
import re
import shutil
import statistics as st

ROOT_DIR=os.getcwd()+"/"
DATA_DIR= ROOT_DIR+ "/data/"
RESULT_DIR = ROOT_DIR + "/result/"
TEMPLATE_GRACE_R2 = ROOT_DIR+"/template_R2.agr"
TEMPLATE_GRACE_RES = ROOT_DIR+"/template_res.agr"

def getFileInfo(fileName):
	"""
	This will get the info from the filename
	Format from re: [delay time, magnet strength, temperature, type of file]
	- type of file is essential for reading mode
	"""
	info = {}
	arr = re.match(r'cpmg_ch3_mq_(\d+)ms_(\d+)mhz_(\d+)c.(\w+)',fileName)
	info["delay"]=arr.group(1)
	info["magnet"]=arr.group(2)
	info["temp"]=arr.group(3)
	info["type"]=arr.group(4)
	return info


def readExpFile(fileName,type):
	data =[]
	file = open(DATA_DIR+fileName,'r', encoding='utf8')
	
	all = file.read()
	file.close()
	allRes = all.split("\n\n")
	
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


def getDataFromFileList():
	"""
	Reads all data from each file to one big data set ordered as:
	[[info],[[residue],[data]]]
	"""
	data = []
	fileList = os.listdir(DATA_DIR)
	print("Program started")
	for f in fileList:
		if "cpmg" not in f :
			continue
		d1 ={}
		d1["info"]= getFileInfo(f)
		
		if not d1["info"]["type"]  =="fit" and not d1["info"]["type"] == "exp": #This is to avoid additional files that have the same name
			continue
		else:
			print("Data file included: "+f)
		d1["resdata"]=readExpFile(f,d1["info"]["type"])
		
		
		data.append(d1)

	return data
def getExpDataMean(data,magnet,index):
	for expData in data:
		if  expData["info"]["type"] == "exp" and not expData["info"]["magnet"] == magnet:
			totErrUp = []
			totErrDown = []
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
	
def writeToR2GraceFile(magnet,R2,R2_name):
	"""
	Writes the created R2 values to a existing tempalate file (This file have all the information of how the plot is supposed to look)
	The template have the syntac INSERT_AXIS for the names, and INSERT_DATA for the R2 values
	"""
	file_R2 = open(ROOT_DIR+"R2_diff_"+magnet+".agr",'w', encoding='utf8')
	template_R2 = open(TEMPLATE_GRACE_R2,'r')
	template = template_R2.read()
	template = template.replace("INSERT_AXIS",R2_name)
	template = template.replace("INSERT_DATA",R2)
	file_R2.write(template)
	file_R2.close()
	template_R2.close()
	
def writeToR2pymolFile(magnet,R2):
	"""
	This will write the same R2 files as above, exept its an new empty file, and there will be no renaming
	"""
	file_R2 = open(ROOT_DIR+"R2_diff_"+magnet+".txt",'w', encoding='utf8')
	for i in R2:
		file_R2.write(i[0]+"\t"+i[1]+"\n")
	file_R2.close()

def calcR2(data):
	"""
	This will make the calculation of R2 diff, which is the absolute value of the difference between the lowset value of the fitted data and the highest.
	There is no error in the fitted data, to get som errors they are taken from the experimental data.
	First the the correct detasets are extracted (info then type from directory) to be fit.
	"""

	fitDataList = []
	for d in data:
		if(d["info"]["type"]=="fit"):
			fitDataList.append(d)
	for fitData in fitDataList:
		
		R2 = ""
		R2_name= "@    xaxis  tick spec "+str(len(fitData["resdata"]))+"\n"
		R2_pymol = []
		for i in range(len(fitData["resdata"])):
				#import pdb; pdb.set_trace()
				
			diff = float(fitData["resdata"][i]["values"][0][1])-float(fitData["resdata"][i]["values"][-1][1])
			errUp,errDown = getExpDataMean(data,fitData["info"]["magnet"],i)
			R2_name+= '@    xaxis  ticklabel '+str(i)+', "'+renameRes(fitData["resdata"][i]["name"])+'"\n@    xaxis  tick major '+str(i)+', '+str(i)+'\n'
			R2 += str(i)+"\t"+str(diff)+"\t"+str(errUp)+"\t"+str(errDown)+"\n"
			R2_pymol.append([fitData["resdata"][i]["name"],str(diff)])
		R2 += "&"
		writeToR2GraceFile(fitData["info"]["magnet"],R2,R2_name)
		writeToR2pymolFile(fitData["info"]["magnet"],R2_pymol)

def writeResToGrace(dataTot):
	plot_dir=ROOT_DIR+"plots/"
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
		shutil.rmtree(RESULT_DIR
		print("Old result directory removed")
	os.mkdir(RESULT_DIR)

def main():
	data = getDataFromFileList()
    
	if len(data)>0:
		if checkData(data):
			createResultFolder()
			calcR2(data)
			writeResToGrace(data)
	else:
		print("No data")

if __name__ == "__main__":
	main()
