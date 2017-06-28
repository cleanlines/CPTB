# Project: CPTB 
# File: CPTBExcelChart.py
# Created: 25/11/2016 4:01 PM
# Author: FS Hand

# create excel charts then add to AGOL
from xlsxwriter import workbook

from Base import Base
from arcresthelper import securityhandlerhelper
from arcrest.agol.services import FeatureService
import xlsxwriter
from Utility import Utility
import datetime
from arcrest.manageorg import Administration
from arcrest.manageorg import ItemParameter
from arcrestpatches import PatchedUser
import string


class CPTBExcelChart(Base):
    def __init__(self,json_object):
        super(CPTBExcelChart, self).__init__()
        self._json_object = json_object
        self.workbook = xlsxwriter.Workbook("{0}_{1}.xlsx".format(Utility.some_date_filename(),json_object["name"]),{'default_date_format': 'dd/mm/yyyy hh:mm'})
        self._domain_lookup = {}

    def __str__(self):
        return self.workbook.filename
        # return "Server Admin Url:{0}, Sever has token:{1}".format(self._server_rest, str(self.__token is not None))

    def __rep__(self):
        return self.workbook.filename
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
                self._domain_lookup[layer.name] = {}
                for f in layer.fields:
                    if f["domain"] is not None:
                        self._domain_lookup[layer.name][f["name"]] = f["domain"]

                result = layer.query(out_fields="*", resultType='standard',returnGeometry=True)
                self._process_features(result,layer.name)
        except Exception as e:
            self._config.log.do_message(e.message,"err")
        finally:
            self.workbook.close()

    def _process_features(self,result,name):
        worksheet =  self.workbook.add_worksheet(name)
        bold = self.workbook.add_format({'bold': 1})
        self._config.log.do_message(str(result.fields),"info")
        if not result.features: return
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
            row_number +=1
        self._add_graphs(worksheet,row_number,sorted_features,result.geometryType)


    def _add_graphs(self,worksheet,row,features,geomtype):
        #TODO: you can get the domain vals from the result object
        # TODO: columns past z - get the division to see which one we are AA, AB etc then the modulus for the actual column like AC etc then +1 on the second for the second column
        reports = {}
        report_labels = {} # think about this as different graphs will have different y axis label
        cols = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        for feature in features:
            # self._generate_condition_chart(feature,reports,report_labels,geomtype)
            self._chart_by_geom_or_count("conditiongrades")(feature, reports, report_labels, geomtype)
            self._generate_renewal_chart(feature, reports, report_labels)
            self._chart_by_geom_or_count("assettype")(feature,reports,report_labels,geomtype)
            self._chart_by_geom_or_count("materialtype")(feature, reports, report_labels, geomtype)

        self._add_no_count_domain_values(worksheet.name,reports)
        current_col = 1
        insert_chart_col = 1
        for k,v in reports.items():
            sorted_keys = sorted(v.keys())
            sorted_vals = []
            for sk in sorted_keys:
                sorted_vals += [v[sk]]

            data = [sorted_keys,sorted_vals]
            worksheet.write_column(cols[current_col] + str(row + 2), data[0])
            worksheet.write_column(cols[current_col+1] + str(row + 2), data[1])
            chart = self.workbook.add_chart({'type': 'column'})
            worksheet.insert_chart(row + 9,insert_chart_col , chart)

            chart.add_series({'values': "='{0}'!${1}${2}:${3}${4}".format(worksheet.name, cols[current_col+1],str(row + 2),cols[current_col+1], str(row + 1 +len(sorted_keys))),
                              'categories':"'{0}'!${1}${2}:${3}${4}".format(worksheet.name,cols[current_col], str(row + 2),cols[current_col], str(row + 1 + len(sorted_keys))),
                              'name':report_labels[k]["title"]})

            chart.set_y_axis({"name":report_labels[k]["yaxis"]})
            current_col +=3
            insert_chart_col += 9

    def _add_no_count_domain_values(self,name,reports):
        try:
            domains = self._domain_lookup[name]
            if domains:
                for k,v in reports.items():
                    a_report = reports[k]
                    fd = self._config.reports["reportset"][k]
                    if not isinstance(fd["one"], basestring):
                        if fd["one"][1] in domains:
                            this_domain = domains[fd["one"][1]]
                            for coded_vals in this_domain['codedValues']:
                                graph_val = fd["one"][0] + " " + str(coded_vals['code'])
                                print graph_val," ",a_report
                                if graph_val not in a_report:
                                    a_report[graph_val.strip()] = 0
                            sorted(a_report)
        except Exception as e:
            print e.message

    def _chart_by_geom_or_count(self,lookup):
        def _chart(feature,reports,report_labels,geomtype):
            a_report = self._config.reports["reportset"][lookup]
            report_labels[lookup] = {"title": self._config.reports["reportset"][lookup]["title"]}

            if lookup not in reports.keys():
                reports[lookup] = {}

            graph_val = feature.get_value(a_report["one"][1])
            if not graph_val:
                graph_val = "None"
            else:
                graph_val = a_report["one"][0] + " " + str(graph_val)

            if geomtype == "esriGeometryPoint" or geomtype == "esriGeometryMultipoint":  # will we have multippoints?
                if graph_val not in reports[lookup].keys():
                    reports[lookup][graph_val] = 1
                else:
                    reports[lookup][graph_val] += 1
                report_labels[lookup]["yaxis"] = "Total Count"
            else:
                n = self._get_geometry_value(feature)(geomtype)
                if graph_val not in reports[lookup].keys():
                    reports[lookup][graph_val] = n
                else:
                    reports[lookup][graph_val] += n
                report_labels[lookup]["yaxis"] = "Total " + str(self._geometry_column_name(geomtype)[0])
        return _chart

    def _generate_condition_chart(self,feature,reports,report_labels,geomtype):
        a_report = self._config.reports["reportset"]["conditiongrades"]
        report_labels["conditiongrades"] = {"title":self._config.reports["reportset"]["conditiongrades"]["title"]}

        if "conditiongrades" not in reports.keys():
            reports["conditiongrades"] = {}

        graph_val = feature.get_value(a_report["one"][1])
        if not graph_val:
            graph_val = "None"
        else:
            graph_val = a_report["one"][0] + " " + str(graph_val)

        if geomtype == "esriGeometryPoint" or geomtype == "esriGeometryMultipoint":  # will we have multippoints?
            if graph_val not in reports["conditiongrades"].keys():
                reports["conditiongrades"][graph_val] = 1
            else:
                reports["conditiongrades"][graph_val] += 1
            report_labels["conditiongrades"]["yaxis"] = "Total Count"
        else:
            n = self._get_geometry_value(feature)(geomtype)
            if graph_val not in reports["conditiongrades"].keys():
                reports["conditiongrades"][graph_val] = n
            else:
                reports["conditiongrades"][graph_val] += n
            report_labels["conditiongrades"]["yaxis"] = "Total " +str(self._geometry_column_name(geomtype)[0])

    def _generate_renewal_chart(self,feature, reports, report_labels):
        a_report = self._config.reports["reportset"]["totalrenewals"]
        report_labels["totalrenewals"] = {"yaxis":"Total Cost","title":self._config.reports["reportset"]["totalrenewals"]["title"]}
        if "totalrenewals" not in reports.keys():
            reports["totalrenewals"] = {}
        graph_val = feature.get_value(a_report["one"])
        if not graph_val:
            yr = "None"
        else:
            yr = self._return_date_value(graph_val).year

        cost  = feature.get_value(a_report["two"])
        if not cost:
            cost = 0

        if yr not in reports["totalrenewals"].keys():
            reports["totalrenewals"][yr] = cost
        else:
            reports["totalrenewals"][yr] += cost

    def _upload_to_arcgis_online(self):
        token = securityhandlerhelper.securityhandlerhelper(self._config.agolconfig)
        admin = Administration(self._config.agolconfig["org_url"], token.securityhandler)
        content = admin.content
        user = content.users.user()
        patchedUser = PatchedUser(url=user.root, securityHandler= token.securityhandler,initalize=True)
        item_params = ItemParameter()
        item_params.title = "XLSX Report" +Utility.get_file_name(self.workbook.filename)
        item_params.type = "Microsoft Excel"
        item_params.tags = "XLSX,Report"

        possible_folder = [f["id"]for f in user.folders if f["title"] == self._config.reports["reportfolder"]]
        if possible_folder:
            folder = possible_folder[0]
        else:
            folder = None

        patchedUser.patchedAddItem(filePath=self.workbook.filename, itemParameters=item_params,folder=folder)

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
            try:
                self._config.log.do_message("Value:"+str(some_value),"info")
            except Exception as e:
                self._config.log.do_message(e.message,"error")
                self._config.log.do_message("Value:" + some_value.encode('utf-8') + " - GOOD", "info")
                printable = set(string.printable)
                filter(lambda x: x in printable, some_value)
                self._config.log.do_message("Updated: "+ some_value, "info")

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






