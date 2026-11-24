"""Run before Qt/native package hooks and before the application imports."""
from anclicker.app.resource_bundle import bootstrap
bootstrap()
