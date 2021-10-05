This program is used to transform and rearrange data output from a fitting program called Chemex that 
uses NMR data.
The data created from Chemex is consisting of two different files (*.exp, *.fit) for each magnet, usually two. 
In each of these files datapoints for each atom that exist from the NMR data, for the .exp files the data is set up as:

[ATOMNAME]
Delay	R2	R2_error_Up	R2_error_down

For the .fit file:

[ATOMNAME]
Delay   R2 

What this program does is to split the data from each file to:
1. 	All data (2 .fit, 2 .exp) in a file named ATOMNAME, the data file will have a format of grace
2. 	R2 difference, the absolute value of the difference of the first R2 and the last R2 of the .fit file.
	All these R2 differences will be combined in two different files, one is a grace format, and the other
	is a simple .txt files set as:
	
	ATOMNAME R2diff

Python used:
Python 3.9.7

Packages:
sys,os,re,shutil,statistics

Run with:
python main.py


