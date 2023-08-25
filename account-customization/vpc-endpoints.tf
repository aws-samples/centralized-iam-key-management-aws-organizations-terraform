resource "aws_vpc_endpoint" "smtp" {
  count             = var.create_smtp_endpoint ? 1 : 0
  vpc_id            = var.vpc_id
  service_name      = "com.amazonaws.${data.aws_region.current.name}.email-smtp"
  vpc_endpoint_type = "Interface"
  security_group_ids = [
    aws_security_group.vpc_endpoint_sg[0].id
  ]
  subnet_ids          = [var.subnet_id]
  private_dns_enabled = true
}

resource "aws_vpc_endpoint" "ssm" {
  count             = var.create_ssm_endpoint ? 1 : 0
  vpc_id            = var.vpc_id
  service_name      = "com.amazonaws.${data.aws_region.current.name}.ssm"
  vpc_endpoint_type = "Interface"
  security_group_ids = [
    aws_security_group.vpc_endpoint_sg[0].id
  ]
  subnet_ids          = [var.subnet_id]
  private_dns_enabled = true
}

resource "aws_vpc_endpoint" "sts" {
  count             = var.create_sts_endpoint ? 1 : 0
  vpc_id            = var.vpc_id
  service_name      = "com.amazonaws.${data.aws_region.current.name}.sts"
  vpc_endpoint_type = "Interface"
  security_group_ids = [
    aws_security_group.vpc_endpoint_sg[0].id
  ]
  subnet_ids          = [var.subnet_id]
  private_dns_enabled = true
}

resource "aws_vpc_endpoint" "s3" {
  count             = var.create_s3_endpoint ? 1 : 0
  vpc_id            = var.vpc_id
  service_name      = "com.amazonaws.${data.aws_region.current.name}.s3"
  vpc_endpoint_type = "Gateway"
  security_group_ids = [
    aws_security_group.vpc_endpoint_sg[0].id
  ]
  private_dns_enabled = false
}

resource "aws_vpc_endpoint" "secretsmanager" {
  count             = var.create_secretsmanager_endpoint ? 1 : 0
  vpc_id            = var.vpc_id
  service_name      = "com.amazonaws.${data.aws_region.current.name}.secretsmanager"
  vpc_endpoint_type = "Interface"
  security_group_ids = [
    aws_security_group.vpc_endpoint_sg[0].id
  ]
  subnet_ids          = [var.subnet_id]
  private_dns_enabled = true
}