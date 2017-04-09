==========
Quickstart
==========


* We create a different key for every single secret. While this might be a bit
  more than we really need, it does allow for clear auditing of every single
  access.

Steps
-----

1. Create project (you may want to put the storage buckets in a different
   proejct).
2. Create users
  - User 1: Manager
     - ``roles/cloudkms.admin``
   - User 2: Consumer
     - ``roles/cloudkms.cryptoKeyEncrypterDecrypter``, or if you want them to
       have even more limited access: ``roles/cloudkms.cryptKeyDecrypter``.
3. Create CloudStorage bucket
   - Create a bucket: gsutil mb -p [PROJECT_NAME] -c [STORAGE_CLASS] -l [BUCKET_LOCATION] gs://[BUCKET_NAME]/
     By default you probably want ``multi_regional`` for your bucket. In that
     case you will want to set the bucket location to ``us``, ``asia``, or
     ``eu`` so it's closest to most of your infrastructure.
   - Grant User 1 ``roles/storage.objectAdmin``
   - Grant User 2 ``roles/storage.objectViewer``
4. Create a KeyRing for managing all the secret keys::

     gcloud kms keyrings create aletheia --location global
5. Finally, we need to create a key for the project. It should share the name
   of your project for ease of discovery::

     gcloud kms keys create project-1234 --location global --keyring aletheia --purpose encryption
