# Sleep Number Bed Integration for Home Assistant

Component to control Sleep Number smart beds. The default SleepIQ integration in Home Assistant does not allow setting the sleep number. This one does.

## Setup

Copy files to `custom_components` directory, then add to `configuration.yaml`:

```
number:
  - platform: sleepiqplus
    username: email
    password: pass
```

## License

AGPL 3.0
