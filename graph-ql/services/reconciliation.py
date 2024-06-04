from fastapi import HTTPException
import requests
import json
from urllib.parse import urlencode
from config.constant import RECON_ENDPOINT


def reconcile_entities(queries):
    results = {}
    # Define the reconciliation endpoint URL

    reconciliation_endpoint = RECON_ENDPOINT+"/gleifdata1/"  # Change this to your actual reconciliation endpoint  
    # reconciliation_endpoint = "http://localhost:9900/gleifdata1/"

    # print(queries)
    # Send reconciliation queries to the service
    encoded_queries = urlencode({"queries": json.dumps(queries)})
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    response = requests.post(reconciliation_endpoint, data=encoded_queries, headers=headers)
     
    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        # Parse the response
        reconciliation_results = response.json()
        # Process the results
        for query_key, result_data in reconciliation_results.items():
            if "result" in result_data:
                company_results = []
                for result in result_data["result"]:
                    company_results.append({
                        "id": result['id'],
                        "name": result['name'],
                        "score": result['score'],
                        #"company": queries[query_key]['query']
                    })
                results[queries[query_key]['query']] = company_results
            else:
                pass
    else:
        pass
        #raise HTTPException(status_code=response.status_code, detail="Failed to send reconciliation queries")

    return results