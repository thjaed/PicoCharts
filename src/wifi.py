import network # type: ignore
from time import sleep

import secrets
from config import VERBOSE_OUTPUT as v
from bootscreen import BootScreen

bs = BootScreen()

wifi_connected = False

def wifi_connect():
    bs.print("Connecting to WiFi")
    print("Connecting to WiFi")
    global wifi_connected, wlan
    # Init Wi-Fi Interface
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    
    # Scan for Wi-Fi networks
    networks = wlan.scan()

    # Print Wi-Fi networks
    if v: print("Available WiFi Networks:")
    for network_info in networks:
        print(network_info[0].decode('UTF-8'))
       
    for k in secrets.WIFI_NETWORKS: # Known networks
        for net_info in networks: # Available networks
            if k == net_info[0].decode('UTF-8'):
                if v: print(f"Found Known Network: {k}")
                bs.print(f"Found Network: {k}")
                try:
                    wlan.connect(k, secrets.WIFI_NETWORKS[k])
                     # Wait for Wi-Fi connection
                    connection_timeout = 10
                    while connection_timeout > 0:
                       if wlan.status() >= 3: # if connected
                           break
                       connection_timeout -= 1
                       if v: print('Waiting for Wi-Fi connection...')
                       bs.print(f"Connecting...")
                       sleep(1)
                    
                    if wlan.status() != 3:
                        bs.print(f"WiFi Connection Error")
                        raise RuntimeError('Failed to establish a network connection')
                    else:
                        wifi_connected = True
                        bs.print("Connection Successful")
                        print('Connection successful!')
                        network_info = wlan.ifconfig()
                        if v: print('IP address:', network_info[0])
                        break
                    
                except RuntimeError as e:
                    print(f"Error in connecting to {k}: {e}")