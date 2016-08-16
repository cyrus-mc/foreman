#!/usr/bin/ruby 
# This hook will query global inheritted parameters puppet and puppet_ca of the host and set the
# puppet and puppet CA smart proxy for the host accordingly.
#
# This way we don't have to have a separate host group hierarchy per location / role

require 'rubygems'
require 'json'
require 'yaml'
require 'rest-client'
require 'ipaddr'
require 'logger'

def get_key (hash, key)
	# check if the key exists in hash
	if hash.has_key?(key)
		return hash[key]
	else
		# raise exception if not found
		raise( "Key #{ key } is not valid" )
	end
end

# hostname pass as first argument
HOSTNAME=ARGV[1]

# before going any further check for trigger, indicates if script has already run
if ! File.file?("/tmp/foreman-hooks/#{HOSTNAME}.set_environment") then
  exit 0
end

# setup logging
logging = Logger.new('/var/log/foreman/hooks.log')

# our hostnames are messed up, so we need some mapping to the real environment
env_to_hostname_map = {
  "qa"     => "qa",
  "dev"    => "development",
  "stg"    => "staging",
  "dryrun" => "staging",
  "uat"    => "staging",
  "pit"    => "production"
}

env_to_domain_map = {
  "smarshdev" => "development",
  "smarshqa"  => "qa",
  "smarshinc" => "production"
}

# a JSON representation of the hook object will be bassed in on stdin
begin
	object_data = $stdin.gets
	hook_object = JSON.parse(object_data)
rescue JSON::ParseError => e
	print e
end

event_details = nil

event_details = get_key hook_object, 'host'
logging.info(event_details)

# delete file so we don't run this script again
File.delete("/tmp/foreman-hooks/#{HOSTNAME}.set_environment")

# get the host_id from the event details
host_id = get_key event_details, 'id'
hostname = get_key event_details, 'name'

# determine current environment
c_env = get_key event_details, 'environment_id'

# only set environment if it isn't currently set
#if c_env.nil? then

  # create our rest client
  client = RestClient::Resource.new('https://0.0.0.0',
    	         		  :user		=> 'api-user',
				  :password	=> 'api-user',
				  :headers	=> { :content_type => 'application/json', :accept => :json })

  # grab the details of our host (hopefully we have the ID by this point)
  #hosts = JSON.parse(client["api/hosts/#{host_id}"].get)
  #host = JSON.parse(client["api/hosts?search=name=#{HOSTNAME}"].get)

  request_body_map = {
    :id => "#{host_id}",
    #:id => "#{host['results'][0]['id']}",
    :host => {},
  }

  # we have a few different hostname patters
  # 
  #   env-role-c##-n##.domain
  #   role-##-##.domain
  #
  # In the second case, the domain identifies the environment
  # First pattern takes precendence

  # default environment
  n_env = "production"

  if hostname.start_with?("dev", "qa", "stg", "dryrun", "pit") then
    h_env = hostname.split("-")[0]   

    if env_to_hostname_map.key?(h_env) then
      n_env = env_to_hostname_map[h_env]
    end
  else
    # parse the domain
    h_env = hostname.split(".")[-2]

    if env_to_domain_map.key?(h_env) then
      n_env = env_to_domain_map[h_env]
    end

    # determine pod and node number
    r = /([a-z]*)-(\d{1,2})(-(\d{1,2}))?/
    m = r.match hostname

    # if back reference 3 is nil that means no POD number given
    if m[3] == nil then
      # node is back reference 2
      new_parameters = { 1 => { :name => 'node', :value => m[2], :nested => true } }
    else
      # pod is backreference 2 and node is back reference 4
      new_parameters = { 1 => { :name => 'pod', :value => m[2], :nested => true },
                         2 => { :name => 'node', :value => m[4], :nested => true } }
    end
  end
  request_body_map[:host][:host_parameters_attributes] = new_parameters

  # get environment ID 
  environments = JSON.parse(client["api/v2/environments?search=name=#{n_env}"].get)
  request_body_map[:host][:environment_id] = environments['results'][0]['id']

  # make API call to update host
  logging.info(request_body_map)
  response = client["api/hosts/#{host_id}"].put(request_body_map.to_json)

#end

exit 0
