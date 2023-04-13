import argparse
from colorama import Fore
import csv
from datetime import datetime
from random import randint
from time import sleep
from typing import List, Optional
from uuid import uuid4
import requests

from hl7.client import MLLPClient
from jinja2 import Environment, PackageLoader, select_autoescape

_WORKING_MAP = {}

_MODEL_PARAMS = {
    "mean_time_between_events": 0.5,
}

_FAKE_LOCATIONS = ["Heywood Ward", "Seacole Ward", "Mason Ward", "Fry Ward", "Bevan Ward", "Nightingale Ward", "Willink Ward"]

def csv_row_to_dict(row: List[str]):
    given_name_list = row[3].split(' ')
    ret_obj = {
        "pid": {
            "nhs_number": row[0],
            "dob": json_date_to_fhir_date(row[1]),
            "family_name": row[2],
            "given_name_first": given_name_list[0],
        }
    }
    
    if len(given_name_list) > 1:
        ret_obj["pid"]["given_name_middle"] = " ".join(given_name_list[1:len(given_name_list)])
    
    return ret_obj

def json_date_to_fhir_date(fhir_date: str) -> str:
    return fhir_date[0:4] + fhir_date[5:7] + fhir_date[8:10]

def fill_message_with_data_obj(data_obj: dict) -> str:
    env = Environment(
        loader=PackageLoader("templates", ""),
        autoescape=select_autoescape(disabled_extensions=('txt',))
    )

    template = env.get_template("vanilla.hl7")

    app_data_obj = {
        "msh": {
            "sending_app" : "SUNNY_TIE",
            "sending_fac" : "SUNNYSIDE",
            "dest_app": "HANS",
            "dest_fac" : "NHSENGLAND",
            "timestamp": datetime.now().strftime("%Y%m%d%H%M%S")
        }
    }
    data_obj["msh"] = {}
    data_obj["msh"]["message_control_id"] = uuid4()

    data_obj["pv1"] = {}
    data_obj["pv1"]["ward"] = _FAKE_LOCATIONS[randint(0, len(_FAKE_LOCATIONS) - 1)]

    raw_message = template.render(
                data=data_obj, 
                app_data=app_data_obj)

    raw_message = raw_message.replace("\n", "\r")

    return raw_message

def main(
    mode,
    host = None,
    port = None,
    path = None,
    ):
    print(Fore.WHITE, end="")
    # reading in loop
    with open('data/working.csv', newline='') as csvfile:
        csvreader = csv.reader(csvfile)
        row_num = 0
        for patient in csvreader:
            if row_num == 0:
                row_num += 1
                continue
            pat_obj = csv_row_to_dict(patient)
            _WORKING_MAP[row_num] = pat_obj
            row_num += 1

    # working loop
    try:
        for i in range(1, len(_WORKING_MAP)):
            pat_obj = _WORKING_MAP[i]
            pat_msg = fill_message_with_data_obj(pat_obj)
            if mode == "stdout":
                print_v2_stdout(pat_msg)
            elif mode == "http":
                make_http_request(host, port, path, pat_msg)
            elif mode == "mllp":
                make_mllp_request(host, port, pat_msg)
            sleep(_MODEL_PARAMS["mean_time_between_events"])
            i += 1
    except KeyboardInterrupt:
        print(f"[{Fore.CYAN}INFO{Fore.WHITE}] Exiting")

def print_v2_stdout(msg):
    print(msg.replace("\r", "\r\n"))

def make_mllp_request(host, port, msg):
    try:
        with MLLPClient(host, int(port)) as client:
            client.send_message(msg)
        print(f"[{Fore.CYAN}INFO{Fore.WHITE}] Sent message: ", end="")
        print_v2_stdout(msg)
    except ConnectionRefusedError as ex:
        print(f"[{Fore.RED}ERROR{Fore.WHITE}] Failed to connect: " + str(ex))


def make_http_request(host, port, path, msg):
    try:
        if port:
            port = ":" + port
        else:
            port = ""
        url = host + port + (path or "/")
        requests.post(url=url, data=msg)
        print(f"[{Fore.CYAN}INFO{Fore.WHITE}] Sent message: ", end="")
        print_v2_stdout(msg)
    except requests.exceptions.ConnectionError:
        print(f"[{Fore.RED}ERROR{Fore.WHITE}] Failed to connect to {url}")

if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("-m", "--mode", help="mode (http/mllp/stdout)")
    arg_parser.add_argument("-d", "--host", help="destination host (e.g. https://example.com)")
    arg_parser.add_argument("-p", "--port", help="destination port (e.g. 8080)")
    arg_parser.add_argument("-P", "--path", help="path (if in http mode, e.g. /lab/adt")


    args = arg_parser.parse_args()
    main(
        mode=args.mode or "stdout",
        host=args.host or None,
        port=args.port or None,
        path=args.path or None,
        )