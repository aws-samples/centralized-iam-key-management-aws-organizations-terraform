# Iam-Access-keys-Rotation



## Getting started

Security is an essential part of every organization and organization enforcing set of rules related to password and key. One of the important rule is the Identity Access Management (IAM) key rotation on regular intervals of time to enforce security. Amazon Web Services (AWS) secret access keys are generally created and configured locally whenever teams need access to AWS from the Command Line Interface (CLI) or applications outside AWS. To maintain strong security across the organization, old security keys must be changed or deleted after the requirement is completed or after a specific period. The process of managing rotations across multiple accounts across organisations is time-consuming and tedious. Our goal here is to automate the rotation process of rotating access keys using Account Factory for Terraform (AFT) and AWS services across organizations.

This solution automates the rotating of IAM access keys using Terraform, where we will deploy Lambda functions, event bridges, and IAM roles. Event bridge is scheduled to run at regular intervals and invokes Lambda functions. The Lambda function lists all the user access keys based on when they were created. It creates a new access key and secret key, if the old keys are older than specified rotation period(e.g. 45 days) defined in organization and notifies the security person using SNS/SES. Secrets will be created in secrets manager for that particular user, store old secret key in AWS secret manager and configure permission to access the old key. To ensure that the old access key is not being used, it will be disabled after inactive_period(e.g. 60 days i.e 15 days after the Keys are rotated). Finally after inactive_buffer configuration (e.g. 90 days i.e 45 days after the Keys are rotated), old access keys will be deleted from AWS Secret manager. In this solution, we are expecting users to stop using the old access/secret keys after inactive_period configured in lambda environment variable


## Architecture
![image](https://github.com/aws-samples/centralized-iam-key-management-aws-organizations-terraform/assets/65273458/0d657ede-41ae-451d-93a3-c81a66adddde)


## Solution workflow

1. An EventBridge event service will trigger account-inventory lambda function after every 24 hours.
2. This **account-inventory** Lambda function queries AWS Organizations for a list of all AWS account IDs, account names, and account emails. 
3. The **account-inventory** Lambda function initiates an **IAM-access-key-auto-rotation** Lambda function for each AWS account and passes the metadata to it for additional processing.
4. The **IAM-access-key-auto-rotation** Lambda function uses an assumed IAM role to access the AWS account. The Lambda script runs an audit against all users and their IAM access keys in the account.
5. The IAM key rotation threshold(rotation period) configured during deploying  **IAM-access-key-auto-rotation** lambda function as environment variable. In case modification on rotation period, we need redeploy IAM-access-key-auto-rotation lambda function with updated environment variable. Refer below Input Parameter  needs to be provided during deploying the solution
6. The **IAM-access-key-auto-rotation** lambda function validate the access key age as per configuration.
    1. If the IAM access key's age hasn’t exceeded the Organizations defined threshold, the Lambda function takes no further action.
    2. If the IAM access key's age has exceeded the Organizations defined rotation period in IAM-access-key-auto-rotation lambda function environment variable, it will create new keys for the IAM user and save old key  in secrets manager, limiting permissions to the user whose access keys are deviating from security standards. A resource-based policy is also created that allows only the specified IAM principal to access and retrieve the secret.
    3. This IAM-Access-key-rotation Lambda rotates the key as per defined rules and invokes to Notification lambda function.
7. In case key rotated ,the IAM-access-key-auto-rotation Lambda function rotate the access key of the user.
8. creates and updates a secret in AWS Secrets Manager and assigned required policy to access the information from Account owner.
9. **IAM-access-key-auto-rotation** Lambda function initiates notification Lambda function
10. A **notification** Lambda function queries the S3 bucket for an email template and dynamically generate emails with the relevant activity metadata, 
11. A **notification** Lambda function invokes AWS SES for further action.
12. Eventually, AWS SES sent email to the account owner's email address with related informations.

## Implementation
1. Clone the git repo.

   `git clone https://github.com/aws-samples/Iam-Access-keys-Rotation`

2. Make sure repository should consists  three directories:

    `$ cd Iam-Access-keys-Rotation`

    `$ ls`
    
        org-account-customization
        global-account-customization
        account-customization`

3. AFT Bootstrapping Configuration

    `$ cd aft-bootstrap`

    `$ terraform init`

    `$ terraform apply —auto-approve`

4. global-account-customization configuration

-    Manually copy  all terraform files from “global-account-customization” to “aft-global-customizations/terraform” folder.
-    Push the code to AWS code commit

   
5. aft-account-customizations configuration

    1. As part of AFT folder setup , there should be a existing folder “aft-account-customizations”

    2. Created folder with vended Account number

    3. Copy manual all terraform files from “account-customization” to aft-account-customizations/<Vended Account>/terraform folder.

    4. Push the code to AWS code commit


## Parameters
   1. Create a “input.auto.tfvars” file in the “aft-global-customizations” repo inside terraform folder and provide required input Data.

   2. Create a “input.auto.tfvars” file in the “aft-account-customizations” repo inside <AccountName>/terraform/ and pushed the code to AWS code  commit.

   3. Once code pushed to AWS code commit , the pipeline will be trigger automatically.

## Validation

  1. Login to  Deployment Account from AWS console.

  2. Go to IAM Console and check user credential(Access Key & secret key) should be rotated as per organisation rule.

  3. Once IAM key rotated , the old value will be stored in secret manager .

  4. Secret name should be like this “Account_<Account ID>_User_<username>_AccessKey”

  5. Once IAM key rotated , user will notified on email as per email address  configured in AWS SES.
***


## Security 
See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications)
 for more information.

## License
This project is licensed under the MIT-0 License.

This package depends on and may incorporate or retrieve a number of third-party software packages (such as open source packages) at install-time or build-time or run-time ("External Dependencies"). The External Dependencies are subject to license terms that you must accept in order to use this package. If you do not accept all of the applicable license terms, you should not use this package. We recommend that you consult your company’s open source approval policy before proceeding.

Provided below is a list of External Dependencies and the applicable license identification as indicated by the documentation associated with the External Dependencies as of Amazon's most recent review.

THIS INFORMATION IS PROVIDED FOR CONVENIENCE ONLY. AMAZON DOES NOT PROMISE THAT THE LIST OR THE APPLICABLE TERMS AND CONDITIONS ARE COMPLETE, ACCURATE, OR UP-TO-DATE, AND AMAZON WILL HAVE NO LIABILITY FOR ANY INACCURACIES. YOU SHOULD CONSULT THE DOWNLOAD SITES FOR THE EXTERNAL DEPENDENCIES FOR THE MOST COMPLETE AND UP-TO-DATE LICENSING INFORMATION.

YOUR USE OF THE EXTERNAL DEPENDENCIES IS AT YOUR SOLE RISK. IN NO EVENT WILL AMAZON BE LIABLE FOR ANY DAMAGES, INCLUDING WITHOUT LIMITATION ANY DIRECT, INDIRECT, CONSEQUENTIAL, SPECIAL, INCIDENTAL, OR PUNITIVE DAMAGES (INCLUDING FOR ANY LOSS OF GOODWILL, BUSINESS INTERRUPTION, LOST PROFITS OR DATA, OR COMPUTER FAILURE OR MALFUNCTION) ARISING FROM OR RELATING TO THE EXTERNAL DEPENDENCIES, HOWEVER CAUSED AND REGARDLESS OF THE THEORY OF LIABILITY, EVEN IF AMAZON HAS BEEN ADVISED OF THE POSSIBILITY OF SUCH DAMAGES. THESE LIMITATIONS AND DISCLAIMERS APPLY EXCEPT TO THE EXTENT PROHIBITED BY APPLICABLE LAW.
