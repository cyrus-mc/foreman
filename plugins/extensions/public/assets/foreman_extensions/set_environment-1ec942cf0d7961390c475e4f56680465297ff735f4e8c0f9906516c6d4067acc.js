function setEnvironment(t){var e=t.value.split("-")[0],n=document.getElementById("s2id_host_environment_id"),r=n.children[0].children[0],o=document.getElementById("host_environment_id");for(i=0;i<o.options.length;i++)if(o.options[i].text.startsWith(e))return o.selectedIndex=i,r.textContent=o.options[i].text,!0;for(i=0;i<o.options.length;i++)if(o.options[i].text.startsWith("production"))return o.selectedIndex=i,r.textContent=o.options[i].text,!0;return!0}