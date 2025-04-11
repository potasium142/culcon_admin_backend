import logging
from paypalserversdk.http.auth.o_auth_2 import ClientCredentialsAuthCredentials
from paypalserversdk.controllers.payments_controller import PaymentsController
from paypalserversdk.logging.configuration.api_logging_configuration import (
    LoggingConfiguration,
    RequestLoggingConfiguration,
    ResponseLoggingConfiguration,
)
from paypalserversdk.paypal_serversdk_client import PaypalServersdkClient
from paypalserversdk.configuration import Environment
from config import env

client = PaypalServersdkClient(
    client_credentials_auth_credentials=ClientCredentialsAuthCredentials(
        o_auth_client_id=env.PAYPAL_CLIENT_ID,
        o_auth_client_secret=env.PAYPAL_CLIENT_SECRET,
    ),
    environment=Environment.SANDBOX,
    logging_configuration=LoggingConfiguration(
        log_level=logging.ERROR,
        request_logging_config=RequestLoggingConfiguration(log_body=True),
        response_logging_config=ResponseLoggingConfiguration(log_headers=True),
    ),
)

payment_controller: PaymentsController = client.payments
