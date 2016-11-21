import arcpy
arcpy.env.overwriteOutput = True
inFCs = arcpy.GetParameter(0)
#inFCs = [r'D:\Clients\CPTB\160926_AGOL_Data_Extract\New_Data\Utilities.gdb\Electricity_Lines']
areaFC = r'E:\Clients\CPTB\160926_AGOL_Data_Extract\New_Data\Park_Operations.gdb\Area_Name'
areaLyr = arcpy.MakeFeatureLayer_management(areaFC, 'areaLyr')
count = 0
if len(inFCs) > 0:
    for FC in inFCs:
        desc = arcpy.Describe(FC)
        #arcpy.AddMessage('******* ' + desc.name + ' *******')
        with arcpy.da.Editor(desc.path) as edit:
            uCur = arcpy.da.UpdateCursor(FC, ["SHAPE@", 'GlobalID', 'Area'])
            for uRow in uCur:
                count += 1
                #arcpy.AddMessage('{0}: {1}'.format(count, uRow[1]))
                areaNames = []
                geomObj, assetGID, area = uRow
                selectLyr = arcpy.SelectLayerByLocation_management('areaLyr', "INTERSECT", geomObj, "", "NEW_SELECTION")[0]
                sCur = arcpy.da.SearchCursor(selectLyr, ["SHAPE@", 'AreaName'])
                for sRow in sCur:
                    areaNames.append(sRow[1])
                    areaString = ', '.join(areaNames)
                    arcpy.AddMessage(areaString)
                    uRow[2] = areaString
                    #arcpy.AddMessage(areaString)
                try:
                    uCur.updateRow(uRow)
                except:
                    arcpy.AddMessage('Trouble with ' + areaString)
