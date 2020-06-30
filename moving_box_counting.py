###############################################
# Script name..: Moving box-counting
# Created on...: 2016/02/09
# Author.......: Paulo Miguel Haddad Martim
# Purpose......: Perform the moving box-counting method for the determination of the fractal dimension of geometrical patterns (points or lines)
# Use..........: To use this script, import 'Fractal Tools' toolbox file in ArcMap ('FractalTools.tbx')
# Requirements.: Modules os, arcpy
# History......: Modified by Paulo Haddad on 2016/04/26 to refactor code
#              : Modified by Paulo Haddad on 2016/06/08 to use points rather than pixels in the analysis
###############################################
# Main input: shapefile with the pattern to be analyzed, largest box size, number of iterations, dislocation for each box counting, shapefile with study area limits
# Main output: a point shapefile. Points are centered in each square where a box-counting was performed. Table will contain analysis results 
# How does this script work?
# It converts the pattern provided to several rasters, one for each box size
# Each raster is then converted to a point shapefile, representing all pixels different from 'NoData'
# It divides the study area into a grid of squares with side provided by the user
# For each square on the grid, it counts the points representing pixels which cointain features of interest for different pixel sizes
# The grid will present some overlap between different squares
# Results for each box-counting execution (box size X number of boxes covering features of interest) are saved on points at each square center
# To ensure that the couting for the largest box is correct, the script uses the second box size and makes sure that all four boxes are empty
# This happens because as the sampling window in dislocated half the box size, it can sample "half pixels" for the largest box size, which induces to error
# For the same reason, dislocation can only be done with intervals equal to half the largest box size, or equal to the largest box size itself
###############################################

import os, arcpy

# This function uses a feature class to determine the extent of the study area, used to limit the analysis
def extents(fc):
	my_extent = arcpy.Describe(fc).extent
	my_extent_w = my_extent.XMin
	my_extent_s = my_extent.YMin
	my_extent_e = my_extent.XMax
	my_extent_n = my_extent.YMax
	return [my_extent_w, my_extent_s, my_extent_e, my_extent_n]

# This function performs the box-counting in a given extent for all grid sizes, represented as point shapefiles
def boxcount (pixel_as_points, id):
	first_pass = True
	cell_size = max_box
	for pixel_as_point in pixel_as_points:
		
		# Collect x,y coordinates for all points representing pixels
		scursor = arcpy.da.SearchCursor(pixel_as_point, 'SHAPE@XY')
		on_list = set()
		for point in scursor:
			x, y = point[0]
			on_list.add((x, y))
		
		# For every point representing a pixel, verifies if it is within the current box
		count = 0
		for point in on_list:
			x, y = point[0], point[1]
			if (x >= b_xmin and x <= b_xmin + max_box) and (y >= b_ymax - max_box and y <= b_ymax):
				count = count + 1
		if first_pass == True:
			if count <> 0: count = 1
			first_pass = False
		
		# Creates a point for each box count, in the center of the box
		with arcpy.da.InsertCursor(output_shape, ["SHAPE@XY", "Id", "box_size", "boxcount"]) as cursor:
			xy = (b_xmin + (max_box / 2), b_ymax - (max_box / 2))
			cursor.insertRow([xy, id, cell_size, count])
		cell_size = cell_size / 2

# Input shapefile with the pattern to be analized (Point or Polyline)
input = arcpy.GetParameterAsText(0)
desc_input = arcpy.Describe(input)

# Field used to assign values to the output raster. It can be any field
fld = arcpy.GetParameterAsText(1)

# Set the output directory for rasters and shapefiles used in the calculations
output_dir = arcpy.GetParameterAsText(2)

# Set output shapefile. It is a point shapefile with analyses results
output_shape = arcpy.GetParameterAsText(3)

# Set maximum box size
max_box = float(arcpy.GetParameterAsText(4))

# Set the number of desired iterations. In each iteration, the box side will be halved
i = int(arcpy.GetParameterAsText(5)) - 1

# Set box deslocation both into x and y axis. Usually, it is ('max_box' / 2)
dislocation = float(arcpy.GetParameterAsText(6))

# Set the study area extent using a shapefile
study_area = arcpy.GetParameterAsText(7)
study_area_limits = extents(study_area)
arcpy.env.extent = ' '.join([str(value) for value in study_area_limits])

raster_list = list()
pix_to_point_list = list()
delta = int(max_box)
while i >= 0:
	
	# The name of the raster generated in each step is its 'delta' value. It is saved in the output directory
	output_raster = os.path.join(output_dir, str(delta) + "m.tif")
	raster_list.append(output_raster)
	if desc_input.shapeType == 'Point':
		arcpy.PointToRaster_conversion(input, fld, output_raster, "MOST_FREQUENT", "", delta)
	if desc_input.shapeType == 'Polyline':
		arcpy.PolylineToRaster_conversion(input, fld, output_raster, "MAXIMUM_LENGTH", "", delta)
	pixel_to_point = arcpy.RasterToPoint_conversion(output_raster, os.path.join(output_dir, str(delta) + "m"))
	pix_to_point_list.append(pixel_to_point)
	delta = delta / 2
	i = i - 1

# Duplicates the input for second largest box in order to compute the box count for the largest box size
pix_to_point_list[0] = pix_to_point_list[1]

# Creates the output point shapefile. The automatically created field ('Id') stores a number that identifies the box where the couting was done
arcpy.CreateFeatureclass_management(os.path.dirname(output_shape), os.path.basename(output_shape), "POINT", spatial_reference = study_area)

# Stores the box size for a given count, in a given box and box size
arcpy.AddField_management(output_shape, "box_size", "DOUBLE")

# Stores the box count for a given count, in a given box and box size
arcpy.AddField_management(output_shape, "boxcount", "DOUBLE")

# Starts in the upper left corner
b_xmin = study_area_limits[0]
b_ymax = study_area_limits[3]

# Box ID
ID = 0

# While the box is inside the study area (in the y axis)
while round(b_ymax - max_box) >= round(study_area_limits[1]):
	
	# While the box is inside the study area (in the x axis)
	while round(b_xmin + max_box) <= round(study_area_limits[2]):
		ID = ID + 1
		boxcount(pix_to_point_list, ID)
		b_xmin = b_xmin + dislocation # Move box to the east
	b_ymax = b_ymax - dislocation # Move box to the south
	b_xmin = study_area_limits[0] # Return the box to the west extremity, to start to count a new row of boxes

# Set the geoprocessing extent back to default
arcpy.env.extent = "DEFAULT"