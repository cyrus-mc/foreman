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

client = RestClient::Resource.new('https://0.0.0.0',
				:user		=> 'api-user',
				:password	=> 'api-user',
				:headers	=> { :content_type => 'application/json',
						     :accept => :json })
						     #"version" => "2" })
File.open('/tmp/test-foreman', 'a') { |file| file.write("Host id #{host_id} hostname: #{hostname}") }
facts = JSON.parse(client["api/v2/discovered_hosts/#{host_id}"].get)
File.open('/tmp/test-foreman', 'a') { |file| file.write(facts) }
File.open('/tmp/test-foreman', 'a') { |file| file.write(hook_object) }

exit 0
