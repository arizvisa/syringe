import ptypes
from .. import layer, stackable, terminal
from .. import utils, address

class LINKTYPE_(ptypes.pint.enum):
    '''https://www.tcpdump.org/linktypes.html -- LINKTYPE_'''
    _values_ = [
        ('NULL', 0),                            # BSD loopback encapsulation.
        ('ETHERNET', 1),                        # IEEE 802.3 Ethernet (10Mb, 100Mb, 1000Mb, and up); the 10MB in the DLT_ name is historical.
        ('EXP_ETHERNET', 2),                    # Experimental Ethernet (3Mb).
        ('AX25', 3),                            # AX.25 layer 2 packets,
        ('PRONET', 4),                          # Reserved for Proteon ProNET Token Ring.
        ('CHAOS', 5),                           # Reserved for MIT Chaosnet.
        ('IEEE802_5', 6),                       # IEEE 802.5 Token Ring; the IEEE802, without _5, in the DLT_ name is historical.
        ('ARCNET_BSD', 7),                      # Reserved for ARCNET Data Packets with BSD encapsulation.
        ('SLIP', 8),                            # SLIP, with a header giving packet direction
        ('PPP', 9),                             # PPP.
        ('FDDI', 10),                           # FDDI, as specified by ANSI INCITS 239-1994.
        ('PPP_HDLC', 50),                       # PPP in HDLC-like framing.
        ('PPP_ETHER', 51),                      # PPPoE session packets.
        ('SYMANTEC_FIREWALL', 99),              # Symantec Enterprise (ex-Axent Raptor) firewall.
        ('ATM_RFC1483', 100),                   # LLC/SNAP-encapsulated ATM
        ('RAW', 101),                           # Raw IP; the packet begins with an IPv4 or IPv6 header, with the version field of the header indicating whether it's an IPv4 or IPv6 header.
        ('C_HDLC', 104),                        # Cisco PPP with HDLC framing.
        ('IEEE802_11', 105),                    # IEEE 802.11 wireless LAN.
        ('ATM_CLIP', 106),                      # Linux Classical IP over ATM.
        ('FRELAY', 107),                        # Frame Relay LAPF.
        ('LOOP', 108),                          # OpenBSD loopback encapsulation.
        ('ENC', 109),                           # Encapsulated packets for IPsec.
        ('NETBSD_HDLC', 112),                   # Cisco HDLC.
        ('LINUX_SLL', 113),                     # Linux "cooked" capture encapsulation.
        ('LTALK', 114),                         # Apple LocalTalk packets.
        ('PFLOG', 117),                         # OpenBSD pflog; the link-layer header contains a struct pfloghdr structure, as defined by the host on that the file was saved. (This differs from operating system to operating system and release to release; there is nothing in the file to indicate what the layout of that structure is.)
        ('IEEE802_11_PRISM', 119),              # Prism monitor mode information, followed by an 802.11 frame.
        ('IP_OVER_FC', 122),                    # IP and ATM over Fibre Channel.
        ('SUNATM', 123),                        # ATM traffic captured from a SunATM device.
        ('IEEE802_11_RADIOTAP', 127),           # Radiotap link-layer information followed by an 802.11 header.
        ('TZSP', 128),                          # Tazmen Sniffer Protocol (TZSP) is a generic encapsulation for any other link type, which includes a means to include meta-information with the packet, e.g. signal strength and channel for 802.11 packets.
        ('ARCNET_LINUX', 129),                  # ARCnet Data Packets with Linux encapsulation.
        ('JUNIPER_MLPPP', 130),                 # Juniper Networks private data link type.
        ('JUNIPER_MLFR', 131),                  # Juniper Networks private data link type.
        ('JUNIPER_ES', 132),                    # Juniper Networks private data link type.
        ('JUNIPER_GGSN', 133),                  # Juniper Networks private data link type.
        ('JUNIPER_MFR', 134),                   # Juniper Networks private data link type.
        ('JUNIPER_ATM2', 135),                  # Juniper Networks private data link type.
        ('JUNIPER_SERVICES', 136),              # Juniper Networks private data link type.
        ('JUNIPER_ATM1', 137),                  # Juniper Networks private data link type.
        ('APPLE_IP_OVER_IEEE1394', 138),        # Apple IP-over-IEEE 1394 cooked header.
        ('MTP2_WITH_PHDR', 139),                # SS7 MTP2 packets, with a pseudo-header.
        ('MTP2', 140),                          # SS7 MTP2 packets.
        ('MTP3', 141),                          # SS7 MTP3 packets.
        ('SCCP', 142),                          # SS7 SCCP packets.
        ('DOCSIS', 143),                        # DOCSIS MAC frames, as described by the DOCSIS 4.0 MAC and Upper Layer Protocols Interface Specification or earlier specifications for MAC frames.
        ('LINUX_IRDA', 144),                    # Linux-IrDA packets
        ('IBM_SP', 145),                        # IBM SP switch.
        ('IBM_SN', 146),                        # IBM Next Federation switch.
        ('USER0', 147),                         # Reserved for private use; see above.
        ('USER1', 148),                         # Reserved for private use; see above.
        ('USER2', 149),                         # Reserved for private use; see above.
        ('USER3', 150),                         # Reserved for private use; see above.
        ('USER4', 151),                         # Reserved for private use; see above.
        ('USER5', 152),                         # Reserved for private use; see above.
        ('USER6', 153),                         # Reserved for private use; see above.
        ('USER7', 154),                         # Reserved for private use; see above.
        ('USER8', 155),                         # Reserved for private use; see above.
        ('USER9', 156),                         # Reserved for private use; see above.
        ('USER10', 157),                        # Reserved for private use; see above.
        ('USER11', 158),                        # Reserved for private use; see above.
        ('USER12', 159),                        # Reserved for private use; see above.
        ('USER13', 160),                        # Reserved for private use; see above.
        ('USER14', 161),                        # Reserved for private use; see above.
        ('USER15', 162),                        # Reserved for private use; see above.
        ('IEEE802_11_AVS', 163),                # AVS monitor mode information followed by an 802.11 header.
        ('JUNIPER_MONITOR', 164),               # Juniper Networks private data link type.
        ('BACNET_MS_TP', 165),                  # BACnet MS/TP frames.
        ('PPP_PPPD', 166),                      # PPP preceded by a direction octet and an HDLC-like control field.
        ('JUNIPER_PPPOE', 167),                 # Juniper Networks private data link type.
        ('JUNIPER_PPPOE_ATM', 168),             # Juniper Networks private data link type.
        ('GPRS_LLC', 169),                      # General Packet Radio Service Logical Link Control, as defined by 3GPP TS 04.64.
        ('GPF_T', 170),                         # Transparent-mapped generic framing procedure, as specified by ITU-T Recommendation G.7041/Y.1303.
        ('GPF_F', 171),                         # Frame-mapped generic framing procedure, as specified by ITU-T Recommendation G.7041/Y.1303.
        ('GCOM_T1E1', 172),                     # Gcom's T1/E1 line monitoring equipment.
        ('GCOM_SERIAL', 173),                   # Gcom's T1/E1 line monitoring equipment.
        ('JUNIPER_PIC_PEER', 174),              # Juniper Networks private data link type.
        ('ERF_ETH', 175),                       # Endace ERF records of type TYPE_ETH.
        ('ERF_POS', 176),                       # Endace ERF records of type TYPE_POS_HDLC.
        ('LINUX_LAPD', 177),                    # Linux vISDN LAPD frames
        ('JUNIPER_ETHER', 178),                 # Juniper Networks private data link type. Ethernet frames prepended with meta-information.
        ('JUNIPER_PPP', 179),                   # Juniper Networks private data link type. PPP frames prepended with meta-information.
        ('JUNIPER_FRELAY', 180),                # Juniper Networks private data link type. Frame Relay frames prepended with meta-information.
        ('JUNIPER_CHDLC', 181),                 # Juniper Networks private data link type. C-HDLC frames prepended with meta-information.
        ('MFR', 182),                           # FRF.16.1 Multi-Link Frame Relay frames.
        ('JUNIPER_VP', 183),                    # Juniper Networks private data link type.
        ('A429', 184),                          # ARINC 429 frames. Every frame contains a 32-bit A429 word, in little-endian format.
        ('A653_ICM', 185),                      # ARINC 653 interpartition communication messages. Please refer to the A653-1 standard for more information.
        ('USB_FREEBSD', 186),                   # USB with FreeBSD header.
        ('BLUETOOTH_HCI_H4', 187),              # Bluetooth HCI UART Transport Layer packets.
        ('IEEE802_16_MAC_CPS', 188),            # IEEE 802.16 MAC Common Part Sublayer.
        ('USB_LINUX', 189),                     # USB packets, beginning with a Linux USB header.
        ('CAN20B', 190),                        # Controller Area Network (CAN) v. 2.0B.
        ('IEEE802_15_4_LINUX', 191),            # IEEE 802.15.4, with address fields padded, as is done by Linux drivers.
        ('PPI', 192),                           # Per-Packet Information header preceding packet data.
        ('IEEE802_16_MAC_CPS_RADIO', 193),      # IEEE 802.16 MAC Common Part Sublayer plus radiotap header.
        ('JUNIPER_ISM', 194),                   # Juniper Networks private data link type.
        ('IEEE802_15_4_WITHFCS', 195),          # IEEE 802.15.4 packets with FCS.
        ('SITA', 196),                          # Various link-layer types, with a pseudo-header, for SITA.
        ('ERF', 197),                           # Endace ERF records.
        ('RAIF1', 198),                         # Special header prepended to Ethernet packets when capturing from a u10 Networks board.
        ('IPMB_KONTRON', 199),                  # IPMB packet for IPMI, beginning with a 2-byte header, followed by the I2C slave address, followed by the netFn and LUN, etc…
        ('JUNIPER_ST', 200),                    # Juniper Networks private data link type.
        ('BLUETOOTH_HCI_H4_WITH_PHDR', 201),    # Bluetooth HCI UART Transport Layer packets with a direction pseudo-header.
        ('AX25_KISS', 202),                     # KISS frames between a host and an AX.25 TNC.
        ('LAPD', 203),                          # Q.921 LAPD frames.
        ('PPP_WITH_DIR', 204),                  # PPP, with a direction header.
        ('C_HDLC_WITH_DIR', 205),               # Cisco PPP with HDLC framing, with a direction header.
        ('FRELAY_WITH_DIR', 206),               # Frame Relay LAPF, with a direction header.
        ('LAPB_WITH_DIR', 207),                 # X.25 LAPB, with a direction header.
        ('IPMB_LINUX', 209),                    # Legacy names (do not use) for Linux I2C below.
        ('I2C_LINUX', 209),                     # Linux I2C packets.
        ('FLEXRAY', 210),                       # FlexRay automotive bus frames or symbols, preceded by a pseudo-header
        ('MOST', 211),                          # Media Oriented Systems Transport (MOST) bus for multimedia transport.
        ('LIN', 212),                           # Local Interconnect Network (LIN) automotive bus, with a metadata header
        ('X2E_SERIAL', 213),                    # X2E-private data link type used for serial line capture.
        ('X2E_XORAYA', 214),                    # X2E-private data link type used for the Xoraya data logger family.
        ('IEEE802_15_4_NONASK_PHY', 215),       # IEEE 802.15.4 packets with PHY header.
        ('LINUX_EVDEV', 216),                   # Linux evdev events from /dev/input/eventN devices.
        ('GSMTAP_UM', 217),                     # GSM Um interface, preceded by a "gsmtap" header.
        ('GSMTAP_ABIS', 218),                   # GSM Abis interface, preceded by a "gsmtap" header.
        ('MPLS', 219),                          # MPLS, with an MPLS label as the link-layer header.
        ('USB_LINUX_MMAPPED', 220),             # USB packets, beginning with an extended Linux USB header.
        ('DECT', 221),                          # DECT packets, with a pseudo-header.
        ('AOS', 222),                           # AOS Space Data Link Protocol.
        ('WIHART', 223),                        # WirelessHART (Highway Addressable Remote Transducer) from the HART Communication Foundation (IEC/PAS 62591).
        ('FC_2', 224),                          # Fibre Channel FC-2 frames.
        ('FC_2_WITH_FRAME_DELIMS', 225),        # Fibre Channel FC-2 frames with SOF and EOF.
        ('IPNET', 226),                         # Solaris ipnet
        ('CAN_SOCKETCAN', 227),                 # Controller Area Network (CAN) frames, with a metadata header.
        ('IPV4', 228),                          # Raw IPv4; the packet begins with an IPv4 header.
        ('IPV6', 229),                          # Raw IPv6; the packet begins with an IPv6 header.
        ('IEEE802_15_4_NOFCS', 230),            # IEEE 802.15.4 packets without FCS.
        ('DBUS', 231),                          # Raw D-Bus messages.
        ('JUNIPER_VS', 232),                    # Juniper Networks private data link type.
        ('JUNIPER_SRX_E2E', 233),               # Juniper Networks private data link type.
        ('JUNIPER_FIBRECHANNEL', 234),          # Juniper Networks private data link type.
        ('DVB_CI', 235),                        # DVB-CI messages, with a pseudo-header.
        ('MUX27010', 236),                      # Variant of 3GPP TS 27.010 multiplexing protocol.
        ('STANAG_5066_D_PDU', 237),             # STANAG 5066 D_PDUs.
        ('JUNIPER_ATM_CEMIC', 238),             # Juniper Networks private data link type.
        ('NFLOG', 239),                         # Linux netlink NETLINK NFLOG socket log messages.
        ('NETANALYZER', 240),                   # Ethernet frames with Hilscher netANALYZER pseudo-header.
        ('NETANALYZER_TRANSPARENT', 241),       # Ethernet frames with netANALYZER pseudo-header, preamble and SFD, preceded by a Hilscher.
        ('IPOIB', 242),                         # IP-over-InfiniBand.
        ('MPEG_2_TS', 243),                     # MPEG-2 Transport Stream transport packets.
        ('NG40', 244),                          # Frames from ng4T GmbH's ng40 protocol tester.
        ('NFC_LLCP', 245),                      # NFC Logical Link Control Protocol frames, with a pseudo-header.
        ('PFSYNC', 246),                        # Packet filter state syncing.
        ('INFINIBAND', 247),                    # InfiniBand data packets.
        ('SCTP', 248),                          # SCTP packets, as defined by RFC 4960, with no lower-level protocols such as IPv4 or IPv6.
        ('USBPCAP', 249),                       # USB packets, beginning with a USBPcap header.
        ('RTAC_SERIAL', 250),                   # Serial-line packets from the Schweitzer Engineering Laboratories "RTAC" product.
        ('BLUETOOTH_LE_LL', 251),               # Bluetooth Low Energy link-layer packets.
        ('WIRESHARK_UPPER_PDU', 252),           # Upper-protocol layer PDU saves from Wireshark; the actual contents are determined by two tags, one or more of which is stored with each packet.
        ('NETLINK', 253),                       # Linux Netlink capture encapsulation.
        ('BLUETOOTH_LINUX_MONITOR', 254),       # Bluetooth Linux Monitor.
        ('BLUETOOTH_BREDR_BB', 255),            # Bluetooth Basic Rate and Enhanced Data Rate baseband packets.
        ('BLUETOOTH_LE_LL_WITH_PHDR', 256),     # Bluetooth Low Energy link-layer packets, with a pseudo-header.
        ('PROFIBUS_DL', 257),                   # PROFIBUS data link layer packets.
        ('PKTAP', 258),                         # Apple PKTAP capture encapsulation.
        ('EPON', 259),                          # Ethernet-over-passive-optical-network packets, including preamble octets.
        ('IPMI_HPM_2', 260),                    # IPMI HPM.2 trace packets.
        ('ZWAVE_R1_R2', 261),                   # Z-Wave RF profile R1 and R2 packets.
        ('ZWAVE_R3', 262),                      # Z-Wave RF profile R3 packets.
        ('WATTSTOPPER_DLM', 263),               # WattStopper Digital Lighting Management (DLM) and Legrand Nitoo Open protocol packets.
        ('ISO_14443', 264),                     # Messages between ISO 14443 contactless smartcards (Proximity Integrated Circuit Card, PICC) and card readers (Proximity Coupling Device, PCD), with the message format specified by the PCAP format for ISO14443 specification.
        ('RDS', 265),                           # IEC 62106 Radio data system (RDS) groups.
        ('USB_DARWIN', 266),                    # USB packets captured on a Darwin-based operating system (macOS, etc.).
        ('OPENFLOW', 267),                      # OpenFlow messages with an additional 12-octet header, as used in OpenBSD switch interface monitoring.
        ('SDLC', 268),                          # SNA SDLC packets
        ('TI_LLN_SNIFFER', 269),                # TI LLN sniffer frames.
        ('LORATAP', 270),                       # LoRaWan packets with a LoRaTap pseudo-header.
        ('VSOCK', 271),                         # Protocol for communication between host and guest machines in VMware and KVM hypervisors.
        ('NORDIC_BLE', 272),                    # Messages to and from a Nordic Semiconductor nRF Sniffer for Bluetooth LE packets.
        ('DOCSIS31_XRA31', 273),                # DOCSIS packets and bursts, preceded by a pseudo-header giving metadata about the packet.
        ('ETHERNET_MPACKET', 274),              # IEEE 802.3 mPackets.
        ('DISPLAYPORT_AUX', 275),               # DisplayPort AUX channel monitoring messages.
        ('LINUX_SLL2', 276),                    # Linux "cooked" capture encapsulation v2.
        ('SERCOS_MONITOR', 277),                # Sercos Monitor.
        ('OPENVIZSLA', 278),                    # OpenVizsla FPGA-based USB sniffer frames.
        ('EBHSCR', 279),                        # Elektrobit High Speed Capture and Replay (EBHSCR) format.
        ('VPP_DISPATCH', 280),                  # Records in traces from the http://fd.io VPP graph dispatch tracer, in the the graph dispatcher trace format.
        ('DSA_TAG_BRCM', 281),                  # Ethernet frames, with a Broadcom switch tag inserted.
        ('DSA_TAG_BRCM_PREPEND', 282),          # Ethernet frames, with a Broadcom switch tag prepended.
        ('IEEE802_15_4_TAP', 283),              # IEEE 802.15.4 packets, with a pseudo-header containing TLVs with metadata preceding the 802.15.4 header.
        ('DSA_TAG_DSA', 284),                   # Ethernet frames, with a Marvell DSA switch tag inserted.
        ('DSA_TAG_EDSA', 285),                  # Ethernet frames, with a Marvell EDSA switch tag inserted.
        ('ELEE', 286),                          # Reserved for ELEE lawful intercept protocol.
        ('Z_WAVE_SERIAL', 287),                 # Serial frames transmitted between a host and a Z-Wave chip over an RS-232 or USB serial connection, as described in section 5 of the Z-Wave Serial API Host Application Programming Guide.
        ('USB_2_0', 288),                       # USB 2.0, 1.1, or 1.0 packets.
        ('ATSC_ALP', 289),                      # ATSC Link-Layer Protocol frames.
        ('ETW', 290),                           # Event Tracing for Windows messages.
        ('NETANALYZER_NG', 291),                # Reserved for Hilscher Gesellschaft fuer Systemautomation mbH netANALYZER NG hardware and software.
        ('ZBOSS_NCP', 292),                     # ZBOSS NCP Serial Protocol, with a pseudo-header.
        ('USB_2_0_LOW_SPEED', 293),             # Low-Speed USB 2.0, 1.1, or 1.0 packets..
        ('USB_2_0_FULL_SPEED', 294),            # Full-Speed USB 2.0, 1.1, or 1.0 packets.
        ('USB_2_0_HIGH_SPEED', 295),            # High-Speed USB 2.0 packets.
        ('AUERSWALD_LOG', 296),                 # Auerswald Logger Protocol packets.
        ('ZWAVE_TAP', 297),                     # Z-Wave packets, with a metadata header.
        ('SILABS_DEBUG_CHANNEL', 298),          # Silicon Labs debug channel protocol, as described in the specification.
        ('FIRA_UCI', 299),                      # Ultra-wideband (UWB) controller interface protocol (UCI).
        ('MDB', 300),                           # MDB (Multi-Drop Bus) messages, with a pseudo-header.
        ('DECT_NR', 301),                       # DECT-2020 New Radio (NR) MAC layer.
    ]

class DLT_(ptypes.pint.enum):
    '''https://www.tcpdump.org/linktypes.html -- DLT_'''
    _values_ = [
        ('NULL', 0),                                # BSD loopback encapsulation.
        ('EN10MB', 1),                              # IEEE 802.3 Ethernet (10Mb, 100Mb, 1000Mb, and up); the 10MB in the DLT_ name is historical.
        ('EN3MB', 2),                               # Experimental Ethernet (3Mb).
        ('AX25', 3),                                # AX.25 layer 2 packets,
        ('PRONET', 4),                              # Reserved for Proteon ProNET Token Ring.
        ('CHAOS', 5),                               # Reserved for MIT Chaosnet.
        ('IEEE802', 6),                             # IEEE 802.5 Token Ring; the IEEE802, without _5, in the DLT_ name is historical.
        ('ARCNET', 7),                              # Reserved for ARCNET Data Packets with BSD encapsulation.
        ('SLIP', 8),                                # SLIP, with a header giving packet direction
        ('PPP', 9),                                 # PPP.
        ('FDDI', 10),                               # FDDI, as specified by ANSI INCITS 239-1994.
        ('REDBACK_SMARTEDGE', 32),                  # Redback SmartEdge 400/800.
        ('PPP_SERIAL', 50),                         # PPP in HDLC-like framing.
        ('PPP_ETHER', 51),                          # PPPoE session packets.
        ('SYMANTEC_FIREWALL', 99),                  # Symantec Enterprise (ex-Axent Raptor) firewall.
        ('ATM_RFC1483', 100),                       # LLC/SNAP-encapsulated ATM
        ('RAW', 101),                               # Raw IP; the packet begins with an IPv4 or IPv6 header, with the version field of the header indicating whether it's an IPv4 or IPv6 header.
        ('C_HDLC', 104),                            # Cisco PPP with HDLC framing.
        ('IEEE802_11', 105),                        # IEEE 802.11 wireless LAN.
        ('ATM_CLIP', 106),                          # Linux Classical IP over ATM.
        ('FRELAY', 107),                            # Frame Relay LAPF.
        ('LOOP', 108),                              # OpenBSD loopback encapsulation.
        ('ENC', 109),                               # Encapsulated packets for IPsec.
        ('HDLC', 112),                              # Cisco HDLC.
        ('LINUX_SLL', 113),                         # Linux "cooked" capture encapsulation.
        ('LTALK', 114),                             # Apple LocalTalk packets.
        ('ECONET', 115),                            # Acorn Econet.
        ('IPFILTER', 116),                          # OpenBSD ipfilter.
        ('PFLOG', 117),                             # OpenBSD pflog; the link-layer header contains a struct pfloghdr structure, as defined by the host on that the file was saved. (This differs from operating system to operating system and release to release; there is nothing in the file to indicate what the layout of that structure is.)
        ('CISCO_IOS', 118),                         # Cisco internal use.
        ('PRISM_HEADER', 119),                      # Prism monitor mode information, followed by an 802.11 frame.
        ('AIRONET_HEADER', 120),                    # Reserved for Aironet 802.11 cards, with an Aironet link-layer header.
        ('IP_OVER_FC', 122),                        # IP and ATM over Fibre Channel.
        ('SUNATM', 123),                            # ATM traffic captured from a SunATM device.
        ('RIO', 124),                               # RapidIO.
        ('PCI_EXP', 125),                           # PCI Express.
        ('AURORA', 126),                            # Xilinx Aurora.
        ('IEEE802_11_RADIO', 127),                  # Radiotap link-layer information followed by an 802.11 header.
        ('TZSP', 128),                              # Tazmen Sniffer Protocol (TZSP) is a generic encapsulation for any other link type, which includes a means to include meta-information with the packet, e.g. signal strength and channel for 802.11 packets.
        ('ARCNET_LINUX', 129),                      # ARCnet Data Packets with Linux encapsulation.
        ('JUNIPER_MLPPP', 130),                     # Juniper Networks private data link type.
        ('JUNIPER_MLFR', 131),                      # Juniper Networks private data link type.
        ('JUNIPER_ES', 132),                        # Juniper Networks private data link type.
        ('JUNIPER_GGSN', 133),                      # Juniper Networks private data link type.
        ('JUNIPER_MFR', 134),                       # Juniper Networks private data link type.
        ('JUNIPER_ATM2', 135),                      # Juniper Networks private data link type.
        ('JUNIPER_SERVICES', 136),                  # Juniper Networks private data link type.
        ('JUNIPER_ATM1', 137),                      # Juniper Networks private data link type.
        ('APPLE_IP_OVER_IEEE1394', 138),            # Apple IP-over-IEEE 1394 cooked header.
        ('MTP2_WITH_PHDR', 139),                    # SS7 MTP2 packets, with a pseudo-header.
        ('MTP2', 140),                              # SS7 MTP2 packets.
        ('MTP3', 141),                              # SS7 MTP3 packets.
        ('SCCP', 142),                              # SS7 SCCP packets.
        ('DOCSIS', 143),                            # DOCSIS MAC frames, as described by the DOCSIS 4.0 MAC and Upper Layer Protocols Interface Specification or earlier specifications for MAC frames.
        ('LINUX_IRDA', 144),                        # Linux-IrDA packets
        ('IBM_SP', 145),                            # IBM SP switch.
        ('IBM_SN', 146),                            # IBM Next Federation switch.
        ('USER0', 147),                             # Reserved for private use; see above.
        ('USER1', 148),                             # Reserved for private use; see above.
        ('USER2', 149),                             # Reserved for private use; see above.
        ('USER3', 150),                             # Reserved for private use; see above.
        ('USER4', 151),                             # Reserved for private use; see above.
        ('USER5', 152),                             # Reserved for private use; see above.
        ('USER6', 153),                             # Reserved for private use; see above.
        ('USER7', 154),                             # Reserved for private use; see above.
        ('USER8', 155),                             # Reserved for private use; see above.
        ('USER9', 156),                             # Reserved for private use; see above.
        ('USER10', 157),                            # Reserved for private use; see above.
        ('USER11', 158),                            # Reserved for private use; see above.
        ('USER12', 159),                            # Reserved for private use; see above.
        ('USER13', 160),                            # Reserved for private use; see above.
        ('USER14', 161),                            # Reserved for private use; see above.
        ('USER15', 162),                            # Reserved for private use; see above.
        ('IEEE802_11_RADIO_AVS', 163),              # AVS monitor mode information followed by an 802.11 header.
        ('JUNIPER_MONITOR', 164),                   # Juniper Networks private data link type.
        ('BACNET_MS_TP', 165),                      # BACnet MS/TP frames.
        ('PPP_PPPD', 166),                          # PPP preceded by a direction octet and an HDLC-like control field.
        ('JUNIPER_PPPOE', 167),                     # Juniper Networks private data link type.
        ('JUNIPER_PPPOE_ATM', 168),                 # Juniper Networks private data link type.
        ('GPRS_LLC', 169),                          # General Packet Radio Service Logical Link Control, as defined by 3GPP TS 04.64.
        ('GPF_T', 170),                             # Transparent-mapped generic framing procedure, as specified by ITU-T Recommendation G.7041/Y.1303.
        ('GPF_F', 171),                             # Frame-mapped generic framing procedure, as specified by ITU-T Recommendation G.7041/Y.1303.
        ('GCOM_T1E1', 172),                         # Gcom's T1/E1 line monitoring equipment.
        ('GCOM_SERIAL', 173),                       # Gcom's T1/E1 line monitoring equipment.
        ('JUNIPER_PIC_PEER', 174),                  # Juniper Networks private data link type.
        ('ERF_ETH', 175),                           # Endace ERF records of type TYPE_ETH.
        ('ERF_POS', 176),                           # Endace ERF records of type TYPE_POS_HDLC.
        ('LINUX_LAPD', 177),                        # Linux vISDN LAPD frames
        ('JUNIPER_ETHER', 178),                     # Juniper Networks private data link type. Ethernet frames prepended with meta-information.
        ('JUNIPER_PPP', 179),                       # Juniper Networks private data link type. PPP frames prepended with meta-information.
        ('JUNIPER_FRELAY', 180),                    # Juniper Networks private data link type. Frame Relay frames prepended with meta-information.
        ('JUNIPER_CHDLC', 181),                     # Juniper Networks private data link type. C-HDLC frames prepended with meta-information.
        ('MFR', 182),                               # FRF.16.1 Multi-Link Frame Relay frames.
        ('JUNIPER_VP', 183),                        # Juniper Networks private data link type.
        ('A429', 184),                              # ARINC 429 frames. Every frame contains a 32-bit A429 word, in little-endian format.
        ('A653_ICM', 185),                          # ARINC 653 interpartition communication messages. Please refer to the A653-1 standard for more information.
        ('USB_FREEBSD', 186),                       # USB with FreeBSD header.
        ('BLUETOOTH_HCI_H4', 187),                  # Bluetooth HCI UART Transport Layer packets.
        ('IEEE802_16_MAC_CPS', 188),                # IEEE 802.16 MAC Common Part Sublayer.
        ('USB_LINUX', 189),                         # USB packets, beginning with a Linux USB header.
        ('CAN20B', 190),                            # Controller Area Network (CAN) v. 2.0B.
        ('IEEE802_15_4_LINUX', 191),                # IEEE 802.15.4, with address fields padded, as is done by Linux drivers.
        ('PPI', 192),                               # Per-Packet Information header preceding packet data.
        ('IEEE802_16_MAC_CPS_RADIO', 193),          # IEEE 802.16 MAC Common Part Sublayer plus radiotap header.
        ('JUNIPER_ISM', 194),                       # Juniper Networks private data link type.
        ('IEEE802_15_4_WITHFCS', 195),              # IEEE 802.15.4 packets with FCS.
        ('SITA', 196),                              # Various link-layer types, with a pseudo-header, for SITA.
        ('ERF', 197),                               # Endace ERF records.
        ('RAIF1', 198),                             # Special header prepended to Ethernet packets when capturing from a u10 Networks board.
        ('IPMB_KONTRON', 199),                      # IPMB packet for IPMI, beginning with a 2-byte header, followed by the I2C slave address, followed by the netFn and LUN, etc…
        ('JUNIPER_ST', 200),                        # Juniper Networks private data link type.
        ('BLUETOOTH_HCI_H4_WITH_PHDR', 201),        # Bluetooth HCI UART Transport Layer packets with a direction pseudo-header.
        ('AX25_KISS', 202),                         # KISS frames between a host and an AX.25 TNC.
        ('LAPD', 203),                              # Q.921 LAPD frames.
        ('PPP_WITH_DIR', 204),                      # PPP, with a direction header.
        ('C_HDLC_WITH_DIR', 205),                   # Cisco PPP with HDLC framing, with a direction header.
        ('FRELAY_WITH_DIR', 206),                   # Frame Relay LAPF, with a direction header.
        ('LAPB_WITH_DIR', 207),                     # X.25 LAPB, with a direction header.
        ('IPMB_LINUX', 209),                        # Legacy names (do not use) for Linux I2C below.
        ('I2C_LINUX', 209),                         # Linux I2C packets.
        ('FLEXRAY', 210),                           # FlexRay automotive bus frames or symbols, preceded by a pseudo-header
        ('MOST', 211),                              # Media Oriented Systems Transport (MOST) bus for multimedia transport.
        ('LIN', 212),                               # Local Interconnect Network (LIN) automotive bus, with a metadata header
        ('X2E_SERIAL', 213),                        # X2E-private data link type used for serial line capture.
        ('X2E_XORAYA', 214),                        # X2E-private data link type used for the Xoraya data logger family.
        ('IEEE802_15_4_NONASK_PHY', 215),           # IEEE 802.15.4 packets with PHY header.
        ('LINUX_EVDEV', 216),                       # Linux evdev events from /dev/input/eventN devices.
        ('GSMTAP_UM', 217),                         # GSM Um interface, preceded by a "gsmtap" header.
        ('GSMTAP_ABIS', 218),                       # GSM Abis interface, preceded by a "gsmtap" header.
        ('MPLS', 219),                              # MPLS, with an MPLS label as the link-layer header.
        ('USB_LINUX_MMAPPED', 220),                 # USB packets, beginning with an extended Linux USB header.
        ('DECT', 221),                              # DECT packets, with a pseudo-header.
        ('AOS', 222),                               # AOS Space Data Link Protocol.
        ('WIHART', 223),                            # WirelessHART (Highway Addressable Remote Transducer) from the HART Communication Foundation (IEC/PAS 62591).
        ('FC_2', 224),                              # Fibre Channel FC-2 frames.
        ('FC_2_WITH_FRAME_DELIMS', 225),            # Fibre Channel FC-2 frames with SOF and EOF.
        ('IPNET', 226),                             # Solaris ipnet
        ('CAN_SOCKETCAN', 227),                     # Controller Area Network (CAN) frames, with a metadata header.
        ('IPV4', 228),                              # Raw IPv4; the packet begins with an IPv4 header.
        ('IPV6', 229),                              # Raw IPv6; the packet begins with an IPv6 header.
        ('IEEE802_15_4_NOFCS', 230),                # IEEE 802.15.4 packets without FCS.
        ('DBUS', 231),                              # Raw D-Bus messages.
        ('JUNIPER_VS', 232),                        # Juniper Networks private data link type.
        ('JUNIPER_SRX_E2E', 233),                   # Juniper Networks private data link type.
        ('JUNIPER_FIBRECHANNEL', 234),              # Juniper Networks private data link type.
        ('DVB_CI', 235),                            # DVB-CI messages, with a pseudo-header.
        ('MUX27010', 236),                          # Variant of 3GPP TS 27.010 multiplexing protocol.
        ('STANAG_5066_D_PDU', 237),                 # STANAG 5066 D_PDUs.
        ('JUNIPER_ATM_CEMIC', 238),                 # Juniper Networks private data link type.
        ('NFLOG', 239),                             # Linux netlink NETLINK NFLOG socket log messages.
        ('NETANALYZER', 240),                       # Ethernet frames with Hilscher netANALYZER pseudo-header.
        ('NETANALYZER_TRANSPARENT', 241),           # Ethernet frames with netANALYZER pseudo-header, preamble and SFD, preceded by a Hilscher.
        ('IPOIB', 242),                             # IP-over-InfiniBand.
        ('MPEG_2_TS', 243),                         # MPEG-2 Transport Stream transport packets.
        ('NG40', 244),                              # Frames from ng4T GmbH's ng40 protocol tester.
        ('NFC_LLCP', 245),                          # NFC Logical Link Control Protocol frames, with a pseudo-header.
        ('PFSYNC', 246),                            # Packet filter state syncing.
        ('INFINIBAND', 247),                        # InfiniBand data packets.
        ('SCTP', 248),                              # SCTP packets, as defined by RFC 4960, with no lower-level protocols such as IPv4 or IPv6.
        ('USBPCAP', 249),                           # USB packets, beginning with a USBPcap header.
        ('RTAC_SERIAL', 250),                       # Serial-line packets from the Schweitzer Engineering Laboratories "RTAC" product.
        ('BLUETOOTH_LE_LL', 251),                   # Bluetooth Low Energy link-layer packets.
        ('WIRESHARK_UPPER_PDU', 252),               # Upper-protocol layer PDU saves from Wireshark; the actual contents are determined by two tags, one or more of which is stored with each packet.
        ('NETLINK', 253),                           # Linux Netlink capture encapsulation.
        ('BLUETOOTH_LINUX_MONITOR', 254),           # Bluetooth Linux Monitor.
        ('BLUETOOTH_BREDR_BB', 255),                # Bluetooth Basic Rate and Enhanced Data Rate baseband packets.
        ('BLUETOOTH_LE_LL_WITH_PHDR', 256),         # Bluetooth Low Energy link-layer packets, with a pseudo-header.
        ('PROFIBUS_DL', 257),                       # PROFIBUS data link layer packets.
        ('PKTAP', 258),                             # Apple PKTAP capture encapsulation.
        ('EPON', 259),                              # Ethernet-over-passive-optical-network packets, including preamble octets.
        ('IPMI_HPM_2', 260),                        # IPMI HPM.2 trace packets.
        ('ZWAVE_R1_R2', 261),                       # Z-Wave RF profile R1 and R2 packets.
        ('ZWAVE_R3', 262),                          # Z-Wave RF profile R3 packets.
        ('WATTSTOPPER_DLM', 263),                   # WattStopper Digital Lighting Management (DLM) and Legrand Nitoo Open protocol packets.
        ('ISO_14443', 264),                         # Messages between ISO 14443 contactless smartcards (Proximity Integrated Circuit Card, PICC) and card readers (Proximity Coupling Device, PCD), with the message format specified by the PCAP format for ISO14443 specification.
        ('RDS', 265),                               # IEC 62106 Radio data system (RDS) groups.
        ('USB_DARWIN', 266),                        # USB packets captured on a Darwin-based operating system (macOS, etc.).
        ('OPENFLOW', 267),                          # OpenFlow messages with an additional 12-octet header, as used in OpenBSD switch interface monitoring.
        ('SDLC', 268),                              # SNA SDLC packets
        ('TI_LLN_SNIFFER', 269),                    # TI LLN sniffer frames.
        ('LORATAP', 270),                           # LoRaWan packets with a LoRaTap pseudo-header.
        ('VSOCK', 271),                             # Protocol for communication between host and guest machines in VMware and KVM hypervisors.
        ('NORDIC_BLE', 272),                        # Messages to and from a Nordic Semiconductor nRF Sniffer for Bluetooth LE packets.
        ('DOCSIS31_XRA31', 273),                    # DOCSIS packets and bursts, preceded by a pseudo-header giving metadata about the packet.
        ('ETHERNET_MPACKET', 274),                  # IEEE 802.3 mPackets.
        ('DISPLAYPORT_AUX', 275),                   # DisplayPort AUX channel monitoring messages.
        ('LINUX_SLL2', 276),                        # Linux "cooked" capture encapsulation v2.
        ('SERCOS_MONITOR', 277),                    # Sercos Monitor.
        ('OPENVIZSLA', 278),                        # OpenVizsla FPGA-based USB sniffer frames.
        ('EBHSCR', 279),                            # Elektrobit High Speed Capture and Replay (EBHSCR) format.
        ('VPP_DISPATCH', 280),                      # Records in traces from the http://fd.io VPP graph dispatch tracer, in the the graph dispatcher trace format.
        ('DSA_TAG_BRCM', 281),                      # Ethernet frames, with a Broadcom switch tag inserted.
        ('DSA_TAG_BRCM_PREPEND', 282),              # Ethernet frames, with a Broadcom switch tag prepended.
        ('IEEE802_15_4_TAP', 283),                  # IEEE 802.15.4 packets, with a pseudo-header containing TLVs with metadata preceding the 802.15.4 header.
        ('DSA_TAG_DSA', 284),                       # Ethernet frames, with a Marvell DSA switch tag inserted.
        ('DSA_TAG_EDSA', 285),                      # Ethernet frames, with a Marvell EDSA switch tag inserted.
        ('ELEE', 286),                              # Reserved for ELEE lawful intercept protocol.
        ('Z_WAVE_SERIAL', 287),                     # Serial frames transmitted between a host and a Z-Wave chip over an RS-232 or USB serial connection, as described in section 5 of the Z-Wave Serial API Host Application Programming Guide.
        ('USB_2_0', 288),                           # USB 2.0, 1.1, or 1.0 packets.
        ('ATSC_ALP', 289),                          # ATSC Link-Layer Protocol frames.
        ('ETW', 290),                               # Event Tracing for Windows messages.
        ('NETANALYZER_NG', 291),                    # Reserved for Hilscher Gesellschaft fuer Systemautomation mbH netANALYZER NG hardware and software.
        ('ZBOSS_NCP', 292),                         # ZBOSS NCP Serial Protocol, with a pseudo-header.
        ('USB_2_0_LOW_SPEED', 293),                 # Low-Speed USB 2.0, 1.1, or 1.0 packets..
        ('USB_2_0_FULL_SPEED', 294),                # Full-Speed USB 2.0, 1.1, or 1.0 packets.
        ('USB_2_0_HIGH_SPEED', 295),                # High-Speed USB 2.0 packets.
        ('AUERSWALD_LOG', 296),                     # Auerswald Logger Protocol packets.
        ('ZWAVE_TAP', 297),                         # Z-Wave packets, with a metadata header.
        ('SILABS_DEBUG_CHANNEL', 298),              # Silicon Labs debug channel protocol, as described in the specification.
        ('FIRA_UCI', 299),                          # Ultra-wideband (UWB) controller interface protocol (UCI).
        ('MDB', 300),                               # MDB (Multi-Drop Bus) messages, with a pseudo-header.
        ('DECT_NR', 301),                           # DECT-2020 New Radio (NR) MAC layer.
   ]

class layer(layer):
    cache = {}

    # FIXME: This enumeration should actually be treated
    #        as a centralized database for the link types
    class _enum_(ptypes.pint.enum):
        _values_ = DLT_._values_ + LINKTYPE_._values_

class stackable(stackable):
    _layer_ = layer

class terminal(terminal):
    _layer_ = layer

from . import ethernet, null
