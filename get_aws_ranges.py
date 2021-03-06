# -------------------------------------------------------------------------------
# Name:         get_aws_ranges
# Purpose:      Produces a csv of ip ranges that Amazon AWS use globally
#
# Requirements: > Python 3.5
#
# Author:       Niels Jensen
#
# Created:      10/07/18
# -------------------------------------------------------------------------------
import urllib.error
import urllib.request
import time
import os
import json
import argparse
import ipaddress

aws_ip_ranges_url = "https://ip-ranges.amazonaws.com/ip-ranges.json"


def get_data():
    """
    Download the latest ip-ranges.json file from AWS and read it as json data

    :return: json data
    """
    # set path to save the .json file to be the same as the one that the script runs from
    json_file = "{0}/aws_subnets.json".format(os.path.dirname(os.path.abspath(__file__)))
    try:
        # download the latest version of the ip-ranges file from amazon
        urllib.request.urlretrieve(aws_ip_ranges_url, json_file)
    except (urllib.error.HTTPError, urllib.error.URLError):
        # Determine if file exists from previous run (or manual download)
        if not os.path.exists(json_file):
            # File doesnt exist, exit script with error message
            print('Error: Could not download the ip-ranges.json file and no file from a previous run exists.\n'
                  'You could try manually downloading the file from {0}, \n'
                  'saving it in the same directory as this script.'.format(aws_ip_ranges_url))
            return None
        else:
            # File does exist, get last modified date and display this info
            os.path.getctime(json_file)
            file_last_modified = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(os.path.getctime(json_file)))
            print("Could not download latest ip-ranges.json from Amazon, will use file from previous run.\n"
                  "File: {0}, last modified date: {1}\n".format(json_file.split("/")[-1], file_last_modified))
            input("Press enter to continue...")
    with open(json_file) as file:
        return json.load(file)


def print_regions(data):
    """
    Parse & print json data for regions that AWS provides public ip subnet data for

    :param data: json; data in the form of their published ip-ranges.json file
    :return: None
    """
    region_set = set([entry["region"] for entry in data["prefixes"]])
    print(', '.join(region_set))


def print_services(data, region=None):
    """
    Parse & print json data for service ip subnets, can optionally add a region to get that region's services

    :param data: json;  data in the form of their published ip-ranges.json file
    :param region: string; region as per AWS' region names
    :return: None
    """
    if not region:
        service_set = set([entry["service"] for entry in data["prefixes"]])
    else:
        service_set = set([entry["service"] for entry in data["prefixes"] if entry["region"].upper() == region.upper()])
    print(', '.join(service_set))


def find_subnets(data, search_ip):
    """
    Parse & print json data for subnets, regions & services for a specific ip

    :param data: json; data in the form of their published ip-ranges.json file
    :param search_ip: string; ipv4 address
    :return: None
    """
    try:
        # set the ip address provided as an ipaddress object
        ip = ipaddress.ip_address(search_ip)
    except ValueError:
        print('Error: IP address provided ({0})is not a valid ipv4 address.'.format(search_ip))
        return None

    # Search the json ip prefixes for the ip address, if the ip is within the subnet, add it to the results list
    search_results = [entry for entry in data["prefixes"] if ip in ipaddress.ip_network(entry["ip_prefix"])]

    if search_results:
        # output the results
        print("ip found in the following regions:")
        for result in search_results:
            print("Region: {0},  Service: {1},  Subnet: {2}".format(result["region"],
                                                                    result["service"],
                                                                    result["ip_prefix"],))
    else:
        print("ip not found in current AWS ip ranges")


def print_results(data, region=None, service=None):
    """
    Parse & print json data, output varies on optional region and service strings passed as args

    :param data: json;  data in the form of their published ip-ranges.json file
    :param region: string; region as per AWS' region names
    :param service: string; service as noted by AWS
    :return: None
    """
    for entry in data["prefixes"]:
        if not region:
            # No region specified, display all
            print("{0},{1},{2}".format(entry["ip_prefix"], entry["service"], entry["region"]))
        else:
            if service:
                if entry["region"] == region and entry["service"].upper() == service.upper():
                    print("{0},{1}".format(entry["ip_prefix"], entry["service"]))
            else:
                if entry["region"].upper() == region.upper():
                    print("{0},{1}".format(entry["ip_prefix"], entry["service"]))


def main():
    """
    Parse command-line arguments and get results based on data provided

    :return: None
    """
    # Setup parser and get arguments
    parser = argparse.ArgumentParser("Get public ip ranges with associated services for AWS.  "
                                     "Useful for building firewall policies")
    parser.add_argument("--list_regions",
                        help="shows all regions with public facing ip lists",
                        action="store_true")
    parser.add_argument("--list_services",
                        help="shows all services that AWS use, can also optionally specify a region",
                        action="store_true")
    parser.add_argument("--region",
                        help="the region you wish to return the ip ranges for")
    parser.add_argument("--service",
                        help="the service you wish to return the ip ranges for")
    parser.add_argument("--findip",
                        help="search for the region, service and subnet an ip address belongs to")
    args = parser.parse_args()

    # Get latest json data
    data = get_data()

    if data:
        if args.list_regions:
            # print region list, ignores all other arguments
            print_regions(data)
        elif args.list_services:
            # print service list, ignores the --service optional argument
            print_services(data, region=args.region)
        elif args.findip:
            # search for the region, service and subnet an ip belongs to
            find_subnets(data, args.findip)
        else:
            # print ip ranges
            print_results(data, region=args.region, service=args.service)
    else:
        exit(1)


if __name__ == "__main__":  # This will call the main() body when the script is run
    main()
