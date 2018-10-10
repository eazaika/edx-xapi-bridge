 Experience API Bridge
=========================

Python Parse the edX tracking log, convert the events to xAPI format, and publish them to an LRS.

As of August 2018 there is an official edX effort underway to integrate xAPI reporting to an LRS and other possible stores with the core edx-platform.  See [Open edX Proposal for xAPI Integration Support, primarily for Adaptive Learning capabilities.](https://github.com/edx/open-edx-proposals/pull/73).


## Installation

### Manual

```sh
$ git clone https://github.com/adlnet/edx-xapi-bridge.git
$ cd edx-xapi-bridge
$ virtualenv env
$ source env/bin/activate
(env)$ pip install -r requirements.txt
(env)$ deactivate
$ 
```

### Ansible

Appsembler, Inc.'s fork of the Open edX `configuration` repo provides an [Ansible role](https://github.com/appsembler/configuration/blob/appsembler/ficus/master/playbooks/roles/xapi_bridge/) to aid with installation.  The role will create the user, permissions, virtualenv, and Python dependencies to run the xapi_bridge.  Settings are still configured as below. 

## Configuration

Rename the file *xapi-bridge/settings-dist.py* to *settings.py* and change the properties to match your environment. There are several properties you will want to customize, and they are documented below.

* `PUBLISH_MAX_PAYLOAD` and `PUBLISH_MAX_WAIT_TIME`

	To save bandwidth and server time, the xAPI Bridge will publish edX events in batches of variable size, depending on the configuration. It will wait to publish a batch until either `PUBLISH_MAX_PAYLOAD` number of events have accumulated, or `PUBLISH_MAX_WAIT_TIME` seconds have elapsed since the oldest event was queued for publishing. You should tune these values based on the expected usage of the edX LMS and the performance of the LRS.
	
	Reasonable default values are `10` and `60`, respectively.

* `LRS_ENDPOINT`, `LRS_USERNAME`, `LRS_PASSWORD`, and `LRS_BASICAIUTH_HASH`

	The URL and login credentials of the LRS to which you want to publish edX events. The endpoint URL should end in a slash, e.g. `"http://mydoma.in/xAPI/"`.  For authentication to the LRS, you can use either `LRS_USERNAME` and `LRS_PASSWORD` in combination, or pass them combined as `LRS_BASICAUTH_HASH`.

* `OPENEDX_PLATFORM_URI`

    The URI to the Open edX LMS generating the parsed tracking logs.  Used to complete the `platform` parameter of the statements, and to access the User API for user information such as values for `mbox`. This should use the HTTPS scheme if the connection is not made over a private network.

* *OPENEDX_OAUTH2_CLIENT_ID*, *OPENEDX_OAUTH2_CLIENT_SECRET*

    The client_id and client_secret of an OAuth2 client created in your Open edX LMS.  This is used to authenticate to the LMS User API to retrieve email and name for users used as Actors in your xAPI statements.  To generate these,

    * Log in to your LMS with superuser credentials
    * Navigate to `/admin/oauth2/client/`
    * Click "Add client"
    * Create a new OAuth2 client specifying
      *  name: This can be anything but "edx-xapi-bridge" is a good default.
      *  user: `xapi_bridge`.  If you used [the Ansible role](https://github.com/appsembler/configuration/blob/appsembler/ficus/master/playbooks/roles/xapi_bridge/) for setting up xapi_bridge, this user already exists in your LMS.
      *  For url and redirect_url you can just specify https://github.com/appsembler/edx-xapi-bridge.  These aren't used since the xAPI bridge doesn't expose any URLs, but serve to indicate which application the client is for
      *  For client type, specify Confidential (Web application)
      *  Logout URL can be left blank
      *  Copy the auto-generated client id and client secret to *OPENEDX_OAUTH2_CLIENT_ID* and *OPENEDX_OAUTH2_CLIENT_SECRET* in your settings file.
    *  Also, if you are going to connect without using HTTPS (which you should only do for testing) you will need to set `EDXAPP_OAUTH_ENFORCE_SECURE: false` in your `lms.env.json` file.
      

* `IGNORED_EVENT_TYPES`
    
    A Python sequence of event types to ignore.  Elements should match the `"event_type"` value from the tracking log.
    

## Running

There is no process management yet, so just run the module directly:

```sh
$ source env/bin/activate
(env)$ python xapi-bridge [watchfile]
(env)$ deactivate
$
```

The program can optionally take one argument, which is the file path to the log to be watched. If omitted, it is assumed to be the default location in the edX Development Stack, `/edx/var/log/tracking.log`.

**NOTE**: The tracking log typically has very strict permissions on it, so make sure the user account running the xAPI-Bridge has permissions to read the log file.  If you used [the Ansible role](https://github.com/appsembler/configuration/blob/appsembler/ficus/master/playbooks/roles/xapi_bridge/) for setting up xapi_bridge, your xapi user already has these permissions.

## License

Copyright 2014 United States Government, as represented by the Secretary of Defense.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

