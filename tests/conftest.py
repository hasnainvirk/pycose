import json
import os
import pathlib
from binascii import unhexlify

import pytest

from pycose.attributes import CoseHeaderParam, CoseAlgorithm
from pycose.cosekey import KTY, CoseEllipticCurves

path_examples = os.path.join(pathlib.Path(__file__).parent.absolute(), 'examples')

aes_ccm_examples = os.path.join(path_examples, 'aes-ccm-examples')
aes_gcm_examples = os.path.join(path_examples, 'aes-gcm-examples')
encrypted_tests = os.path.join(path_examples, 'encrypted-tests')
enveloped_tests = os.path.join(path_examples, 'enveloped-tests')
ecdh_direct_examples = os.path.join(path_examples, 'ecdh-direct-examples')

algs_to_be_replaced = {
    'A128GCM': CoseAlgorithm.A128GCM,
    'A192GCM': CoseAlgorithm.A192GCM,
    'A256GCM': CoseAlgorithm.A256GCM,
    'AES-CCM-16-128/64': CoseAlgorithm.AES_CCM_16_64_128,
    'AES-CCM-16-256/64': CoseAlgorithm.AES_CCM_16_64_256,
    'AES-CCM-16-128/128': CoseAlgorithm.AES_CCM_16_128_128,
    'AES-CCM-64-128/128': CoseAlgorithm.AES_CCM_64_128_128,
    'AES-CCM-64-128/64': CoseAlgorithm.AES_CCM_64_64_128,
    'AES-CCM-64-256/64': CoseAlgorithm.AES_CCM_64_64_256,
    'AES-CCM-16-256/128': CoseAlgorithm.AES_CCM_16_128_256,
    'AES-CCM-64-256/128': CoseAlgorithm.AES_CCM_64_128_256,
    'direct': CoseAlgorithm.DIRECT,
    "ECDH-ES-512": CoseAlgorithm.ECDH_ES_HKDF_512,
    "ECDH-ES": CoseAlgorithm.ECDH_ES_HKDF_256,
}

params_to_be_replaced = {
    'ctyp': CoseHeaderParam.CONTENT_TYPE,
    'kid': CoseHeaderParam.KID,
    'alg': CoseHeaderParam.ALG,
    'partialIV_hex': CoseHeaderParam.PARTIAL_IV,
}

key_attr_to_be_replaced = {
    "EC": KTY.EC2,
    "OKP": KTY.OKP,
    "P-256": CoseEllipticCurves.P_256,
    "P-384": CoseEllipticCurves.P_384,
    "P-521": CoseEllipticCurves.P_521,
}


@pytest.fixture
def protected_header(request):
    test_case = json.load(open(request.param, 'r'))
    _fix_header_algorithm_names(test_case['input']['enveloped'], 'protected')
    return test_case['input']['enveloped']['protected']


@pytest.fixture
def encrypt0_test_cases(request):
    test_input = json.load(open(request.param, 'r'))
    if 'encrypted' in test_input['input']:
        _fix_header_attribute_names(test_input['input']['encrypted'], 'protected')
        _fix_header_attribute_names(test_input['input']['encrypted'], 'unprotected')
        _fix_header_algorithm_names(test_input['input']['encrypted'], 'protected')
        _fix_header_algorithm_names(test_input['input']['encrypted'], 'unprotected')
        return test_input


@pytest.fixture
def encrypt_test_cases(request):
    test_input = json.load(open(request.param, 'r'))
    if 'enveloped' in test_input['input']:
        _fix_header_attribute_names(test_input['input']['enveloped'], 'protected')
        _fix_header_attribute_names(test_input['input']['enveloped'], 'unprotected')
        _fix_header_algorithm_names(test_input['input']['enveloped'], 'protected')
        _fix_header_algorithm_names(test_input['input']['enveloped'], 'unprotected')

        recipients = test_input['input']['enveloped']['recipients']
        _fix_recipients(recipients)

        return test_input


@pytest.fixture
def ecdh_direct_enc_test_cases(request):
    test_input = json.load(open(request.param, 'r'))

    if 'enveloped' in test_input['input']:
        _fix_header_attribute_names(test_input['input']['enveloped'], 'protected')
        _fix_header_algorithm_names(test_input['input']['enveloped'], 'protected')
        _fix_header_algorithm_names(test_input['input']['enveloped'], 'unprotected')
        _fix_header_attribute_names(test_input['input']['enveloped'], 'unprotected')

        recipients = test_input['input']['enveloped']['recipients']
        _fix_recipients(recipients)

        return test_input


def _fix_recipients(recipients: dict) -> None:
    for r_info in recipients:
        _fix_header_attribute_names(r_info, 'unprotected')
        _fix_header_attribute_names(r_info, 'protected')
        _fix_header_algorithm_names(r_info, 'unprotected')
        _fix_header_algorithm_names(r_info, 'protected')

        if 'key' in r_info:
            _fix_key_object(r_info, 'key')

        if 'sender_key' in r_info:
            _fix_key_object(r_info, 'sender_key')

        if 'recipients' in r_info:
            _fix_recipients(r_info['recipients'])


def _fix_key_object(data: dict, key: str) -> None:
    updated = {k: key_attr_to_be_replaced[v] if v in key_attr_to_be_replaced else v for k, v in data[key].items()}
    data[key] = updated


def _fix_header_algorithm_names(data: dict, key) -> None:
    try:
        header_dict = data[key]
    except KeyError:
        return

    header_dict = {k: (v if v not in algs_to_be_replaced else algs_to_be_replaced[v]) for k, v in header_dict.items()}
    data[key] = header_dict


def _fix_header_attribute_names(data: dict, key) -> None:
    try:
        header_dict = data[key]
    except KeyError:
        return

    header_dict = {(k if k not in params_to_be_replaced else params_to_be_replaced[k]): v for k, v in
                   header_dict.items()}
    if CoseHeaderParam.KID in header_dict and type(header_dict[CoseHeaderParam.KID]) == str:
        header_dict[CoseHeaderParam.KID] = header_dict[CoseHeaderParam.KID].encode('utf-8')
    if CoseHeaderParam.PARTIAL_IV in header_dict and type(header_dict[CoseHeaderParam.PARTIAL_IV]) == str:
        header_dict[CoseHeaderParam.PARTIAL_IV] = unhexlify(header_dict[CoseHeaderParam.PARTIAL_IV].encode('utf-8'))
    data[key] = header_dict
