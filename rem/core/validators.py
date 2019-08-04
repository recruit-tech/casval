from datetime import datetime
from enum import IntFlag

import pytz
from flask_marshmallow import Marshmallow
from marshmallow import ValidationError
from marshmallow import validate
from marshmallow import validates
from marshmallow import validates_schema

from .utils import Utils

marshmallow = Marshmallow()

DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S"

AUDIT_LIST_MAX_COUNT = 300
AUDIT_GET_DEFAULT_COUNT = 10
SCAN_MAX_COMMENT_LENGTH = 1000

SCAN_SCHEDULABLE_DAYS_FROM_NOW = 10
SCAN_MIN_DURATION_IN_SECONDS = 3600  # 1 hours

VULN_FIX_REQUIRED_STATUS = ["REQUIRED", "RECOMMENDED", "OPTIONAL", "UNDEFINED", ""]


class Validators:
    @staticmethod
    def validate_target(value):
        if Utils.is_ipv4(value):
            if not Utils.is_public_address(value):
                raise ValidationError(ErrorReasonEnum.target_is_private_ip.name)
        elif Utils.is_domain(value):
            if not Utils.is_host_resolvable(value):
                raise ValidationError(ErrorReasonEnum.could_not_resolve_target_fqdn.name)
        else:
            raise ValidationError(ErrorReasonEnum.target_is_not_fqdn_or_ipv4.name)


class ErrorReasonEnum(IntFlag):
    audit_id_not_found = 0
    audit_submitted = 1
    target_is_private_ip = 2
    could_not_resolve_target_fqdn = 3
    target_is_not_fqdn_or_ipv4 = 4
    target_is_scheduled = 5

    @property
    def name(self):
        return super().name.replace("_", "-")


class PagenationInputSchema(marshmallow.Schema):
    page = marshmallow.Integer(required=False, validate=[validate.Range(min=1)], missing=1)
    count = marshmallow.Integer(
        required=False,
        validate=[validate.Range(min=1, max=AUDIT_LIST_MAX_COUNT)],
        missing=AUDIT_GET_DEFAULT_COUNT,
    )


class AuthInputSchema(marshmallow.Schema):
    password = marshmallow.String(required=True, validate=[validate.Length(min=1, max=128)])


class AuditListInputSchema(PagenationInputSchema):
    unsafe_only = marshmallow.Boolean(required=False)
    submitted = marshmallow.Boolean(required=False)
    approved = marshmallow.Boolean(required=False)
    keyword = marshmallow.String(required=False)


class AuditTokenInputSchema(marshmallow.Schema):
    password = marshmallow.String(required=False, missing="")


class ContactSchema(marshmallow.Schema):

    SEPARATER_NAME_EMAIL = ":"
    SEPARATER_CONTACTS = ","
    EXCLUDE_SEPARATERS = r"^[^:,]+$"

    name = marshmallow.String(
        required=True, validate=[validate.Length(min=1, max=128), validate.Regexp(EXCLUDE_SEPARATERS)]
    )
    email = marshmallow.String(required=True, validate=[validate.Email(), validate.Length(min=1, max=256)])


class AuditInputSchema(marshmallow.Schema):
    name = marshmallow.String(required=True, validate=[validate.Length(min=1, max=128)])
    description = marshmallow.String(required=False, validate=[validate.Length(min=0, max=128)])
    contacts = marshmallow.Nested(ContactSchema, required=True, many=True, validate=validate.Length(min=1))


class AuditUpdateSchema(marshmallow.Schema):
    name = marshmallow.String(required=False, validate=[validate.Length(min=1, max=128)])
    description = marshmallow.String(required=False, validate=[validate.Length(min=0, max=128)])
    contacts = marshmallow.Nested(ContactSchema, required=False, many=True, validate=validate.Length(min=1))
    password = marshmallow.String(required=False, validate=[validate.Length(min=8, max=128)])
    submitted = marshmallow.Boolean(required=True)
    approved = marshmallow.Boolean(required=True)
    ip_restriction = marshmallow.Boolean(required=False)
    password_protection = marshmallow.Boolean(required=False)
    rejected_reason = marshmallow.String(required=False, validate=[validate.Length(min=0, max=128)])


class ScanInputSchema(marshmallow.Schema):
    target = marshmallow.String(required=True)

    @validates("target")
    def validate_target(self, value):
        Validators.validate_target(value)


class ScanUpdateSchema(marshmallow.Schema):
    target = marshmallow.String(required=False)
    start_at = marshmallow.DateTime(required=True)
    end_at = marshmallow.DateTime(required=True)
    task_uuid = marshmallow.String(required=True)
    scheduled = marshmallow.Boolean(required=True)
    comment = marshmallow.String(
        required=True, validate=[validate.Length(min=0, max=SCAN_MAX_COMMENT_LENGTH)]
    )

    @validates("target")
    def validate_target(self, value):
        Validators.validate_target(value)

    @validates_schema
    def validate_schedule(self, value):
        if "start_at" in value and "end_at" in value:
            start_at = value["start_at"].replace(tzinfo=pytz.utc)
            end_at = value["end_at"].replace(tzinfo=pytz.utc)
            jst = pytz.timezone("Asia/Tokyo")
            now = datetime.now(tz=pytz.utc).astimezone(jst)

            if end_at <= now:
                raise ValidationError("'end_at' has elapsed")
            if end_at <= start_at:
                raise ValidationError("'end_at' is equal or earlier than 'start_at'")

            start_from_now = start_at - now
            if start_from_now.days > SCAN_SCHEDULABLE_DAYS_FROM_NOW:
                raise ValidationError(
                    "'start_at' must be within {} days from now".format(SCAN_SCHEDULABLE_DAYS_FROM_NOW)
                )

            scan_duration = end_at - start_at
            if scan_duration.days is 0 and scan_duration.seconds < SCAN_MIN_DURATION_IN_SECONDS:
                raise ValidationError(
                    "Duration between 'end_at' and 'start_at' must be equal or more than {} seconds".format(
                        SCAN_MIN_DURATION_IN_SECONDS
                    )
                )


class VulnListInputSchema(PagenationInputSchema):
    fix_required = marshmallow.String(required=False, validate=[validate.OneOf(VULN_FIX_REQUIRED_STATUS)])
    keyword = marshmallow.String(required=False)


class VulnUpdateSchema(marshmallow.Schema):
    fix_required = marshmallow.String(required=False, validate=[validate.OneOf(VULN_FIX_REQUIRED_STATUS)])
    advice = marshmallow.String(
        required=False, validate=[validate.Length(min=0, max=SCAN_MAX_COMMENT_LENGTH)]
    )
