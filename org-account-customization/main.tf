## IAM Role to list organization

resource "aws_iam_role" "org_list_role" {
  name               = var.org_list_role
  path               = "/"
  assume_role_policy = data.aws_iam_policy_document.org_list_assumerole_policy.json
}

resource "aws_iam_role_policy" "org_list_policy" {
  name   = "allow-list-account"
  role   = aws_iam_role.org_list_role.id
  policy = data.aws_iam_policy_document.allow_list_orgs_policy.json
}
