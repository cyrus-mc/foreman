#!/usr/bin/ruby

# include required libraries
require "rubygems"
require "zabbixapi"

# hostname pass as first argument
HOSTNAME=ARGV[1]

begin
  # create connection to zabbix API
  zbx = ZabbixApi.connect(
    :url => "http://pit-zabbix-01.smarshinc.com/zabbix/api_jsonrpc.php",
    :user => 'admin',
    :password => 'zabbix'
  )

  # find host ID (returns nil if not found)
  host_id = zbx.hosts.get_id(:host => "#{HOSTNAME}")

  if ! host_id.nil? then
    result = zbx.hosts.delete host_id
  end
rescue
  # catch all errors and squash
end

# successful
exit 0
