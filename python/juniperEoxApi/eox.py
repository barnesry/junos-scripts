#! venv/bin/python

# Juniper Documentation : https://jnprprod.devportal-aw-us.webmethods.io/portal/apis
#
# This script takes as input an excel file as input which expects a header row and one of these headers must 
# match 'Part Number' which is then stripped out and fed into the Juniper EoX API to build a corresponding 
# table. 
#
# Output options are either in the original Juniper format (screen) or to an alternate format (excel)
#
# Screen output is tab separated and should be copy/pasteable directly into excel for further adjustment
# Excel format currently adheres to a specific format and is translated at export to this format.
#
# Example:
# python3 eox.py --inputfile input/eol_sku_list.xlsx --outputfile eol_result.xlsx --outformat screen
#
# barnesry@ 2023-Jan-30
#


import os
import requests
from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session
import datetime
from random import randrange
import json
import argparse
from pandas import DataFrame, read_csv
import pandas as pd

# allows us to build our web query
from jinja2 import Environment, PackageLoader, select_autoescape
env = Environment(
    loader=PackageLoader("eox"),
    autoescape=select_autoescape()
)



class EoxApi():
    def __init__(self):
        self.prodEoxApiBaseUrl = "https://apigw.juniper.net/css-eoxapi/1.0"
        self.prodEoxApiAuthUrl = "https://apigw.juniper.net/invoke/pub.apigateway.oauth2/getAccessToken"
        self.random_range = 10
        
        ## Set these from your environment variables loaded by your favorite shell rc file
        ## so we don't store credentials in our script
        self.app_id = os.environ['EOX_APP_ID']
        self.customer_source_id = os.environ['EOX_CUSTOMER_SOURCE_ID']
        self.api_client_id = os.environ['EOX_PROD_API_CLIENT_ID']
        self.api_client_secret = os.environ['EOX_PROD_API_CLIENT_SECRET']
        

        self.api_map = {'queryeoxproduct' : f"https://{self.prodEoxApiBaseUrl}/css-eoxapi/1.0/queryeoxproduct",
                        'queryeoxsoftware' : f"https://{self.prodEoxApiBaseUrl}/css-eoxapi/1.0/queryeoxsoftware",
                        'geteoxlov' : f"https://{self.prodEoxApiBaseUrl}/css-eoxapi/1.0/geteoxlov"}
                       
    def auth(self):
        # check that we have appropriate auth credentials available
        if self.api_client_id and self.api_client_secret:
            pass
        else:
            error_msg("Must have EOX_PROD_API_CLIENT_ID and EOX_PROD_API_CLIENT_SECRET set in your environment in order to continue...")
            quit("Exiting!!")

        self.api_client = BackendApplicationClient(client_id=self.api_client_id)
        oauth = OAuth2Session(client=self.api_client)

        # get token after providing key and secret
        token = oauth.fetch_token(token_url=self.prodEoxApiAuthUrl,
            client_id=self.api_client_id,
            client_secret=self.api_client_secret
            )

        # generate an OAuth2Session object with the token
        self.client = OAuth2Session(self.api_client_id, token=token)
    
    def __generate_unique_transaction_id(self):
        transaction_id = f"{randrange(self.random_range)}Rj{randrange(self.random_range)}qAf{randrange(self.random_range)}pQ{randrange(self.random_range)}fQ{randrange(self.random_range)}lqw{randrange(self.random_range)}QtS{randrange(self.random_range)}j{randrange(self.random_range)}BlackWidow{randrange(self.random_range)}Pm{randrange(self.random_range)}uI"
        
        # print(transaction_id)
        return transaction_id
        

    def check_skus(self, sku_list):
        # returns JSON of query
        # takes list as input
        url = '/queryeoxproduct'
        uri = self.prodEoxApiBaseUrl + url

        template = env.get_template("queryEoxProduct.j2")
        
        request_body = template.render(appid = self.app_id,
            current_timestamp = timestamp_in_zulu(),
            customer_unique_transaction_id = self.__generate_unique_transaction_id(), 
            customer_source_id = self.customer_source_id,
            sku_list = sku_list )

        headers = { "Content-Type": "application/json", 
                    "Accept": "application/json" }
        
        # debug
        # print(request_body)
        
        self.response = self.client.post(uri, data=request_body, headers=headers)
        return self.response.json()

    def __to_df(self):
        # build a pandas dataframe for export to excel
        api_response = self.response.json()

        # let's store this as an list of dicts
        data = []

        for sku in api_response["queryEOXProductResponse"]["data"]["productEOX"]:
            eox_product = sku["eoxProduct"]
            eol_announce_date = sku["eolAnnounceDate"]
            last_order_date = sku["lastOrderDate"]
            #same_day_support_discontinued = sku["sameDaySupportDiscontinuedDate"]
            #next_day_support_discontinued = sku["nextDaySupportDiscontinuedDate"]
            try:
                end_of_hw_engineering_date = sku["endofHwEngineeringDate"]
            except:
                end_of_hw_engineering_date = "N/A"
            try:
                end_of_sw_engineering_date = sku["endofSwEngineeringDate"]
            except:
                end_of_sw_engineering_date = "N/A"
            try:
                end_of_support_date = sku["endofSupportDate"]
            except:
                end_of_support_date = "N/A"
            try:
                replacement_part = sku["replacementPart"]
            except:
                replacement_part = "N/A"   
                
            # append our new row
            data.append( { 'EoX Product' : eox_product,
                            'EoL Announce Date' : eol_announce_date, 
                            'Last Order Date' : last_order_date,
                            'EndofHwEngineering' : end_of_hw_engineering_date,
                            'EndOfSwEngineering' : end_of_sw_engineering_date,
                            'EndOfSupport' : end_of_support_date,
                            'ReplacementPart' : replacement_part } )

        # Create our DataFrame from our list
        df = pd.DataFrame(data)
        return df

    def to_table(self):
        api_response = self.response.json()
        # print headers
        print(f"{'EoX Product':<20}\t{'EoL Announce Date':^20}\t{'Last Order Date':^20}\t\
            {'EndofHwEngineering':^20}\t{'EndOfSwEngineering':^20}\t{'EndOfSupport':^20}\t{'ReplacementPart':^20}")
        for sku in api_response["queryEOXProductResponse"]["data"]["productEOX"]:
            eox_product = sku["eoxProduct"]
            eol_announce_date = sku["eolAnnounceDate"]
            last_order_date = sku["lastOrderDate"]
            #same_day_support_discontinued = sku["sameDaySupportDiscontinuedDate"]
            #next_day_support_discontinued = sku["nextDaySupportDiscontinuedDate"]
            try:
                end_of_hw_engineering_date = sku["endofHwEngineeringDate"]
            except:
                end_of_hw_engineering_date = "N/A"
            try:
                end_of_sw_engineering_date = sku["endofSwEngineeringDate"]
            except:
                end_of_sw_engineering_date = "N/A"
            try:
                end_of_support_date = sku["endofSupportDate"]
            except:
                end_of_support_date = "N/A"
            try:
                replacement_part = sku["replacementPart"]
            except:
                replacement_part = "N/A"            

            print(f"{eox_product:<20}\t{eol_announce_date:^20}\t{last_order_date:^20}\
                \t{end_of_hw_engineering_date:^20}\t{end_of_sw_engineering_date:^20}\
                \t{end_of_support_date:^20}\t{replacement_part:^20}\t")

    def to_excel(self, current_date, outfilename):
        header_map = {  'Part Number' : 'EoX Product',
                        'EO Sale Notification' : 'EoL Announce Date',
                        'EO Sale Date(Actual)' : 'Last Order Date',
                        'EO Sale Date(Estimate)' : "N/A",
                        'EO SW Support' : 'EndOfSwEngineering',
                        'EO Security Vulnerability Fixes' : 'EndOfSwEngineering',
                        'EO HW/RMA Support' : 'EndOfSupport',
                        'EO Useful Life' : 'EndOfSupport' 
                    }

        # not quite the same mapping in reverse so we're missing a couple column mappings which we'll fill
        # in with "N/A" before export
        header_map_inverse = {  'EoX Product' : 'Part Number',
                                'EoL Announce Date' : 'EO Sale Notification',
                                'Last Order Date' : 'EO Sale Date(Actual)',
                                'EndOfSwEngineering' : 'EO SW Support',
                                'EndOfSupport' : 'EO HW/RMA Support'
                            }
        
        data = self.__to_df()

        # inserting generic columns we want in the final output
        data.insert(0, 'Manufacturer', 'JUNIPER')
        data.insert(2, 'Update Month', current_date)
        data.insert(5, 'EO Sale Date(Estimate)', "N/A")
        data.insert(7, 'EO Security Vulnerability Fixes', "N/A")
        # rename the header row using our map dict
        data.rename(columns=header_map_inverse, errors="raise", inplace=True)

        result = data.to_excel(outfilename, index=False, header=True)

        if result == None:
            print(f'Success! File successfully exported to {outputfile}!')


#############
# FUNCTIONS #
#############
def error_msg():
    print('ABORTING : Please set auth via environment variables before retrying...')
    print('  export EOX_PROD_API_CLIENT_ID=\"client_id\"')
    print('  export EOX_PROD_API_CLIENT_SECRET=\"client_secret\"')

def timestamp_in_zulu():
    # javascript compliant timestamps for API timestamps
    # Example : "2022-12-10T00:59:47.245Z"
    return datetime.datetime.now(datetime.timezone.utc).isoformat(sep='T', timespec='milliseconds').replace("+00:00", "Z")

def generate_unique_transaction_id(random_range):
    transaction_id = f"{randrange(random_range)}Rj{randrange(random_range)}qAf{randrange(random_range)}pQ{randrange(random_range)}fQ{randrange(random_range)}lqw{randrange(random_range)}QtS{randrange(random_range)}j{randrange(random_range)}BlackWidow{randrange(random_range)}Pm{randrange(random_range)}uI"
    return transaction_id



# execute only if called directly (not as a module)
if __name__ == "__main__":


    parser = argparse.ArgumentParser()
    parser.add_argument('--inputfile', required=True, dest='inputfile', help='.xls file to open')
    parser.add_argument('--outputfile', required=True, dest='outputfile', help='.xls file to write to')
    parser.add_argument('--outformat', required=True, dest='outformat', help='dump to screen in tab format or write to excel')
    parser
    args = parser.parse_args()

    
    
    # open input/yourinputfile.xls
    if os.path.exists(args.inputfile):
        inputfile = args.inputfile

    # write to output/yourfile.xlsx
    if args.outputfile.endswith('xlsx'):
        if not os.path.exists('output'):
            os.makedirs('output')
        outputfile = os.path.join('output', args.outputfile)     
    else:
        quit("Excel format export only supports .xlsx!!")


    # generate our execution timestamp eg. "Jan 2023" for inclusion in our output table
    current_date = datetime.date.today().strftime("%b %Y")

    # read the customer provided file and parse out the interesting column to get our SKUs to query
    #file = r'input/customer_sku_file_feb_2023.xlsx'
    df = pd.read_excel(inputfile)

    # find and strip the SKU list from the resulting import
    sku_list = (df['Part Number']).to_list()


    # setup our API object
    eox = EoxApi()

    # auth to api endpoint using our supplied credentials stored in ENV
    eox.auth()

    # submit query with interesting SKUs supplied as a list
    eox_response = eox.check_skus(sku_list)

    if args.outformat == 'screen':
        #dump our match results into a table
        eox.to_table()
    elif args.outformat == 'excel':
        eox.to_excel(current_date, outputfile)
    else:
        quit("Uknown Output Option Supplied! Quitting.")

    
