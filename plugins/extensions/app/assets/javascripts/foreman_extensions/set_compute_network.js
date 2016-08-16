// this will set the compute network based off
// interface selected subnet (names must match)
function setComputeNetwork(sel_obj) {

  var selected_value = sel_obj.options[sel_obj.selectedIndex].text.split(" ")[0];

  // grab div element containing list of compute networks
  var nics_div = document.getElementById('ms-host_compute_attributes_nics');

  // <div><div><div><ul> first child is the selectable list
  var selectable_list = nics_div.children[0].children[1];
  var selection_list = nics_div.children[1].children[1];
  
  // loop through all the networks (<li> elements)
  // find one that matches
  for (i = 0; i < selectable_list.children.length; i++) {
    if (selected_value == selectable_list.children[i].children[0].innerText) {
      // generate onclick event
      selectable_list.children[i].click();
    }
  }

  // now unselect any that might have been previously selected
  for (i = 0; i < selection_list.children.length; i++) {
    if (selected_value != selection_list.children[i].children[0].innerText) {
      // generate onclick event
      selection_list.children[i].click();
    }
  }
}
