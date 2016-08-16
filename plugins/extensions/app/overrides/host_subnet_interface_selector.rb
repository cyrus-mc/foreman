selector_text = <<END_OF_STRING
<%= select_f f, :subnet_id, accessible_subnets, :id, :to_label,
               { :include_blank => accessible_subnets.any? ? true : _("No subnets")},
               { :disabled => accessible_subnets.empty? ? true : false,
                 :help_inline => :indicator,
                 :class => 'interface_subnet', :'data-url' => freeip_subnets_path, :onchange => 'setComputeNetwork(this)',
                 :size => "col-md-8", :label_size => "col-md-3" } %>
END_OF_STRING

environment_selector_text = <<END_OF_STRING
        <%= select_f f, :environment_id, Environment.with_taxonomy_scope_override(@location,@organization).order(:name), :id, :to_label, { :include_blank => true },
           {:onchange => 'update_puppetclasses(this)', :'data-url' => hostgroup_or_environment_selected_hosts_path,
            :'data-host-id' => @host.id, :help_inline => :indicator} %>
END_OF_STRING

input_field_text = <<END_OF_STRING
<%= text_f f, :name, :size => "col-md-5", :value => name_field(@host), :onchange => "setEnvironment(this)",
            :help_inline => _("This value is used also as the host's primary interface name.") %>
END_OF_STRING

Deface::Override.new(:virtual_path => 'hosts/_form',
                     :name => 'add_javascript_to_host',
                     :insert_before => 'div#primary', 
                     :partial => 'foreman_extensions/hosts/host_tab_pane')

Deface::Override.new(:virtual_path => 'nic/_base_form',
		     :name => 'add_onchange_function',
                     :replace => "erb[loud]:contains('accessible_subnets')",
                     :text => selector_text)

Deface::Override.new(:virtual_path => 'hosts/_form',
                     :name => 'override_inherit_environment',
                     :replace => "erb[loud]:contains(':environment_id')",
                     :text => environment_selector_text)

Deface::Override.new(:virtual_path => 'hosts/_form',
                     :name => 'add_set_environment',
                     :replace => "erb[loud]:contains('name_field(@host)')",
                     :text => input_field_text)
