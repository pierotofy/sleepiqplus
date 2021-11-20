"""
Support for setting SleepIQ sleep number from SleepNumber.
"""

import logging

import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.helpers import discovery
from homeassistant.helpers.entity import Entity
from homeassistant.const import CONF_USERNAME, CONF_PASSWORD
from homeassistant.util import Throttle
from requests.exceptions import HTTPError

DOMAIN = 'sleepiqplus'

REQUIREMENTS = ['sleepyq==0.8.1']

LEFT = 'left'
RIGHT = 'right'
SIDES = [LEFT, RIGHT]

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Required(CONF_USERNAME): cv.string,
        vol.Required(CONF_PASSWORD): cv.string,
    }),
}, extra=vol.ALLOW_EXTRA)


def setup_platform(hass, config, add_entities, discovery_info=None):
    global client
    from sleepyq import Sleepyq
    username = config[DOMAIN][CONF_USERNAME]
    password = config[DOMAIN][CONF_PASSWORD]
    client = Sleepyq(username, password)
    
    try:
        client.login()
        beds = client.beds()
        add_entities(BedNumber(client, bed, LEFT) for bed in beds)
        add_entities(BedNumber(client, bed, RIGHT) for bed in beds)
    except Exception as e:
        _LOGGER.error("Cannot add bed entities: %s" % str(e))

    def handle_set_number(event):
        sleeper_name = event.data.get('sleeper')
        side = event.data.get('side')
        bed_name = event.data.get('bed')
        number = int(event.data.get('number'))
        
        if (sleeper_name or side) and bed_name:
            client.login()
            beds = client.beds()
            sleepers = client.sleepers()

            bed_id = next((b.data.get('bedId') for b in beds if b.data.get('name').lower() == bed_name.lower()), None)
            
            if sleeper_name:
                side_idx = next((s.data.get('side') for s in sleepers if s.data.get('firstName').lower() == sleeper_name.lower()), None)
                side = SIDES[side_idx]

            if bed_id is not None and side is not None:
                client.set_sleepnumber(side, number, bedId=bed_id)
            else:
                _LOGGER.error("Cannot find bedId/side index")
        else:
            _LOGGER.error("No sleeper and/or bed")

    # Capture event
    hass.bus.listen("sleepiq_set_number", handle_set_number)

    return True

class BedNumber(NumberEntity):
    def __init__(self, client, bed, side):
        """Initialize."""
        self.client = client
        self.bed = bed
        self.side = side

        self._name = bed.data.get('name') + side[0] + side[1:].lower()

        fav_data = self.client.get_favsleepnumber(bed.data.get('bedId')).data
        if side == LEFT:
            self._value = fav_data.get('sleepNumberFavoriteLeft')
        else:
            self._value = fav_data.get('sleepNumberFavoriteRight')

    @property
    def name(self):
        return self._name

    def set_value(self, value):
        """Update the current value."""
        try:
            self.client.login()
            self.client.set_sleepnumber(self.side, value, bedId=self.bed.data.get('bedId'))
            self._value = value
        except Exception as e:
            _LOGGER.error("Cannot set bed number: %s" % str(e))

    @property value(self):
        return self._value

    @property
    def min_value(self):
        return 0
    
    @property
    def max_value(self):
        return 100
    
    @property
    def step(self):
        return 5