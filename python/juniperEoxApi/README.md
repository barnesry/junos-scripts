This script takes as input an excel file as input which expects a header row and one of these headers/columns **must**
match 'Part Number' which is then stripped out and fed into the Juniper EoX API to build a corresponding 
table. 

Output options are either in the original Juniper format (screen) or to an alternate format (excel)
Screen output is tab separated and should be copy/pasteable directly into excel for further adjustment
Excel format currently adheres to a specific output format and is translated at export to this format and saved to output/<outputfile>.
 
Example:
    python3 eox.py --inputfile input/eol_sku_list.xlsx --outputfile eol_result.xlsx --outformat screen


    (venv) barnesry@barnesry-mbp juniperEoxApi % python3 eox.py --inputfile ~/Downloads/eol_sku_list.xlsx  --outformat screen
    EoX Product         	 EoL Announce Date  	  Last Order Date   	             EndofHwEngineering 	 EndOfSwEngineering 	    EndOfSupport    	  ReplacementPart
    CFP-100GBASE-LR4    	     2016-02-12     	     2017-12-01                     	     2020-12-01     	     2020-12-01                     	     2022-12-01     	CFP-GEN2-100GBASE-LR4
    CFP-GEN2-CGE-ER4    	     2021-12-21     	     2022-01-15                     	     2022-01-15     	     2022-01-15                     	     2027-01-15     	        N/A
    DPCE-R-4XGE-XFP     	     2015-11-01     	     2016-05-01                     	     2019-05-01     	     2019-05-01                     	     2021-05-01     	        N/A
    FANTRAY-MX80-S      	     2020-06-30     	     2021-06-30                     	     2024-06-30     	     2024-06-30                     	     2026-06-30     	        N/A
    JA2500-A-BSE        	     2021-07-19     	     2021-07-19                     	     2021-07-19     	     2024-07-31                     	     2026-03-31     	  Virtual Machine
    {...}

Juniper Documentation : https://jnprprod.devportal-aw-us.webmethods.io/portal/apis
