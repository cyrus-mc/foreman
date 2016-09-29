#!/usr/bin/env python

import sys
import yaml
import json
import requests
import getpass
import getopt
from requests.packages.urllib3.exceptions import InsecureRequestWarning

def create_session(host, user, password, debug=False):
  """ Create a login session """

  # there is no actual login API call (that I know of)
  url = 'https://%s/api/v2/users' % host

  if debug:
      print "requests.get(%s)" % url

  s = requests.Session()
  # set our authentication parameters
  s.auth = ( user, password )

  response = s.get(url, verify=False)
  if debug:
    print response

  if response.status_code == 200:
    return s
  else:
    return None

def getRecords(host, resource, s, debug=False):
  """ Get all records for a specific resource """

  url = 'https://%s/api/v2/%s' % (host, resource)

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

def checkPermission(userRecord, resource, permission, debug=False):
    """ Check user record for permission to specified resource """

    if userRecord['admin']:
      return True

    if resource in userRecord:
      for entry in userRecord[resource]:
          if entry['name'].lower() == permission.lower():
              return True

    return False

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
  print "\nPlease enter your Active Directory credentials for Foreman server %s\n" % (server)
  username = raw_input('username: ')
  password = getpass.getpass('password: ')

  print "\nBeginning Deployment: \n"

  # create session
  session = create_session(server, username, password)
  if session == None:
    print "Failed to login, please check your username and password!"
    sys.exit(1)

  # grab details about user
  # this should list what organizations and locations this user is authorized to
  userRecord = getRecord(server, 'users', 'login', username, session)
  if userRecord == None:
    print "Failed to retrieve user record, please contact system administrator!"
    sys.exit(1)

  # there are a few different paths we can take here
  #
  #  - default location is specified 
  #  - no default location specified so use profile default location
  location = None
  if 'location' in input_config['build_spec']:
    location = input_config['build_spec']['location']
  elif not userRecord['default_location'] == None:
    location = userRecord['default_location']['name']

  # same logic for organization
  organization = None
  if 'organization' in input_config['build_spec']:
    organization = input_config['build_spec']['organization']
  elif not userRecord['default_organization'] == None:
    organization = userRecord['default_organization']['name']
 
  # loop over the systems to build
  for system in input_config['build_spec']['systems']:
    #spec = input_config['build_spec']['systems'][system]

    # get default settings for this spec (if it exists)
    default_host_settings = {}
    if system['spec'] in config['host_definitions']:
      default_host_settings = config['host_definitions'][system['spec']]

    # now we need to make a decision on the location to build in
    # use global/default or the one specified in the spec
    if 'location' in system:
      location = system['location']

    if 'organization' in system:
      organization = system['organization']

    if organization == None or location == None:
      print "No location or organization specified for this deployment, skipping"
      continue

    # check if user has access to this location
    if not checkPermission(userRecord, 'locations', location):
        print "User is not permitted to deploy in location %s, skipping" % location

    locationRecord = getRecords(server, 'locations/%s' % location, session)

    # check if user has access to this organization
    if not checkPermission(userRecord, 'organizations', organization):
        print "User is not permitted to deploy in organization %s, skipping" % organization

    orgRecord = getRecords(server, 'organizations/%s' % organization, session)

    default_global_settings = config['default_configurations']['locations'][location.lower()]['environment'][system['environment']]
    build_settings = default_global_settings.copy()
    build_settings.update(default_host_settings)
    build_settings.update(system)

    # ok, we should have most of the needed information to build the machine
    # find hostgroup ID
    if not 'hostgroup' in build_settings:
      print "No hostgroup specified, skipping"
      continue

    hostGroupRecord = getRecord(server, 'hostgroups', 'name', build_settings['hostgroup'], session)
    if hostGroupRecord == None:
      print "Unable to query hostgroup. Do you have permission?, skipping"
      continue

    # find compute resource(s) for our location and organization
    computeResourceRecord = getRecords(server, 'compute_resources?search=location_id=%s&organization_id=%s' % (locationRecord['id'], orgRecord['id']), session)
    if computeResourceRecord == None or computeResourceRecord.__len__() == 0:
      print "Unable to find any compute resources to deploy on, please contact your system administrator!"
      sys.exit(1)
    elif computeResourceRecord.__len__() == 1:
      computeresource = computeResourceRecord[0]
    else:
      print "Multiple compute resources found for specified location and organization, please select which one to use"
      # prompt user for the compute resource to use
      i = 0
      for computeresource in computeResourceRecord:
        print '%d : %s' % (i, computeresource['name'])
        i += 1

      tinput = input('select compute resource: ')
      computeresource = computeResourceRecord[tinput]

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

    # we need to dynamically generate the hostname
    # search for all hostgroup + environment + location hosts
    hosts = getRecords(server, 'hosts?search=hostgroup=%s+and+environment=%s+and+location=%s' % (hostGroupRecord['name'], build_settings['environment'], locationRecord['name']), session)

    current_pod = [ '00' ]
    for host in hosts:
      # need to query each host individually to get parameters
      params = getRecords(server, 'hosts/%s/parameters' % host['id'], session)
      for param in params:
          if param['name'] == 'pod':
            current_pod.append(param['value'])

    current_pod.sort()
    pod = int(current_pod[-1]) + 1
    number = 1
    # dynamically figure out next POD number
    if 'number' in system:
      number = system['number']

    # retrieve domain
    #domain = "%s.%s" % (build_settings['site_code'], build_settings['domain'])
    domain = "ost.%s" % (build_settings['domain'])
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
      request_body_map['host']['location_id'] = locationRecord['id']
      request_body_map['host']['organization_id'] = orgRecord['id']
      request_body_map['host']['environment_id'] = "9" # this will be upated via or post hook
      request_body_map['host']['compute_resource_id'] = computeresource['id']
      request_body_map['host']['managed'] = True
      request_body_map['host']['type'] = 'Host::Managed'
      request_body_map['host']['name'] = build_settings['prefix'] + "-" + config['host_definitions'][system['spec']]['name'] + "-%02d-%02d" % (pod, i)
      request_body_map['host']['hostgroup_id'] = hostGroupRecord['id']
      request_body_map['host']['domain_id'] = domainRecord['id']
      request_body_map['host']['subnet_id'] = subnetRecord['id']

      # interface attributes
      request_body_map['host']['interface_attributes'] = {}
      request_body_map['host']['interface_attributes']['ip'] = '10.200.3.10'
      request_body_map['host']['interface_attributes']['domain_id'] = domainRecord['id']
      request_body_map['host']['interface_attributes']['subnet_id'] = subnetRecord['id']
      request_body_map['host']['interface_attributes']['type'] = 'Nic::Managed'
      request_body_map['host']['interface_attributes']['name'] = build_settings['prefix'] + "-" + build_settings['name'] + "-%02d-%02d" % (pod, i)
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
      #print request_body_map
      print "- server %s.%s" % (request_body_map['host']['name'], domainRecord['name'])
      print "\t location: %s" % (locationRecord['name'])
      print "\t organization: %s" % (orgRecord['name'])
      print "\t compute resource: %s" % (computeresource['name'])

      # execute the create request
      #result = createRecord(server, 'hosts', request_body_map, session)
      #print "\t status: %s\n" % (result.status_code)
      #print result.json()
      print request_body_map

if __name__ == '__main__':
  sys.exit(main(sys.argv[1:]))
