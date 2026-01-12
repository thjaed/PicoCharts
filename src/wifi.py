import network # type: ignore
import usocket # type: ignore

from time import sleep

import secrets

WIFI_TIMEOUT = 10
wifi_connected = None

def test_connection(type):
    try:
        if type == "BASIC":
            # Basic connectivity test
            # Needed because if DNS lookup fails, getaddrinfo hangs indefinetly
            addr = usocket.getaddrinfo("8.8.8.8", 53)[0][-1]
        elif type == "WEB":
            # ClassCharts connectivity test with DNS lookup
            addr = usocket.getaddrinfo("classcharts.com", 80)[0][-1]
        s = usocket.socket()
        s.settimeout(3)
        s.connect(addr)
        s.close()
        return True
    except Exception as e:
        return False
    
def wifi_connect():
    yield "Finding WiFi Networks"
    global wifi_connected, WIFI_TIMEOUT

    # Init Wi-Fi Interface
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    
    # Scan for Wi-Fi networks
    networks = wlan.scan()

    # Look for known networks
    found_nets = []
    for k in secrets.WIFI_NETWORKS:
        for net_info in networks:
            if k == net_info[0].decode('UTF-8'): # Decode network name
                found_nets.append(k)
    
    # Remove duplicate entries
    no_dups = []
    [no_dups.append(i) for i in found_nets if i not in no_dups]
    found_nets = no_dups

    if len(found_nets) == 0: # If no networks found
        wifi_connected = False
        yield "No networks found"
        yield False
    
    else: # If a known net was found
        tries = 0
        for net in found_nets:
            tries += 1
            yield f"Connecting to {net}"
            wlan.connect(net, secrets.WIFI_NETWORKS[net])

            # Wait for Wi-Fi connection
            while WIFI_TIMEOUT > 0:
                if wlan.status() >= 3: # if connected stop waiting
                    break
                WIFI_TIMEOUT -= 1
                sleep(1)
        
            # connection test
            basic_test = test_connection(type="BASIC")

            if wlan.status() != 3 or basic_test == False: # if not connected
                wifi_connected = False
                yield "Failed to connect"
                if tries == len(found_nets):
                    yield False
                    break

            elif basic_test and test_connection(type="WEB"): # if connected
                wifi_connected = True
                yield "Connection Succesful"
                yield True
                break