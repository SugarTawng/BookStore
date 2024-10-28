import requests
from util import common
from system.error_code import ERROR_CODE
import os
import time

AUTOMATION_LINK= "https://n8n.rockship.co/webhook/" 

WEBHOOK_SLUG = {
    "UPDATE_ORDER": "0f480428-3427-4471-a119-411f4a2087ce",
    "CREATE_ORDER": "19eaa4da-2cf4-43b9-af10-472dbe9ada87",
    "CREATE_USER": "sign-up",
    "CREATE_EXPERT_REQUEST": "create_expert_request",
    "UPDATE_EXPERT_REQUEST": "update_expert_request",
    "CV_POWERUP_UPLOAD": "cv-powerup-upload",
    "SUBMIT_ASSIGNMENT": "submit-assignment",
    "CONTACT_EXPERT": "create_expert_contact",
    "CREATE_CONTACT": "1269b7e8-1f7b-4934-9b3b-b2259c240b4c"
}
class AutomationApiHandler:
    @staticmethod
    def call(operation, webhook_slug, data = None, json_info = None):
        try:
            #configure environment
            if data and "env" not in data:
                data['env'] = 'product' if os.environ.get('ENV') == 'PRODUCT' else 'dev'
            if json_info and "env" not in json_info:
                json_info['env'] = 'product' if os.environ.get('ENV') == 'PRODUCT' else 'dev'
            #configure prefix link
            webhook_link = AUTOMATION_LINK + webhook_slug
            #configure method to send
            methods = {
                "post": requests.post,
                "patch": requests.patch,
                "get": requests.get,
                "delete": requests.delete,
            }
            #send the request to automation api
            start_time = time.time()
            webhook_response = methods.get(operation, lambda *_: None)(webhook_link, data, json_info)
            #check for response
            print("Time to call automation webhook: ", time.time() - start_time)
            if webhook_response is None or webhook_response.status_code != 200:
                return None, ERROR_CODE["AUTOMATION_WEBHOOK_FAILED"]
            return webhook_response, None
        except Exception as err:
            common.push_log_to_sentry(message="Automation api call failed", extra_data={'error': str(err)})
            return None, err
