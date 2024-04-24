'''
AllJoyn and DBus Interface Definitions
alljoyn_core/inc/alljoyn/AllJoynStd.h
alljoyn_core/inc/alljoyn/DBusStd.h
'''

class org:
    '''alljoyn_core/inc/alljoyn/AllJoynStd.h:52'''

    class alljoyn:
        '''alljoyn_core/inc/alljoyn/AllJoynStd.h:53'''

        class About:
            '''alljoyn_core/inc/alljoyn/AllJoynStd.h:56'''
            ObjectPath = "/About";
            InterfaceName = "org.alljoyn.About";
            WellKnownName = "org.alljoyn.About";

        class Icon:
            '''alljoyn_core/inc/alljoyn/AllJoynStd.h:65'''
            ObjectPath = "/About/DeviceIcon";
            InterfaceName = "org.alljoyn.Icon";
            WellKnownName = "org.alljoyn.Icon";

        class Bus:
            '''alljoyn_core/inc/alljoyn/AllJoynStd.h:74'''
            ErrorName = "org.alljoyn.Bus.ErStatus";
            ObjectPath = "/org/alljoyn/Bus";
            InterfaceName = "org.alljoyn.Bus";
            WellKnownName = "org.alljoyn.Bus";
            Secure = "org.alljoyn.Bus.Secure";

            class Application:
                '''alljoyn_core/inc/alljoyn/AllJoynStd.h:83'''
                InterfaceName = "org.alljoyn.Bus.Application";

            class Peer:
                '''alljoyn_core/inc/alljoyn/AllJoynStd.h:88'''
                ObjectPath = "/org/alljoyn/Bus/Peer";

                class HeaderCompression:
                    '''alljoyn_core/inc/alljoyn/AllJoynStd.h:90'''
                    InterfaceName = "org.alljoyn.Bus.Peer.HeaderCompression";

                class Authentication:
                    '''alljoyn_core/inc/alljoyn/AllJoynStd.h:93'''
                    InterfaceName = "org.alljoyn.Bus.Peer.Authentication";

                class Session:
                    '''alljoyn_core/inc/alljoyn/AllJoynStd.h:96'''
                    InterfaceName = "org.alljoyn.Bus.Peer.Session";

            class Security:
                '''alljoyn_core/inc/alljoyn/AllJoynStd.h:102'''
                ObjectPath = "/org/alljoyn/Bus/Security";

                class Application:
                    '''alljoyn_core/inc/alljoyn/AllJoynStd.h:104'''
                    InterfaceName = "org.alljoyn.Bus.Security.Application";

                class ClaimableApplication:
                    '''alljoyn_core/inc/alljoyn/AllJoynStd.h:107'''
                    InterfaceName = "org.alljoyn.Bus.Security.ClaimableApplication";

                class ManagedApplication:
                    '''alljoyn_core/inc/alljoyn/AllJoynStd.h:110'''
                    InterfaceName = "org.alljoyn.Bus.Security.ManagedApplication";

        class Daemon:
            '''alljoyn_core/inc/alljoyn/AllJoynStd.h:118'''
            ErrorName = "org.alljoyn.Daemon.ErStatus";
            ObjectPath = "/org/alljoyn/Bus";
            InterfaceName = "org.alljoyn.Daemon";
            WellKnownName = "org.alljoyn.Daemon";

            class Debug:
                '''alljoyn_core/inc/alljoyn/AllJoynStd.h:125'''
                ObjectPath = "/org/alljoyn/Debug";
                InterfaceName = "org.alljoyn.Debug";

    class allseen:
        InterfaceName = "org.allseen.Introspectable";
        IntrospectDocType = "<!DOCTYPE node PUBLIC \"-//allseen//DTD ALLJOYN Object Introspection 1.1//EN\"\n\"http://www.allseen.org/alljoyn/introspect-1.1.dtd\">\n";

class org(org):
    '''alljoyn_core/inc/alljoyn/DBusStd.h'''

    class freedesktop:
        '''alljoyn_core/inc/alljoyn/DBusStd.h:49'''

        class DBus:
            '''alljoyn_core/inc/alljoyn/DBusStd.h:52'''
            ObjectPath = ""
            InterfaceName = ""
            WellKnownName = ""

            AnnotateNoReply = ""
            AnnotateDeprecated = ""
            AnnotateEmitsChanged = ""

        class Properties:
            '''alljoyn_core/inc/alljoyn/DBusStd.h:62'''
            InterfaceName = ""

        class Peer:
            '''alljoyn_core/inc/alljoyn/DBusStd.h:67'''
            InterfaceName = ""

        class Introspectable:
            '''alljoyn_core/inc/alljoyn/DBusStd.h:72'''
            InterfaceName = ""
            IntrospectDocType = ""
