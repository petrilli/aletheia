"""Secret Storage in Google Cloud Platform

This module implements the core functionality of secret storage inside the 
Google Cloud Platform.  It is built on several Google components:

* Google Cloud Storage - holds the actual encrypted secrets
* Google Key Management Service - manages crypto keys and performs 
  encryption/decryption
* Google IAM - Manages who gets access to what.

The design makes no assumptions as to the internal structure of the secret.
However, because of the limitations of Google KMS, the secret should not be
more than 64kiB.
"""
import base64
import logging

import googleapiclient.discovery as gcp_discovery
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseUpload
from six.moves import StringIO

ALETHEIA_CONTENT_TYPE = 'application/x-aletheia-secret'
ALETHEIA_METADATA_KEY = 'x-aletheia-secret-key'


LOGGER = logging.getLogger(__name__)


def get_kms_client():
    """Returns a Google Cloud Key Management Service client.

    Returns:
      gcp_discovery.Resource: A dynamic client.
    """
    return gcp_discovery.build('cloudkms', 'v1')


def get_cs_client():
    """Returns a Google Cloud Storage client.

    Returns:
        gcp_discovery.Resource: A dynamic client.
    """
    return gcp_discovery.build('storage', 'v1')


class Chest(object):
    """A chest of secrets.

    This object contains a complete set of secrets for a project usually.
    """

    def __init__(self, project_id, chest, bucket, location='global',
                 keyring='aletheia'):
        """Create a new chest.

        Args:
            chest (str): The name of the secret chest we want to use. This
                is often the GCP project ID. It is also the name of the key
                that should be associated with the secret.
        Returns:
            Chest: A new chest.
        """
        # We want to ensure this key actually exists, and that we have access
        kms_client = get_kms_client()

        name = 'projects/{}/locations/{}/keyRings/{}/cryptoKeys/{}'.format(
            project_id, location, keyring, chest)
        cryptokeys = kms_client.projects().locations().keyRings().cryptoKeys()

        _ = cryptokeys.encrypt(
            name=name, body={
                'plaintext': base64.b64encode('THIS IS NOT A SECRET')
            }
        ).execute()

        # Now make sure the bucket exists
        cs_client = get_cs_client()

        try:
            _ = cs_client.buckets().get(bucket=bucket).execute()
        except HttpError:
            raise RuntimeError("Unable to access CS bucket {}".format(bucket))

        # Everything looks good, so let's save it
        self.project_id = project_id
        self.chest = chest
        self.bucket = bucket
        self.location = location
        self.keyring = keyring
        self.keyname = name

        super(Chest, self).__init__()

    def get(self, name):
        """Get the provided secret name.

        Args:
            name (str): The name of the secret.

        Returns:
            SimpleSecret: A Secret.

        Raises:
            ValueError: A ValueError means that a secret with the provided
                name does not exist.
        """
        cs_client = get_cs_client()

        secret_metadata = cs_client.objects().get(bucket=self.bucket,
                                                  object=name).execute()

        # Make sure it's an actual bit of Aletheia data, and that the
        # the associated secret link is there. If it is, grab it.
        if (secret_metadata['contentType'] == ALETHEIA_CONTENT_TYPE and
                ALETHEIA_METADATA_KEY in secret_metadata['metadata']):
            request = cs_client.objects().get_media(
                bucket=self.bucket, object=name)
            return SimpleSecret(name, request.execute(),
                                secret_metadata['metadata'][ALETHEIA_METADATA_KEY])
        else:
            raise ValueError(
                "{} does not have the correct content type or key set".format(
                    name
                )
            )

    def create(self, name, secret):
        """Create a new Secret in the chest.

        Args:
            name (str): The name of the secret. Can be path-like.
            secret (str): The secret itself. It is passed in as a str because
                it is assumed to be reasonably small, as it's not designed
                for managing large secrets.

        Returns:
            SimpleSecret: An initialized secret
        """
        # First, encrypt it
        kms_client = get_kms_client()
        crypto = kms_client.projects().locations().keyRings().cryptoKeys()
        ciphertext = crypto.encrypt(name=self.keyname, body={
            'plaintext': base64.b64encode(secret)
        }).execute()

        # Now store it
        cs_client = get_cs_client()
        cs_client.objects().insert(
            bucket=self.bucket,
            name=name,
            media_body=MediaIoBaseUpload(
                fd=StringIO(ciphertext),
                mimetype=ALETHEIA_CONTENT_TYPE
            ),
            body={
                'metadata': {
                    ALETHEIA_METADATA_KEY: self.keyname
                }
            }
        ).execute()

        return SimpleSecret(name=name, ciphertext=ciphertext,
                            kms_keyname=self.keyname, _plaintext=secret)


class SimpleSecret(object):
    """Something we don't want everyone to know about.
   
    A Secret is where we do most of the work.

    Attributes:
        _ciphertext (str): The local storage copy of the ciphertext
        _kms_keyname (str): Route in Cloud KMS
        _plaintext (str|None): Plaintext cache copy of the secret, or
            None if it's not been resolved yet.
    """
    def __init__(self, name, ciphertext, kms_keyname, _plaintext=None):
        """Create a new secret.

        Initially, the secret is stored only as encrypted ciphertext. It's
        not until you first try and access it that it will decrypt itself,
        and then cache a copy of that for future reference.

        Args:
            name (str): The name of the secret.
            ciphertext (str): Encrypted ciphertext.
            kms_keyname (str): "Route" in Cloud KMS
            _plaintext (str|None): Pre-populated plaintext. This is only used
                when creating a new Secret from scratch through the Chest.
        """
        self.name = name
        self._ciphertext = ciphertext
        self._kms_keyname = kms_keyname
        self._plaintext = _plaintext

        super(SimpleSecret, self).__init__()

    @property
    def plaintext(self):
        """Return the plaintext version of the secret.

        If we don't already have a copy of the plaintext, we will perform the
        initial decryption and cache a copy.  This copy exists for the life of
        the object.
        """
        if self._plaintext is None:
            self._plaintext = self.decrypt()

        return self._plaintext

    def decrypt(self):
        """Decrypt the secret. 
        
        All secrets are stored in base64 format, so we clear that first.
        
        Returns:
          str: The plaintext.
        """
        kms_client = get_kms_client()
        crypto = kms_client.projects().locations().keyRings().cryptoKeys()
        request = crypto.decrypt(name=self._kms_keyname, body={
            'ciphertext': self._ciphertext
        })
        response = request.execute()

        # Base64 encoded response
        return base64.b64decode(response['plaintext'])

    def __repr__(self):
        """Python dunder representation.
        
        The representation includes an indicator if it's encrypted or not.
        
        Returns:
          str: Handy representation of the Secret
        """
        return "Secret(name='{name}', {status})".format(
            name=self.name,
            status="cleartext" if self._plaintext else "encrypted"
        )
