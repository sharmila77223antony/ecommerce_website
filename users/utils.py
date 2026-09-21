import logging

import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException

from django.conf import settings


logger = logging.getLogger(__name__)


def send_otp_email(to_email, otp, name):

    configuration = sib_api_v3_sdk.Configuration()
    configuration.api_key["api-key"] = settings.BREVO_API_KEY

    api_client = sib_api_v3_sdk.ApiClient(configuration)

    api_instance = sib_api_v3_sdk.TransactionalEmailsApi(
        api_client
    )

    send_email = sib_api_v3_sdk.SendSmtpEmail(
        sender={
            "email": settings.DEFAULT_FROM_EMAIL,
            "name": "E-Commerce website",
        },
        to=[
            {
                "email": to_email,
            }
        ],
        subject="Your Email Verification OTP",
        html_content=f"""
        <div style="font-family:Arial;padding:20px">

            <h2>Email Verification</h2>

            <p>Hello {name},</p>

            <p>
                You requested an email verification OTP.
            </p>

            <p>Your OTP is:</p>

            <h1 style="color:#0ea5e9">{otp}</h1>

            <p>
                This OTP is valid for 10 minutes.
            </p>

            <hr>

            <small>
                If you didn't request this, please ignore this email.
            </small>

        </div>
        """,
    )

    try:

        response = api_instance.send_transac_email(
            send_email
        )

        logger.info(
            "Brevo Email Sent: %s",
            response
        )

        return True

    except ApiException as e:

        logger.error(
            "Brevo API Error: %s",
            e.body
        )

        print(
            "BREVO ERROR:",
            e.body
        )

        return False

    except Exception as e:

        logger.exception(
            "Unexpected Email Error: %s",
            e
        )

        print(
            "EMAIL ERROR:",
            str(e)
        )

        return False