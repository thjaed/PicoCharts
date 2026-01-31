from time import sleep
import network # type: ignore
import usocket # type: ignore

import secrets
import state
import config

WIFI_TIMEOUT = 15

def test_connection():
    if not config.FORCE_OFFLINE:
        try:
            # Basic connectivity test
            # Needed because if DNS lookup fails, usocket.getaddrinfo hangs indefinetly
            addr = usocket.getaddrinfo("8.8.8.8", 53)[0][-1]
            s = usocket.socket()
            s.settimeout(3)
            s.connect(addr)
            s.close()
        except:
            state.WiFi.connected = False
            return False

        try:
            # ClassCharts connectivity test with DNS lookup
            addr = usocket.getaddrinfo("classcharts.com", 80)[0][-1]
            s = usocket.socket()
            s.settimeout(3)
            s.connect(addr)
            s.close()
        except:
            state.WiFi.connected = False
            return False

        state.WiFi.connected = True
        return True
    else:
        return False


    
def wifi_connect():
    if not config.FORCE_OFFLINE:
        yield "Finding WiFi Networks"
        global WIFI_TIMEOUT

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
            state.WiFi.connected = False
            yield "No networks found"

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
                test = test_connection()

                if wlan.status() != 3 or test == False: # if not connected
                    yield "Failed to connect"
                    if tries == len(found_nets):
                        state.WiFi.connected = False
                        break

                elif test == True: # if connected
                    yield "Connection Succesful"
                    break
    else:
        state.WiFi.connected == False
        yield "Offline Forced"