from binascii import unhexlify

from pytest import fixture, mark, skip

from cose import CoseMessage, OKP
from cose.attributes.headers import CoseHeaderKeys
from cose.keys.cosekey import KeyOps
from cose.keys.ec2 import EC2
from cose.messages.signer import SignerParams
from cose.messages.signmessage import SignMessage, CoseSignature
from tests.conftest import generic_test_setup, create_cose_key, extract_alg


@fixture
def setup_ec2sign_tests(ec2_sign_test_input: dict) -> tuple:
    return generic_test_setup(ec2_sign_test_input)


@mark.encoding
def test_ec2sign_encoding(setup_ec2sign_tests) -> None:
    _, test_input, test_output, test_intermediate, fail = setup_ec2sign_tests

    sign: SignMessage = SignMessage(
        phdr=test_input['sign'].get('protected', {}),
        uhdr=test_input['sign'].get('unprotected', {}),
        payload=test_input['plaintext'].encode('utf-8'))

    alg = extract_alg(test_input["sign"]["signers"][0])

    signer_key = create_cose_key(EC2, test_input['sign']['signers'][0]['key'], usage=KeyOps.SIGN, alg=alg)

    signer = test_input["sign"]['signers'][0]
    signer = CoseSignature(
        phdr=signer.get('protected'),
        uhdr=signer.get('unprotected'),
        external_aad=unhexlify(signer.get("external", b'')))

    sign.append_signer(signer)

    assert signer._sig_structure == unhexlify(test_intermediate['signers'][0]["ToBeSign_hex"])

    # verify encoding (with automatic tag computation)
    if fail:
        assert sign.encode(sign_params=[SignerParams(private_key=signer_key)]) != unhexlify(test_output)
    else:
        assert sign.encode(sign_params=[SignerParams(private_key=signer_key)]) == unhexlify(test_output)


@mark.decoding
def test_ec2sign_decoding(setup_ec2sign_tests) -> None:
    _, test_input, test_output, test_intermediate, fail = setup_ec2sign_tests

    if fail:
        skip("invalid test input")

    cose_msg: SignMessage = CoseMessage.decode(unhexlify(test_output))

    assert cose_msg.phdr == test_input['sign'].get('protected', {})
    assert cose_msg.uhdr == test_input['sign'].get('unprotected', {})
    assert cose_msg.payload == test_input.get('plaintext', "").encode('utf-8')

    assert len(cose_msg.signers) == 1
    assert cose_msg.signers[0].phdr == test_input['sign']['signers'][0].get('protected', {})
    assert cose_msg.signers[0].uhdr == test_input['sign']['signers'][0].get('unprotected', {})

    # set up potential external data and keys
    cose_msg.signers[0].external_aad = unhexlify(test_input['sign']['signers'][0].get('external', b''))

    alg = cose_msg.signers[0].phdr[CoseHeaderKeys.ALG]
    public_key = create_cose_key(EC2, test_input['sign']['signers'][0]['key'], usage=KeyOps.VERIFY, alg=alg)

    assert cose_msg.signers[0]._sig_structure == unhexlify(test_intermediate['signers'][0]["ToBeSign_hex"])
    assert cose_msg.signers[0].verify_signature(public_key=public_key)


