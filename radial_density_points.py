###############################################
# Script name..: Radial-density for points
# Created on...: 2016/02/03
# Author.......: Paulo Miguel Haddad Martim
# Purpose......: Perform the radial-density method for the determination of the fractal dimension of point patterns (e.g., mineral deposits)
# Use..........: To use this script, import 'Fractal Tools' toolbox file in ArcMap ('FractalTools.tbx')
# Requirements.: Modules os, arcpy, string
# History......: Modified by Paulo Haddad on 2016/04/26 to refactor code
#              : Modified by Paulo Haddad on 2016/06/08 to: change input format; limit the analysis by a study area; add more fields to output
#              : Modified by Paulo Haddad on 2016/08/03 to: add a txt file export with the attribute table of the results shapefile
###############################################
# Main input: a shapefile with the point pattern to be analyzed, an initial radius and a study area
# Main output: a polygon shapefile. Attribute table contains the total area and total point density for each radius calculated
# How does this script work?
# It uses the tool 'Buffer_analysis' on the radius provided by the user to create a shapefile with circles around each and every point, removing overlap areas
# The radius lenght is then doubled and analysis repeated. When the hole study area is covered by the adjointing circles, the analysis is haulted
# It createas a single shapefile merging all shapefiles generated earlier, and then performs density calculations
###############################################

import os
import string

import arcpy

# Input shapefile with the point pattern to be analized
input_points = arcpy.GetParameterAsText(0)

# Set the output directory
output_dir = arcpy.GetParameterAsText(1)

# Set the output shapefile name
file_name = arcpy.GetParameterAsText(2)

# Set the initial radius
threshold = arcpy.GetParameterAsText(3)

# Set the study area limits
study_area = arcpy.GetParameterAsText(4)
arcpy.MakeFeatureLayer_management(study_area, 'study_area_layer')

# Output text file name that will contain analysis results
txt_name = arcpy.GetParameterAsText(5)

# Store generated shapefiles names and threshold values
outputs_to_merge = list()
split_threshold = list()

letter = string.ascii_lowercase
index = 0

while True:
    # The name of the shapefile generated in each step is its threshold value, preceeded by...
    # ...a letter to facilitate ordering in ArcCatalog
    output_shp = os.path.join(output_dir, letter[index] + '_' + str(threshold) + 'm.shp')
    outputs_to_merge.append(output_shp)
    arcpy.Buffer_analysis(input_points, output_shp, str(threshold) + ' Meters', dissolve_option='ALL', method='PLANAR')
    split_threshold.append(int(threshold))

    # Checks if the buffer created already covers the hole study area
    arcpy.SelectLayerByLocation_management('study_area_layer', 'COMPLETELY_WITHIN', output_shp)
    shape_description = arcpy.Describe('study_area_layer')  # Creates a 'Describe object'
    if shape_description.FIDSet != '':
        break

    # If the buffer do not cover the hole study area, the threshold is doubled and analysis proceed
    threshold = 2 * int(threshold)
    index = index + 1

# Merge the shapefiles for each radius in one single shapefile
arcpy.Merge_management(outputs_to_merge, file_name)

# Create field 'radius' to store each radius used (in meters)
arcpy.AddField_management(file_name, 'radius', 'FLOAT')
with arcpy.da.UpdateCursor(file_name, ['radius']) as cursor:
    i = 0
    for row in cursor:
        row[0] = split_threshold[i]
        cursor.updateRow(row)
        i = i + 1

# To facilitate further analysis, add a field with radius in kilometers
arcpy.AddField_management(file_name, 'rdius_km', 'FLOAT')
arcpy.CalculateField_management(file_name, 'rdius_km', 'float(!radius!) / 1000', 'PYTHON_9.3')

# Calculate the total area for each radius used
arcpy.AddGeometryAttributes_management(file_name, 'AREA_GEODESIC', Area_Unit='SQUARE_METERS')

# Create field 'n_points' to store the number of points used, and use 'Calculate Field' tool to obtain this number
arcpy.AddField_management(file_name, 'n_points', 'SHORT')
arcpy.CalculateField_management(file_name, 'n_points', arcpy.GetCount_management(input_points), 'PYTHON_9.3')

# Create field 'rad_dens' to store the radial density for each radius, and use...
# ...'Calculate Field' tool to obtain this number (result in square km)
arcpy.AddField_management(file_name, 'rad_dens', 'FLOAT')
arcpy.CalculateField_management(file_name, 'rad_dens', '(float(!n_points!) / !AREA_GEO!) * 1000000', 'PYTHON_9.3')

# Save a text file with the attribute table of the result shapefile
arcpy.ExportXYv_stats(file_name, ['RADIUS', 'RDIUS_KM', 'AREA_GEO', 'N_POINTS', 'RAD_DENS'], 'SEMI-COLON', txt_name, 'ADD_FIELD_NAMES')
