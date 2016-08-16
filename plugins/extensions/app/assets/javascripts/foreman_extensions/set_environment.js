// this will set the environment based off the hostname
function setEnvironment(object) {

  var environment = object.value.split("-")[0];

  // inner span ID is dynamically set, therefore grab outer div
  // and we know the span is the first child of the first child
  var d_element = document.getElementById('s2id_host_environment_id');
  var s_element = d_element.children[0].children[0];

  // grab the environments and match to our hostname
  var env_list = document.getElementById('host_environment_id');

  // loop over all options
  for (i = 0; i < env_list.options.length; i++) {
    // match start of string
    if (env_list.options[i].text.startsWith(environment)) {
      env_list.selectedIndex = i;
      s_element.textContent = env_list.options[i].text;
      return true;
    }
  }

  // if we get here no match found, set set default
  for (i = 0; i < env_list.options.length; i++) {
    if (env_list.options[i].text.startsWith('production')) {
      env_list.selectedIndex = i;
      s_element.textContent = env_list.options[i].text;
      return true;
    }
  }

  return true;
}
