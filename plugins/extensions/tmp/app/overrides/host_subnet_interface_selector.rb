selector_text = <<END_OF_STRING
<%= select_f f, :subnet_id, accessible_subnets, :id, :to_label,
               { :include_blank => accessible_subnets.any? ? true : _("No subnets")},
               { :disabled => accessible_subnets.empty? ? true : false,
                 :help_inline => :indicator,
                 :class => 'interface_subnet', :'data-url' => freeip_subnets_path, :onchange => 'setComputeNetwork(this)',
                 :size => "col-md-8", :label_size => "col-md-3" } %>
END_OF_STRING

Deface::Override.new(:virtual_path => 'hosts/_form',
                     :name => 'add_javascript_to_host',
                     :insert_before => 'div#primary', 
                     :partial => 'foreman_extensions/hosts/host_tab_pane')

Deface::Override.new(:virtual_path => 'nic/_base_form',
		     :name => 'add_onchange_function',
                     :replace => "erb[loud]:contains('accessible_subnets')",
                     :text => selector_text)
