import time

import matplotlib.pyplot as plt
import numpy as np
import pywifi


# Step 1: Initialize PyWiFi Interface
def get_wifi_scanner():
    wifi = pywifi.PyWiFi()
    if len(wifi.interfaces()) == 0:
        raise RuntimeError("No Wi-Fi adapter detected on this system!")
    iface = wifi.interfaces()[0]  # Select primary Wi-Fi card
    return iface


# Step 2: Perform Real-Time Channel Scan
def scan_realtime_networks(iface):
    print("Initiating real-time 2.4 GHz spectrum scan...")
    iface.scan()
    time.sleep(3)  # Wait for scan buffer to populate
    scan_results = iface.scan_results()
    ap_list = []

    # 2.4 GHz Frequency to Channel Mapping
    freq_to_chan = {2412 + 5 * (ch - 1): ch for ch in range(1, 12)}
    for ap in scan_results:
        # Filter strictly for 2.4 GHz band (2412 MHz - 2462 MHz)
        # Handle frequency values reported in either kHz or MHz.
        freq_mhz = ap.freq / 1000 if ap.freq > 10000 else ap.freq
        if freq_mhz in freq_to_chan:
            channel = freq_to_chan[freq_mhz]
            ssid = ap.ssid if ap.ssid else "Hidden_AP"
            rssi = ap.signal  # RSSI in dBm
            ap_list.append(
                {
                    "ssid": ssid,
                    "channel": channel,
                    "freq": freq_mhz,
                    "rssi": rssi,
                }
            )
            print(
                f"Detected AP: SSID='{ssid}', Channel={channel}, "
                f"RSSI={rssi} dBm"
            )
    return ap_list


# Step 3: Spectral Curve Calculation
def generate_spectral_curve(freq_axis, center_freq, rssi_dbm, bw=20):
    # Convert RSSI (dBm) to Linear Power (mW) for realistic scale
    power_mw = 10 ** (rssi_dbm / 10.0)
    sigma = bw / 2.355
    return power_mw * np.exp(-0.5 * ((freq_axis - center_freq) / sigma) ** 2)


# Step 4: Main Execution and Real-Time Plotting
def main():
    try:
        iface = get_wifi_scanner()
        networks = scan_realtime_networks(iface)
        if not networks:
            print("No 2.4 GHz Access Points detected. Ensure Wi-Fi is enabled.")
            return

        # Frequency spectrum array (2.400 GHz to 2.485 GHz)
        freq_axis = np.linspace(2400, 2485, 1000)
        plt.figure(figsize=(11, 6))

        # Plot spectral mask for every detected real-time Access Point
        for net in networks:
            spectral_mask = generate_spectral_curve(
                freq_axis, net["freq"], net["rssi"]
            )
            label_text = (
                f"{net['ssid']} (Ch {net['channel']}, {net['rssi']} dBm)"
            )
            plt.plot(freq_axis, spectral_mask, label=label_text, linewidth=2)
            plt.fill_between(freq_axis, 0, spectral_mask, alpha=0.2)

        # Highlight standard non-overlapping channels (1, 6, 11) for reference
        plt.axvline(
            2412,
            color="green",
            linestyle="--",
            alpha=0.5,
            label="Ch 1 Center",
        )
        plt.axvline(
            2437,
            color="green",
            linestyle="--",
            alpha=0.5,
            label="Ch 6 Center",
        )
        plt.axvline(
            2462,
            color="green",
            linestyle="--",
            alpha=0.5,
            label="Ch 11 Center",
        )
        plt.title(
            "Real-Time 2.4 GHz Wi-Fi Channel Interference & Power Spectrum",
            fontsize=12,
            fontweight="bold",
        )
        plt.xlabel("Frequency (MHz)", fontsize=10)
        plt.ylabel("Received Power (milliwatts mW)", fontsize=10)
        plt.grid(True, linestyle=":", alpha=0.6)
        plt.legend(loc="upper right", bbox_to_anchor=(1.35, 1.0))
        plt.tight_layout()
        plt.show()
    except Exception as e:
        print(f"Error executing real-time scan: {e}")


if __name__ == "__main__":
    main()
