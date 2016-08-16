#!/usr/bin/ruby

# hook to manage idrac interface (set DNS forward and reverse records)

# query all interfaces of a host, find type: BMC, set domain and subnet and managed: true

# errors will not halt provisioning/initialization, instead it will send an email indicating what went wrong

require 'rubygems'
require 'json'
require 'yaml'
require 'rest-client'
require 'json'
require 'ipaddr'
require 'net/smtp'

def get_key (hash, key)
	# check if the key exists in hash
	if hash.has_key?(key)
		return hash[key]
	else
		# raise exception if not found
		raise( "Key #{ key } is not valid" )
	end

end

SCRIPT_NAME = "after_build-02_manage_idrac_interface"

# assumption: we have only one IDRAC domain (current installation this is subnet_id = 12)
IDRAC_DOMAIN = 12

# a JSON representation of the hook object will be passed in on stdin
begin
	object_data = $stdin.gets
	hook_object = JSON.parse(object_data)
rescue JSON::ParseError => e
	print e
end

# outer key is host
event_details = get_key hook_object, 'host'

# get host_id and hostname
host_id = get_key event_details, 'id'
hostname = get_key event_details, 'name'

# it checks for the existence of /tmp/foreman-hooks/HOSTNAME indicating that this host is in process of being created
#if File.file?("/tmp/foreman-hooks/#{hostname}") then
#  # load file and ensure this script hasn't already run
#  d = YAML::load_file("/tmp/foreman-hooks/#{hostname}")
#  
#  if d['scripts'].include? SCRIPT_NAME
#    # script has already run, exit
#    exit 0
#  else
#    # write out updated file 
#    #d['scripts'].push(SCRIPT_NAME)
#    File.open("/tmp/foreman-hooks/#{hostname}", "w") { |f| f.write d.to_yaml }
#  end
#else
#  # not found, return as a fail safe (we don't want script to run again after initial provisioning)
#  #exit 0
#end

client = RestClient::Resource.new('https://0.0.0.0',
				:user		=> 'api-user',
				:password	=> 'api-user',
				:headers	=> { :content_type => 'application/json',
						     :accept => :json })
						     #"version" => "2" })

client_proxy = RestClient::Resource.new('https://0.0.0.0:8443',
  :ssl_client_cert => OpenSSL::X509::Certificate.new(File.read("/usr/share/foreman/config/hooks/hook_client_cert.pem")),
  :ssl_client_key  => OpenSSL::PKey::RSA.new(File.read("/usr/share/foreman/config/hooks/hook_client_key.pem")),
  :headers	 => { :content_type => 'application/json',
		      :accept => :json })

begin
  interfaces = JSON.parse(client["api/v2/hosts/#{host_id}/interfaces"].get)

  # find BMC interface (if it exists)
  bmc = nil

  interfaces['results'].each do |interface|
    if interface['type'] == 'bmc' then
      bmc = interface
      break
    end
  end

  request_body_map = {
    :host_id => "#{host_id}",
    :interface => {
      :type => 'bmc'
    }
  }

  # BMC present?
  if ! bmc.nil? then

    request_body_map[:id] = bmc['id']
    request_body_map[:interface][:managed] = 'true'
    request_body_map[:interface][:name] = hostname.split('.')[0]

    bmc_ipaddr = IPAddr.new(bmc['ip'])  

    # assumption is that each location only has one idrac network
    location_id = get_key event_details, 'location_id'

    # we need a list of all the su bnets and domains (well just idrac domain)
    # find what subnet and domain the BMC is in
    subnets = JSON.parse(client["api/v2/locations/#{location_id}/subnets"].get)    

    subnets['results'].each do |subnet|
      subnet_ipaddr = IPAddr.new(subnet['network_address'])
   
      if subnet_ipaddr.include?(bmc_ipaddr) then
      
        request_body_map[:interface][:subnet_id] = subnet['id']
        request_body_map[:interface][:domain_id] = IDRAC_DOMAIN

        # get a free IP within this subnet
        request_body_map[:interface][:ip] = JSON.parse(client_proxy["dhcp/#{subnet['network']}/unused_ip"].get)['ip']

        break
      end
    end

    # update our host BMC interface
    response = client["api/hosts/#{host_id}/interfaces/#{bmc['id']}"].put(request_body_map.to_json)
  end
rescue => e
  # on error send email, don't abort provisioning
  message = <<MESSAGE_END
FROM: Foreman Auto-provisioning <foreman@pit-foreman-01.smarshinc.com>
TO: Matthew Ceroni <matthew.ceroni@smarsh.com>
Subject: ERROR : provisioning host #{hostname}

#{e.response}
MESSAGE_END
  Net::SMTP.start('localhost') do |smtp|
    smtp.send_message message, 'foreman@pit-foreman-01.smarshinc.com',
                                'matthew.ceroni@smarsh.com'
  end
  print e.response
end
exit 0
