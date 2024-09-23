# ##############################################################################
# DynamoDB Table - Default
# ##############################################################################
resource "aws_dynamodb_table" "openfactcheck_default" {
  name = "openfactcheck-db-${terraform.workspace}-${var.aws_region}"

  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "PK"

  global_secondary_index {
    name            = "gs1"
    hash_key        = "GS1PK"
    projection_type = "ALL"
  }

  // ID
  attribute {
    name = "PK"
    type = "S"
  }

  // Type
  attribute {
    name = "GS1PK"
    type = "S"
  }

  tags = {
    Name = "OpenFactCheck - DynamoDB - ${terraform.workspace} - ${var.aws_region}"
  }
}
