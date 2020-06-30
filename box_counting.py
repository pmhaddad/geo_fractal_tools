###############################################
# Script name..: Box-counting
# Created on...: 2015/10/15
# Author.......: Paulo Miguel Haddad Martim
# Purpose......: Perform the box-counting method for the determination of the fractal dimension of point patterns (e.g., mineral deposits) and line patterns
# Use..........: To use this script, import 'Fractal Tools' toolbox file in ArcMap ('FractalTools.tbx')
# Requirements.: Modules os, arcpy
# History......: Modified by Paulo Haddad on 2016/04/26 to refactor code
#              : Modified by Paulo Haddad on 2016/06/08 to: accept line features as input; add created rasters to current data frame
###############################################
# Main input: a shapefile with a point or polyline pattern, the largest size for the box, the number of times box size must be halved, study area
# Main output: a text file with the number of boxes that cover points or lines ['n (delta)'] for each box size ('delta')
# How does this script work?
# It uses the tool 'Point to Raster' or 'Polyline to Raster' to convert the pattern shapefile to a raster
# Raster pixel size is indicated by parameter 'delta' (box size). The first pixel size will correpond to the largest box size
# It counts the number of pixels that cover at least one point or line segment in the generated raster ['n(delta)']
# It repeats the procedure as many times as indicated by parameter 'i' (number of iterations). For each iteration 'delta' is equal to half the previous 'delta'
###############################################

import os, arcpy

# Input shapefile with the point pattern to be analized
input = arcpy.GetParameterAsText(0)
desc_input = arcpy.Describe(input)

# Field used to assign values to the output raster. It can be any field
campo = arcpy.GetParameterAsText(1)

# Set the output directory
output_dir = arcpy.GetParameterAsText(2)

# Set the initial box size ('delta') in meters
delta = int(arcpy.GetParameterAsText(3))

# Set the number of desired iterations. In each iteration, the box side will be halved
i = int(arcpy.GetParameterAsText(4)) - 1

# Set the study area extent using a shapefile
study_area = arcpy.GetParameterAsText(5)
arcpy.env.extent = study_area

# Output text file name that will contain analysis results
file_name = arcpy.GetParameterAsText(6)

contagens = list()
raster_list = list()
while i >= 0:
	
	# The name of the raster generated in each step is its 'delta' value. It is saved in the output directory
	output_raster = os.path.join(output_dir, str(delta) + "m.tif")
	raster_list.append(output_raster)
	if desc_input.shapeType == 'Point':
		arcpy.PointToRaster_conversion(input, campo, output_raster, "MOST_FREQUENT", "", delta)
	if desc_input.shapeType == 'Polyline':
		arcpy.PolylineToRaster_conversion(input, campo, output_raster, "MAXIMUM_LENGTH", "", delta)
	# For each raster generated, extract a tuple with the pair 'delta' and 'n(delta)'
	fc = output_raster
	cursor = arcpy.SearchCursor(fc)
	count = 0
	for row in cursor:
		count = count + row.getValue("Count")
	contagens.append((delta, count))
	
	# Halve boxes sides, and prepare for the next iteration
	delta = delta / 2
	i = i - 1

# Save a text file with the results in the format 'n(delta)' X 'delta'
file = open(file_name, 'w')
file.write("delta n(delta)\n")
for contagem in contagens:
	file.write(str(contagem[0]) + ' ' + str(int(contagem[1])) + '\n')
file.close()

# Insert all created rasters to the current data frame
mxd = arcpy.mapping.MapDocument("CURRENT")
data_frame = arcpy.mapping.ListDataFrames(mxd)[0]
for raster in raster_list:
	result = arcpy.MakeRasterLayer_management(raster, raster.split('\\')[-1])
	layer = result.getOutput(0)
	arcpy.mapping.AddLayer(data_frame, layer, 'AUTO_ARRANGE')
	
arcpy.RefreshActiveView()
arcpy.env.extent = "DEFAULT"