#   finish config.system. the intention of this is to have a variable that describes the
#   system that you will be applying types to. this should allow for some templates to
#   be automatically generated for the target system.
#   this can influence the default structures defined in ndk.
#   this will also be used to determine the byteorder and sizes of default pointer types
#   this can be used by provider.py to determine what providers are available
#   this can influence how code_t works.
#   integer.{wordsize,byteorder} should eventually be deprecated

# network should be pretty similar to /sbin/ip

class network(object):
    class link(object):
        """Information for querying things about the datalink layer

        allocating a socket to write to this interface
        enumerating ethernet interfaces and hw addresses
        the static link<->address table (/etc/ethers)
        the dynamic link<->address table (ARP)
        options for an ethernet interface (media type, etc)
        """
    class address(object):
        """Information for querying things about the network layer

        allocating a socket for sending from a specific address
        enumerating addresses associated with an interface
        options for an ipX interface
        """
    class routing(object):
        """Information about the routing table

        loading from the current routing table
        modifying the routing table
        """
    class naming(object):
        """Information about name<->address (dns)

        loading configuration from resolv.conf
        making types of dns queries
        """


