html_tab: str = " &nbsp; &nbsp; &nbsp; "

device_type_help: str = \
    "This represents the name of a group of devices. <br>" \
    "When trying to claim a device the server is asked a question such as: <br>" \
    "%s Please give me a device of this type: '&lt;Device_type_definition&gt;' <br>" \
    "The server will then look for any devices of this type which he has configured and return the ip/port of an " \
    "available device in this group of devices." % html_tab

device_description_help: str = \
    "This is meant to provide information on the use or any special properties of the device."

device_status_help: str = \
    "This should represent the current state of the device. <br>" \
    "In most cases it should be set automatically if a working 'check_status' function is defined for the device " \
    "type. <br>" \
    "If this is not the case it should be set manually to 'On' if its turned on and you expect the device to be " \
    "available for claiming by a build agent."

device_enabled_help: str = \
    "If this is True/Set/Checked the device can be claimed by a build agent. (If it is 'On' and not yet claimed). <br>"

device_owner_help: str = \
    "This is the IP/DNS-name of the computer that made the request to claim the device. <br>" \
    "This may not always be set if this information is not available and is meant for debugging purposes. <br>" \
    "You should leave this blank in most cases as it will be set automatically. <br>" \
    "If you manually connect a device to a build agent it makes sense to use this field."

device_allocated_help: str = \
    "If this is True/Set/Checked the device is currently in a claimed state and cannot be claimed by another build " \
    "agent unless released first."

allocation_priority_help: str = \
    "This value determines the order in which devices are allocated to requests. Low first. High last. If two " \
    "devices have the same priority value which one will be allocated first is not officially determined although it " \
    "will have a set order." \

device_function_name_help: str = \
    "The name of the function. <br>" \
    "This will be displayed as the text for the buttons on the admin pages. <br>" \
    "A Script with this name with '.sh' attached to the end of it must exist in the appropriate folder on the " \
    "server. <br>" \
    "If wanted we can add the functionality to upload the scripts."

device_function_association_type: str = \
    "A function can only be defined for a specific type. The function (if the script by that name exists) will only " \
    "be available for that device type. <br>" \
    "This was done to allow different types of devices to be handled differently for certain default functions. <br>" \
    "Default function names: <br>" \
    "%s check_status <br>" \
    "%s restart <br>" \
    "%s start <br>" \
    "%s stop <br><br>" \
    "The server will call the restart function of a device type on a device every time it is released if the " \
    "restart function for that device type exists. If it does not exists the step is skipped. <br>" \
    "Future functionality will start/stop devices on demand. <br><br>" \
    "The currently implemented default functions for types are: <br>" \
    "%s for cloud-default all default functions <br>" \
    "%s for type-0 'check_status', 'restart' and 'check_params' <br>" \
    "The functions for type-0 are meant to be used for testing purposes and simply return an exit code and/or the " \
    "parameters passed to the function, which are determined by the devices current state" % \
    (html_tab, html_tab, html_tab, html_tab, html_tab, html_tab)
