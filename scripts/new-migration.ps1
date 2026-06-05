param([Parameter(Mandatory=$true)][string]$Message)
alembic revision --autogenerate -m $Message
