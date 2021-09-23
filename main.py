import os
import sys
import numpy as np
import re
import shutil

ROOT_DIR="/Users/xlidje/Desktop/Courses/Python/chemex2grace/"
DATA_DIR=ROOT_DIR+"data/"

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
	file = open(ROOT_DIR+"data/"+fileName,'r', encoding='utf8')
	currentRes=""
	values=[]
	firstline =True
	for l in file:
		str =l.strip()
		r = re.match(r"\[([A-Za-z0-9_]+)-([A-Za-z0-9_]+)\]",str)

		if(r):
			if(len(values)>0):
				dataset={}
				dataset["name"]=currentRes
				v=[]
				for i in values:
					if  len(i)>1:
						v.append(i)
				dataset["values"]=v

				values.clear()
				data.append(dataset)

			currentRes=r.group(1).strip()
		elif(str.startswith("#")):
			continue
		elif type == "fit":
			values.append(str.split(" =    "))
		elif type == "exp":
			if len(str.split())>1:
				values.append([str.split()[0],str.split()[2],str.split()[3],str.split()[4]])
		firstline=False
	
	file.close()

	data_sorted = sorted(data,key=lambda x: x["name"][1:])

	return data_sorted

def getDataFromFileList():
	"""
	Reads all data from each file to one big data set ordered as:
	[[info],[[residue],[data]]]
	"""
	data = []
	fileList = os.listdir(ROOT_DIR+"data/")
	print("Program started")
	for f in fileList:
		if "cpmg" not in f :
			continue
		d1 ={}
		d1["info"]= getFileInfo(f)
		
		if not d1["info"]["type"]  =="fit" and not d1["info"]["type"] == "exp":
			continue
		else:
			print("Data file included: "+f)
		d1["resdata"]=readExpFile(f,d1["info"]["type"])
		
		
		data.append(d1)

	return data
	
def calcR2(data):
	fitDataList = []
	for d in data:
		if(d["info"]["type"]=="fit"):
			fitDataList.append(d)
	R2 = []
	for fitData in fitDataList:
		file_R2 = open(ROOT_DIR+"data/R2_diff_"+fitData["info"]["magnet"],'w', encoding='utf8')

		for i in range(len(fitData["resdata"])):
			if(fitData["resdata"][i]["name"]==fitData["resdata"][i]["name"]):
			
				diff = float(fitData["resdata"][i]["values"][0][1])-float(fitData["resdata"][i]["values"][-1][1])
				file_R2.write('%8s %10f\n' % (fitData["resdata"][i]["name"],diff))
				R2.append([fitData["resdata"][i]["name"],diff])
		file_R2.close()
		
def writeResToGrace(dataTot):
	plot_dir=DATA_DIR+"plots/"
	if os.path.exists(plot_dir):
		shutil.rmtree(plot_dir)
	os.mkdir(plot_dir)
	
	for i in range(len(dataTot[0]["resdata"])):
		resName = dataTot[0]["resdata"][i]["name"]
		res_file = open(plot_dir+resName,"a")
		for data in dataTot:
			for l in data["resdata"][i]["values"]:
				res_file.write(l[0]+"\t"+l[1]+"\n")
			
			
		
		


	
def checkData(dataTot):
	length_str = ""
	length = []
	for data in dataTot:
		length.append(len(data["resdata"]))
		length_str +=str(len(data["resdata"]))+" "

	m = min(length)
	everyMatch = True
	for data in dataTot:
		for i in range(m):
			if  not dataTot[0]["resdata"][i]["name"] == data["resdata"][i]["name"]:
				everyMatch = False
	if everyMatch:
		print("All data sets are equal residues with lengths of: "+ length_str)
	return everyMatch
	
    
def main():
	data = getDataFromFileList()
	if len(data)>0:
		if checkData(data):
			calcR2(data)
			writeResToGrace(data)
	else:
		print("No data")
	
			


if __name__ == "__main__":
	main()
