from relays.two_port_relay import relay_on_off

relay_on_off('open','01')

time.sleep(5)

relay_on_off('close','01')