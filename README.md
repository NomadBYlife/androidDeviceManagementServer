# AndroidResourceManagementServer

A python project using Django to allocate android devices, emulated and real,
to instance of build agents for our CI system  

#### Make Commands

Initial run:  

    make all 

Automated testing(no user created):  

    make auto

User creation:  

    make user

Just testing  

    make retest

Update packages/client  

    make update

Run server  

    make runserver

#### Configuration

The time frame how long notifications will be displayed for users can be configured in server_config.py  

    notification_min_time  
        sets how far in the future a notification can be marked as read
        which is the earliest point in time at which it can disappear
        
    notification_max_time  
        is a theoretical boundary
        the server will attempt to set a background task check timer so that the time a notification is
        being shown will always stay below this value
        if the chosen value is too low compared to the min_time it will be ignored

#### Required Ubuntu packages:  

    python3 python3-venv python3-dev

#### Callable URLs:  

example urls:  

    emulators1.testagent.dev.kobil.com:11359/admin/

    /admin/  
    accesses the admin page
    
    /admin/devices/device/
    probably the page you want most often
    lists all devices and their current state
    devices can be altered from here

    /devices/
    list of devices and their current status in JSON format

    /devices/detail/<device_key>/
    A specific device and its current status in JSON format.
    Where 'device_key' is equal to the collapsible entry in the "/devices/" list (without the trailing colon)

    /device/release/<device_key>/
    /devices/claim/<device_type>/
    /devices/function/<function_name>/<device_key>/
    These three URLs are only meant to be called by the script client used by automation.
    Use the admin pages instead if you want to alter a devices state manually or call one of its functions.
