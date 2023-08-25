#=================================
# Variable inputs for AWS S3
#=================================

s3_bucket_name                   = "aft-iam-access-key-rotation-bucket-security"
s3_bucket_prefix                 = "code_sources"

#=================================
# Variable inputs for Lambda
#=================================

admin_email_address              = "<Input management email id>"
resource_owner_tag               = "Input Correct tag"
notifier_execution_role          = "notifier-execution_role"
iam_exception_group              = "IAMKeyRotationExemptionGroup"
iam_role_name                    = "asa-iam-key-rotation-lambda-assumed-role"
execution_role_name              = "asa-iam-key-rotation-lambda-execution-role"
inventory_execution_role_name    = "asa-iam-key-rotation-account-inventory-lambda-execution-role"
org_list_account                 = "<Input Vending account Number>"
org_list_role                    = "asa-iam-key-rotation-list-accounts-role"
email_template_enforcment        = "iam-auto-key-rotation-enforcement.html"
email_template_audit             = "iam-auto-key-rotation-enforcement.html"
smtp_user_param_name             = "/iam-key-rotation/smtp/user"
smtp_password_param_name         = "/iam-key-rotation/smtp/password"
rotation_period                  = "input correct value"
inactive_period                  =  "input correct value"
inactive_buffer                  =  "input correct value"
recovery_grace_period            =  "input correct value"
dry_run_flag                     = false
store_secrets_in_central_account = false
credential_replication_region    = "Input region name"
run_lambda_in_vpc                = false

#=================================
# Variable inputs for AWS VPC 
#=================================

vpc_id                           = "<Input VPC ID of vending account>"
vpc_cidr                         = "<Input Subnet CIDR of vending account>"
subnet_id                        = "<Input Subnet ID of vending account>"

#=================================
# Variable inputs for vpc_endpoint
#=================================

create_endpoint_sg               = false
create_smtp_endpoint             = false
create_ssm_endpoint              = false
create_sts_endpoint              = false
create_s3_endpoint               = false
create_secretsmanager_endpoint   = false
