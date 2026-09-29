import logging
import boto3
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from storages.backends.s3boto3 import S3Boto3Storage

logger = logging.getLogger(__name__)


class PrivateMediaStorage(S3Boto3Storage):
    default_acl = "private"
    file_overwrite = False
    custom_domain = False
    querystring_auth = True

    def __init__(self, **settings_dict):
        bucket_name = settings_dict.get("bucket_name") or getattr(settings, "AWS_STORAGE_BUCKET_NAME", None)
        if not bucket_name:
            raise ImproperlyConfigured("AWS_STORAGE_BUCKET_NAME must be configured to use PrivateMediaStorage.")
        
        if "querystring_expire" not in settings_dict:
            settings_dict["querystring_expire"] = getattr(settings, "AWS_QUERYSTRING_EXPIRE", 3600)
            
        super().__init__(**settings_dict)


def get_s3_client():
    client_kwargs = {
        "region_name": getattr(settings, "AWS_S3_REGION_NAME", "us-east-1"),
    }
    
    access_key = getattr(settings, "AWS_ACCESS_KEY_ID", None)
    secret_key = getattr(settings, "AWS_SECRET_ACCESS_KEY", None)
    if access_key and secret_key:
        client_kwargs["aws_access_key_id"] = access_key
        client_kwargs["aws_secret_access_key"] = secret_key

    endpoint_url = getattr(settings, "AWS_S3_ENDPOINT_URL", None)
    if endpoint_url:
        client_kwargs["endpoint_url"] = endpoint_url

    return boto3.client("s3", **client_kwargs)


def generate_presigned_url(object_key, expiration=None, http_method="get_object"):
    bucket_name = getattr(settings, "AWS_STORAGE_BUCKET_NAME", None)
    if not bucket_name:
        raise ImproperlyConfigured("AWS_STORAGE_BUCKET_NAME must be configured to generate presigned URLs.")

    if expiration is None:
        expiration = getattr(settings, "AWS_QUERYSTRING_EXPIRE", 3600)

    client = get_s3_client()
    return client.generate_presigned_url(
        ClientMethod=http_method,
        Params={
            "Bucket": bucket_name,
            "Key": object_key,
        },
        ExpiresIn=expiration,
    )
