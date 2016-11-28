# Project: CPTB 
# File: CPTBExcelChart.py
# Created: 25/11/2016 4:01 PM
# Author: FS Hand

# create excel charts then add to AGOL - yeah!
from xlsxwriter import workbook

from Base import Base
from arcresthelper import securityhandlerhelper
from arcrest.agol.services import FeatureService
import xlsxwriter
from Utility import Utility
import datetime



class CPTBExcelChart(Base):
    def __init__(self,json_object):
        super(CPTBExcelChart, self).__init__()
        self._json_object = json_object
        self.workbook = xlsxwriter.Workbook(Utility.some_filename()+".xlsx",{'default_date_format': 'dd/mm/yyyy hh:mm'})
        print self.workbook.filename




    def __str__(self):
        return "chart object"
        # return "Server Admin Url:{0}, Sever has token:{1}".format(self._server_rest, str(self.__token is not None))

    def __rep__(self):
        return "chart object"
        # return "Server Admin Url:{0}, Sever has token:{1}".format(self._server_rest, str(self.__token is not None))

    def __enter__(self):
        return self

    def __exit__(self, some_type, value, traceback):
        try:
            if not self.workbook.fileclosed:
                self.workbook.close()
        except:
            pass
        # cleanup if required


    def do_reporting(self):
        self._create_report_for_service()
        self._upload_to_arcgis_online()

    def _create_report_for_service(self):
        try:
            token = securityhandlerhelper.securityhandlerhelper(self._config.agolconfig)
            fs = FeatureService(url=self._json_object["url"], securityHandler=token.securityhandler, initialize=True)
            # get some config lookup for a particular layer
            for layer in fs.layers:
                result = layer.query(out_fields="*", resultType='standard',returnGeometry=True)
                self._process_features(result,layer.name)
        except Exception as e:
            self._config.log.do_message(e.message,"err")
        finally:
            self.workbook.close()

    def _process_features(self,result,name):
        worksheet =  self.workbook.add_worksheet(name)
        bold = self.workbook.add_format({'bold': 1})
        headings = [fd["alias"] for fd in result.fields if fd["name"].upper() not in self._config.reports["skipfields"]]+self._geometry_column_name(result.geometryType)
        worksheet.write_row('A1',headings,bold)
        row_number = 1
        if self._config.reports["sortfield"] in [ fd["name"] for fd in result.fields]:
            sorted_features = sorted(result.features,key=lambda rec:rec.get_value(self._config.reports["sortfield"]))
        else:
            sorted_features = result.features

        for feature in sorted_features:
            # row_data = [feature.get_value(fd["name"]) for fd in result.fields ]
            col_number = 0
            for fd in result.fields:
                if fd["name"].upper() in self._config.reports["skipfields"]: continue
                self._config.log.do_message("Field:" + str(fd["name"]), "info")
                write_fd_val = self._write_value_function(fd["type"])
                write_fd_val(worksheet,row_number,col_number,feature.get_value(fd["name"]))
                col_number +=1
            # add in the geom
            write_fd_val = self._write_value_function("esriFieldTypeDouble") # use the result geom type for consistency
            write_fd_val(worksheet, row_number, col_number,self._get_geometry_value(feature)(result.geometryType))
            # worksheet.write_row(row_number,0,row_data)
            row_number +=1
        self._add_graphs(worksheet,row_number,sorted_features,result.geometryType)


    def _add_graphs(self,worksheet,row,features,geomtype):

        data = [[1,2,3,4,5],
                [2,4,6,8,10],
                [3,6,9,12,15]] # same as pdf row data in cols

        # worksheet.write_column('A'+str(row+2), data[0])
        # worksheet.write_column('B'+str(row+2), data[1])
        # worksheet.write_column('C'+str(row+2), data[2])
        #
        # chart.add_series({'values': '={0}!$A${1}:$A${2}'.format(worksheet.name,str(row+2),str(row+7))})
        # chart.add_series({'values': '={0}!$B${1}:$B${2}'.format(worksheet.name,str(row+2),str(row+7))})
        # chart.add_series({'values': '={0}!$C${1}:$C${2}'.format(worksheet.name,str(row+2),str(row+7))})


        #TODO: you can get the domain vals from the result object

        reports = {}
        report_labels = {} # think about this as different graphs will have different y axis label


        for feature in features:
            for a_report in self._config.reports["reportset"]:
                print a_report
                if a_report["Name"] not in reports.keys():
                    reports[a_report["Name"]] = {}

                graph_val = feature.get_value(a_report["One"][1])
                if not graph_val:
                    graph_val = "None"
                else:
                    graph_val = a_report["One"][0]+" "+str(graph_val)

                if geomtype == "esriGeometryPoint" or geomtype == "esriGeometryMultipoint": # will we have multippoints?
                    if graph_val not in  reports[a_report["Name"]].keys():
                        reports[a_report["Name"]][graph_val] = 1
                    else:
                        reports[a_report["Name"]][graph_val] += 1
                    reports[a_report["Name"]]["yaxis"] = "Count"
                else:
                    n = self._get_geometry_value(feature)(geomtype)
                    if graph_val not in  reports[a_report["Name"]].keys():
                        reports[a_report["Name"]][graph_val] = n
                    else:
                        reports[a_report["Name"]][graph_val] += n

        print reports
        # we have all the raw data we need
        for k,v in reports.items():
            print k # graph title

            sorted_keys = sorted(v.keys())
            sorted_vals = []
            for sk in sorted_keys:
                sorted_vals += [v[sk]]

            data = [sorted_keys,sorted_vals] #TODO: build it dynmically
            worksheet.write_column('A' + str(row + 2), data[0])
            worksheet.write_column('B' + str(row + 2), data[1])
            chart = self.workbook.add_chart({'type': 'column'})
            worksheet.insert_chart(row + 9, 1, chart)

            chart.add_series({'values': '={0}!$B${1}:$B${2}'.format(worksheet.name, str(row + 2), str(row + 2 +len(sorted_keys))),
                              'categories':'{0}!$A${1}:$A${2}'.format(worksheet.name, str(row + 2), str(row + 2 + len(sorted_keys))),
                              'name':k})

            chart.set_y_axis({"name":"Total " + str(self._geometry_column_name(geomtype)[0])}) # fix this bug see error

        print 'whip'








        #




        # Insert the chart into the worksheet.

        #["renewal_year","count"],


    def _upload_to_arcgis_online(self):
        pass #TODO: implement me


    def _geometry_column_name(self,geometry_type):
        vals = {"esriGeometryPoint":[],
        "esriGeometryMultipoint":[],
        "esriGeometryPolyline":["Length"],
        "esriGeometryPolygon":["Area"],
        "esriGeometryEnvelope":["Area"]}
        return vals[geometry_type]

    def _get_geometry_value(self,feature):
        def _get_geom(geom_type):
            vals = {"esriGeometryPoint": lambda: None,
                    "esriGeometryMultipoint": lambda: None,
                    "esriGeometryPolyline": lambda: feature.geometry.length,
                    "esriGeometryPolygon": lambda: feature.geometry.area,
                    "esriGeometryEnvelope": lambda: feature.geometry.area}
            return vals[geom_type]()
        return _get_geom

    def _write_value_function(self, type):
        def _write_value(workbook,row,col,some_value):
            self._config.log.do_message("Value:"+str(some_value),"info")
            write_row_value = {"esriFieldTypeOID": lambda: workbook.write_number(row,col,some_value),
                                   "esriFieldTypeGlobalID": lambda:workbook.write_string(row,col,some_value),
                                   "esriFieldTypeString": lambda:workbook.write_string(row,col,some_value),
                                   "esriFieldTypeDate": lambda: workbook.write_datetime(row,col,self._return_date_value(some_value)),
                                   "esriFieldTypeDouble": lambda:workbook.write_number(row,col,some_value),
                                   "esriFieldTypeInteger": lambda:workbook.write_number(row,col,some_value)
                                }
            if some_value:
                write_row_value[type]()
            else:
                workbook.write_blank(row,col,some_value)
        return _write_value

    def _return_date_value(self,milliseconds):
        if milliseconds > 0:
            return datetime.datetime.fromtimestamp(milliseconds / 1000.0)
        else:
            return datetime.datetime(1970, 1, 1) + datetime.timedelta(milliseconds=milliseconds)






