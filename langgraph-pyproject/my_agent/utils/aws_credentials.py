import boto3
from typing import Optional
import time


class AWSSessionFactory:
    _instance = None
    _session: Optional[boto3.Session] = None
    _credentials_expiry: Optional[float] = None
    _role_arn: str

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AWSSessionFactory, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        # Only set _role_arn if it hasn't been set yet
        if not hasattr(self, '_role_arn'):
            self._role_arn = "arn:aws:iam::020824146127:role/langgraph-role-5ee1f46"

    def _create_session(self) -> boto3.Session:
        """Create a new session by assuming the role."""
        sts_client = boto3.client('sts')

        assumed_role = sts_client.assume_role(
            RoleArn=self._role_arn,
            RoleSessionName="LocalDevelopmentSession"
        )

        credentials = assumed_role['Credentials']
        self._credentials_expiry = credentials['Expiration'].timestamp()

        return boto3.Session(
            aws_access_key_id=credentials['AccessKeyId'],
            aws_secret_access_key=credentials['SecretAccessKey'],
            aws_session_token=credentials['SessionToken']
        )

    def get_session(self) -> boto3.Session:
        """Get the current session, creating a new one if necessary."""
        current_time = time.time()

        # Create new session if none exists or if credentials are about to expire
        # (adding 5-minute buffer)
        if (self._session is None or
                self._credentials_expiry is None or
                current_time + 300 > self._credentials_expiry):
            self._session = self._create_session()

        return self._session
