#!/usr/bin/env python

import sys
import yaml
import json
import requests
import getpass
import getopt
from requests.packages.urllib3.exceptions import InsecureRequestWarning

def create_session(url, user, password):
  s = requests.Session()

  # set our authentication parameters
  s.auth = ( user, password )

  # we should be able to login once and then set a cookie
  response = s.get(url, verify=False)
  if response.status_code == 200:
    return s
  else:
    return None

def getRecords(url, s, debug=False):
  """ Get all records for a specific resource """
  if debug:
    print "requests.get(%s)" % url

  response = s.get(url, verify=False)

  if debug:
    print response

  if response.status_code == 200:
    # retrieve the results
    r_json = response.json()

    if debug:
      print r_json

    if 'results' in r_json:
      return r_json['results']
    else:
      return r_json
  else:
    return None

def getRecord(host, resource, key, value, s, debug=False):
  """Get a specific record based on field = value """

  url = 'https://%s/api/v2/%s' % (host, resource)

  if debug:
    print "requets.get(%s)" % (url)

  response = s.get(url, verify=False)

  if debug:
    print response

  if response.status_code == 200:
    # retrieve the results
    r_json = response.json()

    if debug:
      print r_json

    result = None
    if 'results' in r_json:
      # loop through the array and check each record for key matching value
      for record in r_json['results']:

        if debug:
            print record

        if key in record:
          if record[key] == value:
            result = record
    else:
      if key in r_json:
        if r_json[key] == value:
          result = r_json

    return result
  else:
    return None
  

def createRecord(server, resource, input_data, s, debug=False):
  """ Create specified resource, else return if it already exists """

  url = 'https://%s/api/v2/%s' % (server, resource)
  if debug:
    print "requests.put(%s)" % url

  try:
    headers = { 'Content-Type': 'application/json' }
    response = s.post(url, data=json.dumps(input_data), headers=headers, verify=False)

    if debug:
      print response
  except:
    print "Unexpected error: ", sys.exc_info()[0]

  return response

# main function, where the fun starts
def main(argv):

  # disable insecure requests warning
  requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

  # parse arguments
  try:
    opts, args = getopt.getopt(argv, "i:s:", [ "input-file=", "server=" ])
  except getopt.GetoptError:
    print "Check help"
    sys.exit(2)

  input_file = None
  server = None
  for opt, arg in opts:
    if opt in ("-i", "--input-file"):
      input_file = arg
    if opt in ("-s", "--server"):
      server = arg

  if input_file == None or server == None:
    print "Check help"
    sys.exit(2)

  # read in configuration files
  try:

    fh = open('config.yaml', 'r')
    yaml_obj = yaml.load_all(fh)
    config = yaml_obj.next()
    fh.close()

    fh = open(input_file, 'r')
    yaml_obj = yaml.load_all(fh)
    input_config = yaml_obj.next()
    fh.close()
  except IOError as e:
    print "I/O error({0}) : {1}".format(e.errno, e.strerror)
  except yaml.YAMLError, exc:
    print "Error parsing YAML : ", exc

  # first thing we need is to authenticate
  username = raw_input('username: ')
  password = getpass.getpass('password: ')

  # create session
  session = create_session('https://%s/api/v2/locations' % server, username, password)
  if session == None:
    print "Failed to login, please check your username and password!"
    sys.exit(1)

  userRecord = getRecords("http://%s/api/v2/users/%s" % (server, username), session)
  if userRecord == None:
    print "Failed to retrieve user record, please contact system administrator!"
    sys.exit(1)

  if userRecord['locations'].__len__() == 0:
    print "User does not have access to deploy in any locations, please contact your system administrator!"
    sys.exit(1)
  elif userRecord['organizations'].__len__() == 0:
    print "User does not have access to deploy in any organization, please contact your system administrator!"
    sys.exit(1)

  # prompt user to select their location
  i = 0
  for location in userRecord['locations']:
    print "%d : %s" % (i, location['name'])
    i += 1

  tinput = input('select location: ')
  location = userRecord['locations'][tinput] 
  
  # prompt user to select their organization
  i = 0
  for organization in userRecord['organizations']:
    print "%d : %s" % (i, organization['name'])
    i += 1

  tinput = input('select organization: ')
  organization = userRecord['organizations'][tinput]

  # find compute resource(s) for our location and organization
  computeResourceRecord = getRecords('https://%s/api/v2/compute_resources?search=location_id=%s&organization_id=%s' % (server, location['id'], organization['id']), session)
  if computeResourceRecord == None:
    print "Unable to find any compute resources to deploy on, please contact your system administrator!"
    sys.exit(1)

  # prompt user for the compute resource to use
  i = 0
  for computeresource in computeResourceRecord:
    print '%d : %s' % (i, computeresource['name'])
    i += 1

  tinput = input('select compute resource: ')
  computeresource = computeResourceRecord[tinput]

  print "Building systems for environment %s" % (input_config['build_spec']['environment'])
  default_global_settings = config['default_configurations']['locations'][location['name'].lower()]['environment'][input_config['build_spec']['environment']]

  # loop over the systems to build
  for system in input_config['build_spec']['systems']:
    spec = input_config['build_spec']['systems'][system]
    default_host_settings = config['host_definitions'][spec['spec']]
    build_settings = default_global_settings.copy()
    build_settings.update(default_host_settings)
    build_settings.update(spec)

    # ok, we should have most of the needed information to build the machine
    # find hostgroup ID
    hostGroupRecord = getRecords('https://%s/api/v2/hostgroups/%s' % (server, build_settings['hostgroup']), session) 
    if hostGroupRecord == None:
      print "Unable to query hostgroup. Do you have permission?"
      sys.exit(3)

    # did we specify a custom flavor (outside of what is set by hostgroup)?
    flavorRecord = None
    if 'flavor' in build_settings:
        # find out the ID for that flavor
        flavorRecord = getRecord(server, 'compute_resources/%s/available_flavors' % (computeresource['id']), 'name', build_settings['flavor'], session)
        if flavorRecord == None:
            print "Unable to find specified flavor, defaulting to hostgroup setting"

    # retrieve compute resource network ID
    networkRecord = getRecord(server, 'compute_resources/%s/available_networks' % (computeresource['id']), 'name', build_settings['network'], session)
    if networkRecord == None:
        print "Unable to find specified network %s, sipping" % build_settings['network']
        continue

    number = 1
    pod = 1
    if 'number' in spec:
      number = spec['number']

    # retrieve domain
    domain = "%s.%s" % (build_settings['site_code'], build_settings['domain'])
    domainRecord = getRecord(server, 'domains', 'name', domain, session)
    if domainRecord == None:
        print "Unable to find specified domain %s, skipping" % domain

    # retrieve subnet
    subnetRecord = getRecord(server, 'subnets', 'name', build_settings['network'], session)
    if subnetRecord == None:
        print "Unable to find specified subnet %s, skipping" % build_settings['network']

    for i in range(1, number + 1): 
      request_body_map = {}
      request_body_map['host'] = {}
      request_body_map['host']['location_id'] = location['id']
      request_body_map['host']['organization_id'] = organization['id']
      request_body_map['host']['environment_id'] = "3" # this will be upated via or post hook
      request_body_map['host']['compute_resource_id'] = computeresource['id']
      request_body_map['host']['managed'] = True
      request_body_map['host']['type'] = 'Host::Managed'
      request_body_map['host']['name'] = config['host_definitions'][spec['spec']]['name'] % (pod, i)
      request_body_map['host']['hostgroup_id'] = hostGroupRecord['id']
      request_body_map['host']['domain_id'] = domainRecord['id']
      request_body_map['host']['subnet_id'] = subnetRecord['id']

      # interface attributes
      request_body_map['host']['interface_attributes'] = {}
      request_body_map['host']['interface_attributes']['ip'] = '10.200.3.10'
      request_body_map['host']['interface_attributes']['domain_id'] = domainRecord['id']
      request_body_map['host']['interface_attributes']['subnet_id'] = subnetRecord['id']
      request_body_map['host']['interface_attributes']['type'] = 'Nic::Managed'
      request_body_map['host']['interface_attributes']['name'] = build_settings['name'] % (pod, i)
      request_body_map['host']['interface_attributes']['managed'] = "1"
      request_body_map['host']['interface_attributes']['primary'] = "1"
      request_body_map['host']['interface_attributes']['provision'] = "1"
      request_body_map['host']['interface_attributes']['virtual'] = "0"

      # compute attributes
      request_body_map['host']['compute_attributes'] = {}
      request_body_map['host']['compute_attributes']['nics'] = []
      request_body_map['host']['compute_attributes']['nics'].insert(0, networkRecord['id'])
      
      # did we specify a flavor and was it found?
      if not flavorRecord == None:
        request_body_map['host']['compute_attributes']['flavor_ref'] = flavorRecord['id']

      # create the host
      print request_body_map
      #result = createRecord(server, 'hosts', request_body_map, session)
      #print result.json()

if __name__ == '__main__':
  sys.exit(main(sys.argv[1:]))
