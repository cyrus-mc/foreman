#!/usr/bin/env bash

# source hook_functions.sh
source ~foreman/config/hooks/hook_functions.sh

# this is a simple hook, it drops a file in $TMPDIR indicating when a machine if first created
# other hooks will use this to drive logic

# the reason for the need for this script is that at this point in the provisioning process, the host isn't available
# via the API, so actions on the host itself can't be initiated. Other hooks / orchestration scripts will key off
# the file in $TMPDIR

TMPDIR='/tmp/foreman-hooks'

# check if $TMPDIR exists
if [[ -e $TMPDIR ]]; then

  if [[ ! -d $TMPDIR ]]; then
    # $TMPDIR exists but is a file, email admin so they can investigate (don't fail)
    exit 0
  fi
else
  # directory doesn't exist, create it
  mkdir -p $TMPDIR

  # check if success
  if [[ $? -ne 0 ]]; then
    # failed to create $TMPDIR, don't exit as that will cause the host to not be created at all
    # in this situation other hooks will not run as expected (they will assume host was already present)

    # send email so that someone can look into the issue
    exit 0
  fi
fi

# create file with filename = hostname
hostname=$(hook_data host.name)

if [[ -z $hostname ]]; then

  # failed to get hostname
  exit 0
fi

# create initial provisioning file, this file will be used by subsequent scripts to determine what has already been run
cat << _EOF_ > $TMPDIR/$hostname
---
name: $hostname
scripts:
 - create-initiate
_EOF_

# dump the whole contents of the event for debugging purposes
cp $HOOK_OBJECT_FILE $TMPDIR/${hostname}.after_build

#echo "STATE=create" > $TMPDIR/$hostname

if [[ $? -ne 0 ]]; then
  # failed, email someone so they can investigate what is going on
  exit 0
fi

