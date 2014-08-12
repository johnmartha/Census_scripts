'''----------------------------------------------------------------------------------
 Tool Name:   Cost Distance Matrix
 Source Name: CostDistanceMatrix.py
 Version:     ArcGIS 10
 Author:      ESRI, Inc.
 Required Arguments:
              Input Features (feature class or feature layer)
              Near Features (feature class or feature layer)
              Cost Raster
              Output Table
 Description: Creates a new table that contains the cost distance along a least cost path
              from every feature in the Input Features to every feature in the Near Features.
----------------------------------------------------------------------------------'''

#import system modules
import arcpy
import os
import sys

#main function, all functions run in CostDistanceMatrix
def CostDistanceMatrix(input, near, cost, outtable):
    #set geoprocessing environments
    arcpy.env.overwriteOutput = True
    arcpy.env.workspace = os.path.join(os.path.dirname(os.getcwd()), "data")
    arcpy.env.scratchWorkspace = os.path.join(os.path.dirname(os.getcwd()), "data", "scratch")

    #check for Spatial Analyst extension
    if arcpy.CheckExtension("Spatial").lower() == "available":
        arcpy.CheckOutExtension("Spatial")
    else:
        arcpy.AddError("Spatial Analyst extension is not available. Tool cannot be used.")
        sys.exit()

    #calculate cost distance paths between input and near features
    matrix = CostPathProcess(input, near, cost)

    #create output table and write values to table
    CreateOutput(matrix, outtable)

#calculate cost distance paths between input and near features
def CostPathProcess(input, near, cost):
    #get the OID and Shape field names of the input and near features
    inputOIDname = arcpy.Describe(input).OIDFieldName #input features OID field
    nearOIDname = arcpy.Describe(near).OIDFieldName #near features OID field
    inputShapename = arcpy.Describe(input).ShapeFieldName #input features shape field
    nearShapename = arcpy.Describe(near).ShapeFieldName #near features shape field

    #create matrix to hold all cost values
    matrix = []
    #create variable to keep track of iterations
    i = 0

    inputcur = arcpy.SearchCursor(input)

    try:
        #start loop to go through each input feature
        for inputFeature in inputcur:
            inputOID = inputFeature.getValue(inputOIDname)
            inputShape = inputFeature.getValue(inputShapename)
            #start loop to go through each near feature
            nearcur = arcpy.SearchCursor(near)
            for nearFeature in nearcur:
                nearOID = nearFeature.getValue(nearOIDname)
                nearShape = nearFeature.getValue(nearShapename)

                #run Cost Path processing to get cost distance
                print "Calculating path between: %s & %s" % (str(inputOID), str(nearOID))
                arcpy.extent = "MAXOF"
                #only run cost distance on the first iteration through near features
                if i == 0:
                    #run Cost Distance tool
                    costdist = arcpy.sa.CostDistance(inputShape, cost, "", os.path.join(arcpy.env.scratchWorkspace, "costback"))
                #run Cost Path tool
                costpath = arcpy.sa.CostPath(nearShape, costdist, os.path.join(arcpy.env.scratchWorkspace, "costback"), "EACH_CELL")
                #reset extent
                arcpy.extent = ""

                #crack open the cost path raster to get the value
                costpathcur = arcpy.SearchCursor(costpath, "VALUE > 1")
                try:
                    for row in costpathcur:
                        pathValue = row.getValue("PATHCOST")
                except:
                    raise
                finally:
                    if costpathcur:
                        del costpathcur

                matrix.append([inputOID, nearOID, pathValue])
                i += 1
            #set iteration back to 0 after iterating through all near features for a single input feature
            i = 0
    except:
        raise
    finally:
        if inputcur:
            del inputcur
        if nearcur:
            del nearcur

    #return matrix of cost distance values as list of lists
    return matrix

#create output table and write values to table
def CreateOutput(matrix, outtable):
    #start here!

#run the script
if __name__ == '__main__':
    #set tool inputs
    input = "Trailheads.shp"
    near = "Campsites.shp"
    cost = "slope"
    outtable = os.path.join(os.path.dirname(os.getcwd()), "data", "CostDistanceMatrix.dbf")

    CostDistanceMatrix(input, near, cost, outtable)
    print "Finished!"
