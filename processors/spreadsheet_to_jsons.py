import logging
import json
import requests
import time
import field_convertors

if __name__ == "__main__":
    inp,out,key,sheet = sys.argv[1:4]
    processor = spreadsheet_to_jsons().process(inp,out,key,sheet)

class spreadsheet_to_jsons(object):
    def process(self,input,output,key="",sheet=None,num_cols=2,convertors={},
                spreadsheet_name_key=None,spreadsheet_index_key=None):

        if sheet is None:
            sheets = [ None ]
        else:
            if type(sheet) is str or type(sheet) is unicode:
                sheets = [ sheet ]
            else:
                sheets = sheet
        out = None
        for sheet in sheets:
            sheetp = "sheet=%s&" % sheet if sheet is not None else ""
            columns = ",".join([ chr(65+i) for i in range(num_cols) ])
            params = (key,sheetp,columns)
            URL="https://docs.google.com/a/open-budget.org.il/spreadsheets/d/%s/gviz/tq?%stq=select+%s&tqx=reqId:1;out:json;+responseHandler:x" % params
            print URL
            retries = 3
            while retries > 0:
                try:
                    user_agent = {'User-agent': 'Mozilla/5.0'}
                    data = requests.get(URL,headers=user_agent) # remove JavaScript handler
                    print data
                    data = data.text[2:-2]
                    break
                except Exception,e:
                    logging.error("Failed to open url, retries=%d (%s)" % (retries, str(e)))
                time.sleep(10)
                retries = retries - 1
                assert(retries > 0)
            data = json.loads(data)

            header = [x['label'] for x in data['table']['cols']]
            start=0
            if list(set(header))[0] == "":
                header = [x['v'] if x is not None else None for x in data['table']['rows'][0]['c']]
                start = 1
            rows = [[x['v'] if x is not None else None for x in data['table']['rows'][i]['c']] for i in range(start,len(data['table']['rows']))]

            _convertors = dict([ (h, field_convertors.__dict__[convertors.get(h,'id')]) for h in header ])
            rows = [ dict([(k,_convertors[k](v)) for k,v in zip(header,row)]) for row in rows ]
            if spreadsheet_name_key is not None and sheet is not None:
                for row in rows:
                    row[spreadsheet_name_key] = sheet
            if spreadsheet_index_key is not None:
                for i,row in enumerate(rows):
                    row[spreadsheet_index_key] = i
            if len(rows) > 0 and out is None:
                out = file(output,'w')
            for row in rows:
                out.write(json.dumps(row,sort_keys=True)+"\n")
