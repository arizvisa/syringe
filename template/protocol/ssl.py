import ptypes
from ptypes import *

class c_int(pint.int32_t): pass
class c_uint(pint.uint32_t): pass
class c_long(pint.uint32_t): pass
class c_ulong(pint.uint32_t): pass
class c_void_p(ptype.pointer_t): _object_ = ptype.undefined

SSL_MAX_KEY_ARG_LENGTH= 8
SSL_MAX_MASTER_KEY_LENGTH =       48
SSL_MAX_SSL_SESSION_ID_LENGTH = 32
SSL_MAX_SID_CTX_LENGTH = 32

PROTO_SSL_2_0 = 0x0002
PROTO_SSL_3_0 = 0x0300
PROTO_TLS_1_0 = 0x0301
PROTO_TLS_1_1 = 0x0302
PROTO_TLS_1_2 = 0x0303
PROTO_DTLS_1_0_OPENSSL_PRE_0_9_8f = 0x0100
PROTO_DTLS_1_0 = 0xfeff
PROTO_DTLS_1_1 = 0xfefd

class ssl_session_st(pstruct.type):
    _fields_ = [
        (pint.int32_t, 'version'), 
        (pint.uint32_t, 'key_arg_length'),
        (dyn.clone(pstr.string,length=SSL_MAX_KEY_ARG_LENGTH), 'key_arg'),
        (c_int, "master_key_length"),
        (dyn.clone(pstr.string,length=SSL_MAX_MASTER_KEY_LENGTH), "master_key"),
        (c_int, ), "session_id_length",
        (dyn.clone(pstr.string,length=SSL_MAX_SSL_SESSION_ID_LENGTH), "session_id"),
        (c_int, "sid_ctx_length"),
        (dyn.clone(pstr.string,length=SSL_MAX_SID_CTX_LENGTH), "sid_ctx"),
        (c_int, "not_resumable"),
        (c_void_p, "sess_cert"),
        (c_void_p, "peer"),
        (c_long, "verify_result"),
        (c_int, "references"),
        (c_long, "timeout"),
        (c_long, "time"),
        (c_int, "compress_meth"),
        (c_void_p, "cipher"),
        (c_ulong, "cipher_id"),
        (c_void_p, "ciphers"),
        (c_void_p, "ex_data_sk"),
        (c_int, "ex_data_dummy"),
        (c_void_p, "prev"),
        (c_void_p, "next"),
    ]
    def validate(self, **attrs):
        res = self.clone().load(**attrs)
        #version = [lambda val,obj,mem: PASS if val in (PROTO_SSL_2_0,PROTO_DTLS_1_0_OPENSSL_PRE_0_9_8f,PROTO_DTLS_1_0,PROTO_DTLS_1_1) or (val > 700 and val < 1000) else FAIL]),
        #key_arg_length = [lambda val,obj,mem: PASS if val==SSL_MAX_KEY_ARG_LENGTH else FAIL]),
        #key_arg = [lambda val,obj,mem: PASS if len(val)==obj.key_arg_length else FAIL]),
        #master_key_length = [Validate.not_null]),
        #master_key = [lambda val,obj,mem: PASS if len(val)==obj.master_key_length else FAIL]),
        #session_id = [lambda val,obj,mem: PASS if len(val)==obj.session_id_length else FAIL]),
        #references = [Validate.not_null]),
